# RAGAS Evaluation Results

**Generated:** 2026-03-12T21:53:10.854139
**n:** 100 questions  |  **Model:** gpt-4o-mini

## Faithfulness Summary (Comparison with Ebrahim's Results)

| Configuration | Mean | SD | Median | 95% CI | Hallucination Rate | % High-Risk (<0.5) | n |
|---|---|---|---|---|---|---|---|
| Ibrahim: Base LLM | 0.58 | 0.22 | 0.61 | [0.42–0.74] | 0.40 | 20% | 10 |
| Ibrahim: WebRAG | 0.86 | 0.11 | 0.88 | [0.84–0.88] | 0.14 | 4% | 100 |
| Ours: Baseline | N/A | N/A | N/A | N/A | N/A | N/A | 0 |
| Ours: AI-Generated RAG | 0.73 | 0.39 | 1.00 | [0.65–0.80] | 0.27 | 20% | 100 |
| Ours: Human-Curated RAG | 0.80 | 0.34 | 1.00 | [0.73–0.87] | 0.20 | 17% | 100 |

## Full RAGAS Metrics

| Configuration | Faithfulness | Answer Relevancy | Context Precision | Context Recall |
|---|---|---|---|---|
| Ours: Baseline | N/A | N/A | N/A | N/A |
| Ours: AI-Generated RAG | 0.727 ± 0.386 | 0.564 ± 0.437 | 0.455 ± 0.466 | 0.261 ± 0.343 |
| Ours: Human-Curated RAG | 0.800 ± 0.344 | 0.709 ± 0.377 | 0.655 ± 0.428 | 0.422 ± 0.367 |