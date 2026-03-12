#!/usr/bin/env python3
"""Latency Comparison: WebRAG vs Dataset RAG.

Measures per-question wall-clock latency for three approaches:
  - WebRAG (warm):  cached web content → GPT-4o-mini
  - WebRAG (cold):  re-fetch all 5 URLs per question → GPT-4o-mini
  - Dataset RAG:    ChromaDB retrieval → GPT-4o-mini

Scrapes all 5 source URLs once upfront, then benchmarks each approach
over N test questions. Reports mean/median/SD/p95/min/max and speedup
factors for direct comparison.

Usage:
    python scripts/latency_comparison.py --max-questions 5           # sanity check
    python scripts/latency_comparison.py --max-questions 100 --dataset human_rag
    python scripts/latency_comparison.py --skip-cold                 # skip per-Q cold scrape
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from statistics import mean, median, stdev
from typing import Optional

# ---------------------------------------------------------------------------
# Path setup & .env loading
# ---------------------------------------------------------------------------
_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ROOT))

_ENV_PATH = _ROOT / ".env"
if _ENV_PATH.exists():
    with open(_ENV_PATH) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _key, _val = _line.split("=", 1)
                os.environ.setdefault(_key.strip(), _val.strip())

_OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not _OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not set. Add it to .env or export it.")

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------
import chromadb
from chromadb.config import Settings
from openai import OpenAI

from shared.data_loader import load_ai_generated, load_human_curated
from shared.ragas_utils import load_test_set
from shared.web_scraper import SOURCE_URLS, build_web_context, fetch_all_urls, fetch_url

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MODEL_NAME = "gpt-4o-mini"
TEMPERATURE = 0.3
MAX_TOKENS = 300
TOP_K = 3

TEST_SET_PATH = _ROOT / "data" / "test_set" / "test_set_150q.xlsx"
RESULTS_DIR = _ROOT / "results" / "latency_comparison"

SYSTEM_PROMPT = (
    "You are a compassionate smoking cessation counselor. "
    "Answer questions concisely (2-4 sentences)."
)

ALL_DATASETS = ["human_rag", "ai_rag"]


# ---------------------------------------------------------------------------
# ChromaDB helpers (reused from ragas_evaluation.py pattern)
# ---------------------------------------------------------------------------


def _build_collection(
    chroma_client: chromadb.Client,
    name: str,
    qa_pairs: list[dict],
) -> chromadb.Collection:
    """Build an ephemeral ChromaDB collection from QA pairs."""
    try:
        chroma_client.delete_collection(name)
    except Exception:
        pass

    collection = chroma_client.create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"},
    )
    batch_size = 100
    for i in range(0, len(qa_pairs), batch_size):
        batch = qa_pairs[i : i + batch_size]
        documents = [f"Q: {p['question']}\nA: {p['answer']}" for p in batch]
        ids = [str(p.get("id", f"{name}_{i + j}")) for j, p in enumerate(batch)]
        metadatas = [{"question": p["question"], "answer": p["answer"]} for p in batch]
        collection.add(documents=documents, ids=ids, metadatas=metadatas)
    return collection


def _retrieve_contexts(
    collection: chromadb.Collection,
    query: str,
    n_results: int = TOP_K,
) -> list[str]:
    """Retrieve top-k context chunks via semantic similarity."""
    results = collection.query(query_texts=[query], n_results=n_results)
    if results["documents"] and results["documents"][0]:
        return list(results["documents"][0])
    return []


# ---------------------------------------------------------------------------
# Answer generation helpers
# ---------------------------------------------------------------------------


def _generate_answer_with_context(
    oai_client: OpenAI,
    question: str,
    context: str,
) -> str:
    """Generate an answer using the provided context string."""
    system_prompt = (
        "You are a compassionate smoking cessation counselor.\n"
        "Use the following knowledge base to answer questions.\n"
        "Base your answer on the knowledge provided.\n\n"
        f"KNOWLEDGE BASE:\n{context}"
    )
    try:
        response = oai_client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question},
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"  [WARN] Generation error: {e}")
        return ""


# ---------------------------------------------------------------------------
# Latency statistics helpers
# ---------------------------------------------------------------------------


def _latency_stats(times: list[float]) -> dict:
    """Compute descriptive statistics for a list of latency values (seconds).

    Args:
        times: List of per-question latency values in seconds.

    Returns:
        Dict with mean, median, sd, min, max, p95, n.
    """
    if not times:
        nan = float("nan")
        return {"mean": nan, "median": nan, "sd": nan, "min": nan, "max": nan, "p95": nan, "n": 0}

    sorted_times = sorted(times)
    n = len(sorted_times)
    p95_idx = min(int(n * 0.95), n - 1)

    return {
        "mean": round(mean(times), 4),
        "median": round(median(times), 4),
        "sd": round(stdev(times) if n > 1 else 0.0, 4),
        "min": round(sorted_times[0], 4),
        "max": round(sorted_times[-1], 4),
        "p95": round(sorted_times[p95_idx], 4),
        "n": n,
    }


def _speedup(baseline_mean: float, target_mean: float) -> Optional[float]:
    """Return speedup factor (how many times faster target is than baseline)."""
    if target_mean and target_mean > 0:
        return round(baseline_mean / target_mean, 2)
    return None


# ---------------------------------------------------------------------------
# Main benchmark
# ---------------------------------------------------------------------------


def run_latency_benchmark(
    max_questions: Optional[int],
    dataset: str,
    skip_cold: bool,
) -> dict:
    """Run the full latency benchmark.

    Args:
        max_questions: Cap on test questions (None = all 127).
        dataset: 'human_rag' or 'ai_rag' — which dataset to use for Dataset RAG.
        skip_cold: If True, skip the per-question cold-scrape measurements.

    Returns:
        Full results dict for JSON output.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    print("=" * 70)
    print("LATENCY COMPARISON: WebRAG vs Dataset RAG")
    print(f"Dataset: {dataset}  |  Questions: {max_questions or 127}  |  Skip-cold: {skip_cold}")
    print("=" * 70)

    # --- Load test set ---
    print(f"\nLoading test set from {TEST_SET_PATH.name}...")
    test_rows = load_test_set(TEST_SET_PATH, max_rows=max_questions)
    print(f"  Loaded {len(test_rows)} questions")

    # --- Load RAG dataset ---
    print(f"\nLoading {dataset} dataset...")
    if dataset == "human_rag":
        qa_pairs = load_human_curated()
    else:
        qa_pairs = load_ai_generated()
    print(f"  {len(qa_pairs):,} QA pairs")

    # --- Build ChromaDB collection ---
    print("\nBuilding ChromaDB collection...")
    chroma_client = chromadb.Client(Settings(anonymized_telemetry=False))
    collection = _build_collection(chroma_client, dataset, qa_pairs)
    print(f"  {collection.count()} docs indexed")

    # --- Initialize OpenAI client ---
    oai_client = OpenAI(api_key=_OPENAI_API_KEY)

    # --- Phase A: Cold scrape (fetch all URLs once upfront) ---
    print("\n" + "=" * 70)
    print("PHASE A: Cold scrape (fetch all 5 URLs upfront)")
    print("=" * 70)
    cold_results, cold_scrape_total = fetch_all_urls(SOURCE_URLS, sleep=1.0)
    cached_context = build_web_context(cold_results)
    successful_urls = sum(1 for r in cold_results if r["success"])
    print(f"\n  Total cold-scrape time: {cold_scrape_total:.2f}s")
    print(f"  Context length: {len(cached_context):,} chars from {successful_urls}/5 URLs")

    # Per-URL timing breakdown
    url_timings = [
        {"url": r["url"], "fetch_time_s": r["fetch_time_s"], "success": r["success"]}
        for r in cold_results
    ]

    # --- Phase B: Per-question comparison ---
    print("\n" + "=" * 70)
    print("PHASE B: Per-question latency comparison")
    print("=" * 70)

    # Storage for per-question timing data
    warm_web_rag_times: list[dict] = []    # assembly_time + generation_time
    cold_web_rag_times: list[dict] = []    # scrape_time + generation_time (if not skip_cold)
    dataset_rag_times: list[dict] = []     # retrieval_time + generation_time

    for i, row in enumerate(test_rows, 1):
        question = row["question"]
        print(f"\n[{i:3d}/{len(test_rows)}] {question[:55]}...")

        # --- WebRAG warm: use cached context, just track assembly + generation ---
        t0 = time.perf_counter()
        context_str = cached_context  # already built — measure only GPT call
        t1 = time.perf_counter()
        assembly_time = t1 - t0

        t1 = time.perf_counter()
        _generate_answer_with_context(oai_client, question, context_str)
        t2 = time.perf_counter()
        generation_time = t2 - t1

        warm_web_rag_times.append({
            "q_idx": i - 1,
            "assembly_time_s": round(assembly_time, 4),
            "generation_time_s": round(generation_time, 4),
            "total_time_s": round(assembly_time + generation_time, 4),
        })
        print(f"  WebRAG warm:  {assembly_time + generation_time:.3f}s "
              f"(assembly={assembly_time:.3f}s, gen={generation_time:.3f}s)")

        # --- WebRAG cold: re-fetch all URLs per question ---
        if not skip_cold:
            t0 = time.perf_counter()
            per_q_fetched, per_q_scrape = fetch_all_urls(SOURCE_URLS, sleep=0.5)
            t1 = time.perf_counter()
            per_q_context = build_web_context(per_q_fetched)
            scrape_total = per_q_scrape

            t1 = time.perf_counter()
            _generate_answer_with_context(oai_client, question, per_q_context)
            t2 = time.perf_counter()
            per_q_gen = t2 - t1

            cold_web_rag_times.append({
                "q_idx": i - 1,
                "scrape_time_s": round(scrape_total, 4),
                "generation_time_s": round(per_q_gen, 4),
                "total_time_s": round(scrape_total + per_q_gen, 4),
            })
            print(f"  WebRAG cold:  {scrape_total + per_q_gen:.3f}s "
                  f"(scrape={scrape_total:.3f}s, gen={per_q_gen:.3f}s)")

        # --- Dataset RAG: ChromaDB retrieval + generation ---
        t0 = time.perf_counter()
        contexts = _retrieve_contexts(collection, question)
        t1 = time.perf_counter()
        retrieval_time = t1 - t0

        rag_context = "\n\n".join(contexts)
        t1 = time.perf_counter()
        _generate_answer_with_context(oai_client, question, rag_context)
        t2 = time.perf_counter()
        rag_gen_time = t2 - t1

        dataset_rag_times.append({
            "q_idx": i - 1,
            "retrieval_time_s": round(retrieval_time, 4),
            "generation_time_s": round(rag_gen_time, 4),
            "total_time_s": round(retrieval_time + rag_gen_time, 4),
        })
        print(f"  Dataset RAG:  {retrieval_time + rag_gen_time:.3f}s "
              f"(retrieval={retrieval_time:.4f}s, gen={rag_gen_time:.3f}s)")

    # --- Aggregate statistics ---
    warm_totals = [r["total_time_s"] for r in warm_web_rag_times]
    cold_totals = [r["total_time_s"] for r in cold_web_rag_times]
    dataset_totals = [r["total_time_s"] for r in dataset_rag_times]

    warm_stats = _latency_stats(warm_totals)
    cold_stats = _latency_stats(cold_totals)
    dataset_stats = _latency_stats(dataset_totals)

    # Speedup: Dataset RAG vs WebRAG warm/cold
    speedup_vs_warm = _speedup(warm_stats["mean"], dataset_stats["mean"])
    speedup_vs_cold = _speedup(cold_stats["mean"], dataset_stats["mean"]) if cold_totals else None

    # --- Print summary ---
    print("\n" + "=" * 70)
    print("LATENCY SUMMARY")
    print("=" * 70)
    print(f"\n{'Method':<22} {'Mean':>8} {'Median':>8} {'SD':>8} {'p95':>8} {'n':>5}")
    print("-" * 60)
    print(f"{'WebRAG (warm)':<22} {warm_stats['mean']:>8.3f} {warm_stats['median']:>8.3f} "
          f"{warm_stats['sd']:>8.3f} {warm_stats['p95']:>8.3f} {warm_stats['n']:>5}")
    if cold_stats["n"] > 0:
        print(f"{'WebRAG (cold)':<22} {cold_stats['mean']:>8.3f} {cold_stats['median']:>8.3f} "
              f"{cold_stats['sd']:>8.3f} {cold_stats['p95']:>8.3f} {cold_stats['n']:>5}")
    print(f"{'Dataset RAG':<22} {dataset_stats['mean']:>8.3f} {dataset_stats['median']:>8.3f} "
          f"{dataset_stats['sd']:>8.3f} {dataset_stats['p95']:>8.3f} {dataset_stats['n']:>5}")
    print()
    print(f"Dataset RAG speedup vs WebRAG warm: {speedup_vs_warm}x")
    if speedup_vs_cold:
        print(f"Dataset RAG speedup vs WebRAG cold: {speedup_vs_cold}x")

    # --- Build output dict ---
    output = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "model": MODEL_NAME,
            "num_questions": len(test_rows),
            "dataset": dataset,
            "skip_cold": skip_cold,
            "source_urls": SOURCE_URLS,
            "cold_scrape_total_s": cold_scrape_total,
            "successful_url_fetches": successful_urls,
        },
        "url_timings": url_timings,
        "warm_web_rag": {
            "per_question": warm_web_rag_times,
            "stats": warm_stats,
        },
        "cold_web_rag": {
            "per_question": cold_web_rag_times,
            "stats": cold_stats,
        },
        "dataset_rag": {
            "per_question": dataset_rag_times,
            "stats": dataset_stats,
        },
        "speedup_dataset_vs_warm": speedup_vs_warm,
        "speedup_dataset_vs_cold": speedup_vs_cold,
    }

    # --- Save outputs ---
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    json_path = RESULTS_DIR / f"latency_{timestamp}.json"
    md_path = RESULTS_DIR / f"latency_{timestamp}.md"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    md_content = _format_markdown(output, dataset)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"\n{'=' * 70}")
    print(f"JSON saved: {json_path}")
    print(f"MD  saved:  {md_path}")
    print("=" * 70)

    return output


