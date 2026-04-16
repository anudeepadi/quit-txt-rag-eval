# QuitTxt RAG Evaluation — Analysis, Literature Review & Recommendations

**Date:** March 12, 2026

---

## 1. REDUNDANCIES & WHAT TO REMOVE

### Code Redundancies

The project has **three independent implementations** of the same ChromaDB collection-building and retrieval logic across `fair_rag_evaluation.py`, `ragas_evaluation.py`, and `latency_comparison.py`. Additionally, `fair_rag_evaluation.py` has its own inline data loaders instead of using `shared/data_loader.py`. These should be consolidated into a single `shared/chroma_utils.py`.

Three separate report-generation scripts (`combine_results_table.py`, `generate_report_documents.py`, `generate_clean_report.py`) are one-off generators with hardcoded data. Consolidate to one or mark the others deprecated.

### Files to Remove (~65 files, ~70 MB)

| Category | Count | Rationale |
|---|---|---|
| Superseded RAGAS result files (keep only 20260310_181939) | 26 | Older runs replaced by latest |
| Duplicate test set files (all 4 are identical MD5) | 3 | Keep one canonical copy |
| Unused `data/chroma_db/` directory | 6 | Scripts build ephemeral in-memory; never referenced |
| `.bak` file in `data/ai_generated/` | 1 | Backup artifact |
| `paper/` build artifacts (.aux, .log, .out, .toc) | 4 | No source .tex; superseded by `results/acl_bionlp_2026/` |
| Legacy `docs/agent_state/` files | 10 | Historical agent checkpoints, not operational |
| Superseded fair evaluation analyses | 8 | Intermediate research notes |
| Old latency/combined runs | 5 | Replaced by later runs |

**Full file-by-file deletion list:** See `REDUNDANCY_AUDIT_REPORT.md`

---

## 2. METHODOLOGICAL ASSESSMENT — ARE THE PROCEDURES GOOD?

### What's Working Well

- **Four-way comparison** (baseline / human / AI / web) is a solid experimental design
- **RAGAS framework** is the standard for RAG evaluation (published at EACL 2024)
- **Checkpointing system** for resume across sessions is well-engineered
- **Concise prompting mode** was a smart addition — it directly improves faithfulness

### Methodological Weaknesses

**Problem 1: Missing baseline in RAGAS run.** The latest concise RAGAS eval (20260310) ran only `ai_rag`, `human_rag`, `web_rag` — **no baseline**. Without the baseline, you can't claim RAG improves over no-RAG. You need baseline faithfulness and answer relevancy scores for the same 100 questions under the same concise prompting.

**Problem 2: Missing BERTScore.** Recent literature (2025) strongly recommends BERTScore as the most informative metric for medical QA, since it captures semantic similarity through contextual embeddings. Your current metrics are RAGAS-native (faithfulness, relevancy, context precision/recall) and traditional (BLEU, ROUGE). Adding BERTScore would strengthen the paper significantly.

**Problem 3: No statistical significance testing.** You report means and SDs but never test whether differences are statistically significant. With 100 questions, a paired Wilcoxon signed-rank test or bootstrap confidence intervals on the per-question score differences would determine if human_rag (0.789) is genuinely better than ai_rag (0.724) or if p > 0.05.

**Problem 4: Context precision has NaN gaps.** In the latest results, `context_precision` is N/A for `human_rag` and `web_rag`. This was likely a rate-limit or API error during the RAGAS batch scoring. These need to be re-run.

**Problem 5: Single LLM (GPT-4o-mini only).** All generation uses one model. Reviewers will ask: "Does this generalize?" Testing with at least one additional model (e.g., Llama 3, Gemini Flash) would make findings more robust.

**Problem 6: LLM-as-judge circularity in autoresearch.** The faithfulness proxy uses GPT-4o-mini to judge GPT-4o-mini's own outputs. This self-evaluation bias is a known limitation. The full RAGAS faithfulness metric partially addresses this (it decomposes claims), but calling it out is important.

### Suggested Improvements

| Improvement | Effort | Impact |
|---|---|---|
| Re-run RAGAS with baseline included | Medium (hours) | **Critical** — can't publish without it |
| Add BERTScore metric | Low (pip install, few lines) | High — expected by reviewers |
| Statistical significance tests | Low (scipy.stats) | High — required for publication |
| Fix context_precision NaN gaps | Medium (re-run affected configs) | Medium — completeness |
| Test with second LLM | High (cost + time) | Medium — generalizability |
| Domain-specific embeddings (PubMedBERT) | Medium | Medium — better retrieval |

