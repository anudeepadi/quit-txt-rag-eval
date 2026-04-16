# COMPREHENSIVE REDUNDANCY AND DEAD CODE AUDIT REPORT
## Project: gemini-protocol (Smoking Cessation RAG)
**Date:** 2026-03-12

---

## EXECUTIVE SUMMARY

This project has **significant code duplication**, **redundant data files**, **superseded results**, and **legacy documentation**. Identified:
- **3 major code duplication issues** across evaluation scripts
- **4 identical duplicate test set files** (all same MD5)
- **14 superseded RAGAS result files** (older runs)
- **Multiple alternative report generators** (3 scripts)
- **Stale/legacy directories and files** (docs/agent_state, paper/, etc.)
- **1 unused data directory** (chroma_db - ephemeral, never persisted)
- **1 unused backup file** (4.3MB)

**Estimated cleanup potential:** ~50-70 files can be removed or consolidated.

---

## 1. CODE DUPLICATION

### 1.1 ChromaDB Collection Building (CRITICAL)

**Issue:** Three independent implementations of the same logic exist.

#### fair_rag_evaluation.py (Lines 154-183)
```
def create_collection(client, name, qa_pairs) -> Collection
  - Delete if exists
  - Create with cosine similarity
  - Add docs in batches of 100
  - Return collection
```
**Status:** Not using shared/data_loader; has inline data loaders (lines 124-151)

#### ragas_evaluation.py (Lines 134-168)
```
def build_collection(chroma_client, name, qa_pairs) -> Collection
  - Delete if exists
  - Create with cosine similarity
  - Add docs in batches of 100
  - Return collection
```
**Status:** Uses shared.data_loader (line 61), but duplicates ChromaDB logic

#### latency_comparison.py (Lines 83-105)
```
def _build_collection(chroma_client, name, qa_pairs) -> Collection
  - Delete if exists
  - Create with cosine similarity
  - Add docs in batches of 100
  - Return collection
```
**Status:** Uses shared.data_loader (line 55), but duplicates ChromaDB logic. Comment on line 79 acknowledges duplication: "reused from ragas_evaluation.py pattern"

**Recommendation:** Extract to shared/chroma_utils.py

```python
# shared/chroma_utils.py
def build_chroma_collection(chroma_client, name, qa_pairs, batch_size=100):
    """Build ChromaDB collection with batching and error handling."""
    try:
        chroma_client.delete_collection(name)
    except Exception:
        pass
    
    collection = chroma_client.create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"},
    )
    
    for i in range(0, len(qa_pairs), batch_size):
        batch = qa_pairs[i : i + batch_size]
        documents = [f"Q: {p['question']}\nA: {p['answer']}" for p in batch]
        ids = [str(p.get("id", f"{name}_{i + j}")) for j, p in enumerate(batch)]
        metadatas = [{"question": p["question"], "answer": p["answer"]} for p in batch]
        collection.add(documents=documents, ids=ids, metadatas=metadatas)
    
    return collection
```

Then import in all three scripts.

---

### 1.2 Context Retrieval (MEDIUM)

**Issue:** Retrieval functions are duplicated.

#### ragas_evaluation.py (Lines 171-189)
```
def retrieve_contexts(collection, query, n_results=TOP_K) -> list[str]
```

#### latency_comparison.py (Lines 108-117)
```
def _retrieve_contexts(collection, query, n_results=TOP_K) -> list[str]
```

**Recommendation:** Move to shared/chroma_utils.py alongside build_chroma_collection()

---

### 1.3 Data Loading Inconsistency (MEDIUM)

**Issue:** fair_rag_evaluation.py does NOT use shared/data_loader.py despite it existing.

#### fair_rag_evaluation.py (Lines 124-151)
Inline implementations of:
- load_human_curated() - duplicates shared.data_loader.load_human_curated()
- load_ai_generated() - duplicates shared.data_loader.load_ai_generated()

**Difference:** fair_rag_evaluation.py manually adds "id" field if missing (lines 132-134, 148-149), while shared version assumes IDs exist or doesn't add them.

**Recommendation:** Either:
1. Update shared/data_loader.py to optionally add IDs, OR
2. Update fair_rag_evaluation.py to use shared functions and add IDs after loading

---

