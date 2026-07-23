# RAGAS Evaluation Results

**Generated:** 2026-07-21T05:05:29.800903
**n:** 100 questions  |  **Model:** gpt-4o-mini

## Faithfulness Summary (Comparison with Ebrahim's Results)

| Configuration | Mean | SD | Median | 95% CI | Hallucination Rate | % High-Risk (<0.5) | n |
|---|---|---|---|---|---|---|---|
| Ibrahim: Base LLM | 0.58 | 0.22 | 0.61 | [0.42–0.74] | 0.40 | 20% | 10 |
| Ibrahim: WebRAG | 0.86 | 0.11 | 0.88 | [0.84–0.88] | 0.14 | 4% | 100 |
| Ours: AI-Generated RAG | 0.82 | 0.31 | 1.00 | [0.76–0.88] | 0.18 | 12% | 100 |
| Ours: Human-Curated RAG | 0.77 | 0.33 | 1.00 | [0.71–0.84] | 0.23 | 15% | 100 |

## Full RAGAS Metrics

| Configuration | Faithfulness | Answer Relevancy | Context Precision | Context Recall |
|---|---|---|---|---|
| Ours: AI-Generated RAG | 0.817 ± 0.314 | 0.673 ± 0.382 | 0.611 ± 0.438 | 0.353 ± 0.353 |
| Ours: Human-Curated RAG | 0.771 ± 0.330 | 0.700 ± 0.393 | 0.650 ± 0.431 | 0.414 ± 0.374 |