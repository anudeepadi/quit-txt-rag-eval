# Evaluation Re-Run Plan — Paper-Quality Results

**Date:** March 12, 2026
**Target:** ACL BioNLP 2026 Workshop (deadline: April 17, 2026)

---

## Overview

The current evaluation (run 20260310_181939) is missing the **baseline** configuration in concise mode. Additionally, **context_precision** has NaN values for human_rag and web_rag, **BERTScore** is not computed, and **statistical significance tests** are absent. This plan addresses all four gaps.

---

## Prerequisites

```bash
# 1. Install dependencies (if not already installed)
pip install -r requirements.txt

# 2. Verify OPENAI_API_KEY is set
grep OPENAI_API_KEY .env
# Should show your key. If not: echo "OPENAI_API_KEY=sk-..." >> .env

# 3. Verify test set exists
ls data/test_set/test_set_150q.xlsx
```

---

## Step 1: Re-Run RAGAS with Baseline (CRITICAL)

**What this does:** Generates baseline (no-RAG) answers for 100 questions in concise mode, then runs RAGAS scoring across ALL 4 configs. The `--resume` flag means ai_rag, human_rag, and web_rag will skip answer generation (already checkpointed) but ALL configs will be re-scored by RAGAS, which fixes the context_precision NaN issue.

```bash
python scripts/ragas_evaluation.py \
    --configs baseline ai_rag human_rag web_rag \
    --max-questions 100 \
    --concise \
    --resume
```

**Expected behavior:**
- Baseline: generates 100 new answers (~2 min with rate limiting)
- ai_rag / human_rag / web_rag: skips to "checkpoint" for all 100 questions
- RAGAS scoring: runs faithfulness + answer_relevancy + context_precision + context_recall for all 4 configs
- Rate limit cooldowns: ~65s between metrics, ~120s between configs
- **Total estimated time: 45-90 minutes** (depends on API rate limits)

**Output files:**
- `results/ragas_evaluation/ragas_eval_concise_YYYYMMDD_HHMMSS.json` — full results
- `results/ragas_evaluation/ragas_eval_concise_YYYYMMDD_HHMMSS.md` — summary table
- `results/ragas_evaluation/checkpoint_concise_baseline_100.jsonl` — baseline answers

**What to check after:**
1. All 4 configs have faithfulness scores (not NaN)
2. context_precision has values for human_rag and web_rag (was NaN before)
3. Baseline faithfulness should be lower than RAG configs (validates RAG benefit)

---

## Step 2: Run BERTScore Evaluation

**What this does:** Computes BERTScore (Precision, Recall, F1) for all 4 configs using the checkpoint JSONL files. Uses DeBERTa-xlarge-mnli embeddings for semantic similarity against ground truth.

```bash
# Install bert-score if not already installed
pip install bert-score

python scripts/bertscore_evaluation.py \
    --configs baseline ai_rag human_rag web_rag \
    --max-questions 100
```

**Expected behavior:**
- Loads checkpoint files for each config
- Computes BERTScore against ground truth references
- **Total estimated time: 5-15 minutes** (CPU-only; faster with GPU)

**Output files:**
- `results/bertscore/bertscore_YYYYMMDD_HHMMSS.json` — per-question scores
- `results/bertscore/bertscore_YYYYMMDD_HHMMSS.md` — summary table

**Note:** Step 2 requires Step 1 to complete first (needs baseline checkpoint).

---

## Step 3: Run Statistical Significance Tests

**What this does:** Runs paired Wilcoxon signed-rank tests between all config pairs for each metric, computes Cliff's delta effect sizes, and generates bootstrap 95% confidence intervals.

```bash
python scripts/statistical_tests.py \
    --configs baseline ai_rag human_rag web_rag
```

**Expected behavior:**
- Loads RAGAS scores from the latest results JSON
- Loads BERTScore F1 scores (if available from Step 2)
- Runs 6 pairwise comparisons × 5 metrics = 30 tests
- **Total estimated time: < 1 minute**

**Output files:**
- `results/statistical_tests/statistical_tests_YYYYMMDD_HHMMSS.json` — all test results
- `results/statistical_tests/statistical_tests_YYYYMMDD_HHMMSS.md` — formatted report

**Key questions this answers:**
- Is human_rag (0.789) significantly better than ai_rag (0.724)? → p-value tells you
- Is any RAG config significantly better than baseline? → validates the core hypothesis
- How large are the differences? → Cliff's delta gives effect size

---

## Complete Run Sequence

```bash
# Full pipeline — run these in order:

# Step 1: RAGAS with baseline (~45-90 min)
python scripts/ragas_evaluation.py \
    --configs baseline ai_rag human_rag web_rag \
    --max-questions 100 \
    --concise \
    --resume

# Step 2: BERTScore (~5-15 min)
python scripts/bertscore_evaluation.py \
    --configs baseline ai_rag human_rag web_rag \
    --max-questions 100

# Step 3: Statistical tests (< 1 min)
python scripts/statistical_tests.py \
    --configs baseline ai_rag human_rag web_rag
```

**Total estimated time: ~1-2 hours**
**Estimated API cost: ~$2-5 (GPT-4o-mini for 100 baseline answers + RAGAS scoring)**

---

## What You'll Have After

| Metric | Before | After |
|---|---|---|
| Baseline scores | Missing | Complete |
| context_precision | NaN for 2 configs | Complete for all |
| BERTScore | Not computed | Full P/R/F1 per config |
| Statistical tests | None | Wilcoxon + Cliff's d + 95% CI |
| Paper readiness | Not publishable | Ready for ACL BioNLP submission |

---

## Troubleshooting

**Rate limit errors during RAGAS scoring:**
The script includes 65s cooldowns between metrics and 120s between configs. If you still hit rate limits, increase `_METRIC_COOLDOWN` and `_INTER_CONFIG_COOLDOWN` in `ragas_evaluation.py`.

**BERTScore runs slowly:**
By default it uses CPU. If you have a GPU, the `bert_score` library will auto-detect and use it. You can also use a lighter model: `--model-type roberta-large` (faster but slightly less accurate).

**Checkpoint corruption:**
If a run is interrupted, delete the partial checkpoint and re-run:
```bash
rm results/ragas_evaluation/checkpoint_concise_baseline_100.jsonl
# Then re-run Step 1
```

**Missing OPENAI_API_KEY:**
```bash
export OPENAI_API_KEY="sk-your-key-here"
# Or add to .env file
```
