#!/usr/bin/env python3
"""Run concise RAGAS evaluation for the generated web-source KB in isolation."""

import argparse
import importlib.util
import json
import os
from datetime import datetime
from pathlib import Path


CODE_ROOT = Path(__file__).parent.parent
PROJECT_ROOT = CODE_ROOT.parent
DATASET = PROJECT_ROOT / "datasets" / "web-source" / "web_source_generated_qa.jsonl"
RESULTS_DIR = CODE_ROOT / "results" / "web_source_ragas"


def load_evaluator():
    path = Path(__file__).with_name("ragas_evaluation.py")
    spec = importlib.util.spec_from_file_location("ragas_evaluation", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def main(max_questions: int, resume: bool, split: str = "test") -> Path:
    if not DATASET.exists():
        raise FileNotFoundError(f"Generated web-source KB missing: {DATASET}")

    # The shared loader honors this process-local override. The evaluator's
    # ai_rag label is retained internally, while checkpoints/results are moved
    # to a dedicated namespace below.
    os.environ["AI_QA_JSONL"] = str(DATASET)
    evaluator = load_evaluator()
    evaluator.RESULTS_DIR = RESULTS_DIR / "raw"
    original_checkpoint_path = evaluator._checkpoint_path
    evaluator._checkpoint_path = lambda _config, count, concise: original_checkpoint_path(
        "web_source_rag", count, concise
    )

    raw_result = evaluator.run_evaluation(
        configs=["ai_rag"],
        max_questions=max_questions,
        resume=resume,
        concise=True,
        split=split,
    )
    # Relabel EVERY ai_rag-keyed section, not just faithfulness_stats. Leaving
    # all_scores under "ai_rag" made this run look like the AI KB to anything
    # keying off the config name, which silently corrupts cross-run comparisons.
    for section in ("faithfulness_stats", "all_scores", "full_metrics"):
        block = raw_result.get(section)
        if isinstance(block, dict) and "ai_rag" in block:
            block["web_source_rag"] = block.pop("ai_rag")

    raw_result["metadata"]["configs_run"] = ["web_source_rag"]
    raw_result["metadata"]["dataset_path"] = str(DATASET)
    raw_result["metadata"]["dataset_size"] = sum(
        1 for line in DATASET.read_text(encoding="utf-8").splitlines() if line.strip()
    )

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    output = RESULTS_DIR / f"web_source_ragas_concise_n{max_questions}_{datetime.now():%Y%m%d_%H%M%S}.json"
    output.write_text(json.dumps(raw_result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Web-source result saved: {output}")
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-questions", type=int, default=None,
                        help="Cap questions (default: whole split)")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--split", choices=["test", "dev", "full"], default="test",
                        help="Question set (default: frozen test split)")
    args = parser.parse_args()
    main(args.max_questions, args.resume, args.split)
