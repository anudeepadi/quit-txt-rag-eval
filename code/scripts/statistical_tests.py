#!/usr/bin/env python3
"""Statistical Significance Tests for RAG Evaluation.

Loads per-question scores from RAGAS evaluation results and checkpoint files,
then runs paired Wilcoxon signed-rank tests between all configuration pairs.
Also computes bootstrap 95% confidence intervals and effect sizes (Cliff's delta).

This addresses a key methodological gap: determining whether differences between
human_rag, ai_rag, web_rag, and baseline are statistically significant.

Usage:
    python scripts/statistical_tests.py                             # all pairs
    python scripts/statistical_tests.py --configs baseline human_rag ai_rag
    python scripts/statistical_tests.py --metric faithfulness
"""

import argparse
import json
import os
import sys
from datetime import datetime
from itertools import combinations
from pathlib import Path
from statistics import mean, stdev, median

import numpy as np

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ROOT))

RESULTS_DIR = _ROOT / "results" / "ragas_evaluation"
OUTPUT_DIR = _ROOT / "results" / "statistical_tests"

ALL_CONFIGS = ["baseline", "ai_rag", "human_rag", "web_rag"]
METRICS = ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


def load_ragas_scores(results_json: Path | None = None) -> dict[str, dict[str, list[float]]]:
    """Load per-question RAGAS scores, merging across result files if needed.

    When results are split across multiple files (e.g. baseline in one run,
    RAG configs in another), this merges all recent concise result files to
    build a complete picture.

    Args:
        results_json: Explicit path to results JSON. If None, merges all
            recent concise result files.

    Returns:
        Dict mapping config -> metric -> list of per-question scores.
    """
    if results_json is not None:
        print(f"Loading RAGAS scores from: {results_json.name}")
        with open(results_json, encoding="utf-8") as f:
            data = json.load(f)
        return data.get("all_scores", {})

    # Merge scores from all concise result files
    candidates = sorted(RESULTS_DIR.glob("ragas_eval_concise_*.json"))
    if not candidates:
        candidates = sorted(RESULTS_DIR.glob("ragas_eval_*.json"))
    if not candidates:
        raise FileNotFoundError(f"No RAGAS results found in {RESULTS_DIR}")

    merged: dict[str, dict[str, list[float]]] = {}
    for path in candidates:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        file_scores = data.get("all_scores", {})
        for config, metrics in file_scores.items():
            # Only keep configs with real data (skip all-NaN entries)
            has_data = any(
                any(v == v for v in vals)  # v != v means NaN
                for vals in metrics.values()
            )
            if has_data and config not in merged:
                merged[config] = metrics
                print(f"  Loaded {config} from {path.name}")

    if not merged:
        raise FileNotFoundError("No valid RAGAS scores found across result files")

    return merged


def load_bertscore_results() -> dict[str, list[float]]:
    """Load BERTScore F1 per-question scores if available.

    Returns:
        Dict mapping config -> list of per-question F1 scores.
    """
    bertscore_dir = _ROOT / "results" / "bertscore"
    candidates = sorted(bertscore_dir.glob("bertscore_*.json"))
    if not candidates:
        return {}

    latest = candidates[-1]
    print(f"Loading BERTScore from: {latest.name}")

    with open(latest, encoding="utf-8") as f:
        data = json.load(f)

    result = {}
    for config, scores in data.get("results", {}).items():
        if "per_question_f1" in scores:
            result[config] = scores["per_question_f1"]
    return result


# ---------------------------------------------------------------------------
# Statistical tests
# ---------------------------------------------------------------------------


def wilcoxon_test(x: list[float], y: list[float]) -> dict:
    """Run paired Wilcoxon signed-rank test.

    Args:
        x: Scores for config A.
        y: Scores for config B (same length, same question order).

    Returns:
        Dict with statistic, p_value, n_valid, and significance assessment.
    """
    from scipy.stats import wilcoxon

    # Filter out NaN pairs
    pairs = [(a, b) for a, b in zip(x, y) if not (np.isnan(a) or np.isnan(b))]
    if len(pairs) < 5:
        return {
            "statistic": None,
            "p_value": None,
            "n_valid": len(pairs),
            "significant_005": None,
            "significant_001": None,
            "note": "Too few valid pairs for test",
        }

    x_clean = [p[0] for p in pairs]
    y_clean = [p[1] for p in pairs]

    # Check if all differences are zero
    diffs = [a - b for a, b in pairs]
    if all(d == 0 for d in diffs):
        return {
            "statistic": 0,
            "p_value": 1.0,
            "n_valid": len(pairs),
            "significant_005": False,
            "significant_001": False,
            "note": "All differences are zero",
        }

    try:
        stat, p_val = wilcoxon(x_clean, y_clean, alternative="two-sided")
        return {
            "statistic": float(stat),
            "p_value": float(p_val),
            "n_valid": len(pairs),
            "significant_005": p_val < 0.05,
            "significant_001": p_val < 0.01,
        }
    except Exception as e:
        return {
            "statistic": None,
            "p_value": None,
            "n_valid": len(pairs),
            "significant_005": None,
            "significant_001": None,
            "note": str(e),
        }


