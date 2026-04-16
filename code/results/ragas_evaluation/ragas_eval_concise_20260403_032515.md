# RAGAS Evaluation Results

**Generated:** 2026-04-03T03:34:14.512523
**n:** 100 questions  |  **Model:** gpt-4o-mini

## Faithfulness Summary (Comparison with Ebrahim's Results)

| Configuration | Mean | SD | Median | 95% CI | Hallucination Rate | % High-Risk (<0.5) | n |
|---|---|---|---|---|---|---|---|
| Ibrahim: Base LLM | 0.58 | 0.22 | 0.61 | [0.42–0.74] | 0.40 | 20% | 10 |
| Ibrahim: WebRAG | 0.86 | 0.11 | 0.88 | [0.84–0.88] | 0.14 | 4% | 100 |
| Ours: AI-Generated RAG | 0.63 | 0.39 | 0.75 | [0.55–0.71] | 0.37 | 27% | 100 |

## Full RAGAS Metrics

| Configuration | Faithfulness | Answer Relevancy | Context Precision | Context Recall |
|---|---|---|---|---|
| Ours: AI-Generated RAG | 0.629 ± 0.394 | 0.392 ± 0.439 | N/A | 0.178 ± 0.307 |