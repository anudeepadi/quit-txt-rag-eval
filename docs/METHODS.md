# QuitTxt RAG Evaluation — Methods and Approaches

## Research Question

Does augmenting GPT-4o-mini with a domain-specific knowledge base (RAG) improve its smoking cessation counseling responses? And can an AI-generated knowledge base match a human-curated one?

---

## Experimental Conditions

Four RAG configurations are compared across all experiments:

| Config ID | Label | Knowledge Source | Dataset Size |
|---|---|---|---|
| `baseline` | No RAG (Baseline) | None — LLM parametric knowledge only | N/A |
| `human_rag` | Human-Curated RAG | Expert-written QA pairs (`human_curated_qa.jsonl`) | 4,431 pairs |
| `ai_rag` | AI-Generated RAG | Gemini 2.0 Flash QA pairs (`ai_generated_qa.jsonl`) | 5,936 pairs |
| `web_rag` | Web-Scraped RAG | GPT-4o-mini QA from 5 authority sites (`web_scraped_qa.jsonl`) | 278 pairs |

---

## Shared Infrastructure

### Language Model

All answer generation uses **GPT-4o-mini** (OpenAI) with:
- Temperature: 0.3
- Max tokens: 300 (verbose mode) or 150 (concise mode)

### Retrieval System

**ChromaDB** with cosine similarity (HNSW index):
- Documents: QA pairs formatted as `"Q: {question}\nA: {answer}"`
- Top-k retrieval: k=3 (default)
- Embeddings: ChromaDB's default sentence-transformer embeddings
- Collections are built ephemeral (in-memory) per evaluation run

### Prompt Templates

**Baseline (no RAG):**
```
System: You are a compassionate smoking cessation counselor.
        Answer questions concisely (2-4 sentences).
User:   {question}
```

**RAG (verbose mode):**
```
System: You are a compassionate smoking cessation counselor.
        Use the following knowledge base to answer questions.
        Base your answer on the knowledge provided.

        KNOWLEDGE BASE:
        {retrieved_contexts}
User:   {question}
```

**RAG (concise mode):**
```
System: You are a smoking cessation counselor.
        Answer the question in 2-3 sentences using ONLY facts from the
        knowledge base below.
        Do NOT add information, examples, or details not explicitly stated
        in the knowledge base.

        KNOWLEDGE BASE:
        {retrieved_contexts}
User:   {question}
```

---

## Evaluation Pipelines

### Pipeline 1: Fair RAG Evaluation (Phase 1 — January 2026)

**Script:** `scripts/fair_rag_evaluation.py`

| Aspect | Detail |
|---|---|
| Test set | 15 hand-crafted questions with reference answers (embedded in script) |
| Configs | baseline, ai_rag, human_rag |
| Metrics | BLEU (corpus-level, sacrebleu), ROUGE-1/2/L (per-question average, rouge-score) |
| Runs | Single run per config |
| Output | `results/fair_evaluation_jan2026/` |

**Method:** For each test question, generate answers under all three configurations using identical ChromaDB retrieval (k=3, cosine). Compute corpus-level BLEU and average ROUGE against reference answers. Check whether the expected hierarchy (Baseline < AI < Human) holds.

**Key finding:** Baseline outperformed all RAG configs on ROUGE-L (0.231 vs 0.224), suggesting domain saturation — GPT-4o-mini already knows smoking cessation well.

---

### Pipeline 2: RAGAS Evaluation (Phase 2 — February–March 2026)

**Script:** `scripts/ragas_evaluation.py`

| Aspect | Detail |
|---|---|
| Test set | 127 clean questions from 150-question LFV-reviewed Excel test set |
| Configs | baseline, ai_rag, human_rag, web_rag |
| Metrics | RAGAS Faithfulness, Answer Relevancy, Context Precision, Context Recall |
| Modes | Verbose (default) and Concise (strict grounding prompts) |
| Checkpointing | Per-config JSONL files for resume across sessions |
| Rate limiting | 65s cooldown between metrics, 120s between configs (200K TPM) |
| Output | `results/ragas_evaluation/` |

**Method:** For each of 127 test questions:
1. Retrieve top-3 contexts from the config's ChromaDB collection
2. Generate answer via GPT-4o-mini with the RAG prompt template
3. Evaluate using RAGAS 0.4.x collections API:
   - **Faithfulness**: Are claims in the response supported by retrieved contexts?
   - **Answer Relevancy**: Is the response relevant to the user's question?
   - **Context Precision**: Are retrieved contexts relevant to the question?
   - **Context Recall**: Do retrieved contexts cover the reference answer?