# ---------------------------------------------------------------------------
# Markdown formatting
# ---------------------------------------------------------------------------


def _format_markdown(output: dict, dataset: str) -> str:
    """Format latency results as a Markdown report."""
    meta = output["metadata"]
    warm = output["warm_web_rag"]["stats"]
    cold = output["cold_web_rag"]["stats"]
    dataset_s = output["dataset_rag"]["stats"]

    lines = [
        "# Latency Comparison: WebRAG vs Dataset RAG",
        "",
        f"**Generated:** {meta['generated_at']}",
        f"**Questions:** {meta['num_questions']}  |  **Dataset:** {dataset}  |  **Model:** {meta['model']}",
        f"**Cold-scrape total (Phase A):** {meta['cold_scrape_total_s']:.2f}s across {meta['successful_url_fetches']}/5 URLs",
        "",
        "## Table 3: Latency Comparison (seconds per question)",
        "",
        "| Method | Mean | Median | SD | p95 | Min | Max | n |",
        "|---|---|---|---|---|---|---|---|",
    ]

    def _row(label: str, s: dict) -> str:
        if s["n"] == 0:
            return f"| {label} | N/A | N/A | N/A | N/A | N/A | N/A | 0 |"
        return (
            f"| {label} | {s['mean']:.3f} | {s['median']:.3f} | "
            f"{s['sd']:.3f} | {s['p95']:.3f} | {s['min']:.3f} | {s['max']:.3f} | {s['n']} |"
        )

    lines.append(_row("WebRAG (warm, cached)", warm))
    if cold["n"] > 0:
        lines.append(_row("WebRAG (cold, per-Q scrape)", cold))
    lines.append(_row(f"Dataset RAG ({dataset})", dataset_s))

    lines += [
        "",
        "## Speedup Factors",
        "",
        f"- Dataset RAG vs WebRAG (warm): **{output['speedup_dataset_vs_warm']}x faster**",
    ]
    if output["speedup_dataset_vs_cold"] is not None:
        lines.append(
            f"- Dataset RAG vs WebRAG (cold): **{output['speedup_dataset_vs_cold']}x faster**"
        )

    lines += [
        "",
        "## URL Fetch Timing (Phase A)",
        "",
        "| URL | Fetch Time (s) | Success |",
        "|---|---|---|",
    ]
    for u in output["url_timings"]:
        domain = u["url"].split("/")[2]
        lines.append(f"| {domain} | {u['fetch_time_s']:.3f} | {'Yes' if u['success'] else 'No'} |")

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Latency comparison: WebRAG vs Dataset RAG"
    )
    parser.add_argument(
        "--max-questions",
        type=int,
        default=None,
        metavar="N",
        help="Cap test questions for sanity checks (default: all 127)",
    )
    parser.add_argument(
        "--dataset",
        choices=ALL_DATASETS,
        default="human_rag",
        help="Which dataset to use for Dataset RAG (default: human_rag)",
    )
    parser.add_argument(
        "--skip-cold",
        action="store_true",
        default=False,
        help="Skip cold (per-question) web scrape measurements",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    run_latency_benchmark(
        max_questions=args.max_questions,
        dataset=args.dataset,
        skip_cold=args.skip_cold,
    )
