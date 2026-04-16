"""RAGAS evaluation utilities.

Provides helpers for loading the LFV-reviewed test set,
computing faithfulness statistics matching Ebrahim's table columns,
and formatting comparison tables as Markdown.
"""

import math
import statistics
from pathlib import Path
from typing import Optional

import openpyxl


# ---------------------------------------------------------------------------
# Excel column indices (1-based, matching the actual spreadsheet)
# ---------------------------------------------------------------------------
_COL_QUESTION = 1
_COL_ANSWER = 2
_COL_COMMENTS_LFV = 83


def load_test_set(excel_path: Path, max_rows: Optional[int] = None) -> list[dict]:
    """Load the LFV-reviewed test set from Excel, returning only clean rows.

    Skips any row where the 'Comments LFV' column (col 83) is non-empty,
    which matches the manual review criteria (23 flagged, 127 clean).

    Args:
        excel_path: Path to the 150_qa_testset.xlsx file.
        max_rows: Optional cap on the number of rows returned (for sanity checks).

    Returns:
        List of dicts with keys 'question' and 'ground_truth'.
    """
    wb = openpyxl.load_workbook(excel_path, read_only=True, data_only=True)
    ws = wb.active

    rows = []
    for row_idx in range(2, ws.max_row + 1):  # skip header row
        question = ws.cell(row=row_idx, column=_COL_QUESTION).value
        answer = ws.cell(row=row_idx, column=_COL_ANSWER).value
        comment = ws.cell(row=row_idx, column=_COL_COMMENTS_LFV).value

        # Skip empty rows and flagged rows
        if question is None:
            continue
        has_comment = comment is not None and str(comment).strip()
        if has_comment:
            continue

        rows.append(
            {
                "question": str(question).strip(),
                "ground_truth": str(answer).strip() if answer else "",
            }
        )

        if max_rows is not None and len(rows) >= max_rows:
            break

    wb.close()
    return rows


def compute_faithfulness_stats(scores: list[float]) -> dict:
    """Compute summary statistics for a list of faithfulness scores.

    Matches the columns in Ebrahim's reference table:
    Mean | SD | Median | 95% CI | Hallucination Rate | % High-Risk (<0.5) | n

    Args:
        scores: List of per-question faithfulness scores in [0, 1].

    Returns:
        Dict with keys: mean, sd, median, ci_lower, ci_upper,
        hallucination_rate, pct_high_risk, n.
    """
    # Filter out NaN values before computing statistics
    valid = [s for s in scores if s == s and not math.isnan(s)]
    n = len(valid)
    if n == 0:
        return {
            "mean": float("nan"),
            "sd": float("nan"),
            "median": float("nan"),
            "ci_lower": float("nan"),
            "ci_upper": float("nan"),
            "hallucination_rate": float("nan"),
            "pct_high_risk": float("nan"),
            "n": 0,
        }

    mean = statistics.mean(valid)
    sd = statistics.stdev(valid) if n > 1 else 0.0
    median = statistics.median(valid)

    # 95% CI using t-distribution approximation (z=1.96 for large n)
    se = sd / math.sqrt(n)
    z = 1.96
    ci_lower = max(0.0, mean - z * se)
    ci_upper = min(1.0, mean + z * se)

    hallucination_rate = 1.0 - mean
    high_risk_count = sum(1 for s in valid if s < 0.5)
    pct_high_risk = high_risk_count / n * 100

    return {
        "mean": round(mean, 4),
        "sd": round(sd, 4),
        "median": round(median, 4),
        "ci_lower": round(ci_lower, 4),
        "ci_upper": round(ci_upper, 4),
        "hallucination_rate": round(hallucination_rate, 4),
        "pct_high_risk": round(pct_high_risk, 1),
        "n": n,
    }