Faithfulness statistics are computed to match Ibrahim's table format: Mean, SD, Median, 95% CI, Hallucination Rate (1 - mean), % High-Risk (<0.5).

**Ibrahim's reference benchmarks** (from prior work):
- Base LLM: Faithfulness 0.58 (n=10)
- WebRAG: Faithfulness 0.86 (n=100)

---

### Pipeline 3: Latency Comparison

**Script:** `scripts/latency_comparison.py`

| Aspect | Detail |
|---|---|
| Test set | Same 127-question LFV test set |
| Approaches | WebRAG warm (cached), WebRAG cold (re-scrape per question), Dataset RAG |
| Metric | Wall-clock seconds per question (mean, median, SD, p95, min, max) |
| Output | `results/latency_comparison/` |

**Method:**
1. **Phase A (Cold scrape):** Fetch all 5 source URLs once, time total
2. **Phase B (Per-question):**
   - **WebRAG warm:** Use cached web content, measure only GPT generation time
   - **WebRAG cold:** Re-fetch all 5 URLs per question + GPT generation
   - **Dataset RAG:** ChromaDB retrieval + GPT generation
3. Compute speedup factors (Dataset RAG vs WebRAG)

---

### Pipeline 4: Web Dataset Builder

**Script:** `scripts/build_web_dataset.py`

Builds the web-scraped QA dataset from authoritative sources:
1. Load URLs from `data/source_web_links.json`
2. Fetch and clean HTML (remove nav, footer, scripts; truncate to 10K chars)
3. Feed to GPT-4o-mini with structured prompt to generate 8 QA pairs per page
4. Checkpoint per-URL to `data/web_scraped_dataset/checkpoints/`
5. Deduplicate by word overlap (75% threshold)
6. Save final dataset to `data/web_scraped_qa.jsonl`

---

### Pipeline 5: Autoresearch (Autonomous Optimization)

**Scripts:** `autoresearch/prepare.py`, `autoresearch/experiment.py`, `autoresearch/run_experiment.py`

| Aspect | Detail |
|---|---|
| Test set | 20 questions (fixed subset for fast iteration) |
| Metric | LLM-as-judge faithfulness proxy (0–1 scale) |
| Agent loop | Modify `experiment.py` → run → log to `results.tsv` → analyze → iterate |
| Output | `autoresearch/results.tsv` |

**Method:** An autonomous agent iteratively modifies `experiment.py` (hypothesis, config, temperature, max_tokens, top_k, RAG template), runs `run_experiment.py`, and logs results. The scoring uses a fast LLM-as-judge proxy: GPT-4o-mini rates how well each response is grounded in its retrieved context on a 0–10 scale, normalized to 0–1. Each experiment logs whether it was an improvement (KEEP/DISCARD) over the previous best.

**Architecture:**
- `prepare.py` — Fixed infrastructure (data loading, ChromaDB building, scoring, logging). Never modified by the agent.
- `experiment.py` — Agent-writable config (the only file the agent changes).
- `run_experiment.py` — Harness that loads `experiment.py` config, runs the evaluation loop, scores, and logs.
- `program.md` — Instructions for the autonomous agent.

---

## Report Generation

| Script | Output | Description |
|---|---|---|
| `scripts/combine_results_table.py` | `results/combined_results/` | Merges RAGAS + latency results into one markdown report |
| `scripts/generate_report_documents.py` | `results/report/professor_report.docx` | Word doc with tables for professors |
| `scripts/generate_clean_report.py` | `results/report/results_for_professors.docx` | Cleaner Word report with explanations |

---

## Key Findings Summary

1. **Domain saturation:** Baseline GPT-4o-mini matches or outperforms RAG on traditional metrics (BLEU/ROUGE), suggesting the model's parametric knowledge already covers smoking cessation well.

2. **AI ≈ Human:** AI-generated knowledge base achieves 91–102% of human-curated RAG performance across metrics, supporting the viability of automated knowledge base construction.

3. **Faithfulness improves with RAG:** RAGAS faithfulness scores show RAG conditions (0.72–0.86) outperform baseline (0.58), especially with concise prompting that constrains the model to retrieved facts.

4. **Data leakage:** 47% of the 150-question test set had significant overlap with training datasets, which reversed earlier conclusions and required switching to the 127 clean questions.

5. **Latency advantage:** Dataset RAG is ~1.4x faster per question than WebRAG (warm) and significantly faster than cold WebRAG.