---

## 3. EXISTING LITERATURE — WHAT'S ALREADY PUBLISHED?

### RAG for Medical/Health QA (2024–2025)

The field is **extremely active**. A PLOS ONE systematic review (2025) identified 70 studies on RAG for healthcare between 2020–2025. Key papers:

| Paper | Venue | Relevance |
|---|---|---|
| "Rethinking RAG for Medicine" (arXiv, Nov 2025) | arXiv | Found retrieved content covers only 33% of must-have statements. Tested GPT-4o + Llama 3.1 with evidence filtering and query reformulation. |
| "MKRAG: Medical Knowledge RAG" (AMIA 2024) | AMIA | Used RAG to improve Vicuna-7B on MedQA (44.5% → 48.5%). Closest to your approach. |
| "Medical QA Dialogue Datasets in RAG" (Nature Sci Rep, Dec 2025) | Nature | Compared dialogue-based retrieval sources. ROUGE-1 +12.6%, BERTScore +1.5%. |
| "MEGA-RAG" (Frontiers Public Health, 2025) | Frontiers | Multi-evidence guided RAG for public health hallucination reduction. |
| "Biomedical Literature Q&A Using RAG" (arXiv, 2025) | arXiv | Multi-metric evaluation (BLEU + ROUGE-L + BERTScore). BERTScore found most informative. |
| "RAG in Healthcare: Comprehensive Review" (MDPI, Sept 2025) | MDPI | Identified naïve/advanced/modular RAG architectures. Notes retrieval noise and domain shift challenges. |

### Smoking Cessation AI/Chatbots (2024–2025)

Several recent papers are directly relevant:

| Paper | Venue | Key Finding |
|---|---|---|
| "ChatGPT-Based Chatbot for Help Quitting Smoking" (JMIR, 2025) | JMIR | BeFreeBot pilot study integrating ChatGPT into SMS cessation intervention |
| "Assessing ChatGPT Adherence to Public Health Guidelines" (JMIR, 2025) | JMIR | Content analysis of ChatGPT smoking cessation advice quality |
| "NLP Chatbot for Cigarette Smoking Cessation" (IEEE, 2025) | IEEE Xplore | NLP-supported cessation chatbot |
| "AI-Enabled Personalized Cessation with Aipaca" (JMIR, 2025) | JMIR | Mixed methods feasibility study of personalized AI cessation |
| "Conversational Chatbot for Cessation: QuitBot RCT" (JMIR mHealth, 2024) | JMIR | 11-step user-centered design + RCT results |
| "NLP Chatbot Interventions Systematic Review" (JMIR mHealth, 2025) | JMIR | Systematic review of NLP chatbot interventions for smoking |
| "Quin: Prototype Chatbot for Smoking Cessation" (Nicotine & Tobacco Research, 2024) | Oxford | NLP chatbot grounded in evidence-based counseling |

### Gap Analysis: What's YOUR Unique Contribution?

**The niche:** No existing paper compares human-curated vs. AI-generated knowledge bases for RAG in a healthcare setting. The closest is the Nature Scientific Reports paper on dialogue datasets, but it doesn't compare human vs. AI curation.

**Your angle:**
1. **AI-generated KB viability** — Can Gemini 2.0 Flash generate a knowledge base that matches expert curation? (Unique)
2. **Domain saturation finding** — GPT-4o-mini's parametric knowledge already covers smoking cessation well, limiting RAG benefit (Novel finding)
3. **Data leakage detection** — 47% test-set overlap discovery is methodologically valuable
4. **QuitTxt clinical context** — Grounded in a real SMS intervention program (Clinical relevance)

---

## 4. PAPER VIABILITY ASSESSMENT

### Verdict: **VIABLE, but needs more work**

### Strengths for Publication

- Clear, well-defined research question
- Four-way comparison with real clinical dataset
- Interesting null-ish result (domain saturation) — reviewers like surprising findings
- AI-generated KB comparison is novel in healthcare RAG
- QuitTxt provides real clinical grounding

### Weaknesses That Must Be Fixed Before Submission