def compute_metric_stats(scores: list[float]) -> dict:
    """Compute mean and SD for any RAGAS metric (handles NaN scores).

    Args:
        scores: Per-question metric scores (may include float('nan')).

    Returns:
        Dict with keys: mean, sd, n_valid.
    """
    valid = [s for s in scores if not (s != s)]  # filter NaN
    n_valid = len(valid)
    if n_valid == 0:
        return {"mean": float("nan"), "sd": float("nan"), "n_valid": 0}
    mean = statistics.mean(valid)
    sd = statistics.stdev(valid) if n_valid > 1 else 0.0
    return {"mean": round(mean, 4), "sd": round(sd, 4), "n_valid": n_valid}


def format_results_markdown(
    config_stats: dict,
    ebrahim_reference: list[dict],
    full_metrics: dict,
) -> str:
    """Format results as Markdown tables for the paper.

    Args:
        config_stats: Dict mapping config name -> faithfulness stats dict.
        ebrahim_reference: List of Ebrahim's rows as reference (pre-formatted).
        full_metrics: Dict mapping config name -> {metric: [scores]} for all metrics.

    Returns:
        Markdown string with two tables: faithfulness summary + full RAGAS metrics.
    """
    lines = []

    # ------------------------------------------------------------------
    # Table 1: Faithfulness summary (matches Ebrahim's exact columns)
    # ------------------------------------------------------------------
    lines.append("## Faithfulness Summary (Comparison with Ebrahim's Results)")
    lines.append("")
    header = (
        "| Configuration | Mean | SD | Median | 95% CI | "
        "Hallucination Rate | % High-Risk (<0.5) | n |"
    )
    sep = "|---|---|---|---|---|---|---|---|"
    lines.append(header)
    lines.append(sep)

    # Ebrahim reference rows first
    for row in ebrahim_reference:
        lines.append(
            f"| {row['config']} | {row['mean']:.2f} | {row['sd']:.2f} | "
            f"{row['median']:.2f} | [{row['ci_lower']:.2f}–{row['ci_upper']:.2f}] | "
            f"{row['hallucination_rate']:.2f} | {row['pct_high_risk']:.0f}% | {row['n']} |"
        )

    # Our results
    config_labels = {
        "baseline": "Ours: Baseline",
        "ai_rag": "Ours: AI-Generated RAG",
        "human_rag": "Ours: Human-Curated RAG",
    }
    for config_key, label in config_labels.items():
        if config_key not in config_stats:
            continue
        s = config_stats[config_key]
        if s["n"] == 0 or s["mean"] != s["mean"]:  # NaN check
            lines.append(f"| {label} | N/A | N/A | N/A | N/A | N/A | N/A | 0 |")
        else:
            lines.append(
                f"| {label} | {s['mean']:.2f} | {s['sd']:.2f} | "
                f"{s['median']:.2f} | [{s['ci_lower']:.2f}–{s['ci_upper']:.2f}] | "
                f"{s['hallucination_rate']:.2f} | {s['pct_high_risk']:.0f}% | {s['n']} |"
            )

    lines.append("")

    # ------------------------------------------------------------------
    # Table 2: Full RAGAS metrics across all configs
    # ------------------------------------------------------------------
    lines.append("## Full RAGAS Metrics")
    lines.append("")
    lines.append(
        "| Configuration | Faithfulness | Answer Relevancy | "
        "Context Precision | Context Recall |"
    )
    lines.append("|---|---|---|---|---|")

    for config_key, label in config_labels.items():
        if config_key not in full_metrics:
            continue
        fm = full_metrics[config_key]

        def _fmt(metric_key: str) -> str:
            stats = compute_metric_stats(fm.get(metric_key, []))
            if stats["n_valid"] == 0:
                return "N/A"
            return f"{stats['mean']:.3f} ± {stats['sd']:.3f}"

        lines.append(
            f"| {label} | {_fmt('faithfulness')} | {_fmt('answer_relevancy')} | "
            f"{_fmt('context_precision')} | {_fmt('context_recall')} |"
        )

    return "\n".join(lines)
