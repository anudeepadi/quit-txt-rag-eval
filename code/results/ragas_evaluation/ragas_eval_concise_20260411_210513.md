# RAGAS Evaluation Results

**Generated:** 2026-04-11T21:41:14.021163
**n:** 100 questions  |  **Model:** gpt-4o-mini

## Faithfulness Summary (Comparison with Ebrahim's Results)

| Configuration | Mean | SD | Median | 95% CI | Hallucination Rate | % High-Risk (<0.5) | n |
|---|---|---|---|---|---|---|---|
| Ibrahim: Base LLM | 0.58 | 0.22 | 0.61 | [0.42–0.74] | 0.40 | 20% | 10 |
| Ibrahim: WebRAG | 0.86 | 0.11 | 0.88 | [0.84–0.88] | 0.14 | 4% | 100 |
| Ours: Baseline | 0.13 | 0.30 | 0.00 | [0.07–0.19] | 0.87 | 86% | 100 |
| Ours: AI-Generated RAG | 0.67 | 0.42 | 1.00 | [0.58–0.75] | 0.33 | 28% | 100 |
| Ours: Human-Curated RAG | 0.78 | 0.34 | 1.00 | [0.71–0.84] | 0.22 | 16% | 100 |

## Full RAGAS Metrics

| Configuration | Faithfulness | Answer Relevancy | Context Precision | Context Recall |
|---|---|---|---|---|
| Ours: Baseline | 0.130 ± 0.304 | 0.834 ± 0.292 | N/A | N/A |
| Ours: AI-Generated RAG | 0.666 ± 0.420 | 0.482 ± 0.448 | 0.272 ± 0.388 | 0.197 ± 0.302 |
| Ours: Human-Curated RAG | 0.778 ± 0.342 | 0.693 ± 0.390 | N/A | 0.425 ± 0.371 |