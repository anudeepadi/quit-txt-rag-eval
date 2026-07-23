#!/usr/bin/env python3
"""Held-out re-analysis + non-inferiority / equivalence test for the RAG parity claim.

Addresses two reviewer objections (Ebrahim, 2026-07-21):

  1. Benchmark overfitting. The evo optimization loop selected prompts and made
     keep/discard decisions using the FIRST 20 rows of test_set_150q.xlsx
     (data_gen_prepare.py: N_EVAL=20, rows[:20]). The reported RAGAS parity
     number was then computed on a 100-question set that CONTAINS those same
     questions. This script identifies the overlap, removes it, and recomputes
     the AI-vs-human faithfulness comparison on the genuinely held-out subset.

  2. "Not significant" is not "equivalent". The original analysis used a
     two-sided Wilcoxon test and read non-significance as parity. That is the
     absence-of-evidence fallacy. This script runs a paired non-inferiority
     test and a TOST equivalence test against a PRE-DEFINED margin.

No API calls: it reuses the per-question scores already stored in the RAGAS
result JSON. Deterministic.
"""

import argparse
import json
import sys
import math
import re
import statistics
from pathlib import Path

import openpyxl
from scipy import stats

_ROOT = Path(__file__).parent.parent.parent  # gemini-protocol/

# The two paths that both point at the 150-question test set.
OPT_TEST_SET = _ROOT / "datasets" / "eval-rag" / "test_set_150q.xlsx"

# Number of leading rows the evo loop consumed for prompt selection.
N_OPT = 20

# Pre-defined non-inferiority / equivalence margin on faithfulness [0, 1].
# Placeholder to agree with the reviewer before final reporting. 0.05 = the
# AI KB is deemed "not meaningfully worse" if it trails human by < 5 points.
DEFAULT_MARGIN = 0.05


def _norm(text: object) -> str:
    """Normalize question text for matching across the two loaders."""
    return re.sub(r"[^a-z0-9]+", " ", str(text).lower()).strip()


def load_optimization_questions(path: Path, n: int) -> set[str]:
    """The first `n` raw rows (col A), matching data_gen_prepare.load_test_questions."""
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(min_row=2, values_only=True))
    wb.close()
    return {_norm(r[0]) for r in rows[:n] if r and r[0]}


def load_test_questions_in_order(path: Path, n: int) -> list[str]:
    """The RAGAS test questions in evaluation order.

    Deliberately re-derived from the test set via the SAME loader the eval uses
    (`ragas_utils.load_test_set`), not from a per-question checkpoint. The
    checkpoints are resume caches: a partial rerun appends duplicate q_idx rows
    (observed 104 rows for a 100-question run), so they are not a stable source
    of ordering.
    """
    sys.path.insert(0, str(_ROOT / "code"))
    from shared.ragas_utils import load_test_set

    return [_norm(r["question"]) for r in load_test_set(path, max_rows=n)]


def paired_noninferiority(diffs: list[float], margin: float) -> dict:
    """One-sided paired test that AI is non-inferior to human.

    H0: mean(AI - human) <= -margin   (AI is meaningfully worse)
    H1: mean(AI - human)  > -margin    (AI is non-inferior)
    """
    n = len(diffs)
    mean = statistics.mean(diffs)
    sd = statistics.stdev(diffs) if n > 1 else 0.0
    se = sd / math.sqrt(n) if n > 0 else float("nan")
    t = (mean + margin) / se if se else float("inf")
    p = stats.t.sf(t, df=n - 1)  # one-sided upper tail
    return {"n": n, "mean_diff": mean, "sd": sd, "se": se, "t": t,
            "p_value": p, "non_inferior": p < 0.05, "margin": margin}


