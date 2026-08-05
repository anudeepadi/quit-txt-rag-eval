#!/usr/bin/env python3
"""Intent tests for the non-inferiority / TOST equivalence test.

These encode WHY the test exists, not just that it runs. The parity claim in
the paper rests on this function: a two-sided Wilcoxon can only fail to detect
a difference, so claiming "the AI-generated KB is as good as the expert KB"
requires rejecting the null that it is worse by at least the pre-registered
margin. Each case below asserts a decision the reviewer would check by hand.

Run:  python -m pytest code/tests/test_noninferiority.py -v
      python code/tests/test_noninferiority.py          # no pytest needed
"""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from statistical_tests import noninferiority_test  # noqa: E402

MARGIN = 0.05
SEED = 0


def _arms(shift: float, n: int = 100, noise: float = 0.01, seed: int = SEED):
    """Build a paired (candidate, reference) pair of arms offset by `shift`."""
    rng = np.random.default_rng(seed)
    ref = list(rng.uniform(0.6, 0.95, n))
    cand = [r + shift + rng.normal(0, noise) for r in ref]
    return cand, ref


def test_identical_arms_are_non_inferior_and_equivalent():
    """An arm that matches the reference must clear both bars.

    If this fails, the test is too conservative to ever support a parity
    claim — the paper's central result would be unprovable by construction.
    """
    cand, ref = _arms(0.0)
    r = noninferiority_test(cand, ref, MARGIN)
    assert r["non_inferior"] is True
    assert r["equivalent"] is True


def test_drop_smaller_than_margin_is_non_inferior():
    """A 0.01 drop is inside the pre-registered acceptable margin of 0.05.

    The margin is the whole point: small regressions are tolerated by
    agreement, so they must not be reported as failures.
    """
    cand, ref = _arms(-0.01)
    r = noninferiority_test(cand, ref, MARGIN)
    assert r["non_inferior"] is True
    assert r["equivalent"] is True


def test_drop_larger_than_margin_is_rejected():
    """A 0.10 drop exceeds the margin and MUST fail.

    This is the test's reason for existing. If a clearly-worse arm passes,
    the non-inferiority claim is a rubber stamp and the result is not
    publishable.
    """
    cand, ref = _arms(-0.10)
    r = noninferiority_test(cand, ref, MARGIN)
    assert r["non_inferior"] is False
    assert r["equivalent"] is False


def test_large_improvement_is_non_inferior_but_not_equivalent():
    """Better-by-more-than-margin is non-inferior yet NOT equivalent.

    Equivalence is two-sided (TOST). Conflating the two would let us claim
    "the same as expert content" about an arm that is measurably different,
    which is the opposite of what the reviewer asked for.
    """
    cand, ref = _arms(0.10)
    r = noninferiority_test(cand, ref, MARGIN)
    assert r["non_inferior"] is True
    assert r["equivalent"] is False


def test_nan_pairs_are_dropped_not_counted():
    """NaN scores (failed RAGAS calls) must not inflate n or shift the result.

    Silently treating a failed metric call as 0.0 would manufacture a
    difference that never happened.
    """
    cand, ref = _arms(0.0, n=50)
    cand_with_nan = cand + [float("nan")] * 10
    ref_with_nan = ref + [0.8] * 10
    r = noninferiority_test(cand_with_nan, ref_with_nan, MARGIN)
    assert r["n_valid"] == 50


def test_too_few_pairs_returns_none_not_a_verdict():
    """Under 5 usable pairs must return None, never a confident verdict.

    A verdict from 3 questions would read as evidence in the results table.
    """
    r = noninferiority_test([0.8, 0.9], [0.8, 0.9], MARGIN)
    assert r["non_inferior"] is None
    assert "note" in r


def test_margin_is_honoured_not_hardcoded():
    """A stricter margin must be able to flip the verdict.

    The margin is a pre-registered input; if it were ignored, the reviewer's
    agreed threshold would have no effect on the reported conclusion.
    """
    cand, ref = _arms(-0.03)
    assert noninferiority_test(cand, ref, 0.05)["non_inferior"] is True
    assert noninferiority_test(cand, ref, 0.01)["non_inferior"] is False


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if not name.startswith("test_") or not callable(fn):
            continue
        try:
            fn()
            print(f"PASS  {name}")
        except AssertionError as e:
            failures += 1
            print(f"FAIL  {name}: {e}")
    print(f"\n{'ALL PASS' if failures == 0 else f'{failures} FAILED'}")
    sys.exit(1 if failures else 0)
