# data/ — Datasets

All datasets used in the QuitTxt RAG evaluation project.

## Files

| File | Records | Description |
|---|---|---|
| `human_curated_qa.jsonl` | 4,431 | Expert-written smoking cessation QA pairs. Gold-standard knowledge base. |
| `web_scraped_qa.jsonl` | 278 | QA pairs generated from 5 authoritative web sources via GPT-4o-mini. |
| `quittxt_sms_message_templates.xlsx` | 26 rows | SMS intervention message templates (EN/ES). Reference only. |

## Subdirectories

| Directory | Description |
|---|---|
| `ai_generated/` | 5,936 AI-generated QA pairs (Gemini 2.0 Flash, Dec 2025). Available as JSON and JSONL. |
| `test_set/` | 150-question held-out test set (Excel). 127 clean + 23 flagged by LFV reviewer. |
| `chroma_db/` | Pre-built ChromaDB vector store (SQLite). May be stale — scripts rebuild in-memory. |
| `web_scraped_dataset/` | Intermediate checkpoints from web scraping pipeline. |

## Dataset Schema

All QA datasets share a common structure:
```json
{"id": "...", "question": "...", "answer": "..."}
```

The web-scraped dataset adds provenance fields:
```json
{"question": "...", "answer": "...", "source": "domain.com", "url": "https://..."}
```

## Legacy Files

The root-level `qa.jsonl` is the original location of the human-curated dataset. The canonical copy is now `data/human_curated_qa.jsonl`. Both are identical.

See `DATA_DICTIONARY.md` in the project root for full provenance details.
