# Reviewer Packet — Response to Ebrahim's Review

**Date:** 2026-08-04
**Repo:** https://github.com/anudeepadi/quit-txt-rag-eval
**Purpose:** Close out the eight review items, and get the two decisions that
block the next optimization run.

---

## TL;DR — two decisions needed from you

1. **Non-inferiority margin δ.** I implemented the test; it needs a margin
   agreed *before* the frozen test set is unblinded. **I propose δ = 0.05
   faithfulness.** Justification in §M2.
2. **Acceptance floors (your item 3).** Enforcement is currently
   reporting-only. The measured distributions are in §D3 — I need your minimum
   thresholds before I turn filtering on in epoch 5.

Everything else is implemented and pushed.

---

## Status of all eight items

| # | Your item | Status |
|---|---|---|
| M1 | Benchmark overfitting / held-out test set | **Done** |
| M2 | Equivalence / non-inferiority test with predefined margin | **Implemented — needs your δ** |
| M3 | Refusals scored as zero is wrong | **Done** |
| M4 | Retrieval relevance, context recall, completeness, hallucination, appropriate refusal | **Done** (one data gap, §M4) |
| D1 | Specify what the AI dataset improves vs expert content | **Done** |
| D2 | Every QA pair linked to its source / evidence span | **Done at chunk level — span-level gap, §D2** |
| D3 | Define what makes a generated sample acceptable | **Measured — needs your thresholds** |
| D4 | Version manifest per dataset version | **Done** |

---

## M1 — Held-out test set

You were right that the same 150 questions could not serve as both the
optimization signal and the test set. The split is now frozen and hashed:

| Split | n | SHA-256 (16) | Visible to optimization? |
|---|---|---|---|
| DEV | 50 | `a6e045dc9f0957d9` | Yes |
| TEST | 77 | `8666ccf57f5b035f` | **No — never evaluated** |

- Source: `datasets/eval-rag/test_set_150q.xlsx`, 127 questions after cleaning.
- Manifest: `datasets/eval-rag/question_split_manifest.json`.
- The 16 questions consumed by the pre-split evo loop fall inside DEV by
  construction, so TEST is uncontaminated.
- Plan: all remaining prompt selection happens on DEV; TEST is evaluated
  **once**, after the configuration is frozen. That single number is what goes
  in the paper.

## M2 — Non-inferiority and equivalence test

Implemented in `code/scripts/statistical_tests.py` as
`noninferiority_test()`, with intent tests in
`code/tests/test_noninferiority.py` (7 cases, all passing).

**Method.** Paired nonparametric TOST on the per-question differences
d = candidate − reference, plus a bootstrap CI on the mean difference
(10,000 resamples, seeded):

- Non-inferiority — H0: median(d) ≤ −δ, rejected via one-sided Wilcoxon on
  (d + δ).
- Equivalence — TOST, both one-sided tests must reject; the difference is
  bounded inside ±δ.

**Proposed margin: δ = 0.05 faithfulness.** The measured run-to-run noise
floor is sd = 0.0115 with a minimum detectable effect of ~0.03, so 0.05 is
~1.7× noise — small enough to be a meaningful clinical claim, large enough
that we are not testing against measurement error. **If you prefer a
different δ, say so before I unblind TEST** — changing it afterwards would
invalidate the claim.

**Illustrative run** (on the older n=100 evaluation, `ai_rag` vs `human_rag`,
faithfulness — this set overlaps optimization-visible data, so it is a
mechanism demo, *not* the result):

| Test | Value |
|---|---|
| Two-sided Wilcoxon | p = 0.0991 → **ns** (cannot establish anything) |
| Mean difference | +0.0460 |
| One-sided 95% lower bound | −0.0051 |
| p (non-inferiority, δ=0.05) | < 1e-6 → **non-inferior** |
| p (equivalence, TOST) | < 1e-6 → **equivalent** |

This is exactly the gap you identified: the two-sided test returns "not
significant", which is not evidence of parity. The non-inferiority test
answers the question the paper actually asks.

## M3 — Refusal scoring

Refusals are no longer collapsed to zero. `code/shared/answer_quality.py`
provides `classify_refusal()` / `is_refusal()`, and the evaluation reports:

- `is_refusal` — 1.0 refusal, 0.0 substantive
- `appropriate_refusal` — 1.0 appropriate, 0.0 inappropriate, **NaN when the
  answer is not a refusal** (so it never contaminates the mean)

This matters because refusal rates differ sharply between the two knowledge
bases, and refusals score ~0.46–0.55 faithfulness against ~0.82–0.89 for
substantive answers. Scoring them all as 0 would have penalized *correct*
refusals — which in a smoking-cessation context are often the safest response.

## M4 — Metric coverage

