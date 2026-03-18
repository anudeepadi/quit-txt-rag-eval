# QuitTxt RAG Evaluation — Testing Bundle

**Date:** March 13, 2026
**Questions:** 100 (from 150-question test set)
**Model:** gpt-4o-mini (concise mode)

## What's in here

### Checkpoint files (generated answers + contexts)
Each line is one question with: question, generated answer, retrieved contexts, and ground truth.

| File | Config | Description |
|---|---|---|
| `checkpoint_concise_baseline_100.jsonl` | Baseline | No RAG — raw LLM answers |
| `checkpoint_concise_ai_rag_100.jsonl` | AI RAG | RAG with 5,936 AI-generated QA pairs |
| `checkpoint_concise_human_rag_100.jsonl` | Human RAG | RAG with 4,431 human-curated QA pairs |
| `checkpoint_concise_web_rag_100.jsonl` | Web RAG | RAG with 278 web-scraped QA pairs |

### Evaluation results (scored)
| File | What |
|---|---|
| `ragas_eval_concise_20260312_212656.json` | RAGAS scores: ai_rag + human_rag (4 metrics) |
| `ragas_eval_concise_20260312_220211.json` | RAGAS scores: baseline only |
| `bertscore_20260313_003525.json` | BERTScore P/R/F1 for all 4 configs |
| `statistical_tests_20260313_015454.json` | Wilcoxon tests + Cliff's delta + bootstrap 95% CIs |

### Reference
| File | What |
|---|---|
| `test_set_150q.xlsx` | Full 150-question test set (100 used in evals) |

## Quick start

```python
import json

# Load a checkpoint file
with open("checkpoint_concise_human_rag_100.jsonl") as f:
    rows = [json.loads(line) for line in f]

# Each row has: q_idx, question, answer, contexts, ground_truth
print(rows[0]["question"])
print(rows[0]["answer"])
print(rows[0]["ground_truth"])
```

## Key results snapshot

| Config | Faithfulness | Answer Relevancy | BERTScore F1 |
|---|---|---|---|
| Baseline | 0.147 | 0.832 | 0.898 |
| AI RAG | 0.727 | 0.564 | 0.885 |
| Human RAG | 0.800 | 0.709 | 0.889 |
| Web RAG | 0.719 | 0.526 | 0.883 |