def cliffs_delta(x: list[float], y: list[float]) -> dict:
    """Compute Cliff's delta effect size.

    Cliff's delta ranges from -1 to +1:
      |d| < 0.147: negligible
      |d| < 0.33: small
      |d| < 0.474: medium
      |d| >= 0.474: large

    Args:
        x: Scores for config A.
        y: Scores for config B.

    Returns:
        Dict with delta value and magnitude label.
    """
    pairs = [(a, b) for a, b in zip(x, y) if not (np.isnan(a) or np.isnan(b))]
    if len(pairs) < 2:
        return {"delta": None, "magnitude": "insufficient data"}

    x_clean = [p[0] for p in pairs]
    y_clean = [p[1] for p in pairs]

    n = len(x_clean)
    count = sum(1 if xi > yi else -1 if xi < yi else 0
                for xi, yi in zip(x_clean, y_clean))
    delta = count / n

    abs_d = abs(delta)
    if abs_d < 0.147:
        mag = "negligible"
    elif abs_d < 0.33:
        mag = "small"
    elif abs_d < 0.474:
        mag = "medium"
    else:
        mag = "large"

    return {"delta": round(delta, 4), "magnitude": mag}


def bootstrap_ci(
    x: list[float],
    n_boot: int = 10000,
    ci: float = 0.95,
    seed: int = 42,
) -> dict:
    """Compute bootstrap confidence interval for the mean.

    Args:
        x: List of scores.
        n_boot: Number of bootstrap samples.
        ci: Confidence level.
        seed: Random seed for reproducibility.

    Returns:
        Dict with mean, lower, upper bounds.
    """
    x_clean = [v for v in x if not np.isnan(v)]
    if len(x_clean) < 2:
        return {"mean": None, "ci_lower": None, "ci_upper": None}

    rng = np.random.default_rng(seed)
    arr = np.array(x_clean)
    boot_means = np.array([
        rng.choice(arr, size=len(arr), replace=True).mean()
        for _ in range(n_boot)
    ])

    alpha = 1 - ci
    lower = float(np.percentile(boot_means, 100 * alpha / 2))
    upper = float(np.percentile(boot_means, 100 * (1 - alpha / 2)))

    return {
        "mean": round(float(arr.mean()), 4),
        "ci_lower": round(lower, 4),
        "ci_upper": round(upper, 4),
        "n": len(x_clean),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def run_statistical_tests(
    configs: list[str],
    metrics: list[str] | None = None,
    results_file: Path | None = None,
) -> dict:
    """Run statistical significance tests across all config pairs.

    Args:
        configs: List of configurations to compare.
        metrics: List of metrics to test. None = all available.
        results_file: Explicit RAGAS results JSON. None = merge latest.

    Returns:
        Full results dict.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if metrics is None:
        metrics = METRICS.copy()

    print("=" * 70)
    print("STATISTICAL SIGNIFICANCE TESTS")
    print(f"Configs: {configs}  |  Metrics: {metrics}")
    print("=" * 70)

    # Load RAGAS scores
    ragas_scores = load_ragas_scores(results_file)

    # Try to load BERTScore
    bertscore_data = load_bertscore_results()
    if bertscore_data:
        metrics.append("bertscore_f1")
        print(f"  BERTScore data found for: {list(bertscore_data.keys())}")

    # --- Bootstrap CIs per config per metric ---
    print("\n--- Bootstrap 95% Confidence Intervals ---")
    ci_results = {}
    for config in configs:
        ci_results[config] = {}
        for metric in metrics:
            if metric == "bertscore_f1":
                scores = bertscore_data.get(config, [])
            else:
                scores = ragas_scores.get(config, {}).get(metric, [])
            if scores:
                ci = bootstrap_ci(scores)
                ci_results[config][metric] = ci
                if ci["mean"] is not None:
                    print(f"  {config:>15} | {metric:<22} | "
                          f"mean={ci['mean']:.4f} [{ci['ci_lower']:.4f}, {ci['ci_upper']:.4f}] "
                          f"(n={ci['n']})")

    # --- Pairwise Wilcoxon tests ---
    print("\n--- Pairwise Wilcoxon Signed-Rank Tests ---")
    pairwise_results = {}
    config_pairs = list(combinations(configs, 2))

    for metric in metrics:
        pairwise_results[metric] = {}
        print(f"\n  Metric: {metric}")
        print(f"  {'Pair':<35} {'p-value':>10} {'Sig?':>6} {'Cliff d':>10} {'Effect':>12}")
        print(f"  {'-'*73}")

        for c1, c2 in config_pairs:
            if metric == "bertscore_f1":
                x = bertscore_data.get(c1, [])
                y = bertscore_data.get(c2, [])
            else:
                x = ragas_scores.get(c1, {}).get(metric, [])
                y = ragas_scores.get(c2, {}).get(metric, [])

            if not x or not y:
                continue

            # Ensure same length (align by question index)
            min_len = min(len(x), len(y))
            x = x[:min_len]
            y = y[:min_len]

            wilcox = wilcoxon_test(x, y)
            effect = cliffs_delta(x, y)

            pair_key = f"{c1}_vs_{c2}"
            pairwise_results[metric][pair_key] = {
                "wilcoxon": wilcox,
                "cliffs_delta": effect,
            }

            p_str = f"{wilcox['p_value']:.6f}" if wilcox['p_value'] is not None else "N/A"
            sig_str = "**" if wilcox.get("significant_001") else ("*" if wilcox.get("significant_005") else "ns")
            d_str = f"{effect['delta']:.4f}" if effect['delta'] is not None else "N/A"

            print(f"  {c1} vs {c2:<20} {p_str:>10} {sig_str:>6} {d_str:>10} {effect['magnitude']:>12}")

    # --- Save outputs ---
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    output = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "configs": configs,
            "metrics": metrics,
            "test": "Wilcoxon signed-rank (two-sided)",
            "effect_size": "Cliff's delta",
            "confidence_intervals": "Bootstrap 95% (10000 samples)",
        },
        "confidence_intervals": ci_results,
        "pairwise_tests": pairwise_results,
    }

    json_path = OUTPUT_DIR / f"statistical_tests_{timestamp}.json"
    md_path = OUTPUT_DIR / f"statistical_tests_{timestamp}.md"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False, default=str)

    # Generate markdown report
    md_lines = [
        "# Statistical Significance Tests\n\n",
        f"**Generated:** {datetime.now().isoformat()}\n",
        f"**Test:** Wilcoxon signed-rank (two-sided, paired)\n",
        f"**Effect size:** Cliff's delta\n",
        f"**Confidence intervals:** Bootstrap 95% (10,000 samples)\n\n",
        "## Bootstrap 95% Confidence Intervals\n\n",
        "| Config | Metric | Mean | 95% CI | n |\n",
        "|---|---|---|---|---|\n",
    ]
    for config in configs:
        for metric in metrics:
            ci = ci_results.get(config, {}).get(metric, {})
            if ci and ci.get("mean") is not None:
                md_lines.append(
                    f"| {config} | {metric} | {ci['mean']:.4f} | "
                    f"[{ci['ci_lower']:.4f}, {ci['ci_upper']:.4f}] | {ci['n']} |\n"
                )

    md_lines.append("\n## Pairwise Comparisons\n\n")
    for metric in metrics:
        pairs = pairwise_results.get(metric, {})
        if not pairs:
            continue
        md_lines.append(f"\n### {metric}\n\n")
        md_lines.append("| Comparison | p-value | Significant? | Cliff's d | Effect Size |\n")
        md_lines.append("|---|---|---|---|---|\n")
        for pair_key, result in pairs.items():
            w = result["wilcoxon"]
            e = result["cliffs_delta"]
            p_str = f"{w['p_value']:.6f}" if w['p_value'] is not None else "N/A"
            sig = "p<0.01" if w.get("significant_001") else ("p<0.05" if w.get("significant_005") else "ns")
            d_str = f"{e['delta']:.4f}" if e['delta'] is not None else "N/A"
            md_lines.append(f"| {pair_key.replace('_vs_', ' vs ')} | {p_str} | {sig} | {d_str} | {e['magnitude']} |\n")

    md_lines.append("\n## Interpretation Guide\n\n")
    md_lines.append("**Significance levels:** * p<0.05, ** p<0.01, ns = not significant\n\n")
    md_lines.append("**Cliff's delta magnitudes:** |d|<0.147 negligible, <0.33 small, <0.474 medium, ≥0.474 large\n")

    with open(md_path, "w", encoding="utf-8") as f:
        f.writelines(md_lines)

    print(f"\nJSON saved: {json_path}")
    print(f"MD   saved: {md_path}")
    print("=" * 70)

    return output


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Statistical significance tests for RAG evaluation"
    )
    parser.add_argument(
        "--configs",
        nargs="+",
        choices=ALL_CONFIGS,
        default=ALL_CONFIGS,
        help="Which configs to compare (default: all four)",
    )
    parser.add_argument(
        "--metrics",
        nargs="+",
        choices=METRICS,
        default=None,
        help="Which RAGAS metrics to test (default: all)",
    )
    parser.add_argument(
        "--results-file",
        type=str,
        default=None,
        help="Explicit path to RAGAS results JSON (default: latest in results/ragas_evaluation/)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    run_statistical_tests(
        configs=args.configs,
        metrics=args.metrics,
        results_file=Path(args.results_file) if args.results_file else None,
    )