## 2. REDUNDANT DATA FILES

### 2.1 Duplicate Test Set Files (CRITICAL - 4 files, all identical)

**Location:** `/data/test_set/`
**MD5 Hash:** `ab671a3d91fb0424fec6bab61ec52621` (all files identical)

Files to DELETE:
- `/data/test_set/150_QA_testset - LFV  review Oct 30 - 2025.xlsx`
- `/data/test_set/150_qa_testset.xlsx`
- `/data/test_set/test_set_150q_clean.xlsx`
- `/data/test_set/test_set_150q_lfv_reviewed_oct2025.xlsx`

**Keep:** Recommend consolidating to a single canonical file, e.g., `test_set_150q.xlsx`

**Size saved:** ~144 KB

---

### 2.2 Unused ChromaDB Directory (STALE)

**Location:** `/data/chroma_db/`
**Issue:** Never referenced in any production code

**Grep result:** No mentions of `data/chroma_db` in any .py files (only in DATA_DICTIONARY.md)

**Analysis:** 
- Contains a single collection (023c9e48-199a-4c4b-9af8-47161bae89b3)
- 5 binary files + 1 SQLite database
- Scripts create ephemeral in-memory ChromaDB clients that don't persist to disk
- This directory appears to be leftover from development

**Status:** SAFE TO DELETE
**Size:** ~50 MB

---

### 2.3 Backup File (UNUSED)

**Location:** `/data/ai_generated/ai_generated_qa_full.json.bak`
**Size:** 4.3 MB
**Status:** Backup of ai_generated_qa_full.json

**Recommendation:** DELETE (backup files should not be stored in repo)

---

## 3. RESULTS DIRECTORY ANALYSIS

### 3.1 Total Files in /results/
**Count:** 140 files across 15 subdirectories

### 3.2 Superseded RAGAS Evaluation Results (14 files)

**Location:** `/results/ragas_evaluation/`

All `.json` files (both regular and concise variants):

| File | Date | Status |
|------|------|--------|
| ragas_eval_20260219_175319.json | Feb 19 18:00 | **SUPERSEDED** |
| ragas_eval_20260219_180045.json | Feb 19 18:11 | **SUPERSEDED** |
| ragas_eval_20260219_181127.json | Feb 19 18:20 | **SUPERSEDED** |
| ragas_eval_20260225_233148.json | Feb 25 23:35 | **SUPERSEDED** |
| ragas_eval_20260225_233521.json | Feb 25 23:38 | **SUPERSEDED** |
| ragas_eval_20260226_004255.json | Feb 26 00:59 | **SUPERSEDED** |
| ragas_eval_20260226_011802.json | Feb 26 01:25 | **SUPERSEDED** |
| ragas_eval_20260302_202643.json | Mar 2 20:31 | **SUPERSEDED** |
| ragas_eval_20260302_203156.json | Mar 2 20:37 | **SUPERSEDED** |
| ragas_eval_20260304_160430.json | Mar 4 16:18 | **SUPERSEDED** |
| ragas_eval_concise_20260309_220655.json | Mar 9 22:12 | **SUPERSEDED** |
| ragas_eval_concise_20260309_224040.json | Mar 9 22:58 | **SUPERSEDED** |
| ragas_eval_concise_20260310_154739.json | Mar 10 15:54 | **SUPERSEDED** |
| ragas_eval_concise_20260310_181939.json | Mar 10 18:54 | **LATEST** ← Keep this one |

**Recommendation:** DELETE all except the last one (20260310_181939)

**Size savings:** ~15-20 MB (14 JSON files × 1-3 MB each)

**Note:** Corresponding .md files also exist for each—DELETE those too (14 additional files)

---

### 3.3 Fair Evaluation Results (Redundant Analysis Iterations)

**Location:** `/results/fair_evaluation_jan2026/`

Multiple runs of the same evaluation with analysis files:

