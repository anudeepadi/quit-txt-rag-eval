#!/usr/bin/env python3
"""Combine RAGAS and latency results into a single paper-ready table.

Reads the most recent output JSON from each experiment directory and
produces a single Markdown document with:
  - Table 1: Faithfulness comparison (Ibrahim's format)
  - Table 2: Full RAGAS metrics (4 metrics)
  - Table 3: Latency comparison
  - Key findings summary

Usage:
    python scripts/combine_results_table.py
    python scripts/combine_results_table.py --ragas PATH --latency PATH
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ROOT))

RAGAS_DIR = _ROOT / "results" / "ragas_evaluation"
LATENCY_DIR = _ROOT / "results" / "latency_comparison"
OUTPUT_DIR = _ROOT / "results" / "combined_results"


# ---------------------------------------------------------------------------
# File discovery helpers
# ---------------------------------------------------------------------------


def _latest_json(directory: Path, prefix: str = "") -> Path:
    """Return the most recently modified JSON file matching the prefix.

    Args:
        directory: Directory to search.
        prefix: Optional filename prefix filter.

    Returns:
        Path to the most recently modified matching JSON.

    Raises:
        FileNotFoundError: If no matching files exist.
    """
    candidates = sorted(
        [p for p in directory.glob(f"{prefix}*.json") if not p.name.startswith("checkpoint")],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        raise FileNotFoundError(
            f"No {prefix}*.json files found in {directory}. "
            "Run the evaluation scripts first."
        )
    return candidates[0]


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------


def _fmt_stat(value: float, decimals: int = 2) -> str:
    """Format a float stat, returning 'N/A' for NaN."""
    if value != value:  # NaN check
        return "N/A"
    return f"{value:.{decimals}f}"


def _faithfulness_table(ragas_data: dict) -> str:
    """Render Table 1: faithfulness comparison (Ibrahim's format)."""
    lines = [
        "## Table 1: Faithfulness Comparison",
        "",
        "| Configuration | Mean | SD | Median | 95% CI | Hallucination Rate | % High-Risk (<0.5) | n |",
        "|---|---|---|---|---|---|---|---|",
    ]

    # Ibrahim's reference rows
    for ref in ragas_data.get("ebrahim_reference", []):
        ci = f"[{_fmt_stat(ref['ci_lower'])}–{_fmt_stat(ref['ci_upper'])}]"
        lines.append(
            f"| {ref['config']} | {_fmt_stat(ref['mean'])} | {_fmt_stat(ref['sd'])} | "
            f"{_fmt_stat(ref['median'])} | {ci} | {_fmt_stat(ref['hallucination_rate'])} | "
            f"{int(ref['pct_high_risk'])}% | {ref['n']} |"
        )

    # Our results
    label_map = {
        "baseline": "Ours: Baseline LLM",
        "ai_rag": "Ours: AI-Generated RAG",
        "human_rag": "Ours: Human-Curated RAG",
    }
    stats = ragas_data.get("faithfulness_stats", {})
    for key, label in label_map.items():
        if key not in stats:
            continue
        s = stats[key]
        if s.get("n", 0) == 0:
            lines.append(f"| {label} | N/A | N/A | N/A | N/A | N/A | N/A | 0 |")
        else:
            ci = f"[{_fmt_stat(s['ci_lower'])}–{_fmt_stat(s['ci_upper'])}]"
            lines.append(
                f"| {label} | {_fmt_stat(s['mean'])} | {_fmt_stat(s['sd'])} | "
                f"{_fmt_stat(s['median'])} | {ci} | {_fmt_stat(s['hallucination_rate'])} | "
                f"{_fmt_stat(s['pct_high_risk'], 1)}% | {s['n']} |"
            )

    return "\n".join(lines)


def _full_ragas_table(ragas_data: dict) -> str:
    """Render Table 2: all four RAGAS metrics."""
    from shared.ragas_utils import compute_metric_stats

    lines = [
        "## Table 2: Full RAGAS Metrics",
        "",
        "| Configuration | Faithfulness | Answer Relevancy | Context Precision | Context Recall |",
        "|---|---|---|---|---|",
    ]

    label_map = {
        "baseline": "Baseline LLM",
        "ai_rag": "AI-Generated RAG",
        "human_rag": "Human-Curated RAG",
    }
    all_scores = ragas_data.get("all_scores", {})

    for key, label in label_map.items():
        if key not in all_scores:
            continue
        fm = all_scores[key]

        def _fmt(metric: str) -> str:
            s = compute_metric_stats(fm.get(metric, []))
            if s["n_valid"] == 0:
                return "N/A"
            return f"{s['mean']:.3f} ± {s['sd']:.3f}"

        lines.append(
            f"| {label} | {_fmt('faithfulness')} | {_fmt('answer_relevancy')} | "
            f"{_fmt('context_precision')} | {_fmt('context_recall')} |"
        )

    return "\n".join(lines)


def _latency_table(latency_data: dict) -> str:
    """Render Table 3: latency comparison."""
    dataset = latency_data.get("metadata", {}).get("dataset", "?")

    lines = [
        "## Table 3: Latency Comparison (seconds per question)",
        "",
        "| Method | Mean | Median | SD | p95 | n |",
        "|---|---|---|---|---|---|",
    ]

    def _row(label: str, s: dict) -> str:
        if s.get("n", 0) == 0:
            return f"| {label} | N/A | N/A | N/A | N/A | 0 |"
        return (
            f"| {label} | {s['mean']:.3f} | {s['median']:.3f} | "
            f"{s['sd']:.3f} | {s['p95']:.3f} | {s['n']} |"
        )

    warm = latency_data.get("warm_web_rag", {}).get("stats", {})
    cold = latency_data.get("cold_web_rag", {}).get("stats", {})
    dataset_s = latency_data.get("dataset_rag", {}).get("stats", {})

    lines.append(_row("WebRAG (warm, cached)", warm))
    if cold.get("n", 0) > 0:
        lines.append(_row("WebRAG (cold, per-Q scrape)", cold))
    lines.append(_row(f"Dataset RAG ({dataset})", dataset_s))

    speedup_warm = latency_data.get("speedup_dataset_vs_warm")
    speedup_cold = latency_data.get("speedup_dataset_vs_cold")
    lines += ["", "**Speedup factors:**"]
    if speedup_warm:
        lines.append(f"- Dataset RAG vs WebRAG (warm): **{speedup_warm}x faster**")
    if speedup_cold:
        lines.append(f"- Dataset RAG vs WebRAG (cold): **{speedup_cold}x faster**")

    return "\n".join(lines)


def _key_findings(ragas_data: dict, latency_data: dict) -> str:
    """Generate a brief key findings section."""
    lines = ["## Key Findings", ""]

    # Faithfulness comparison
    stats = ragas_data.get("faithfulness_stats", {})
    refs = {r["config"]: r for r in ragas_data.get("ebrahim_reference", [])}

    ibr_webrag = None
    for key, val in refs.items():
        if "WebRAG" in key or "webrag" in key.lower():
            ibr_webrag = val

    human_rag = stats.get("human_rag")
    ai_rag = stats.get("ai_rag")
    baseline = stats.get("baseline")

    if human_rag and human_rag.get("n", 0) > 0:
        lines.append(
            f"- **Human-Curated RAG faithfulness:** {human_rag['mean']:.2f} "
            f"(SD={human_rag['sd']:.2f}, n={human_rag['n']})"
        )
    if ai_rag and ai_rag.get("n", 0) > 0:
        lines.append(
            f"- **AI-Generated RAG faithfulness:** {ai_rag['mean']:.2f} "
            f"(SD={ai_rag['sd']:.2f}, n={ai_rag['n']})"
        )
    if baseline and baseline.get("n", 0) > 0:
        lines.append(
            f"- **Baseline LLM faithfulness:** {baseline['mean']:.2f} "
            f"(SD={baseline['sd']:.2f}, n={baseline['n']})"
        )
    if ibr_webrag:
        lines.append(
            f"- **Ibrahim's WebRAG reference:** {ibr_webrag['mean']:.2f} "
            f"(n={ibr_webrag['n']})"
        )

    # Latency
    speedup_warm = latency_data.get("speedup_dataset_vs_warm")
    speedup_cold = latency_data.get("speedup_dataset_vs_cold")
    dataset = latency_data.get("metadata", {}).get("dataset", "?")
    latency_n = latency_data.get("dataset_rag", {}).get("stats", {}).get("n", 0)

    if latency_n > 0:
        ds_mean = latency_data["dataset_rag"]["stats"]["mean"]
        lines.append(
            f"- **Dataset RAG latency ({dataset}):** {ds_mean:.3f}s/question (n={latency_n})"
        )
    if speedup_warm:
        lines.append(f"- **Speedup vs WebRAG (warm):** {speedup_warm}x faster")
    if speedup_cold:
        lines.append(f"- **Speedup vs WebRAG (cold):** {speedup_cold}x faster")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def _merge_ragas_data(primary: dict, extras: list[dict]) -> dict:
    """Merge faithfulness_stats and all_scores from extra RAGAS JSONs into primary.

    Useful when different configs were scored in separate runs due to rate limits.
    Extra JSON stats overwrite primary stats for the same config key ONLY if
    the extra has valid data (n > 0) and primary does not (n == 0).

    Args:
        primary: Primary RAGAS JSON data dict.
        extras: List of additional RAGAS JSON data dicts to merge from.

    Returns:
        New merged dict (primary is not mutated).
    """
    import copy
    merged = copy.deepcopy(primary)

    for extra in extras:
        extra_stats = extra.get("faithfulness_stats", {})
        extra_scores = extra.get("all_scores", {})

        for config_key, stats in extra_stats.items():
            # Overwrite if extra has valid data and primary is missing/empty
            primary_n = merged.get("faithfulness_stats", {}).get(config_key, {}).get("n", 0)
            extra_n = stats.get("n", 0)
            if extra_n > 0 and primary_n == 0:
                merged.setdefault("faithfulness_stats", {})[config_key] = stats
                print(f"  Merged {config_key} faithfulness from extra JSON (n={extra_n})")

        for config_key, scores in extra_scores.items():
            primary_n = len([s for s in merged.get("all_scores", {}).get(config_key, {}).get("faithfulness", []) if s == s])
            extra_valid = sum(1 for s in scores.get("faithfulness", []) if s == s)
            if extra_valid > 0 and primary_n == 0:
                merged.setdefault("all_scores", {})[config_key] = scores
                print(f"  Merged {config_key} scores from extra JSON")

    return merged


def combine(
    ragas_path: Path,
    latency_path: Path,
    extra_ragas_paths: Optional[list[Path]] = None,
) -> Path:
    """Load both result JSONs and produce the combined Markdown.

    Args:
        ragas_path: Path to primary RAGAS evaluation JSON.
        latency_path: Path to latency comparison JSON.
        extra_ragas_paths: Optional additional RAGAS JSONs to merge into primary.

    Returns:
        Path to the written combined Markdown file.
    """
    print(f"Loading RAGAS results:   {ragas_path}")
    print(f"Loading latency results: {latency_path}")

    with open(ragas_path, encoding="utf-8") as f:
        ragas_data = json.load(f)
    with open(latency_path, encoding="utf-8") as f:
        latency_data = json.load(f)

    if extra_ragas_paths:
        extras = []
        for p in extra_ragas_paths:
            print(f"Loading extra RAGAS:     {p}")
            with open(p, encoding="utf-8") as f:
                extras.append(json.load(f))
        ragas_data = _merge_ragas_data(ragas_data, extras)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    ragas_meta = ragas_data.get("metadata", {})
    lat_meta = latency_data.get("metadata", {})

    sections = [
        "# Combined Results: AI-Generated vs Human-Curated RAG",
        "",
        f"**Generated:** {datetime.now().isoformat()}",
        f"**RAGAS source:** `{ragas_path.name}` (n={ragas_meta.get('num_questions', '?')})",
        f"**Latency source:** `{latency_path.name}` (n={lat_meta.get('num_questions', '?')})",
        "",
        _faithfulness_table(ragas_data),
        "",
        _full_ragas_table(ragas_data),
        "",
        _latency_table(latency_data),
        "",
        _key_findings(ragas_data, latency_data),
        "",
    ]

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / f"combined_{timestamp}.md"
    out_path.write_text("\n".join(sections), encoding="utf-8")

    print(f"\nCombined Markdown saved: {out_path}")
    return out_path


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Combine RAGAS and latency results into a paper-ready table"
    )
    parser.add_argument(
        "--ragas",
        type=Path,
        default=None,
        help="Path to primary RAGAS evaluation JSON (default: latest in results/ragas_evaluation/)",
    )
    parser.add_argument(
        "--ragas-extra",
        type=Path,
        nargs="+",
        default=None,
        metavar="PATH",
        help="Additional RAGAS JSON files to merge (fills in missing config slots)",
    )
    parser.add_argument(
        "--latency",
        type=Path,
        default=None,
        help="Path to latency comparison JSON (default: latest in results/latency_comparison/)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()

    ragas_path = args.ragas or _latest_json(RAGAS_DIR, "ragas_eval")
    latency_path = args.latency or _latest_json(LATENCY_DIR, "latency")

    combine(ragas_path, latency_path, extra_ragas_paths=args.ragas_extra)
