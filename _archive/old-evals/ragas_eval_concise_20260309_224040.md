# RAGAS Evaluation Results

**Generated:** 2026-03-09T22:58:50.371153
**n:** 20 questions  |  **Model:** gpt-4o-mini

## Faithfulness Summary (Comparison with Ebrahim's Results)

| Configuration | Mean | SD | Median | 95% CI | Hallucination Rate | % High-Risk (<0.5) | n |
|---|---|---|---|---|---|---|---|
| Ibrahim: Base LLM | 0.58 | 0.22 | 0.61 | [0.42–0.74] | 0.40 | 20% | 10 |
| Ibrahim: WebRAG | 0.86 | 0.11 | 0.88 | [0.84–0.88] | 0.14 | 4% | 100 |
| Ours: Baseline | N/A | N/A | N/A | N/A | N/A | N/A | 0 |
| Ours: AI-Generated RAG | 0.78 | 0.40 | 1.00 | [0.60–0.95] | 0.22 | 20% | 20 |

## Full RAGAS Metrics

| Configuration | Faithfulness | Answer Relevancy | Context Precision | Context Recall |
|---|---|---|---|---|
| Ours: Baseline | N/A | 0.776 ± 0.345 | N/A | N/A |
| Ours: AI-Generated RAG | 0.777 ± 0.405 | 0.553 ± 0.429 | 0.558 ± 0.490 | 0.424 ± 0.392 |