| File | Purpose | Status |
|------|---------|--------|
| fair_rag_evaluation_20260106_033504.json | Results | Keep (dated run) |
| three_way_comparison_20260106_035952.json | Alternative comparison | **REDUNDANT** |
| proper_web_vs_dataset_rag_comparison.json | Alternative comparison | **REDUNDANT** |
| comprehensive_analysis_20260106_123209.json | Summary of above | **REDUNDANT** |
| COMPREHENSIVE_COMPARISON_SUMMARY.md | Analysis | **REDUNDANT** |
| CRITICAL_HONEST_FINDINGS.md | Analysis | **REDUNDANT** |
| HONEST_RESULTS_ANALYSIS.md | Analysis | **REDUNDANT** |
| PUBLISHABLE_QUALITY_SUMMARY.md | Analysis | **REDUNDANT** |
| final_results_summary.md | Analysis | **REDUNDANT** |

**Issue:** Multiple iterative analyses of the same dataset, saved incrementally during research. Only the final conclusions matter.

**Recommendation:** Keep ONLY:
- `final_results_summary.md` (final conclusions)
- `fair_rag_evaluation_20260106_033504.json` (raw results)

DELETE all other `.md` files and redundant JSON variants.

**Size savings:** ~300 KB

---

### 3.4 Latency Comparison (Multiple Runs)

**Location:** `/results/latency_comparison/`

| File | Date | Status |
|------|------|--------|
| latency_20260225_233850.json/.md | Feb 25 23:38 | **SUPERSEDED** |
| latency_20260226_000141.json/.md | Feb 26 00:01 | **SUPERSEDED** |
| latency_20260226_000145.json/.md | Feb 26 00:01 | **LATEST** ← Keep |

**Recommendation:** DELETE files from Feb 25 and Feb 26 (first two runs)

**Size savings:** ~10 KB

---

### 3.5 Combined Results

**Location:** `/results/combined_results/`

| File | Date | Status |
|------|------|--------|
| combined_20260225_234128.md | Feb 25 23:41 | **SUPERSEDED** |
| combined_20260226_013045.md | Feb 26 01:30 | **LATEST** ← Keep |

**Recommendation:** DELETE Feb 25 file

**Size savings:** ~500 bytes

---

## 4. REPORT GENERATORS (ALTERNATIVE IMPLEMENTATIONS)

### Issue: Three separate scripts generate report documents

**Location:** `/scripts/`

#### generate_clean_report.py (Lines 1-50 reviewed)
- Generates Word document (.docx) for professors
- Uses hardcoded data in script (FAITH_TABLE, etc.)
- Last modified: Mar 2

#### generate_report_documents.py (Lines 1-50 reviewed)
- Generates Word document (.docx) + LaTeX (.tex)
- Also uses hardcoded data
- Last modified: Feb 26

#### combine_results_table.py
- Generates Markdown table combining RAGAS + latency results
- Last modified: Feb 26

**Analysis:**
These are ONE-OFF generators designed during research iteration. They are **NOT** production code.

**Questions to answer:**
1. Which is the "final" report generator?
2. Are hardcoded values the source of truth, or should they come from result files?
3. Are the generated .docx and .tex files in `/results/report/` still used?

**Status of generated files:**
- `/results/report/professor_report.docx` - likely from generate_report_documents.py
- `/results/report/results_for_professors.docx` - likely from generate_clean_report.py
- `/results/report/draft_paper.tex` - from generate_report_documents.py

**Recommendation:** Consolidate into ONE canonical report generator, OR designate one as deprecated with a clear note.

---

## 5. LEGACY AND OPERATIONAL STATE DOCUMENTATION

### Location: `/docs/agent_state/`

Files present:
- BOOTSTRAP.md
- HEARTBEAT.md
- IDENTITY.md
- SOUL.md
- AGENTS.md
- TOOLS.md
- USER.md
- RESUME_RAG_INVESTIGATION_STATE.md
- RESUME_RAG_RESEARCH_JAN2026_COMPLETE.md
- IMPLEMENTATION_COMPLETE.md

**Analysis:** These are agent/checkpoint files, likely used by Claude's code exploration sessions or previous autoresearch runs. They contain state information from past research iterations.

**Status:** LEGACY (superseded by current work)

**Recommendation:** 
- DELETE all (they represent historical agent state, not current code)
- If needed for historical record, archive to a separate `_archive/` directory

**Size savings:** ~50 KB

---

## 6. PAPER DIRECTORIES

### /paper/ (Root)
**Files:**
- comprehensive_evaluation_report.aux
- comprehensive_evaluation_report.log
- comprehensive_evaluation_report.out
- comprehensive_evaluation_report.toc

