"""Frozen dev/test split for the 150-question evaluation set.

Single source of truth for which questions the optimization loop may see.

Background. The evo loop previously scored every experiment on the FIRST 20
rows of test_set_150q.xlsx (data_gen_prepare: N_EVAL=20, rows[:20]) while the
final RAGAS number was computed on a 100-question set drawn from the same file.
16 questions appeared in both, so 16% of the reported "test" set had been
directly optimized against. Reviewer objection, 2026-07-21.

The split:
  - Source: the 127 LFV-clean questions (23 of 150 flagged by clinical review).
  - DEV  = clean rows [0:50]   -> the optimization loop may use these.
  - TEST = clean rows [50:127] -> frozen. Never visible to optimization.

The 16 already-burned questions fall inside DEV by construction (they are the
leading rows), so the freeze is honest rather than retroactive.

Use `load_dev_questions()` in anything that influences a decision. Use
`load_test_questions_frozen()` only in final reporting. `assert_not_optimizing()`
makes accidental test access fail loudly instead of silently contaminating a run.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path

from .ragas_utils import load_test_set

_ROOT = Path(__file__).parent.parent.parent  # gemini-protocol/

TEST_SET_XLSX = _ROOT / "datasets" / "eval-rag" / "test_set_150q.xlsx"
MANIFEST_PATH = _ROOT / "datasets" / "eval-rag" / "question_split_manifest.json"

DEV_SIZE = 50

# Set to "1" inside an optimization run so test-set access aborts.
OPTIMIZING_ENV_VAR = "EVO_OPTIMIZING"


@dataclass(frozen=True)
class Question:
    """One evaluation question and its clinician-written reference answer."""

    question: str
    ground_truth: str


class TestSetLeakError(RuntimeError):
    """Raised when frozen test questions are requested during optimization."""


def _load_clean(path: Path | None = None) -> list[Question]:
    """All LFV-clean questions in sheet order (flagged rows already dropped)."""
    rows = load_test_set(path or TEST_SET_XLSX)
    return [Question(question=r["question"], ground_truth=r["ground_truth"]) for r in rows]


def load_dev_questions(path: Path | None = None) -> list[Question]:
    """Questions the optimization loop is allowed to score against."""
    return _load_clean(path)[:DEV_SIZE]


def assert_not_optimizing() -> None:
    """Abort if frozen test questions are touched inside an optimization run."""
    if os.getenv(OPTIMIZING_ENV_VAR) == "1":
        raise TestSetLeakError(
            "Frozen test questions were requested while "
            f"{OPTIMIZING_ENV_VAR}=1. The optimization loop must use "
            "load_dev_questions(). Reading the test set here would "
            "reintroduce the contamination this split exists to prevent."
        )


def load_test_questions_frozen(path: Path | None = None) -> list[Question]:
    """Frozen held-out questions. Final reporting only, never optimization."""
    assert_not_optimizing()
    return _load_clean(path)[DEV_SIZE:]


def _digest(questions: list[Question]) -> str:
    """Stable hash of a question set, for drift detection."""
    joined = "\n".join(q.question for q in questions)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()[:16]


def build_manifest(path: Path | None = None) -> dict:
    """Describe the split so it can be audited and checked for drift."""
    clean = _load_clean(path)
    dev, test = clean[:DEV_SIZE], clean[DEV_SIZE:]
    return {
        "source_file": str((path or TEST_SET_XLSX).relative_to(_ROOT)),
        "n_clean": len(clean),
        "dev": {"n": len(dev), "range": [0, DEV_SIZE], "sha256_16": _digest(dev)},
        "test": {"n": len(test), "range": [DEV_SIZE, len(clean)], "sha256_16": _digest(test)},
        "note": (
            "DEV is optimization-visible. TEST is frozen. The 16 questions "
            "burned by the pre-split evo loop fall inside DEV by construction."
        ),
    }


def verify_manifest(path: Path | None = None) -> bool:
    """True when the on-disk split still matches the recorded manifest."""
    if not MANIFEST_PATH.exists():
        return False
    recorded = json.loads(MANIFEST_PATH.read_text())
    current = build_manifest(path)
    return (
        recorded.get("dev", {}).get("sha256_16") == current["dev"]["sha256_16"]
        and recorded.get("test", {}).get("sha256_16") == current["test"]["sha256_16"]
    )


def write_manifest(path: Path | None = None) -> dict:
    """Persist the split manifest and return it."""
    manifest = build_manifest(path)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


if __name__ == "__main__":
    m = write_manifest()
    print(json.dumps(m, indent=2))
    print(f"\nWrote {MANIFEST_PATH.relative_to(_ROOT)}")
    print(f"DEV  n={m['dev']['n']}  (optimization may use these)")
    print(f"TEST n={m['test']['n']}  (frozen)")
