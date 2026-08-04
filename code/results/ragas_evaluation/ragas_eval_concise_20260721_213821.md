# RAGAS Evaluation Results

**Generated:** 2026-07-21T21:43:37.676252
**n:** 10 questions  |  **Model:** gpt-4o-mini

## Faithfulness Summary (Comparison with Ebrahim's Results)

| Configuration | Mean | SD | Median | 95% CI | Hallucination Rate | % High-Risk (<0.5) | n |
|---|---|---|---|---|---|---|---|
| Ibrahim: Base LLM | 0.58 | 0.22 | 0.61 | [0.42–0.74] | 0.40 | 20% | 10 |
| Ibrahim: WebRAG | 0.86 | 0.11 | 0.88 | [0.84–0.88] | 0.14 | 4% | 100 |
| Ours: AI-Generated RAG | 0.86 | 0.23 | 1.00 | [0.72–1.00] | 0.14 | 10% | 10 |

## Full RAGAS Metrics

| Configuration | Faithfulness | Answer Relevancy | Context Precision | Context Recall |
|---|---|---|---|---|
| Ours: AI-Generated RAG | 0.865 ± 0.233 | 0.484 ± 0.445 | 0.333 ± 0.451 | 0.233 ± 0.417 |