1. **No baseline in latest RAGAS run** — This is a showstopper. Must re-run.
2. **No statistical significance testing** — Every conference/journal will ask for this.
3. **Missing BERTScore** — Reviewers in this space expect it.
4. **Single model limitation** — At minimum, discuss as limitation. Ideally test one more.
5. **Context precision gaps** — Incomplete data undermines credibility.

### Target Venues (Ranked by Fit)

| Venue | Fit | Deadline | Notes |
|---|---|---|---|
| **ACL BioNLP 2026 Workshop** | Excellent | Apr 17, 2026 | Short paper (4 pages). Perfect for a focused comparison study. |
| **JMIR (Journal of Medical Internet Research)** | Very Good | Rolling | Already publishes smoking cessation + AI papers. Open access. |
| **AMIA Annual Symposium 2026** | Good | ~May 2026 | Medical informatics focus. MKRAG was published here. |
| **Nature Scientific Reports** | Good | Rolling | Precedent for RAG QA studies. Longer format. |
| **PLOS Digital Health** | Good | Rolling | Good for clinical AI applications. |
| **arXiv preprint** | Always | Anytime | Publish immediately to establish priority while journal review proceeds. |

### Recommended Strategy

1. Fix methodology gaps (baseline, BERTScore, significance tests) — 1-2 days
2. Submit to **arXiv** immediately to establish priority
3. Prepare **ACL BioNLP short paper** (4 pages, deadline Apr 17) — tight but doable
4. Simultaneously prepare full paper for **JMIR** (rolling deadline)

---

## 5. DO WE NEED TO RE-RUN EVALUATIONS?

### YES — Here's Exactly What to Re-Run

| Run | Why | Priority |
|---|---|---|
| **RAGAS baseline (concise mode, 100q)** | Missing from latest results. Cannot publish without it. | **CRITICAL** |
| **RAGAS with context_precision fix** | human_rag and web_rag have NaN for context_precision | HIGH |
| **Add BERTScore to all configs** | Easy to add, major credibility boost for reviewers | HIGH |
| **Statistical significance tests** | Post-hoc analysis on existing per-question scores | HIGH (no re-run needed) |

### What You Do NOT Need to Re-Run

- **AI-generated dataset itself** — The 5,936 pairs from Gemini 2.0 Flash are fine. Re-generating would change results and waste time.
- **Phase 1 (BLEU/ROUGE on 15 questions)** — Superseded by Phase 2. Keep for historical context but don't present as primary results.
- **Web dataset** — The 278 web-scraped pairs are adequate.
- **Latency comparison** — Results are clean and complete.

### Recommended Re-Run Command

```bash
# 1. Re-run RAGAS with ALL 4 configs (including baseline), concise mode
python scripts/ragas_evaluation.py \
    --configs baseline ai_rag human_rag web_rag \
    --max-questions 100 \
    --concise \
    --resume

# 2. After RAGAS completes, add BERTScore evaluation
# (new script needed — ~30 lines using bert_score package)
pip install bert-score
python scripts/bertscore_evaluation.py

# 3. Statistical tests on per-question scores
python scripts/statistical_tests.py
```

### New Scripts to Write

**`scripts/bertscore_evaluation.py`** — Load checkpoint JSONL files, compute BERTScore (precision/recall/F1) per question per config against ground truth.

**`scripts/statistical_tests.py`** — Load per-question scores from all configs, run paired Wilcoxon signed-rank tests for each pair (baseline vs human_rag, human_rag vs ai_rag, etc.), report p-values and effect sizes.

---

## 6. SUMMARY OF ACTION ITEMS

### Immediate (Before Paper Submission)

- [ ] Re-run RAGAS with baseline included (concise, 100q)
- [ ] Fix context_precision NaN gaps
- [ ] Add BERTScore evaluation
- [ ] Run statistical significance tests
- [ ] Clean up ~65 redundant files (~70 MB)
- [ ] Consolidate ChromaDB code into shared/chroma_utils.py

### Before ACL BioNLP Deadline (Apr 17)

- [ ] Write 4-page short paper with updated results
- [ ] Include comparison table with Ibrahim's benchmarks
- [ ] Discuss domain saturation finding
- [ ] Submit to arXiv as preprint

### Nice-to-Have

- [ ] Test with a second LLM (Llama 3 or Gemini Flash)
- [ ] Try domain-specific embeddings (PubMedBERT) for retrieval
- [ ] Expert evaluation on a subset of responses
