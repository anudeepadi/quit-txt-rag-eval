#!/usr/bin/env python3
"""Intent tests for the non-inferiority / TOST equivalence test.

These encode WHY the test exists, not just that it runs. The parity claim in
the paper rests on these two functions: a two-sided test can only fail to
detect a difference, so claiming "the AI-generated KB is not worse than the
expert KB" requires rejecting the null that it IS worse by at least the
pre-agreed margin. Each case below asserts a decision a reviewer would check
by hand.

Run:  pytest code/tests/test_holdout_noninferiority.py -v
      python code/tests/test_holdout_noninferiority.py    # no pytest needed
"""

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from holdout_noninferiority import (  # noqa: E402
    DEFAULT_MARGIN,
    _clean_pairs,
    paired_noninferiority,
    paired_tost,
)

MARGIN = DEFAULT_MARGIN  # 0.05


def _diffs(shift: float, n: int = 100, noise: float = 0.02, seed: int = 0) -> list[float]:
    """Paired differences centred on `shift` with realistic scatter."""
    rng = random.Random(seed)
    return [shift + rng.gauss(0, noise) for _ in range(n)]


def test_identical_arms_are_non_inferior_and_equivalent() -> None:
    """An arm that matches the reference must clear both bars.

    If this fails the test is too conservative to ever support a parity
    claim, and the paper's central result is unprovable by construction.
    """
    d = _diffs(0.0)
    assert paired_noninferiority(d, MARGIN)["non_inferior"]
    assert paired_tost(d, MARGIN)["equivalent"]


def test_drop_smaller_than_margin_is_non_inferior() -> None:
    """A 0.01 drop sits inside the agreed 0.05 margin.

    The margin exists precisely so small regressions are tolerated by prior
    agreement rather than reported as failures.
    """
    d = _diffs(-0.01)
    assert paired_noninferiority(d, MARGIN)["non_inferior"]


def test_drop_larger_than_margin_is_rejected() -> None:
    """A 0.10 drop exceeds the margin and MUST fail.

    This is the reason the test exists. If a clearly worse arm passes, the
    non-inferiority claim is a rubber stamp and the result is not publishable.
    """
    d = _diffs(-0.10)
    assert not paired_noninferiority(d, MARGIN)["non_inferior"]
    assert not paired_tost(d, MARGIN)["equivalent"]


def test_large_improvement_is_non_inferior_but_not_equivalent() -> None:
    """Better by more than the margin is non-inferior yet NOT equivalent.

    Equivalence is two-sided. Conflating the two would let us claim "the same
    as expert content" about an arm that is measurably different, which is the
    opposite of what the reviewer asked for.
    """
    d = _diffs(0.10)
    assert paired_noninferiority(d, MARGIN)["non_inferior"]
    assert not paired_tost(d, MARGIN)["equivalent"]


def test_margin_is_honoured_not_hardcoded() -> None:
    """A stricter margin must be able to flip the verdict.

    The margin is a pre-registered input agreed with the reviewer. If it were
    ignored, their threshold would have no effect on the reported conclusion.
    """
    d = _diffs(-0.03)
    assert paired_noninferiority(d, 0.05)["non_inferior"]
    assert not paired_noninferiority(d, 0.01)["non_inferior"]


def test_nan_scores_are_dropped_not_counted() -> None:
    """Failed RAGAS calls (NaN) must not enter the comparison.

    Treating a failed metric call as 0.0 would manufacture a difference that
    never happened, and inflate n so the result looks better powered than it is.
    """
    ai = [0.8, float("nan"), 0.9, 0.7]
    hu = [0.8, 0.8, float("nan"), 0.7]
    pairs = _clean_pairs(ai, hu, list(range(4)))
    assert len(pairs) == 2
    assert pairs == [(0.8, 0.8), (0.7, 0.7)]


def test_wider_scatter_weakens_the_verdict() -> None:
    """Same mean difference, more noise, must not be MORE confident.

    Guards against a test that reads only the point estimate. With n fixed,
    a noisier sample has to yield a larger (weaker) p-value.
    """
    tight = paired_noninferiority(_diffs(-0.01, noise=0.01), MARGIN)["p_value"]
    loose = paired_noninferiority(_diffs(-0.01, noise=0.10), MARGIN)["p_value"]
    assert loose > tight


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