**Issue:** Only compilation artifacts (`.aux`, `.log`, `.out`, `.toc`). No actual paper source (.tex) in root.

**Status:** STALE (these are build artifacts from a past LaTeX compilation)

**Recommendation:** DELETE (not needed; actual paper is in results/acl_bionlp_2026/ and results/plos_submission/)

**Size savings:** ~150 KB

---

### /results/acl_bionlp_2026/
**Files:**
- ACL_SUBMISSION_INSTRUCTIONS.md
- acl_manuscript.tex
- custom.bib

**Status:** CURRENT (this is the active submission directory)

**Recommendation:** KEEP

---

### /results/arxiv_submission/
**Files:**
- ARXIV_SUBMISSION_GUIDE.md

**Status:** Planning document, not actual submission

**Recommendation:** KEEP (guides future arxiv submission)

---

### /results/plos_submission/
**Files:**
- cover_letter.tex
- plos_manuscript.tex

**Status:** Alternative submission target

**Recommendation:** KEEP if this is an active submission, otherwise DELETE

---

### /results/github_repo/
**Files:**
- .gitignore
- CITATION.cff
- LICENSE
- README.md
- GITHUB_SETUP.md
- data/FINAL_independent_test_set.json
- results/comprehensive_results.json
- scripts/comprehensive_rag_evaluation.py

**Purpose:** Template/structure for publishing to GitHub

**Status:** KEEP (used for public release)

---

## 7. INDEPENDENT TEST SET RESULTS

### Location: `/results/independent_testset_rag_evaluation/`

This is a large directory (12 subdirectories) with multiple analysis phases:
- 01_data_leakage_audit/
- 02_comprehensive_rag_eval/
- 03_bertscore_vs_rougel/
- 04_ibrahim_style_eval/
- 05_sensitivity_analysis/
- 06_deep_investigation/
- findings/
- figures/
- paper/

**Analysis:** This appears to be a comprehensive research investigation created to verify data integrity and compare methods.

**Status:** 
- Some results are superseded by later analyses
- Findings are summarized in `/findings/FINAL_RESEARCH_SUMMARY.md`

**Recommendation:**
- KEEP the final finding documents
- DELETE intermediate analysis reports that are summarized elsewhere
- CONSOLIDATE findings into a single executive summary

---

## 8. SUMMARY TABLE OF DELETIONS

| Category | Files | Size | Priority |
|----------|-------|------|----------|
| Duplicate test sets (keep 1, delete 3) | 3 | 144 KB | HIGH |
| Superseded RAGAS results (keep latest) | 14 | 15-20 MB | HIGH |
| Superseded RAGAS markdown | 14 | 200 KB | HIGH |
| Stale fair_evaluation analyses | 8 | 300 KB | MEDIUM |
| Legacy agent state docs | 10 | 50 KB | LOW |
| Paper build artifacts | 4 | 150 KB | LOW |
| Unused chroma_db directory | 6 | 50 MB | HIGH |
| Backup file (.bak) | 1 | 4.3 MB | MEDIUM |
| Old latency runs | 4 | 10 KB | LOW |
| Old combined results | 1 | 500 B | LOW |
| **TOTAL POTENTIAL CLEANUP** | **65** | **~70 MB** | — |

---

## 9. RECOMMENDATIONS BY PRIORITY

### CRITICAL (Do immediately)
1. **Delete superseded RAGAS results:** `/results/ragas_evaluation/` - keep only `ragas_eval_concise_20260310_181939.json/.md`
2. **Delete duplicate test sets:** Keep only ONE copy in `/data/test_set/`
3. **Extract ChromaDB logic:** Create `/shared/chroma_utils.py` with `build_chroma_collection()` and `retrieve_contexts()`
4. **Delete chroma_db directory:** `/data/chroma_db/` is unused and large

### HIGH (Do soon)
5. **Consolidate data loaders:** Update `fair_rag_evaluation.py` to use `shared/data_loader.py`
6. **Delete backup file:** `/data/ai_generated/ai_generated_qa_full.json.bak`
7. **Consolidate report generators:** Pick ONE canonical script and mark others as deprecated or delete

