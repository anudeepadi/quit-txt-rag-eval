#!/usr/bin/env python3
"""Retry-only script for ContextPrecision on human_rag + web_rag.

The main ragas_evaluation.py run (20260411_210513) produced NaN for
context_precision on human_rag/web_rag because RAGAS batches all 100
samples into one burst, which exceeds gpt-4o-mini's 200K TPM limit when
contexts are long (~500-1000+ tokens each). ai_rag contexts were short
enough to fit.

This script:
  1. Loads existing checkpoints (answers + retrieved_contexts already cached)
  2. Loads test set (ground_truth / reference)
  3. Calls ContextPrecision.score() one sample at a time for human_rag
     and web_rag, with an explicit pacing sleep between calls.
  4. Writes a patched copy of the results JSON with the filled-in scores.

Usage:
    python scripts/retry_context_precision.py \\
        --source-json results/ragas_evaluation/ragas_eval_concise_20260411_210513.json \\
        --sleep 3.0
"""

from __future__ import annotations

import argparse
import json
import math
import os
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path

_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ROOT))

_ENV_PATH = _ROOT / ".env"
if _ENV_PATH.exists() and _ENV_PATH.is_file():
    for _line in _ENV_PATH.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            k, v = _line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

_OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not _OPENAI_API_KEY:
    raise SystemExit("OPENAI_API_KEY not set. Export it or add it to .env.")

from openai import AsyncOpenAI
from ragas.llms import llm_factory
from ragas.metrics.collections import ContextPrecision

from shared.ragas_utils import load_test_set

MODEL_NAME = "gpt-4o-mini"
TEST_SET_PATH = _ROOT / "data" / "test_set" / "test_set_150q.xlsx"
CHECKPOINT_DIR = _ROOT / "results" / "ragas_evaluation"
DEFAULT_CONFIGS = ("human_rag", "web_rag")


def _load_checkpoint(config: str, n: int) -> list[dict]:
    """Load the 100-question checkpoint (the only one that exists) and slice to n."""
    path = CHECKPOINT_DIR / f"checkpoint_concise_{config}_100.jsonl"
    if not path.exists():
        raise FileNotFoundError(f"checkpoint missing: {path}")
    records = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    return records[:n]


def _score_config(
    metric: ContextPrecision,
    records: list[dict],
    sleep_seconds: float,
    label: str,
) -> list[float]:
    nan = float("nan")
    scores: list[float] = []
    for i, rec in enumerate(records, 1):
        try:
            result = metric.score(
                user_input=rec["question"],
                reference=rec["ground_truth"],
                retrieved_contexts=rec.get("contexts", []),
            )
            # Note: don't use `if result and ...` — MetricResult.__bool__ falls
            # back to __len__, which raises TypeError on scalar float values.
            raw = result.value if result is not None else None
            value = float(raw) if raw is not None else nan
        except Exception as exc:
            print(f"  [{label} {i:3d}/{len(records)}] ERROR: {type(exc).__name__}: {exc}")
            value = nan
        scores.append(value)
        good = "" if math.isnan(value) else f"{value:.3f}"
        print(f"  [{label} {i:3d}/{len(records)}] {good or 'NaN'}")
        if i < len(records):
            time.sleep(sleep_seconds)
    return scores


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-json", type=Path, required=True)
    parser.add_argument("--n", type=int, default=100)
    parser.add_argument("--sleep", type=float, default=3.0,
                        help="Seconds to sleep between per-sample score() calls.")
    parser.add_argument("--configs", nargs="+", default=list(DEFAULT_CONFIGS))
    parser.add_argument("--output-json", type=Path, default=None,
                        help="Where to write the patched results JSON. "
                             "Defaults to <source>.ctxprec_patched.json")
    args = parser.parse_args()

    source_path = args.source_json
    if not source_path.exists():
        raise SystemExit(f"source JSON not found: {source_path}")

    out_path = args.output_json or source_path.with_suffix(".ctxprec_patched.json")

    print(f"Source:  {source_path}")
    print(f"Output:  {out_path}")
    print(f"Configs: {args.configs}")
    print(f"Sleep:   {args.sleep}s between samples")

    source = json.loads(source_path.read_text())

    # Verify test set aligns with checkpoint q_idx
    test_rows = load_test_set(TEST_SET_PATH)[: args.n]
    print(f"Test set: {len(test_rows)} questions")

    async_oai = AsyncOpenAI(api_key=_OPENAI_API_KEY)
    ragas_llm = llm_factory(MODEL_NAME, provider="openai", client=async_oai, max_tokens=8192)
    metric = ContextPrecision(llm=ragas_llm)

    for cfg in args.configs:
        print(f"\n=== {cfg} ===")
        records = _load_checkpoint(cfg, args.n)
        if len(records) != args.n:
            print(f"  [WARN] checkpoint has {len(records)} records, expected {args.n}")
        start = time.time()
        scores = _score_config(metric, records, args.sleep, cfg)
        elapsed = time.time() - start

        valid = [v for v in scores if not math.isnan(v)]
        nan_count = len(scores) - len(valid)
        mean = statistics.mean(valid) if valid else float("nan")
        sd = statistics.stdev(valid) if len(valid) > 1 else 0.0
        print(f"  -> mean={mean:.3f} sd={sd:.3f} valid={len(valid)}/{len(scores)} "
              f"nan={nan_count} time={elapsed:.0f}s")

        source["all_scores"][cfg]["context_precision"] = scores

    source.setdefault("metadata", {})["context_precision_patched_at"] = (
        datetime.now().isoformat()
    )
    source["metadata"]["context_precision_patched_configs"] = list(args.configs)

    out_path.write_text(json.dumps(source, indent=2))
    print(f"\nWrote patched JSON -> {out_path}")


if __name__ == "__main__":
    main()
