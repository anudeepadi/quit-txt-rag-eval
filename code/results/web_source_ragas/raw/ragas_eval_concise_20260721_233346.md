# RAGAS Evaluation Results

**Generated:** 2026-07-21T23:46:56.780491
**n:** 100 questions  |  **Model:** gpt-4o-mini

## Faithfulness Summary (Comparison with Ebrahim's Results)

| Configuration | Mean | SD | Median | 95% CI | Hallucination Rate | % High-Risk (<0.5) | n |
|---|---|---|---|---|---|---|---|
| Ibrahim: Base LLM | 0.58 | 0.22 | 0.61 | [0.42–0.74] | 0.40 | 20% | 10 |
| Ibrahim: WebRAG | 0.86 | 0.11 | 0.88 | [0.84–0.88] | 0.14 | 4% | 100 |
| Ours: AI-Generated RAG | 0.72 | 0.37 | 1.00 | [0.65–0.79] | 0.28 | 22% | 100 |

## Full RAGAS Metrics

| Configuration | Faithfulness | Answer Relevancy | Context Precision | Context Recall |
|---|---|---|---|---|
| Ours: AI-Generated RAG | 0.718 ± 0.368 | 0.495 ± 0.438 | 0.377 ± 0.448 | 0.216 ± 0.322 |