### MEDIUM (Consider)
8. **Clean up legacy research analyses:** `/results/fair_evaluation_jan2026/` - keep only final summary
9. **Archive or delete agent state:** `/docs/agent_state/` - these are historical checkpoints
10. **Clean up paper artifacts:** `/paper/` - delete build artifacts only

### LOW (Optional)
11. **Review independent_testset_rag_evaluation:** Verify findings are captured, remove redundant intermediate reports
12. **Review submission directories:** Decide which actual submissions are active

---

## 10. DETAILED FILE-BY-FILE DELETION LIST

### DELETE THESE FILES:

```
# Duplicate test sets (keep test_set_150q.xlsx or similar)
/data/test_set/150_QA_testset - LFV  review Oct 30 - 2025.xlsx
/data/test_set/150_qa_testset.xlsx
/data/test_set/test_set_150q_clean.xlsx
/data/test_set/test_set_150q_lfv_reviewed_oct2025.xlsx

# Unused data directory (entire directory)
/data/chroma_db/  (entire directory)

# Backup file
/data/ai_generated/ai_generated_qa_full.json.bak

# Superseded RAGAS results (keep 20260310_181939)
/results/ragas_evaluation/ragas_eval_20260219_175319.json
/results/ragas_evaluation/ragas_eval_20260219_175319.md
/results/ragas_evaluation/ragas_eval_20260219_180045.json
/results/ragas_evaluation/ragas_eval_20260219_180045.md
/results/ragas_evaluation/ragas_eval_20260219_181127.json
/results/ragas_evaluation/ragas_eval_20260219_181127.md
/results/ragas_evaluation/ragas_eval_20260225_233148.json
/results/ragas_evaluation/ragas_eval_20260225_233148.md
/results/ragas_evaluation/ragas_eval_20260225_233521.json
/results/ragas_evaluation/ragas_eval_20260225_233521.md
/results/ragas_evaluation/ragas_eval_20260226_004255.json
/results/ragas_evaluation/ragas_eval_20260226_004255.md
/results/ragas_evaluation/ragas_eval_20260226_011802.json
/results/ragas_evaluation/ragas_eval_20260226_011802.md
/results/ragas_evaluation/ragas_eval_20260302_202643.json
/results/ragas_evaluation/ragas_eval_20260302_202643.md
/results/ragas_evaluation/ragas_eval_20260302_203156.json
/results/ragas_evaluation/ragas_eval_20260302_203156.md
/results/ragas_evaluation/ragas_eval_20260304_160430.json
/results/ragas_evaluation/ragas_eval_20260304_160430.md
/results/ragas_evaluation/ragas_eval_concise_20260309_220655.json
/results/ragas_evaluation/ragas_eval_concise_20260309_220655.md
/results/ragas_evaluation/ragas_eval_concise_20260309_224040.json
/results/ragas_evaluation/ragas_eval_concise_20260309_224040.md
/results/ragas_evaluation/ragas_eval_concise_20260310_154739.json
/results/ragas_evaluation/ragas_eval_concise_20260310_154739.md

# Superseded fair evaluation analyses
/results/fair_evaluation_jan2026/three_way_comparison_20260106_035952.json
/results/fair_evaluation_jan2026/proper_web_vs_dataset_rag_comparison.json
/results/fair_evaluation_jan2026/comprehensive_analysis_20260106_123209.json
/results/fair_evaluation_jan2026/COMPREHENSIVE_COMPARISON_SUMMARY.md
/results/fair_evaluation_jan2026/CRITICAL_HONEST_FINDINGS.md
/results/fair_evaluation_jan2026/HONEST_RESULTS_ANALYSIS.md
/results/fair_evaluation_jan2026/PUBLISHABLE_QUALITY_SUMMARY.md

# Old latency runs (keep latest)
/results/latency_comparison/latency_20260225_233850.json
/results/latency_comparison/latency_20260225_233850.md
/results/latency_comparison/latency_20260226_000141.json
/results/latency_comparison/latency_20260226_000141.md

# Old combined results
/results/combined_results/combined_20260225_234128.md

# Legacy agent state docs
/docs/agent_state/BOOTSTRAP.md
/docs/agent_state/HEARTBEAT.md
/docs/agent_state/IDENTITY.md
/docs/agent_state/SOUL.md
/docs/agent_state/AGENTS.md
/docs/agent_state/TOOLS.md
/docs/agent_state/USER.md
/docs/agent_state/RESUME_RAG_INVESTIGATION_STATE.md
/docs/agent_state/RESUME_RAG_RESEARCH_JAN2026_COMPLETE.md
/docs/agent_state/IMPLEMENTATION_COMPLETE.md

# Paper build artifacts
/paper/comprehensive_evaluation_report.aux
/paper/comprehensive_evaluation_report.log
/paper/comprehensive_evaluation_report.out
/paper/comprehensive_evaluation_report.toc
```

