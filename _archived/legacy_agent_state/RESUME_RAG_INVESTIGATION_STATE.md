# RAG Investigation State - Resume Point

**Date Saved:** January 15, 2026
**Last Active:** BERTScore vs ROUGE-L comparison completed

---

## What Was Accomplished

### 1. Ralph Wiggum Investigation Complete
- Identified root cause: **Evaluation metric mismatch** between Adi (ROUGE-L) and Ibrahim (human ratings)
- Created `ibrahim_style_evaluation.py` - tested constraining vs permissive prompts
- Created `bertscore_comparison.py` - compared semantic vs textual similarity

### 2. Key Findings

| Metric | Permissive Penalty | Interpretation |
|--------|-------------------|----------------|
| ROUGE-L | -42.0% | Heavily penalizes natural language |
| BERTScore | -5.6% | Minimal penalty for semantic equivalence |

**Conclusion:** ROUGE-L unfairly penalizes varied, conversational responses. BERTScore aligns better with human judgment.

### 3. Files Created in `results/fresh_analysis_20260110/`
- `bertscore_comparison.py` - BERTScore experiment
- `bertscore_comparison_results.json` - Results data
- `ibrahim_style_evaluation.py` - Prompt comparison
- `ibrahim_style_comparison.json` - Comparison results
- `RALPH_WIGGUM_FINDINGS.md` - Investigation summary

---

## What Was NOT Committed

Git status shows uncommitted files in `results/fresh_analysis_20260110/`:
- All investigation files are saved locally but not committed to git
- User declined the commit when offered

---

## To Resume

1. **Review findings:** Read `RALPH_WIGGUM_FINDINGS.md`
2. **See BERTScore results:** `bertscore_comparison_results.json`
3. **Commit when ready:**
   ```bash
   git add results/fresh_analysis_20260110/
   git commit -m "Add RAG evaluation investigation findings"
   ```

---

## Next Steps (Not Yet Done)

- [ ] Commit findings to git
- [ ] Prepare Monday meeting talking points with Ibrahim
- [ ] Update paper to acknowledge metric limitations
- [ ] Consider adding human evaluation component
- [ ] Run with more questions for statistical significance

---

## Quick Summary for Professor

"The difference between my results and Ibrahim's is NOT a bug - it's what we're measuring:
- ROUGE-L rewards copy-paste responses → favors constraining prompts
- Human evaluation rewards natural responses → favors permissive prompts
- BERTScore (semantic similarity) confirms this with 36.4 percentage point difference
- This is actually a valuable finding about RAG evaluation methodology"
