# results/ — Experimental Results

All outputs from evaluation runs, organized by pipeline and submission target.

## Result Directories

| Directory | Pipeline | Period | Description |
|---|---|---|---|
| `ragas_evaluation/` | RAGAS (Phase 2) | Feb–Mar 2026 | Main results: faithfulness, relevancy, context metrics for 4 configs × 127 questions |
| `fair_evaluation_jan2026/` | BLEU/ROUGE (Phase 1) | Jan 2026 | Early results: BLEU/ROUGE for 3 configs × 15 questions |
| `latency_comparison/` | Latency | Feb 2026 | Timing: WebRAG warm/cold vs Dataset RAG |
| `combined_results/` | Merged | Feb 2026 | RAGAS + latency in single markdown reports |
| `final_paper_results/` | Consolidated | Jan 2026 | Key numbers for the paper |
| `report/` | Documents | Feb–Mar 2026 | Generated .docx and .tex reports |

## Submission Drafts

| Directory | Target | Status |
|---|---|---|
| `acl_bionlp_2026/` | ACL BioNLP 2026 Workshop | Draft (deadline: Apr 17, 2026) |
| `plos_submission/` | PLOS Digital Health | Draft |
| `arxiv_submission/` | arXiv preprint | PDF ready |

## Standalone Files

| File | Description |
|---|---|
| `TECHNICAL_BRIEF_Mar2026.pdf` | Technical brief summarizing all findings |
| `github_repo/` | Scaffolding for public GitHub repository (README, LICENSE, CITATION.cff) |

## File Naming Convention

Result files follow the pattern: `{type}_{YYYYMMDD_HHMMSS}.{ext}`

- `.json` — Machine-readable full results (metrics, scores, metadata)
- `.md` — Human-readable summary tables
- `checkpoint_*.jsonl` — Per-question answer checkpoints (for resume)
