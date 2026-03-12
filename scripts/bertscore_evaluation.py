#!/usr/bin/env python3
"""BERTScore Evaluation: Compute BERTScore across all RAG configurations.

Loads checkpoint JSONL files (per-question answers + ground truth) from the
RAGAS evaluation pipeline and computes BERTScore (Precision, Recall, F1)
for each configuration.

BERTScore uses contextual embeddings from a pre-trained language model
(default: microsoft/deberta-xlarge-mnli) to measure semantic similarity
between generated answers and ground truth references.

Usage:
    python scripts/bertscore_evaluation.py                          # all configs
    python scripts/bertscore_evaluation.py --configs ai_rag human_rag
    python scripts/bertscore_evaluation.py --model-type roberta-large
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from statistics import mean, stdev, median

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ROOT))

RESULTS_DIR = _ROOT / "results" / "ragas_evaluation"
OUTPUT_DIR = _ROOT / "results" / "bertscore"

ALL_CONFIGS = ["baseline", "ai_rag", "human_rag", "web_rag"]


# ---------------------------------------------------------------------------
# Checkpoint loading
# ---------------------------------------------------------------------------


def load_checkpoint(config: str, n: int = 100, concise: bool = True) -> list[dict]:
    """Load checkpoint JSONL file for a given config.

    Args:
        config: Configuration name (baseline, ai_rag, human_rag, web_rag).
        n: The max_questions cap used in the RAGAS run.
        concise: Whether to look for concise checkpoint prefix.

    Returns:
        List of dicts with keys: q_idx, question, answer, contexts, ground_truth.
    """
    prefix = "checkpoint_concise" if concise else "checkpoint"
    path = RESULTS_DIR / f"{prefix}_{config}_{n}.jsonl"
    if not path.exists():
        print(f"  [WARN] Checkpoint not found: {path}")
        return []
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return records


# ---------------------------------------------------------------------------
# BERTScore computation
# ---------------------------------------------------------------------------


def compute_bertscore(
    predictions: list[str],
    references: list[str],
    model_type: str = "microsoft/deberta-xlarge-mnli",
    batch_size: int = 32,
) -> dict:
    """Compute BERTScore for a list of prediction-reference pairs.

    Args:
        predictions: List of generated answers.
        references: List of ground truth answers.
        model_type: HuggingFace model for BERTScore embeddings.
        batch_size: Batch size for scoring.

    Returns:
        Dict with 'precision', 'recall', 'f1' lists and summary stats.
    """
    from bert_score import score

    P, R, F1 = score(
        predictions,
        references,
        model_type=model_type,
        batch_size=batch_size,
        verbose=True,
        device="cpu",  # Safe default; GPU used if available via auto-detect
    )

    p_list = P.tolist()
    r_list = R.tolist()
    f1_list = F1.tolist()

    def _stats(values):
        n = len(values)
        if n == 0:
            return {"mean": 0, "sd": 0, "median": 0, "min": 0, "max": 0, "n": 0}
        m = mean(values)
        s = stdev(values) if n > 1 else 0.0
        return {
            "mean": round(m, 4),
            "sd": round(s, 4),
            "median": round(median(values), 4),
            "min": round(min(values), 4),
            "max": round(max(values), 4),
            "n": n,
        }

    return {
        "precision": p_list,
        "recall": r_list,
        "f1": f1_list,
        "precision_stats": _stats(p_list),
        "recall_stats": _stats(r_list),
        "f1_stats": _stats(f1_list),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def run_bertscore_evaluation(
    configs: list[str],
    n: int = 100,
    concise: bool = True,
    model_type: str = "microsoft/deberta-xlarge-mnli",
) -> dict:
    """Run BERTScore evaluation across all specified configs.

    Args:
        configs: List of config names to evaluate.
        n: Max questions cap from checkpoint files.
        concise: Whether to use concise checkpoints.
        model_type: HuggingFace model for embeddings.

    Returns:
        Full results dict.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    print("=" * 70)
    print("BERTScore EVALUATION")
    print(f"Configs: {configs}  |  Questions: {n}  |  Model: {model_type}")
    print("=" * 70)

    all_results = {}

    for config in configs:
        print(f"\n--- {config} ---")
        records = load_checkpoint(config, n=n, concise=concise)
        if not records:
            print(f"  Skipping {config}: no checkpoint data")
            continue

        predictions = [r["answer"] for r in records]
        references = [r["ground_truth"] for r in records]
        print(f"  Loaded {len(predictions)} question-answer pairs")

        scores = compute_bertscore(predictions, references, model_type=model_type)
        all_results[config] = scores

        stats = scores["f1_stats"]
        print(f"  BERTScore F1: {stats['mean']:.4f} ± {stats['sd']:.4f} "
              f"(median: {stats['median']:.4f})")

    # --- Print comparison table ---
    print("\n" + "=" * 70)
    print("BERTSCORE RESULTS SUMMARY")
    print("=" * 70)
    print(f"\n{'Config':<20} {'P (mean)':>10} {'R (mean)':>10} {'F1 (mean)':>10} "
          f"{'F1 (SD)':>10} {'F1 (med)':>10} {'n':>5}")
    print("-" * 75)
    for config in configs:
        if config not in all_results:
            continue
        r = all_results[config]
        print(f"{config:<20} "
              f"{r['precision_stats']['mean']:>10.4f} "
              f"{r['recall_stats']['mean']:>10.4f} "
              f"{r['f1_stats']['mean']:>10.4f} "
              f"{r['f1_stats']['sd']:>10.4f} "
              f"{r['f1_stats']['median']:>10.4f} "
              f"{r['f1_stats']['n']:>5}")

    # --- Save outputs ---
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    output = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "model_type": model_type,
            "num_questions": n,
            "configs_run": configs,
            "concise_mode": concise,
        },
        "results": {
            config: {
                "precision_stats": all_results[config]["precision_stats"],
                "recall_stats": all_results[config]["recall_stats"],
                "f1_stats": all_results[config]["f1_stats"],
                "per_question_f1": all_results[config]["f1"],
                "per_question_precision": all_results[config]["precision"],
                "per_question_recall": all_results[config]["recall"],
            }
            for config in configs
            if config in all_results
        },
    }

    json_path = OUTPUT_DIR / f"bertscore_{timestamp}.json"
    md_path = OUTPUT_DIR / f"bertscore_{timestamp}.md"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # Generate markdown report
    md_lines = [
        "# BERTScore Evaluation Results\n",
        f"**Generated:** {datetime.now().isoformat()}\n",
        f"**Model:** {model_type}\n",
        f"**Questions:** {n}\n\n",
        "## Summary\n\n",
        "| Config | Precision | Recall | F1 (mean ± SD) | F1 (median) | n |\n",
        "|---|---|---|---|---|---|\n",
    ]
    for config in configs:
        if config not in all_results:
            continue
        r = all_results[config]
        md_lines.append(
            f"| {config} | {r['precision_stats']['mean']:.4f} | "
            f"{r['recall_stats']['mean']:.4f} | "
            f"{r['f1_stats']['mean']:.4f} ± {r['f1_stats']['sd']:.4f} | "
            f"{r['f1_stats']['median']:.4f} | {r['f1_stats']['n']} |\n"
        )

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
        description="BERTScore evaluation for RAG configurations"
    )
    parser.add_argument(
        "--configs",
        nargs="+",
        choices=ALL_CONFIGS,
        default=ALL_CONFIGS,
        help="Which configs to evaluate (default: all four)",
    )
    parser.add_argument(
        "--max-questions",
        type=int,
        default=100,
        metavar="N",
        help="Max questions cap matching checkpoint files (default: 100)",
    )
    parser.add_argument(
        "--model-type",
        type=str,
        default="microsoft/deberta-xlarge-mnli",
        help="HuggingFace model for BERTScore (default: deberta-xlarge-mnli)",
    )
    parser.add_argument(
        "--no-concise",
        action="store_true",
        default=False,
        help="Use non-concise checkpoints instead of concise",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    run_bertscore_evaluation(
        configs=args.configs,
        n=args.max_questions,
        concise=not args.no_concise,
        model_type=args.model_type,
    )