| Metric | Status |
|---|---|
| Faithfulness | Active |
| Answer relevancy | Active |
| Context precision (retrieval relevance) | Active — 100/100 on `ai_rag` and `human_rag` |
| Context recall | Active — 100/100 on both arms |
| Answer completeness | Active (`score_completeness`) |
| Hallucination rate | Active (`ragas_utils.py`, derived as 1 − faithfulness) |
| Appropriate refusal | Active (see M3) |

Retrieval metrics are skipped only for the `baseline` arm, which retrieves no
contexts — they are undefined there rather than missing.

**One data gap:** `web_rag` context_precision is 0/100 in the April run and
needs re-scoring. It does not affect the AI-vs-human comparison.

## D1 — What the AI dataset is intended to improve

Documented in `docs/dataset_generation_protocol.md` §1. Claimed:
**scalability, conversational phrasing, structure.** Retrieval suitability is
listed as an open question. **Coverage is explicitly not claimed** — the
generated KB is derived from the expert KB, so it cannot exceed its coverage.

## D2 — Provenance

Every generated pair carries `source_id`, `source_sha256`, and
`source_excerpt`, persisted to `generated_artifacts/generated_kb.jsonl`. The
RAG index strips provenance before embedding, so retrieval input is
byte-identical to before — the instrumentation is score-neutral.

Verified on exp_0027 (1,736 pairs): 216 distinct sources, 8 pairs per source,
perfectly blocked. Lexical overlap between a pair and its own source is 0.180
versus 0.076 against a shifted source, confirming the links are real.

**Gap I want to flag rather than paper over.** `source_excerpt` is a fixed
300-character truncation of the chunk. Since each chunk produces 8 pairs
spanning the whole chunk, a given pair's supporting sentence often falls
outside that window — 5.4% of pairs share zero content words with their stored
excerpt. So provenance is currently **chunk-level, not span-level**. For the
hallucination analysis you want, I think we need the actual supporting
sentence per pair. That is a small harness change; tell me if you want it
before the next run or as an epoch-5 item.

## D3 — Acceptance criteria (**your decision needed**)

Criteria were defined before optimization round 1
(`docs/dataset_generation_protocol.md` §3). Enforcement beyond
well-formedness is deliberately **reporting-only**, because adding filters
mid-epoch would change scores and break comparability across experiments.

**Measured on the two most recent runs:**

| | exp_0026 | exp_0027 |
|---|---|---|
| Raw pairs | 1,877 | 1,736 |
| Rejected (not well-formed) | 0 | 0 |
| Exact duplicates | 28 | 9 |
| Fuzzy duplicates (Jaccard ≥ 0.9) | 7 | 5 |
| Kept | 1,877 | 1,736 |
| Groundedness (n=15 sample) | 0.953 | 0.973 |
| Clinical accuracy (n=15) | 0.893 | 0.940 |
| Specificity (n=15) | 0.693 | 0.687 |
| Conversational tone (n=15) | 0.740 | 0.840 |

**What I need from you — a minimum acceptable value for each:**

| # | Criterion | Current enforcement | Proposed floor |
|---|---|---|---|
| A1 | Well-formed | Enforced | keep as-is |
| A2 | Not a duplicate | Counted only | hard-reject exact + fuzzy? |
| A3 | Factually consistent with source | Sampled n=15 | groundedness ≥ ? |
| A4 | No unsupported content | Sampled n=15 | same judge |
| A5 | Answer completeness | Deferred (per-pair judge cost) | include in epoch 5? |
| A6 | Relevant to smoking-cessation counseling | Sampled n=15 | clinical accuracy ≥ ? |

Note the sample is n=15 per run, which is thin for setting a hard threshold.
If you want per-pair enforcement on A3/A4 I can budget for it, but it is a
real cost increase — worth deciding together.

## D4 — Version manifest

Every run writes `generated_artifacts/dataset_manifest.json` recording:
source snapshot file + SHA-256, harness commit, hypothesis, model,
full system prompt, parameters (temperature, max_tokens, qa_per_source),
timestamp, accepted/rejected/duplicate counts, and the quality sample.

Working rule adopted: **no dataset number is quotable without its manifest.**

---

## What happens after you reply

1. You confirm δ (or give me a different one) and the A2–A6 floors.
2. I restart the evo optimization loop on the **DEV split only**, from a clean
   epoch-5 baseline.
3. Configuration is frozen.
4. TEST (77 questions) is evaluated **once**, with the non-inferiority test at
   the agreed δ. That is the number we publish.

One correction to my earlier reporting: `evo status` shows `best=0.8347`, but
that score is from exp_0020 in the pre-split July run. The epoch-4 experiments
(exp_0025–0027, 0.820–0.823) ran on the frozen DEV split and are not
comparable to it. The honest current baseline is **0.8227 on DEV**.
