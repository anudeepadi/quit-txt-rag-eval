# QuitTxt Data-Gen Prompt Optimization

## What the target does

`code/autoresearch/data_gen_experiment.py` holds the config for AI QA-pair generation:
`GEN_SYSTEM_PROMPT` (primary lever), `GEN_TEMPERATURE`, `GEN_MAX_TOKENS`, `QA_PER_SOURCE`,
`GEN_MODEL`, plus the RAG-eval params (`RAG_TEMPLATE`, `RAG_TEMPERATURE`, `RAG_MAX_TOKENS`,
`RAG_TOP_K`). The paper goal: AI-generated QA knowledge bases that match or beat the
human-curated KB (current best: combined 0.7583, ~77-83% of human on RAG faithfulness).

## What can change vs what must stay stable

- **Changeable**: everything in `data_gen_experiment.py`. The generation prompt accounts
  for ~80% of variance historically. `HYPOTHESIS` must describe each change.
- **Fixed**: `run_data_gen_experiment.py` (harness), `data_gen_prepare.py` (data loading +
  LLM judges + TSV logging), everything under `datasets/` (incl. the 20-question test slice
  from `test_set_150q.xlsx`). Protected by the `harness_integrity` gate.
- Caution: `RAG_TEMPLATE` is agent-controlled but used for BOTH the generated-KB arm and
  the human-baseline arm - template changes that inflate faithfulness (e.g. verbatim
  context-copying instructions) are a known gaming vector; treat template experiments
  with suspicion and check the human-baseline number moved in lockstep.

## Benchmark output

One run = generate 40 pairs (5 chunks x 8) -> judge 15 pairs on 4 quality dims -> build
ChromaDB -> 20-question RAG eval (faithfulness judge) -> same eval on human KB baseline.
Score = weighted composite (max, 0-1): 0.40*rag_faithfulness + 0.20*specificity +
0.10*tone + 0.15*groundedness + 0.15*clinical. `relative_pct` (vs human baseline) is the
paper-facing number - track it in run_meta traces even though the composite is the metric.

## Benchmark determinism

Sampling-based, variance expected: source-chunk selection is seeded (RANDOM_SEED=42) and
judges run at temp=0.0, but generation runs at the config's temperature and OpenAI is not
bit-deterministic even at 0.0. Treat deltas under ~0.02 as noise; re-run before promoting
a marginal winner.

## Environment

- Needs `OPENAI_API_KEY` (loaded via `evo env` from `code/.env`; the file is untracked so
  worktrees rely on the env evo injects, not the file).
- Python deps: `openai`, `chromadb`, `openpyxl` (system python3 at /usr/local/bin/python3),
  plus `evo-hq-agent` (SDK instrumentation).
- Instrumentation: SDK mode, committed on `evo/run_0000/exp_0000` (ab25928). Per-item
  tasks `qa_pair_01..15` and `rag_q_01..20`; composite passed explicitly to
  `run.finish(score=...)`; aggregate breakdown in the `run_meta` trace.

## Resource profile (for run sizing)

Binding resource: OpenAI API (~120 gpt-4o-mini calls/run, a few cents, ~3-5 min).
Concurrent benchmark runs are safe (no shared state; ChromaDB is in-memory per process;
the TSV append is per-worktree). Rate limits are the only serialization concern -
subagents=2-3 is comfortable; higher may hit 429s (client has max_retries=5).

## Gates

- `harness_integrity` (root, post): fails if an experiment modifies anything in `code/`
  or `datasets/` other than the target and the append-only results TSV, or drops untracked
  files into those trees (closes the sys.path module-shadowing vector).
- Future candidate: min-groundedness score-threshold gate (needs a `--min-score`-style
  flag; costs a full benchmark re-run per check, so deferred).

## Benchmark gaming risks (Goodhart check, reviewer-audited)

1. **Self-referential faithfulness**: RAG answers are judged against the generated KB's
   own retrieved text - a confidently-wrong KB can still score "faithful". Mitigation:
   human-baseline comparison + clinical-accuracy dim; consider correctness-vs-reference
   scoring as a future metric change (do NOT change mid-run; breaks comparability).
2. **RAG_TEMPLATE gaming** (see above).
3. **Quality sampling `[:15]`**: agent controls QA_PER_SOURCE, so the judged fraction
   shrinks as pair count grows - burying weak pairs past index 15 is possible. Watch for
   QA_PER_SOURCE increases paired with quality jumps.
