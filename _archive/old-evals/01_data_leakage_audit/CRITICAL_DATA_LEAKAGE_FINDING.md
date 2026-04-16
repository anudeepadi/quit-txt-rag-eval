# CRITICAL FINDING: Data Leakage in Test Set

**Date:** January 10, 2026
**Analysis Phase:** 1.2 - Test Set Independence Verification

## Executive Summary

**The previous evaluation methodology is INVALID due to significant data leakage between the test questions and training datasets.**

## Detailed Findings

### Leakage Statistics

| Severity | Count | Percentage | Description |
|----------|-------|------------|-------------|
| **SEVERE (>=90%)** | 7 | 47% | Near-identical or exact matches in training data |
| **MODERATE (70-90%)** | 6 | 40% | Similar questions in training data |
| **CLEAN (<70%)** | 2 | 13% | Truly independent questions |

### Exact Matches (100% Similarity)

The following test questions appear **EXACTLY** in the training datasets:

1. **Q5:** "Will I gain weight if I quit smoking?" - EXACT in BOTH datasets
2. **Q6:** "How does smoking affect my cardiovascular health?" - EXACT in Human-curated
3. **Q7:** "What should I do if I relapse after quitting?" - EXACT in Human-curated
4. **Q12:** "How does secondhand smoke affect children?" - EXACT in Human-curated

### Severe Leaks (>=90% Similarity)

| Test Question | Best Match | Similarity |
|---------------|------------|------------|
| Q3: How can I deal with nicotine cravings when they hit? | "How can I deal with cravings when they hit?" | 90.5% |
| Q10: How can I help a family member who wants to quit smoking? | "How can I help a friend or family member who wants..." | 91.9% |
| Q14: How long do withdrawal symptoms typically last? | "How long do these withdrawal symptoms typically la..." | 94.0% |

### Only Clean Questions

Only 2 out of 15 questions are truly independent:

1. **Q8:** "Can you explain how nicotine addiction works in the brain?" (58% max similarity)
2. **Q15:** "Is cold turkey or gradual reduction better for quitting?" (61% max similarity)

## Impact on Previous Results

### Why This Invalidates Previous Findings

1. **Retrieval Advantage:** When test questions match training questions, RAG retrieval is trivially finding the answer rather than generalizing
2. **Inflated Scores:** All RAG approaches would show artificially high performance on leaked questions
3. **Unfair Comparison:** Human-curated has 4 exact matches while AI-generated has 1 - biasing the comparison
4. **Non-generalizable:** Results don't reflect real-world performance on novel questions

### Previous Results Are NOT Trustworthy

The finding that "Raw > Human > AI" may be an artifact of:
- Different leakage rates across datasets
- Retrieval finding exact matches vs. semantic matches
- Evaluation metrics rewarding exact reproduction

## Recommended Actions

### Immediate (Required for Valid Research)

1. **Create new test set** with 0% overlap with training data
2. **Use fuzzy matching** during test set creation to ensure independence
3. **Re-run ALL experiments** with the new test set
4. **Document this finding** in the paper's limitations section

### Test Set Creation Criteria

New test questions must:
- Have <50% similarity to ANY question in EITHER dataset
- Cover the same topics (benefits, cravings, NRT, relapse, etc.)
- Be grammatically distinct (not just word substitutions)
- Be validated by a domain expert if possible

## Conclusion

**The previous research conclusions cannot be trusted.**

A complete re-evaluation with an independent test set is required before any publication claims can be made.

---

*This finding was discovered during Phase 1.2 of the comprehensive re-analysis.*
*Analysis performed using SequenceMatcher fuzzy string matching with multiple thresholds.*
