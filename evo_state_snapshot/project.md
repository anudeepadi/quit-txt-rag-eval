# QuitTxt Data-Gen Prompt Optimization

## What the target does

`code/autoresearch/data_gen_experiment.py` holds the config for AI QA-pair generation:
`GEN_SYSTEM_PROMPT` (primary lever), `GEN_TEMPERATURE`, `GEN_MAX_TOKENS`, `QA_PER_SOURCE`,
`GEN_MODEL`, plus the RAG-eval params (`RAG_TEMPLATE`, `RAG_MAX_TOKENS`, `RAG_TOP_K`).
`RAG_TEMPERATURE` used to live here; it is now fixed infra (see below).
The paper goal: AI-generated QA knowledge bases that match or beat the
human-curated KB (current best: combined 0.7583, ~77-83% of human on RAG faithfulness).

## What can change vs what must stay stable

- **Changeable**: everything in `data_gen_experiment.py`. The generation prompt accounts
  for ~80% of variance historically. `HYPOTHESIS` must describe each change.
- **Fixed**: `run_data_gen_experiment.py` (harness, and since f60f8e3 the home of
  `RAG_TEMPERATURE`, pinned 0.0), `data_gen_prepare.py` (data loading + LLM judges + TSV
  logging), everything under `datasets/` (incl. the 20-question test slice from
  `test_set_150q.xlsx`). Protected by the `harness_integrity` gate.
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

## Measured noise floor (epoch 5, harness f60f8e3, RAG_TEMPERATURE pinned 0.0)

**Pooled sd = 0.0047**, from two configs at three draws each, all at 444/444
chunk coverage with n_chunks_failed=0, run serially on the 50-question dev
split:

| config | draws | mean | sd |
|---|---|---|---|
| exp_0027 prompt (exp_0034/35/36) | 0.8182, 0.8194, 0.8214 | 0.8197 | 0.0016 |
| exp_0025 prompt (exp_0037/39/40) | 0.8255, 0.8351, 0.8229 | 0.8278 | 0.0064 |

Minimum detectable effect (alpha=.05 two-sided, 80% power):

| replicates/arm | required gap |
|---|---|
| 1 | 0.0186 |
| 3 | 0.0107 |
| 5 | 0.0083 |
| 8 | 0.0066 |
| 12 | 0.0054 |

**Use the pooled figure, never a single config's sd.** The first post-fix
measurement quoted sd = 0.0016 from group A alone — three draws, df=2, which
is far too thin to pin a variance. The very next config came back at 0.0064,
4x larger. A 3-draw sd can be off by a factor of 3 in either direction; a
comparison built on one is overconfident by the same factor. Noise is also
prompt-dependent, so a floor measured on one config does not transfer to
another.

### Why it was 4.6x worse, and what to never do again

Before f60f8e3, the RAG answers scored for faithfulness were sampled at
`RAG_TEMPERATURE = 0.3` from the *agent-editable* config. Faithfulness carries
40% of the combined score, so that single knob produced **92% of all
run-to-run variance**. Five replicates of one identical config
(exp_0029-0033) scored 0.7985-0.8472: **sd 0.0216**, faithfulness alone
ranging 0.12, single-run MDE **0.0854**.

Pinning it to 0.0 in protected infra cut the pooled sd to 0.0047 (4.6x) while
leaving the mean unmoved (0.8194 -> 0.8197). The fix removed noise, not signal.

Consequences that stand:

- **Every epoch-3 and epoch-4 ranking is unproven.** All deltas acted on were
  under 0.025, far inside the old 0.0854 band: exp_0025 vs exp_0027 (0.0013),
  the epoch-4 spread (0.0026), exp_0020 vs exp_0021 (0.0120).
- **The framework will manufacture improvements out of noise.** evo committed
  exp_0031 as "+0.0245 vs parent" when it was a byte-identical replicate of
  its parent's config. Pruned 2026-08-05.
- The pre-f60f8e3 figure (sd 0.0115, MDE 0.03, epoch 2, 20 eval questions) was
  1.9x optimistic, and the prediction that 50-question runs would lower the
  floor was wrong — it went up until the sampler was pinned.
- **Any scoring knob reachable from the editable config is a gaming vector**,
  not just a parameter. `RAG_TEMPERATURE` lowered the score's noise *and*
  raised faithfulness without improving the KB. It now lives in
  `run_data_gen_experiment.py` with `RAG_TEMPLATE`-class protection. Audit the
  rest of the config the same way before trusting a result.
- Paper caveat: all faithfulness numbers produced before f60f8e3 carry roughly
  +/-0.05 and need re-running before publication.

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

## Epoch 5 (harness f60f8e3, RAG_TEMPERATURE pinned 0.0)

Harness change: `RAG_TEMPERATURE` moved from the agent-editable config into
`run_data_gen_experiment.py` and pinned at 0.0. Epoch-4 scores are NOT
comparable to epoch-5 scores.

**Working parent: exp_0037 (the exp_0025 prompt), mean 0.8278 over 3 draws.**

Chosen on 2026-08-06 over the exp_0027 prompt (0.8197). The gap is +0.0082
with 95% CI [-0.0025, +0.0188], t=2.135, df=4, **p=0.0997 — not significant**.
Resolving it properly needs 6 draws per arm (~2 hours). It was accepted on
weaker evidence than that, deliberately:

- all three exp_0025-prompt draws sit above the exp_0027-prompt mean, so the
  direction is consistent even though the magnitude is not established;
- the cost of being wrong is ~0.008, small next to what an optimization round
  should find;
- the alternative was spending another two hours certifying a difference no
  reviewer will ask about.

**Do not report this choice as an experimental result.** It is a working
decision under acknowledged uncertainty. If epoch 5 produces a finalist worth
publishing, re-establish the parent comparison at 6+ draws per arm first.

### Void prior results

Every epoch-3 and epoch-4 ranking is unusable, for two independent reasons:

1. **Truncated corpora.** exp_0025-0027 ran concurrently on 2026-07-27 and lost
   roughly half their source chunks to a shared-TPM 429 storm: exp_0026 covered
   234/444 (52.7%), exp_0027 216/444 (48.6%). The fail-loud guard (7fd5468)
   landed after those runs.
2. **A noisy sampler.** At `RAG_TEMPERATURE = 0.3` the single-run MDE was
   0.0854, larger than every delta the optimization acted on.

Re-tested at full coverage on the pinned harness, the July ranking **inverts**:

| prompt | July | epoch 5 | moved |
|---|---|---|---|
| exp_0025 | 0.8214 | 0.8278 (n=3) | +0.0064 |
| exp_0026 | 0.8201 | 0.8250 (n=1) | +0.0049 |
| exp_0027 | 0.8227 *(picked as best)* | 0.8197 (n=3) | -0.0030 |

Round 1 did not fail. It produced two prompts that beat the baseline and the
measurement picked the wrong winner. Note also that exp_0027 accumulated the
most prompt rules (anchor requirement, first-person framing, basis attachment)
and scores lowest of the three — more constraints made it worse.

### Standing rules

- One run per experiment resolves ~0.019. Anything tighter needs replicates;
  see the MDE table above and use the POOLED sd.
- Never run experiments concurrently — that is what caused the 429 truncation.
- Verify `len({source_id}) == 444` in `generated_kb.jsonl` before trusting any
  score.
- Audit the editable config for other scoring levers. `RAG_TOP_K` and
  `RAG_MAX_TOKENS` are still reachable and both plausibly move the score
  without improving the dataset.
