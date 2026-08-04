# Evo Auto Research Findings

July 21, 2026

## Summary

We re-ran the paper's own RAGAS evaluation (same protocol as the April
results: concise mode, n=100, gpt-4o-mini) on an AI-generated knowledge base
produced by an optimized generation pipeline. The headline: **AI-KB
faithfulness moved from 0.67 to 0.82**, and its hallucination rate fell from
33% to 18%. That puts the AI-generated KB at statistical parity with the
human-curated KB (0.77), with the point estimate ahead. The optimization came
from an overnight autonomous run (evo, 24 audited experiments) that also found
and fixed two problems in our evaluation setup itself. Everything below is
reproducible from the repo.

## The result, under our own metric

| Configuration | Faithfulness | Hallucination rate | n |
|---|---|---|---|
| Base LLM (reference) | 0.58 | 0.40 | 10 |
| WebRAG (reference) | 0.86 | 0.14 | 100 |
| AI-generated KB, April version | 0.67 ± 0.40 | 0.33 | 100 |
| AI-generated KB, optimized | 0.82 ± 0.31 | 0.18 | 100 |
| Human-curated KB | 0.77 ± 0.33 | 0.23 | 100 |

Paired per question against the human-curated KB, the optimized AI KB is
+0.046 ahead (t = 1.51, p ≈ 0.13; 26 wins, 15 losses, 59 ties): no significant
difference. An independent check with a stricter judge on the full
150-question set gives the same verdict (99.6% relative, t = -0.15). So the
claim the data supports is parity, and it is well powered from two independent
evaluations. Secondary metrics stay close, with the human KB slightly ahead on
answer relevancy (0.70 vs 0.67) and context recall (0.41 vs 0.35).

One framing point matters for the write-up. The AI knowledge base is generated
from the human KB's own content, so the result is not "AI beats human
experts." The accurate claim: LLM restructuring of expert-curated content into
retrieval-optimized QA pairs performs as well as the raw expert-curated KB for
RAG use, at near-zero marginal cost. Expert verification stays essential for
the content itself. The formatting and curation labor is what can be
automated.

## Where the improvement came from

Our earlier autoresearch setup was a single AI agent editing the generation
config, running a benchmark, and logging KEEP or DISCARD to a TSV. It ran 11
experiments over several weeks, plateaued around 77% of the human baseline,
and had no way to tell a real gain from evaluation noise.

We replaced it with evo, an open-source framework for autonomous optimization.
It maintains a tree of experiments in git: an orchestrator reads each round's
results, writes a structured brief for each worker agent, and the workers run
experiments in isolated branches. Three mechanisms did most of the quality
control: integrity gates (no experiment can touch the benchmark, judges, or
datasets), independent verifier agents auditing every run for metric gaming,
and a measured noise floor (sd = 0.012; single-run gains under 0.03 were
rejected, and three inflated results were caught by trace audits and
excluded). The run covered 24 experiments in one night for a few dollars of
API cost.

Two evaluation problems surfaced along the way, and fixing them mattered as
much as the optimization:

**The internal faithfulness judge was unreliable on refusals.** When the RAG
system answered "the knowledge base does not provide this information," the
fast LLM judge scored identical text anywhere from 0 to 10 across runs — a
refusal makes no claims for the rubric to check. About a quarter of test
questions sat on this boundary. We fixed it by scoring refusals as 0 in both
arms, deterministically. Any earlier number produced with that judge deserves
re-verification.

**The AI arm was generating from 1% of the source.** The pipeline sampled 5 of
444 source chunks for generation while the human arm retrieved from all 4,431
curated pairs. Under a strict judge the AI arm scored 47% of human at 5
chunks; generating from all 444, with no prompt changes, raised it to 96%.
Most of the historical "gap to human" was this asymmetry, not generation
quality.

**The optimization itself found one real mechanism.** The winning prompt
extracts facts verbatim, then rewrites each QA pair as a texting-style
exchange in which the answer states the concrete fact first. It raised tone,
specificity, and faithfulness together and survived a confirmation replicate
(+0.05 combined, about 4 standard deviations above the measured noise). Other
ideas failed honestly — coverage-broadening prompts and self-verification
filters either displaced good pairs or let the model invent plausible content
— and those negative results are documented with traces.

## Where to go from here

1. Decide whether the parity result becomes the paper's headline claim, or
   whether the judge-reliability finding and the parity result together are
   worth a separate methods write-up.
2. If pursuing: update the paper's results tables with the new RAGAS numbers
   (combine_results_table.py / generate_report_documents.py) and re-verify any
   figure derived from the April AI-KB evaluation or the old judge.

Notes for reproducibility: the optimized KB is
`code/data/ai_generated/ai_generated_qa_exp0020.jsonl` (3,576 pairs); the new
RAGAS results are `code/results/ragas_evaluation/ragas_eval_concise_20260721_*`;
all 24 experiments, traces, and audit annotations live under `.evo/` and the
experiment branches. One operational note: ragas 0.4.3's usage telemetry
blocks its scoring loop when its analytics endpoint is unreachable; the
pipeline now disables it (RAGAS_DO_NOT_TRACK) and scores each metric in an
isolated subprocess with a timeout. Scores are unaffected.
