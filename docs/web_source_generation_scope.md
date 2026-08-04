# Scope: Web-Source Generation + Autoresearch

July 21, 2026 — proposal, not yet started

## The question this answers

The current result is deliberately circular: the AI KB is generated *from* the
human-curated KB, so it can restructure that knowledge but never exceed its
coverage, and the "automates curation" claim is weakened by needing the human
KB as input. The stronger, non-circular experiment: generate the KB from
primary web sources (the same authority sites the project already uses), then
run the autoresearch loop on top. If that KB matches or beats the human-curated
KB, the claim becomes: *an AI pipeline can build a retrieval knowledge base
from freely available sources that performs on par with expert curation* —
with the marginal-cost argument fully intact.

Evidence it can work: retrieval over web-derived content already scores 0.86
faithfulness in the reference evaluation (WebRAG) — the highest of any
configuration, above both our optimized AI KB (0.82) and the human KB (0.77).

## What exists already

- 278 web QA pairs from 28 authority domains (CDC, Cleveland Clinic, AAFP,
  smokefree.gov, UCSF, ...), each carrying its source URL
  (`datasets/eval-rag/web_scraped_qa.jsonl`).
- A working scraper/builder (`code/scripts/build_web_dataset.py`) that fetches
  up to 10K chars per page. The original URL list file is gone, but the URLs
  are recoverable from the pairs.
- The optimized generation mechanism (exp_0020's register-translation prompt),
  the strict-refusal judge, the RAGAS pipeline, and the evo machinery — all
  reusable as-is or with small source-loader changes.

## Phases

**Phase 0 — rebuild the source corpus (half a day, ~$0).**
Reconstruct the URL list from the 278 pairs, re-scrape, and this time keep the
raw page text as the generation source (the QA pairs were kept before; the
underlying documents were not). Decision point below on corpus size.

**Phase 1 — web-source KB baseline (1 day, ~$2).**
Run the exp_0020 generation prompt over web-page chunks instead of human-KB
chunks (a small loader swap in `data_gen_prepare.py`). Evaluate under both
judges: the strict-refusal harness (150 questions) and the paper's RAGAS
pipeline (n=100 concise), against the human KB and the existing numbers. This
alone answers whether web-source generation is competitive before any
optimization is spent on it.

**Phase 2 — autoresearch on top (1–2 nights, ~$5–15).**
New evo epoch with the web-source benchmark: same integrity gates, verifier
audits, and measured-noise discipline as before. Likely levers: chunking
strategy, pairs-per-page, register mechanism re-validation on messier source
text, and source-citation constraints. Stop rule: stall after ~4 rounds or
parity with WebRAG's 0.86.

**Phase 3 — write-up (half a day).**
Extend the findings doc: circular vs non-circular comparison table across all
five configurations under one pipeline.

## Risks and honest caveats

1. **Grounding.** Web text is messier than the vetted human KB; generation can
   invent. Mitigations already built: deterministic refusal scoring,
   groundedness floors, verifier audits that catch source-absent content (they
   caught three such inflations in the last run).
2. **Coverage ceiling.** 28 pages ≈ roughly 50K words vs the human KB's much
   larger corpus. The 150 test questions may cover topics absent from those
   pages — the same source-parity trap the last run exposed. This is the main
   reason Phase 0 has a corpus-size decision.
3. **Test-set provenance.** If the test questions were authored against
   human-KB topics, the web arm starts disadvantaged. Worth one team question
   before over-interpreting any gap.
4. **Attribution.** The web KB inherits source URLs; the paper should state
   scraping was for research use of public health-authority content.

## Decision needed before starting

**Corpus size.** Two options:
- *Minimal*: the existing 28 pages. Fastest, most comparable to WebRAG, but
  coverage-capped.
- *Expanded*: crawl additional pages from the same 28 authority domains (target
  ~100–200 pages). Better coverage for the 150-question set; one extra
  half-day and a stronger result if it works. Recommended.

Total estimate either way: 2–4 working days, $10–20 of API spend.
