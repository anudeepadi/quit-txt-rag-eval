# Dataset Generation Protocol

Reproducibility protocol for the AI-generated QA dataset, per reviewer
requirements (Ebrahim, 2026-07-27). Governs every generated dataset version,
including per-experiment KBs produced inside the evo optimization loop.

## 1. What the AI-generated dataset is intended to improve

Stated claim, against the expert-curated KB (4,431 pairs):

| Dimension | Claim | Evidence base |
|---|---|---|
| **Scalability** | Primary. Generation is ~$1 and ~15 min per full KB vs months of clinician time; the pipeline regenerates the KB from any updated source. | Cost/time of epoch-4 runs |
| **Conversational phrasing** | Generated questions target the texting register of a quit-line user rather than clinical FAQ phrasing. | tone dim of the quality judge (currently 0.760 — below target; active optimization axis) |
| **Retrieval suitability** | Pairs are shaped for chunk-level retrieval (self-contained answers, question-form keys). | RAGAS context precision/recall comparison; currently WORSE than human (0.590/0.356 vs 0.628/0.418 held-out) — an honest open gap, not a claim |
| **Coverage** | NOT claimed. The generated KB derives from the human KB as source, so its coverage is bounded above by the source (circularity documented in `docs/methodology_and_review_detail.md`). Web-source generation is the planned path to genuine coverage gains. | held-out refusal analysis |
| **Structure** | Uniform pair schema with per-pair provenance (below) — machine-checkable, which hand-curated content does not provide. | this protocol |

Faithfulness parity (non-inferiority at δ=0.05, p=0.0028 held-out) is the
safety floor that makes the scalability claim usable, not the headline
improvement claim.

## 2. Provenance: every pair links to its source

Every generated pair carries, at generation time:

```json
{
  "question": "...",
  "answer": "...",
  "source_id": "chunk_017",
  "source_sha256": "<sha256 of the exact source chunk text>",
  "source_excerpt": "<first 300 chars of the source chunk>"
}
```

- `source_id` indexes into the run's chunk list (order is deterministic:
  RANDOM_SEED=42).
- `source_sha256` pins the exact text the pair was generated from, so
  hallucination analysis can re-fetch the full chunk from the manifest's
  source snapshot even after the source file changes.
- Persisted in `generated_artifacts/generated_kb.jsonl` per run. The RAG
  index strips provenance fields before embedding (retrieval sees only Q/A,
  identical to pre-protocol behavior — score-neutral).

## 3. Acceptance criteria (defined before optimization round 1)

A generated pair is **acceptable** iff:

| # | Criterion | Check | Enforcement (epoch 4) |
|---|---|---|---|
| A1 | Well-formed | question > 10 chars, answer > 20 chars | **Enforced** (pre-existing filter); rejections now counted |
| A2 | Not a duplicate | normalized-question exact match; fuzzy (Jaccard ≥ 0.9) | **Counted, not filtered** |
| A3 | Factually consistent with source | groundedness judge vs the pair's own source chunk | **Sampled** (seeded n=15/run, pre-existing) |
| A4 | No unsupported content | same judge, groundedness dim | **Sampled** (same n=15) |
| A5 | Complete answer | covers the source content the question targets | Deferred to epoch 5 (needs per-pair judge; cost) |
| A6 | Relevant to smoking-cessation counseling | clinical-accuracy judge dim as proxy | **Sampled** (same n=15) |

Epoch-4 enforcement is deliberately **reporting-only** beyond A1: adding
filters mid-epoch would change scores and break experiment comparability.
Counters feed the manifest (below), so every optimization experiment records
its accepted/rejected/duplicate counts. Filtering (A2 hard-reject, A3/A4
per-pair) is an epoch-5 harness change, to be decided with the reviewer.

## 4. Dataset version manifest

Every generation run writes `generated_artifacts/dataset_manifest.json`:

```json
{
  "generated_at": "<ISO timestamp>",
  "harness_commit": "<git HEAD of the worktree>",
  "hypothesis": "<config HYPOTHESIS string>",
  "source_snapshot": {
    "file": "datasets/human-rag/human_curated_qa.jsonl",
    "sha256": "<file hash>",
    "n_pairs": 4431,
    "n_chunks": 444
  },
  "model": "gpt-4o-mini",
  "parameters": {"temperature": 0.0, "max_tokens": 2500, "qa_per_source": 8},
  "system_prompt": "<full generation prompt text>",
  "counts": {
    "n_raw": 0, "n_rejected_wellformed": 0,
    "n_duplicate_exact": 0, "n_duplicate_fuzzy": 0, "n_kept": 0
  },
  "quality_sample": {"n": 15, "specificity": 0.0, "conversational_tone": 0.0,
                     "groundedness": 0.0, "clinical_accuracy": 0.0}
}
```

Interpretability rule: no dataset number is quotable without its manifest.

## 5. Reproduction

```bash
pip install -r requirements.txt            # pinned; ragas hard-pinned
# OPENAI_API_KEY in code/.env
python3 code/autoresearch/run_data_gen_experiment.py
# -> generated_artifacts/generated_kb.jsonl + dataset_manifest.json
```

Determinism boundary (documented, not claimed away): chunking and sampling are
seeded (RANDOM_SEED=42); OpenAI generation is not bit-reproducible even at
temperature 0.0. Reproduction therefore means same-manifest regeneration with
statistically equivalent quality counters, not byte-identical pairs. The
manifest is what makes two versions comparable.

## Evaluation-side reproducibility (already in place)

- Dev/test split frozen with SHA manifest (`datasets/eval-rag/question_split_manifest.json`);
  optimization sees only the 50 dev questions; the frozen 77 are locked behind
  `EVO_OPTIMIZING` (reads raise `TestSetLeakError`).
- Statistical protocol: paired non-inferiority + TOST with pre-agreed margin
  (`code/scripts/holdout_noninferiority.py`).
