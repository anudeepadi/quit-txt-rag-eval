# QuitTxt RAG Evaluation — Project Structure

```
gemini-protocol/
│
├── .env                          # OpenAI API key (not committed)
├── requirements.txt              # Python dependencies
├── qa.jsonl                      # [LEGACY] Human-curated QA (→ use data/human_curated_qa.jsonl)
├── jobs.db                       # SQLite job queue (Streamlit/background tasks)
│
├── DATA_DICTIONARY.md            # ← Detailed schema & provenance for every dataset
├── METHODS.md                    # ← All experimental methods, pipelines, and findings
├── PROJECT_STRUCTURE.md          # ← This file
│
├── data/                         # ══════ ALL DATASETS ══════
│   ├── human_curated_qa.jsonl    #   4,431 expert-written QA pairs (canonical copy)
│   ├── web_scraped_qa.jsonl      #   278 QA pairs from 5 authority websites
│   ├── quittxt_sms_message_templates.xlsx  # SMS intervention templates (EN/ES)
│   │
│   ├── ai_generated/             #   AI-generated knowledge base
│   │   ├── ai_generated_qa_full.json   # 5,936 pairs + metadata (Gemini 2.0 Flash)
│   │   └── ai_generated_qa.jsonl       # Same pairs in flat JSONL format
│   │
│   ├── test_set/                 #   Held-out evaluation benchmark
│   │   ├── test_set_150q_clean.xlsx              # 150 questions (working copy)
│   │   ├── test_set_150q_lfv_reviewed_oct2025.xlsx  # With LFV reviewer comments
│   │   ├── 150_qa_testset.xlsx                   # [LEGACY] same as clean
│   │   └── 150_QA_testset - LFV  review ...xlsx  # [LEGACY] same as reviewed
│   │
│   ├── chroma_db/                #   Pre-built ChromaDB vector store
│   │   └── chroma.sqlite3        #   ~9.3 MB persistent embeddings
│   │
│   └── web_scraped_dataset/      #   Web scraping intermediates
│       └── checkpoints/          #   48 per-URL checkpoint JSON files
│           └── *.json
│
├── shared/                       # ══════ SHARED UTILITIES ══════
│   ├── __init__.py               #   (implicit — package)
│   ├── data_loader.py            #   Dataset loading functions (human, AI, web)
│   ├── web_scraper.py            #   URL fetching for WebRAG + latency benchmarks
│   ├── ragas_utils.py            #   Test set loader, faithfulness stats, markdown formatting
│   └── metrics.py                #   (if present) Additional metric helpers
│
├── scripts/                      # ══════ EVALUATION SCRIPTS ══════
│   ├── ragas_evaluation.py       #   [MAIN] RAGAS eval: 4 configs × 127 questions
│   ├── fair_rag_evaluation.py    #   Phase 1: BLEU/ROUGE eval on 15 questions
│   ├── latency_comparison.py     #   WebRAG vs Dataset RAG timing benchmark
│   ├── build_web_dataset.py      #   Build web-scraped QA from authority URLs
│   ├── combine_results_table.py  #   Merge RAGAS + latency into combined report
│   ├── generate_report_documents.py  # Generate .docx/.tex reports
│   └── generate_clean_report.py  #   Generate professor-friendly .docx report
│
├── autoresearch/                 # ══════ AUTONOMOUS OPTIMIZATION ══════
│   ├── program.md                #   Agent instructions (the "soul" of the loop)
│   ├── experiment.py             #   ← Agent-writable config (hypothesis, params)
│   ├── run_experiment.py         #   Experiment harness (load config → eval → log)
│   ├── prepare.py                #   Fixed infrastructure (data, scoring, logging)
│   └── results.tsv               #   Experiment log (append-only)
│
├── app/                          # ══════ INTERACTIVE DEMO ══════
│   ├── streamlit_app.py          #   5-tab Streamlit dashboard
│   └── STREAMLIT_README.md       #   App usage instructions
│
├── results/                      # ══════ ALL EXPERIMENTAL RESULTS ══════
│   │
│   ├── ragas_evaluation/         #   Phase 2 RAGAS results (Feb–Mar 2026)
│   │   ├── checkpoint_*.jsonl    #   Per-config answer checkpoints (resume support)
│   │   ├── ragas_eval_*.json     #   Full metric scores (timestamped)
│   │   └── ragas_eval_*.md       #   Human-readable summary tables
│   │
│   ├── fair_evaluation_jan2026/  #   Phase 1 BLEU/ROUGE results (Jan 2026)
│   │   ├── fair_rag_evaluation_*.json
│   │   ├── three_way_comparison_*.json
│   │   ├── comprehensive_comparison_report.pdf
│   │   ├── HONEST_RESULTS_ANALYSIS.md
│   │   ├── CRITICAL_HONEST_FINDINGS.md
│   │   └── PUBLISHABLE_QUALITY_SUMMARY.md
│   │
│   ├── latency_comparison/       #   Timing benchmarks
│   │   ├── latency_*.json
│   │   └── latency_*.md
│   │
│   ├── combined_results/         #   Merged RAGAS + latency reports
│   │   └── combined_*.md
│   │
│   ├── final_paper_results/      #   Consolidated results for paper
│   │   └── final_results_summary.md
│   │
│   ├── report/                   #   Generated documents
│   │   ├── draft_paper.tex / .pdf
│   │   ├── professor_report.docx
│   │   └── results_for_professors.docx
│   │
│   ├── TECHNICAL_BRIEF_Mar2026.pdf
│   │
│   ├── acl_bionlp_2026/         #   ACL BioNLP 2026 submission
│   │   ├── acl_manuscript.tex
│   │   ├── custom.bib
│   │   └── ACL_SUBMISSION_INSTRUCTIONS.md
│   │
│   ├── plos_submission/          #   PLOS Digital Health submission
│   │   ├── plos_manuscript.tex
│   │   └── cover_letter.tex
│   │
│   ├── arxiv_submission/         #   arXiv preprint
│   │   ├── arxiv_manuscript.pdf
│   │   └── ARXIV_SUBMISSION_GUIDE.md
│   │
│   └── github_repo/              #   GitHub repository scaffolding
│       ├── README.md
│       ├── LICENSE
│       ├── CITATION.cff
│       ├── requirements.txt
│       ├── .gitignore
│       └── GITHUB_SETUP.md
│
├── paper/                        #   LaTeX build artifacts
│   └── comprehensive_evaluation_report.*
│
└── docs/                         #   Research notes & agent state
    ├── research_notes/
    │   ├── RESEARCH_RESULTS_SUMMARY.md
    │   ├── RESULTS_ONE_PAGE.md
    │   ├── PUBLICATION_OPTIONS_SUMMARY.md
    │   ├── PUBLICATION_QUICK_REFERENCE.md
    │   └── EMAIL_TO_PROFESSOR.md
    │
    └── agent_state/              #   Agent orchestration metadata
        ├── BOOTSTRAP.md
        ├── IDENTITY.md
        ├── USER.md
        ├── SOUL.md
        ├── AGENTS.md
        ├── TOOLS.md
        ├── HEARTBEAT.md
        ├── IMPLEMENTATION_COMPLETE.md
        └── RESUME_RAG_*.md
```

## Quick Reference: Which Script Does What?

| Task | Script | Input | Output |
|---|---|---|---|
| Run main evaluation | `scripts/ragas_evaluation.py` | test set + 3 datasets | `results/ragas_evaluation/` |
| Run BLEU/ROUGE eval | `scripts/fair_rag_evaluation.py` | 15 embedded questions | `results/final_paper_results/` |
| Benchmark latency | `scripts/latency_comparison.py` | test set + dataset | `results/latency_comparison/` |
| Build web dataset | `scripts/build_web_dataset.py` | source URLs | `data/web_scraped_qa.jsonl` |
| Autonomous optimize | `autoresearch/run_experiment.py` | experiment.py config | `autoresearch/results.tsv` |
| Merge results | `scripts/combine_results_table.py` | RAGAS + latency JSONs | `results/combined_results/` |
| Generate reports | `scripts/generate_report_documents.py` | results data | `results/report/` |
| Interactive explore | `app/streamlit_app.py` | all results | localhost:8501 |