4. **Judge exception defaults**: `score_faithfulness`/`score_qa_quality` return neutral
   0.5 on API errors (in fixed infra) - API outages read as mediocre rather than error.
   Accepted for now; max_retries=5 reduces exposure.
5. **KB/test-question overlap**: 1 exact + 3 fuzzy matches between human-KB questions and
   the 20 eval questions; the KB is the generation source, so both arms see them. Accepted
   as the paper's same-source design; documented here per reviewer.

## Future experiment candidates

- Correctness-vs-reference-answer scoring alongside faithfulness (metric v2).
- Seeded proportional sampling for quality judging instead of `[:15]`.
- Full 150-question eval for finalists (current slice = first 20).
- Judge-error status propagation instead of 0.5 defaults.

## Task category

task-skills: unset (prompt/config optimization - subagent protocol covers it).

## Epoch 2 (v2 baseline, exp_0005, commit ee18d6c)

Deterministic refusal scoring: `_is_refusal()` first-sentence check in
`score_faithfulness` returns 0.0 before the judge is called, both arms.
Rationale: epoch-1 judge oscillated 0<->1 on near-identical refusal text
(verified rag_q_11/14); refusal = KB coverage failure for this metric's purpose.
v2 baseline: combined 0.6363, faith 0.385 (12/20 refusals), human arm 0.82,
honest relative 47%. Epoch-1 scores are NOT comparable to epoch-2 scores.
OPEN METHODOLOGY QUESTION (user decision): generated arm samples 5 source
chunks while human arm uses the full KB — source-sample asymmetry now dominates
the honest metric. Fixing it means changing N_SOURCE_CHUNKS in fixed infra
(epoch 3) and affects the paper's claim framing.

## Measured noise floor (epoch 2, 4 draws of exp_0013 config)

Combined sd = 0.0115 (range 0.027). Single-run-vs-single-run minimum detectable
effect ~= 0.03. Tone is the stable component (0.78-0.79); faithfulness and the
human arm each carry ~+/-0.02-0.03 residual judge noise on substantive answers.
Do not commit/prune on single-run deltas under 0.03 without replicates.
(Measured at 20 eval questions; 50-question epoch-4 runs should have a LOWER
faithfulness noise floor — re-measure before applying the 0.03 threshold hard.)

## Epoch 4 (dev-split eval, harness commit dbeca27)

Reviewer-driven overfitting fix: eval questions now come from the frozen
dev/test split (`code/shared/question_split.py`) — the loop scores on the
50-question DEV slice; the 77-question TEST slice is frozen for paper
reporting and locked behind `EVO_OPTIMIZING=1` (reads raise TestSetLeakError).
The old 20-question slice was rows[:20] of the sheet, 16 of which leaked into
the paper's reported test set. Epoch-3 scores (best 0.8347) are NOT comparable:
different question set, and the old 20 were the easy end of the sheet — expect
epoch-4 absolute scores to be materially lower. Baseline = exp_0020 config +
epoch-2/3 harness, re-scored on the dev split (exp_0025).

Resource profile update: one run = 50-question eval x2 arms + generation at
full source parity ~= 700 gpt-4o-mini calls, ~10-15 min.

**BENCHMARK RUNS MUST BE SERIALIZED (learned 2026-07-27, the hard way).** Two
concurrent runs each fire 444 parallel generation calls (max_workers=8) into
the SHARED 200k org TPM limit; ~half the chunks 429 and the bare-except path
silently returns zero pairs, so both runs score truncated KBs (exp_0026/002:
210/444 chunks lost; exp_0027/001: 228/444). Both were pruned --invalid.
subagents=2 remains fine for EDITING in parallel, but `evo run` executions
must not overlap the generation phase. The v4.2 harness fail-louds above 5%
chunk-call failures, so a recurrence fails the run instead of corrupting it.

Overlap notes updated (epoch-3 "1 exact + 3 fuzzy" is stale — it was measured
when 5/444 chunks seeded generation; at full source parity the whole human KB
is the generation source):
- DEV(50) vs human KB: 4 verbatim + 21/50 fuzzy (jaccard>=0.6). Symmetric
  across arms (same-source design), inherited from exp_0019/0020.
- FROZEN TEST(77) vs human KB: 1 verbatim + 24/77 (31%) fuzzy. The dev/test
  freeze fixes optimization-fit contamination (the reviewer's objection);
  SOURCE-level contamination is a separate channel it does not cover. Flag
  this when the frozen-test number becomes a paper headline.
