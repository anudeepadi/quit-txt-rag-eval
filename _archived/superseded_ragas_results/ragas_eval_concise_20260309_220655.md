# RAGAS Evaluation Results

**Generated:** 2026-03-09T22:12:35.522916
**n:** 5 questions  |  **Model:** gpt-4o-mini

## Faithfulness Summary (Comparison with Ebrahim's Results)

| Configuration | Mean | SD | Median | 95% CI | Hallucination Rate | % High-Risk (<0.5) | n |
|---|---|---|---|---|---|---|---|
| Ibrahim: Base LLM | 0.58 | 0.22 | 0.61 | [0.42–0.74] | 0.40 | 20% | 10 |
| Ibrahim: WebRAG | 0.86 | 0.11 | 0.88 | [0.84–0.88] | 0.14 | 4% | 100 |
| Ours: AI-Generated RAG | 0.92 | 0.18 | 1.00 | [0.76–1.00] | 0.08 | 0% | 5 |

## Full RAGAS Metrics

| Configuration | Faithfulness | Answer Relevancy | Context Precision | Context Recall |
|---|---|---|---|---|
| Ours: AI-Generated RAG | 0.920 ± 0.179 | 0.654 ± 0.395 | 0.867 ± 0.298 | 0.633 ± 0.342 |