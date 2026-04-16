# scripts/ — Evaluation & Analysis Scripts

All evaluation pipelines and report generation scripts.

## Evaluation Scripts

| Script | Purpose | Test Set | Metrics |
|---|---|---|---|
| `ragas_evaluation.py` | **Main evaluation.** Compares 4 configs using RAGAS framework. | 127 questions (LFV clean) | Faithfulness, Answer Relevancy, Context Precision/Recall |
| `fair_rag_evaluation.py` | Phase 1 evaluation with traditional NLP metrics. | 15 hand-crafted questions | BLEU, ROUGE-1/2/L |
| `latency_comparison.py` | Timing benchmark: WebRAG vs Dataset RAG. | 127 questions | Wall-clock latency (mean/median/SD/p95) |
| `build_web_dataset.py` | Builds web-scraped QA dataset from authority URLs. | N/A | N/A (data pipeline) |

## Report Generation Scripts

| Script | Output |
|---|---|
| `combine_results_table.py` | Merges RAGAS + latency results into combined markdown |
| `generate_report_documents.py` | Word (.docx) and LaTeX (.tex) reports with embedded tables |
| `generate_clean_report.py` | Professor-friendly Word report with explanatory sections |

## Usage Examples

```bash
# Full RAGAS evaluation (all 127 questions, all 4 configs)
python scripts/ragas_evaluation.py

# Quick sanity check (20 questions, 2 configs)
python scripts/ragas_evaluation.py --max-questions 20 --configs baseline human_rag

# Resume interrupted evaluation
python scripts/ragas_evaluation.py --resume

# Concise mode (stricter grounding prompts)
python scripts/ragas_evaluation.py --concise --resume

# Latency benchmark
python scripts/latency_comparison.py --max-questions 20

# Build web dataset
python scripts/build_web_dataset.py --resume
```

## Dependencies

All scripts load the OpenAI API key from `.env` in the project root. Required packages are in `requirements.txt`.

See `METHODS.md` in the project root for detailed methodology.
