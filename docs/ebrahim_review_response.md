# Review response: overfitting, non-inferiority, refusals, metrics

Prep for the discussion with Ebrahim. Covers what the project did, what he
flagged, what the code actually does, and where each point stands now.

Date: 2026-07-21

---

## 1. What we did (the project in plain terms)

Goal: can an **AI-generated** knowledge base match a **human-curated** KB as the
retrieval source for a smoking-cessation RAG chatbot?

- A generation prompt produces QA pairs from source content. An evolutionary
  optimization loop (evo) iterates that prompt across ~20 experiments, keeping
  or discarding each change based on a faithfulness score.
- Winning config: `exp_0020`. Large-scale validation reached 83.5% of the human
  baseline on the loop's own metric.
- Final validation with RAGAS reported **faithfulness parity**: AI 0.82 vs
  human 0.77, and a two-sided Wilcoxon test found the difference "not
  significant," which was read as parity.

## 2. What Ebrahim flagged (his four points)

1. **Benchmark overfitting.** If the same 150 questions select prompts, analyze
   failure traces, and drive keep/discard, they are no longer a true test set.
   Fix: use the 150 as a dev set and test on a new unseen set, or freeze the
   config and treat the 150 as test.
2. **No equivalence / non-inferiority test.** "Not significant" is not the same
   as "equivalent." Need a proper test with a pre-defined acceptable margin.
3. **Refusals scored as zero.** Scoring an appropriate refusal as 0 is wrong.
4. **Metric coverage.** Also evaluate retrieval relevance, context recall,
   answer completeness, hallucination, and appropriate refusal.

## 3. What the code actually does (verified)

| Claim | Evidence | Verdict |
|---|---|---|
| Loop selects on a fixed subset | `data_gen_prepare.py:61,102` — `N_EVAL=20`, `rows[:20]` of `test_set_150q.xlsx`, every experiment | Confirmed |
| Final metric reuses the same file | `ragas_evaluation.py` → `load_test_set(test_set_150q.xlsx, 100)` (`ragas_utils.py:24`) | Confirmed — no holdout split |
| Stats test is two-sided only | `statistical_tests.py:163,368` — Wilcoxon two-sided; parity read from "ns" | Confirmed gap |
| Empty answer scored 0.0 | `data_gen_prepare.py:434` | Confirmed for *empty*; RAGAS failures are NaN-filtered, not zeroed (`ragas_utils.py:81`) — need to confirm which pipeline he saw |
| Which metrics ran | JSON `all_scores`: faithfulness, answer_relevancy, context_precision, context_recall, all 100q, both arms | Retrieval relevance + context recall **already exist** |

## 4. Overfitting: quantified, and re-analyzed on held-out data

The loop saw the first 20 rows. 16 of them survive into the 100-question RAGAS
test set (4 were LFV-flagged out). So **16% of the reported test set was
directly optimized against.**

Re-analysis removing those 16 (`code/scripts/holdout_noninferiority.py`, no API
calls, reuses stored per-question scores):

| Slice | n | AI | Human | AI − Human |
|---|---|---|---|---|
| Full 100 (as reported) | 100 | 0.817 | 0.771 | +0.046 |
| Contaminated overlap only | 16 | 0.946 | 0.902 | +0.044 |
| **Held-out (loop-seen removed)** | **84** | **0.792** | **0.746** | **+0.046** |

Reading: contamination inflated both **absolute** scores by ~2 points (the seen
questions are easy and score ~0.90+), but the **AI-vs-human gap is identical
everywhere** (+0.044 to +0.046). The overfitting concern is valid for the
headline number; the comparative conclusion is not driven by it.

## 5. Non-inferiority test (pre-defined margin δ = 0.05)

On the held-out 84, paired non-inferiority test (H0: AI worse than human by ≥ δ):

- **p = 0.0028 → AI is statistically non-inferior to human.**
- Two-sided TOST equivalence at ±0.05 does *not* pass, because the AI edge
  (+0.046) trends toward the upper margin. That is a stronger result than
  parity, not a weaker one: AI is non-inferior and leans better.

δ = 0.05 is a placeholder. **Agree the margin with Ebrahim before final
reporting** — it is a clinical/product judgment, not a statistical one.

## 6. Status of each point

| # | Point | Status | Left to do |
|---|---|---|---|
| 1 | Overfitting | Quantified + held-out re-report done | Author a fresh unseen test set for the paper's headline claim |
| 2 | Non-inferiority | Test built + run on held-out | Agree δ; also non-inferiority testing was designed post-hoc, so pre-register it |
| 3 | Refusals = 0 | Empty→0 confirmed; refusal path needs pinning | Confirm which pipeline he saw; add refusal detection → separate label, not 0 |
| 4 | Metric coverage | Retrieval relevance + context recall already run | Add answer completeness + appropriate-refusal axes; report precision/recall alongside faithfulness |

## 7. Open questions for the discussion

- What margin δ is clinically acceptable for faithfulness non-inferiority?
- New unseen test set: who authors it, how many questions, same distribution?
- Point 3: is the "refusals = 0" behavior in the n=20 LLM-judge benchmark or the
  RAGAS run? Determines the fix location.
- Should the paper's headline number be the held-out 84 (0.79 vs 0.75), not the
  contaminated 100 (0.82 vs 0.77)?
