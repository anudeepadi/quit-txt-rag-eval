# _archived/ — Files Pending Review & Deletion

**Archived:** 2026-03-12

These files were identified as redundant, superseded, or unused during the project audit. They have been moved here for your review before permanent deletion.

## Contents

| Folder | Count | Description |
|---|---|---|
| `superseded_ragas_results/` | 26 | Older RAGAS eval .json/.md files (kept only latest: 20260310_181939) |
| `old_checkpoints/` | 12 | Test-run and non-concise checkpoint files |
| `duplicate_test_sets/` | 4 | All 4 copies had identical MD5; canonical copy kept as `test_set_150q.xlsx` |
| `unused_chroma_db/` | ~7 | Ephemeral ChromaDB directory never referenced by scripts |
| `backup_files/` | 1 | `ai_generated_qa_full.json.bak` (4.3 MB) |
| `legacy_agent_state/` | 10 | Historical agent checkpoint docs from `docs/agent_state/` |
| `paper_build_artifacts/` | 4 | LaTeX .aux/.log/.out/.toc without corresponding .tex source |
| `superseded_fair_eval/` | 7 | Intermediate analysis reports from Phase 1 evaluation |
| `old_latency_runs/` | 4 | Earlier latency benchmark runs (kept latest: 20260226_000145) |
| `old_combined_results/` | 1 | Earlier combined results markdown |

## Safe to Delete

All of these files are superseded by newer results, duplicates of kept files, or build artifacts. The latest/canonical versions remain in their original locations.

To permanently delete: `rm -rf _archived/`
