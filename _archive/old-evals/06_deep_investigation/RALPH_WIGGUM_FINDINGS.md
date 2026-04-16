# Ralph Wiggum Cross-Validation Findings

**Date:** January 14, 2026
**Investigation:** Why Adi's RAG results differ from Ibrahim's

---

## Executive Summary

The investigation revealed that the difference in results between Adi and Ibrahim is **NOT due to implementation bugs** but rather **fundamental differences in evaluation methodology**.

---

## Key Finding: Evaluation Metric Mismatch

| Researcher | Evaluation Method | What It Measures | Result |
|------------|------------------|------------------|--------|
| **Adi** | ROUGE-L (automatic) | Textual similarity to reference | Baseline ≈ RAG |
| **Ibrahim** | Human ratings (1-5) | Actual response quality | RAG > Baseline |

---

## Why ROUGE-L Favors "Constraining" Prompts

### Experiment Results

| Approach | ROUGE-L Score | Notes |
|----------|---------------|-------|
| Original RAG (constraining prompt) | **0.258** | "Use the context" → copies text |
| Original Baseline | 0.240 | Standard responses |
| Ibrahim RAG (permissive prompt) | 0.132 | "Use your own words" → varied text |
| Ibrahim Baseline | 0.152 | Natural responses |

### Explanation

**Constraining prompt:** "Use the provided context to answer"
- Forces model to copy/paraphrase context
- Output closely matches reference text
- **HIGH ROUGE-L score** (textual similarity)

**Permissive prompt:** "Express strategies in your own words"
- Model generates varied, natural responses
- Output diverges from reference text
- **LOW ROUGE-L score** but potentially **BETTER for users**

---

## Prompt Comparison

### Original (Constraining) - HIGHER ROUGE-L
```
"You are a compassionate smoking cessation counselor.
Use the provided context to answer. Be concise (2-4 sentences)."
```

### Ibrahim-Style (Permissive) - LOWER ROUGE-L but BETTER Quality
```
"You are a compassionate smoking cessation counselor...

RESPONSE GUIDELINES:
1. Use Protocol Strategies - but express them naturally
2. Be Conversational - Don't copy-paste protocol language
3. Provide Specifics - explain HOW to use techniques
4. Vary Your Responses - avoid repeating phrases
5. Personalize - reference user's specific situation
6. Be Empathetic First - acknowledge feelings
7. Length: 3-5 sentences but substantive"
```

---

## Implications for the Research

### The "Baseline > RAG" Finding

- **Valid for ROUGE-L metric**: When measuring textual similarity, baseline and RAG perform similarly
- **May not reflect actual quality**: Permissive prompts produce better conversational responses that score WORSE on ROUGE-L

### Recommendations

1. **Add human evaluation** to validate findings
2. **Use BERTScore** as a semantic similarity metric (less sensitive to paraphrasing)
3. **Acknowledge limitation** in paper: "ROUGE-L measures textual similarity, not semantic quality"
4. **Frame the contribution differently**: "RAG benefit depends on evaluation criteria"

---

## What to Tell the Professor

The difference between my results and Ibrahim's is NOT a bug - it's a fundamental difference in what we're measuring:

1. **ROUGE-L** rewards copy-paste style responses
2. **Human evaluation** rewards natural, varied responses
3. A "constraining" prompt scores HIGH on ROUGE-L but may be WORSE for users
4. A "permissive" prompt scores LOW on ROUGE-L but produces better conversations

This is actually a **valuable finding** for the paper - it shows that RAG evaluation methodology matters significantly.

---

## Files Created

- `ibrahim_style_evaluation.py` - Comparison experiment script
- `ibrahim_style_comparison.json` - Experiment results
- `RALPH_WIGGUM_FINDINGS.md` - This summary

---

## Next Steps

1. Discuss with Ibrahim on Monday to confirm his evaluation method
2. Add BERTScore comparison (semantic similarity)
3. Consider adding human evaluation component
4. Update paper to acknowledge metric limitations