---

## 11. CODE CHANGES REQUIRED

### Create shared/chroma_utils.py

```python
"""ChromaDB utilities for RAG evaluation."""

import chromadb

def build_chroma_collection(
    chroma_client: chromadb.Client,
    name: str,
    qa_pairs: list[dict],
    batch_size: int = 100,
) -> chromadb.Collection:
    """Build a ChromaDB collection from QA pairs with batching.
    
    Args:
        chroma_client: Active ChromaDB client.
        name: Collection name (recreated if exists).
        qa_pairs: List of dicts with 'question' and 'answer' keys.
        batch_size: Number of documents per batch.
    
    Returns:
        Populated ChromaDB collection.
    """
    try:
        chroma_client.delete_collection(name)
    except Exception:
        pass
    
    collection = chroma_client.create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"},
    )
    
    for i in range(0, len(qa_pairs), batch_size):
        batch = qa_pairs[i : i + batch_size]
        documents = [f"Q: {p['question']}\nA: {p['answer']}" for p in batch]
        ids = [str(p.get("id", f"{name}_{i + j}")) for j, p in enumerate(batch)]
        metadatas = [{"question": p["question"], "answer": p["answer"]} for p in batch]
        collection.add(documents=documents, ids=ids, metadatas=metadatas)
    
    return collection


def retrieve_contexts(
    collection: chromadb.Collection,
    query: str,
    n_results: int = 3,
) -> list[str]:
    """Retrieve top-k contexts via semantic similarity.
    
    Args:
        collection: ChromaDB collection to query.
        query: User question.
        n_results: Number of top results to return.
    
    Returns:
        List of retrieved document strings.
    """
    results = collection.query(query_texts=[query], n_results=n_results)
    if results["documents"] and results["documents"][0]:
        return list(results["documents"][0])
    return []
```

### Update imports in scripts:

**fair_rag_evaluation.py:**
- Replace lines 124-151 with: `from shared.data_loader import load_ai_generated, load_human_curated`
- Replace lines 154-198 with: `from shared.chroma_utils import build_chroma_collection, retrieve_contexts`

**ragas_evaluation.py:**
- Replace lines 134-189 with: `from shared.chroma_utils import build_chroma_collection, retrieve_contexts`
- Rename functions: `build_collection()` → `build_chroma_collection()`, etc.

**latency_comparison.py:**
- Replace lines 83-117 with: `from shared.chroma_utils import build_chroma_collection, retrieve_contexts`
- Remove private `_build_collection()` and `_retrieve_contexts()`

---

## 12. FINAL CHECKLIST

- [ ] Delete duplicate test set files (3 of 4)
- [ ] Delete /data/chroma_db/ directory
- [ ] Delete ai_generated_qa_full.json.bak
- [ ] Delete superseded RAGAS results (14 files)
- [ ] Delete superseded fair_evaluation analyses (8 files)
- [ ] Delete legacy agent_state docs (10 files)
- [ ] Delete paper build artifacts (4 files)
- [ ] Create shared/chroma_utils.py
- [ ] Update fair_rag_evaluation.py to use shared functions
- [ ] Update ragas_evaluation.py to use shared.chroma_utils
- [ ] Update latency_comparison.py to use shared.chroma_utils
- [ ] Test all three scripts still work after refactoring
- [ ] Consolidate or deprecate report generators (TBD)
- [ ] Update DATA_DICTIONARY.md to remove reference to chroma_db (if deleted)

---

## 13. NOTES

- All deleted files can be recovered from git history if needed
- No production data is being lost; only experimental artifacts and duplicates
- After cleanup: project will be ~70 MB smaller and easier to maintain
- Code duplication removal will improve maintainability and reduce bugs

