# RAGAS Evaluation Results

**Generated:** 2026-03-10T15:54:12.516327
**n:** 20 questions  |  **Model:** gpt-4o-mini

## Faithfulness Summary (Comparison with Ebrahim's Results)

| Configuration | Mean | SD | Median | 95% CI | Hallucination Rate | % High-Risk (<0.5) | n |
|---|---|---|---|---|---|---|---|
| Ibrahim: Base LLM | 0.58 | 0.22 | 0.61 | [0.42–0.74] | 0.40 | 20% | 10 |
| Ibrahim: WebRAG | 0.86 | 0.11 | 0.88 | [0.84–0.88] | 0.14 | 4% | 100 |
| Ours: Human-Curated RAG | 0.95 | 0.14 | 1.00 | [0.89–1.00] | 0.05 | 0% | 20 |

## Full RAGAS Metrics

| Configuration | Faithfulness | Answer Relevancy | Context Precision | Context Recall |
|---|---|---|---|---|
| Ours: Human-Curated RAG | 0.946 ± 0.139 | 0.768 ± 0.337 | 0.754 ± 0.401 | 0.441 ± 0.365 |