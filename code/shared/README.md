# shared/ — Shared Utilities

Reusable modules imported by evaluation scripts and the autoresearch system.

## Modules

| Module | Description |
|---|---|
| `data_loader.py` | Dataset loading functions: `load_human_curated()`, `load_ai_generated()`, `load_web_scraped()`, `load_evaluation_results()` |
| `ragas_utils.py` | Test set loader (`load_test_set()`), faithfulness statistics (`compute_faithfulness_stats()`), metric stats, markdown table formatting |
| `web_scraper.py` | URL fetching for WebRAG evaluation. Fetches 5 authoritative sources (smokefree.gov, CDC, Mayo Clinic, ACS, ALA). Used by latency benchmarks. |

## Key Functions

### data_loader.py
- `load_human_curated()` → loads `data/human_curated_qa.jsonl` (falls back to root `qa.jsonl`)
- `load_ai_generated()` → loads `data/ai_generated/ai_generated_qa.jsonl` or `.json`
- `load_web_scraped()` → loads `data/web_scraped_qa.jsonl`

### ragas_utils.py
- `load_test_set(excel_path, max_rows)` → reads 150-question Excel, skips LFV-flagged rows (col 83), returns 127 clean questions
- `compute_faithfulness_stats(scores)` → mean, SD, median, 95% CI, hallucination rate, % high-risk
- `format_results_markdown(...)` → comparison tables matching Ibrahim's format

### web_scraper.py
- `SOURCE_URLS` — 5 authoritative smoking cessation URLs
- `fetch_url(url)` → fetch + clean HTML, truncate to 3K chars
- `fetch_all_urls(urls, sleep)` → sequential batch fetch with polite delay
- `build_web_context(fetched)` → concatenate into single context string (max 12K chars)
