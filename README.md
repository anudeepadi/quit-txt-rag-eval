# Quitxt RAG Evaluation — Analysis Code

Statistical testing, evaluation, and report-generation code accompanying the
Quitxt performance-benchmarking study (retrieval-augmented generation for a
cross-platform smoking-cessation messaging application).

This repository contains **code only**. The evaluation datasets, raw results,
and per-run RAGAS logs are available from the corresponding author on
reasonable request. Application source code is not included.

## Contents

| Path | Purpose |
|------|---------|
| `code/scripts/statistical_tests.py` | Non-parametric significance testing (Mann-Whitney U, Wilson intervals) |
| `code/scripts/ragas_evaluation.py` | RAGAS metric evaluation pipeline |
| `code/scripts/latency_comparison.py` | Latency benchmarking |
| `code/scripts/bertscore_evaluation.py` | BERTScore comparison |
| `code/scripts/retry_context_precision.py` | Context-precision recomputation |
| `code/scripts/build_web_dataset.py`, `regenerate_ai_dataset.py` | Dataset construction |
| `code/scripts/combine_results_table.py`, `generate_clean_report.py`, `generate_report_documents.py` | Results tables and report generation |
| `code/shared/` | Shared loaders and ChromaDB / RAGAS utilities |
| `paper/` | Paper and report generation scripts |

## Setup

```bash
pip install -r requirements.txt
cp code/.env.example code/.env      # add your OpenAI key; code/.env is gitignored
```

Provide your OpenAI API key via `code/.env` or the `OPENAI_API_KEY`
environment variable. Never commit real keys.

## License

MIT — see [`LICENSE`](LICENSE).
