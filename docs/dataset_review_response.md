# Response to the dataset-generation review

Companion to [`ebrahim_review_response.md`](ebrahim_review_response.md), which
answers the four evaluation-methodology points. This one answers the four
dataset-generation points raised afterwards.

The full protocol is in
[`dataset_generation_protocol.md`](dataset_generation_protocol.md). This
document reports what the protocol produced and names the two decisions still
outstanding.

## Status

| # | Point | Status |
|---|---|---|
| 1 | Specify what the AI dataset improves over expert content | Done |
| 2 | Link every QA pair to its source / evidence span | Done at chunk level; span-level gap below |
| 3 | Define what makes a generated sample acceptable | Measured, thresholds needed |
| 4 | Record source, model, prompt, parameters, date, accept/reject counts | Done |

## 1. What the generated dataset is for

Claimed: **scalability, conversational phrasing, structure.**

Not claimed: **coverage.** The generated KB is derived from the expert KB, so
it cannot cover more ground than its source. Saying otherwise would be
indefensible in review.

Open: **retrieval suitability.** Generated pairs are shorter and phrased as
text-message exchanges, which plausibly helps embedding-based retrieval, but
we have not isolated that effect from the phrasing change.

## 2. Provenance

Every generated pair carries `source_id`, `source_sha256`, and
`source_excerpt`, written to `generated_artifacts/generated_kb.jsonl`.
Provenance is stripped before the RAG index is built, so retrieval input is
byte-identical to the pre-instrumentation runs and none of this moves the
scores.

Verified on the most recent run (exp_0027, 1,736 pairs):

- 216 distinct source chunks, 8 pairs per chunk, perfectly blocked
- Lexical overlap between a pair and its own source: **0.180**
- Same measure against a shifted source (null baseline): **0.076**

The links are real, not incidental.

**The gap, stated plainly.** `source_excerpt` stores the first 300 characters
of the chunk. Each chunk yields 8 pairs drawn from the whole chunk, so many
pairs rest on text past that cutoff. **5.4% of pairs share no content words
with their stored excerpt.** Provenance is therefore chunk-level, not the
per-pair evidence span the review asked for.

For hallucination analysis this matters: verifying a pair against a 300-char
preview that does not contain its supporting sentence would produce false
positives. Fixing it means storing the specific supporting sentence per pair,
which is a small harness change. **Do you want it before the next optimization
run, or as a follow-up?**

## 3. Acceptance criteria — thresholds needed

Criteria were fixed before optimization round 1. Enforcement beyond
well-formedness is deliberately **reporting-only**: adding filters mid-epoch
would shift scores and break comparability between experiments that were
supposed to differ only by prompt.

Measured on the two most recent runs:

| | exp_0026 | exp_0027 |
|---|---|---|
| Raw pairs | 1,877 | 1,736 |
| Rejected, not well-formed | 0 | 0 |
| Exact duplicates | 28 | 9 |
| Fuzzy duplicates (Jaccard >= 0.9) | 7 | 5 |
| Kept | 1,877 | 1,736 |
| Groundedness (n=15 sample) | 0.953 | 0.973 |
| Clinical accuracy (n=15) | 0.893 | 0.940 |
| Specificity (n=15) | 0.693 | 0.687 |
| Conversational tone (n=15) | 0.740 | 0.840 |

Note the duplicates are counted but still kept, so the "kept" figure equals
the raw figure by construction.

What we need from the review:

| # | Criterion | Now | Needs |
|---|---|---|---|
| A1 | Well-formed | Enforced | no change |
| A2 | Not a duplicate | Counted only | hard-reject exact and fuzzy? |
| A3 | Factually consistent with source | Sampled n=15 | minimum groundedness |
| A4 | No unsupported content | Sampled n=15 | same judge |
| A5 | Answer completeness | Deferred | include from epoch 5? |
| A6 | Relevant to smoking-cessation counseling | Sampled n=15 | minimum clinical accuracy |

The n=15 sample is thin for setting a hard threshold. Per-pair judging on
A3/A4 is affordable but not free; worth deciding together rather than
unilaterally.

## 4. Version manifest

Each run writes `generated_artifacts/dataset_manifest.json` with the source
file and its SHA-256, harness commit, hypothesis, model, the full system
prompt, parameters (temperature, max_tokens, qa_per_source), timestamp,
accept/reject/duplicate counts, and the quality sample.

Working rule: **no dataset number is quotable without its manifest.**

## Tests

`code/tests/test_holdout_noninferiority.py` covers the non-inferiority and
TOST functions the parity claim depends on. Seven cases, no API calls. The
load-bearing one asserts that an arm 0.10 worse than the reference **fails** —
without it, a passing verdict proves nothing.

```bash
python code/tests/test_holdout_noninferiority.py
```

## Correction to an earlier number

`evo status` reports `best=0.8347`. That score belongs to exp_0020 from the
July run, before the dev/test split existed. The epoch-4 experiments
(exp_0025 to exp_0027, 0.820 to 0.823) ran on the frozen 50-question dev
split and are not comparable to it. The honest current baseline is **0.8227
on dev**.