def paired_tost(diffs: list[float], margin: float) -> dict:
    """TOST equivalence: is mean(AI - human) inside (-margin, +margin)?"""
    n = len(diffs)
    mean = statistics.mean(diffs)
    sd = statistics.stdev(diffs) if n > 1 else 0.0
    se = sd / math.sqrt(n) if n > 0 else float("nan")
    t_lower = (mean + margin) / se if se else float("inf")   # H0: diff <= -margin
    t_upper = (mean - margin) / se if se else float("-inf")  # H0: diff >= +margin
    p_lower = stats.t.sf(t_lower, df=n - 1)
    p_upper = stats.t.cdf(t_upper, df=n - 1)
    p = max(p_lower, p_upper)
    return {"p_lower": p_lower, "p_upper": p_upper, "p_value": p,
            "equivalent": p < 0.05, "margin": margin}


def _clean_pairs(ai: list[float], hu: list[float], idxs: list[int]) -> list[tuple[float, float]]:
    """Keep only index pairs where both scores are non-NaN."""
    pairs = []
    for i in idxs:
        a, h = ai[i], hu[i]
        if a == a and h == h:  # NaN != NaN
            pairs.append((a, h))
    return pairs


def summarize(label: str, pairs: list[tuple[float, float]], margin: float) -> dict:
    ai = [p[0] for p in pairs]
    hu = [p[1] for p in pairs]
    diffs = [a - h for a, h in pairs]
    ni = paired_noninferiority(diffs, margin)
    tost = paired_tost(diffs, margin)
    row = {
        "label": label, "n": len(pairs),
        "ai_mean": statistics.mean(ai), "human_mean": statistics.mean(hu),
        "mean_diff": statistics.mean(diffs),
        "non_inferiority_p": ni["p_value"], "non_inferior": ni["non_inferior"],
        "tost_p": tost["p_value"], "equivalent": tost["equivalent"],
    }
    print(f"\n[{label}]  n={row['n']}")
    print(f"  AI    faithfulness mean = {row['ai_mean']:.4f}")
    print(f"  Human faithfulness mean = {row['human_mean']:.4f}")
    print(f"  paired diff (AI-Human)  = {row['mean_diff']:+.4f}")
    print(f"  non-inferiority (delta={margin}): p={ni['p_value']:.4g} -> "
          f"{'AI NON-INFERIOR' if ni['non_inferior'] else 'inconclusive'}")
    print(f"  TOST equivalence (delta={margin}): p={tost['p_value']:.4g} -> "
          f"{'EQUIVALENT' if tost['equivalent'] else 'not equivalent'}")
    return row


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--result-json", type=Path,
                    default=_ROOT / "code" / "results" / "ragas_evaluation"
                    / "ragas_eval_concise_20260721_044307.json")
    ap.add_argument("--n-questions", type=int, default=100)
    ap.add_argument("--margin", type=float, default=DEFAULT_MARGIN)
    args = ap.parse_args()

    data = json.loads(args.result_json.read_text())
    ai = data["all_scores"]["ai_rag"]["faithfulness"]
    hu = data["all_scores"]["human_rag"]["faithfulness"]

    opt_qs = load_optimization_questions(OPT_TEST_SET, N_OPT)
    test_qs = load_test_questions_in_order(OPT_TEST_SET, args.n_questions)
    excluded = [i for i, q in enumerate(test_qs) if q in opt_qs]
    held_out = [i for i in range(len(test_qs)) if i not in set(excluded)]

    print("=" * 68)
    print("HELD-OUT RE-ANALYSIS + NON-INFERIORITY TEST (faithfulness)")
    print("=" * 68)
    print(f"Optimization questions (loop-seen): {len(opt_qs)}")
    print(f"Test questions:                     {len(test_qs)}")
    print(f"Contaminated overlap removed:       {len(excluded)}  idx={excluded}")
    print(f"Held-out questions:                 {len(held_out)}")

    summarize("FULL 100 (as originally reported)", _clean_pairs(ai, hu, list(range(len(test_qs))), ), args.margin)
    summarize("CONTAMINATED overlap only", _clean_pairs(ai, hu, excluded), args.margin)
    summarize("HELD-OUT (loop-seen questions removed)", _clean_pairs(ai, hu, held_out), args.margin)

    print("\nNote: margin is a placeholder. Agree delta with the reviewer before")
    print("final reporting. Non-inferiority is the appropriate test for the")
    print("'AI is not worse than human' claim; TOST tests two-sided equivalence.")


if __name__ == "__main__":
    main()
