# RAGAS Evaluation Results

**Generated:** 2026-03-10T18:54:40.415609
**n:** 100 questions  |  **Model:** gpt-4o-mini

## Faithfulness Summary (Comparison with Ebrahim's Results)

| Configuration | Mean | SD | Median | 95% CI | Hallucination Rate | % High-Risk (<0.5) | n |
|---|---|---|---|---|---|---|---|
| Ibrahim: Base LLM | 0.58 | 0.22 | 0.61 | [0.42–0.74] | 0.40 | 20% | 10 |
| Ibrahim: WebRAG | 0.86 | 0.11 | 0.88 | [0.84–0.88] | 0.14 | 4% | 100 |
| Ours: AI-Generated RAG | 0.72 | 0.38 | 1.00 | [0.65–0.80] | 0.28 | 20% | 100 |
| Ours: Human-Curated RAG | 0.79 | 0.35 | 1.00 | [0.72–0.86] | 0.21 | 17% | 100 |

## Full RAGAS Metrics

| Configuration | Faithfulness | Answer Relevancy | Context Precision | Context Recall |
|---|---|---|---|---|
| Ours: AI-Generated RAG | 0.724 ± 0.376 | 0.564 ± 0.436 | 0.481 ± 0.477 | 0.259 ± 0.335 |
| Ours: Human-Curated RAG | 0.789 ± 0.352 | 0.708 ± 0.377 | N/A | 0.423 ± 0.375 |