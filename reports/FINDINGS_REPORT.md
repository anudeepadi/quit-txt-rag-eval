# Comprehensive RAG Evaluation Findings Report

**Date:** January 10, 2026
**Study:** RAG Comparison for Smoking Cessation Counseling
**Test Set:** 15 Independent Questions (<50% similarity to training data)
**Runs:** 5 independent trials
**Model:** GPT-4o-mini (temperature=0.3, max_tokens=200)

---

## Executive Summary

After discovering **severe data leakage** in the original test set (7/15 questions with ≥90% similarity to training data, including 4 exact matches), we created an independent test set and re-ran all experiments. The results reveal a **fundamentally different conclusion** from previous analysis.

### Key Finding

**Baseline (no RAG) outperforms all RAG approaches** on the independent test set. This suggests that for well-known domains like smoking cessation, the LLM's parametric knowledge may be sufficient or even superior to retrieval-augmented approaches.

### Result Hierarchy (ROUGE-L)

| Rank | Approach | ROUGE-L | 95% CI |
|------|----------|---------|--------|
| 1 | **Baseline (No RAG)** | 0.2305 | ±0.0079 |
| 2 | AI-Generated RAG | 0.2245 | ±0.0049 |
| 3 | Human-Curated RAG | 0.2197 | ±0.0038 |
| 4 | Raw Sources RAG | 0.2083 | ±0.0039 |

---

## Professor's Research Targets

### Target 1: AI achieves ≥84% of Human performance
- **Expected:** AI ≥ 84% of Human
- **Actual:** AI = **102.1%** of Human
- **Status:** ✅ **MET** - AI slightly exceeds Human

### Target 2: AI is 40% better than Raw
- **Expected:** AI > Raw by ≥40%
- **Actual:** AI = **+7.8%** better than Raw
- **Status:** ❌ **NOT MET** - Only 7.8% improvement vs 40% target

---

## Complete Metrics Summary

### ROUGE-L (Primary Metric)
| Approach | Mean | Std | 95% CI | Min | Max |
|----------|------|-----|--------|-----|-----|
| Baseline | 0.2305 | 0.0090 | ±0.0079 | 0.2210 | 0.2402 |
| AI-Generated | 0.2245 | 0.0055 | ±0.0049 | 0.2171 | 0.2323 |
| Human-Curated | 0.2197 | 0.0044 | ±0.0038 | 0.2153 | 0.2257 |
| Raw Sources | 0.2083 | 0.0045 | ±0.0039 | 0.2027 | 0.2134 |

### ROUGE-1
| Approach | Mean | Std | 95% CI |
|----------|------|-----|--------|
| Baseline | 0.3422 | 0.0110 | ±0.0096 |
| Human-Curated | 0.3345 | 0.0085 | ±0.0075 |
| AI-Generated | 0.3249 | 0.0045 | ±0.0039 |
| Raw Sources | 0.3158 | 0.0054 | ±0.0047 |

### BLEU
| Approach | Mean | Std | 95% CI |
|----------|------|-----|--------|
| AI-Generated | 0.0566 | 0.0029 | ±0.0025 |
| Baseline | 0.0536 | 0.0047 | ±0.0041 |
| Human-Curated | 0.0451 | 0.0038 | ±0.0034 |
| Raw Sources | 0.0388 | 0.0032 | ±0.0028 |

### METEOR
| Approach | Mean | Std | 95% CI |
|----------|------|-----|--------|
| Baseline | 0.3101 | 0.0109 | ±0.0095 |
| Human-Curated | 0.2962 | 0.0117 | ±0.0103 |
| AI-Generated | 0.2904 | 0.0089 | ±0.0078 |
| Raw Sources | 0.2748 | 0.0095 | ±0.0084 |

---

## Statistical Significance Testing

All comparisons use paired t-tests on 5 runs with ROUGE-L scores.

### Pairwise Comparisons

| Comparison | Difference | Cohen's d | p-value | Significant |
|------------|------------|-----------|---------|-------------|
| AI vs Human | +2.1% | 0.72 (medium) | 0.184 | No |
| AI vs Raw | **+7.8%** | **3.19** (very large) | **0.002** | **Yes (p<0.01)** |
| Human vs Raw | **+5.5%** | **1.89** (large) | **0.014** | **Yes (p<0.05)** |
| AI vs Baseline | -2.6% | -1.07 (large) | 0.074 | No |
| Raw vs Baseline | **-9.7%** | **-3.25** (very large) | **0.002** | **Yes (p<0.01)** |

### Effect Size Interpretation
- |d| < 0.2: negligible
- 0.2 ≤ |d| < 0.5: small
- 0.5 ≤ |d| < 0.8: medium
- |d| ≥ 0.8: large

---

## Critical Methodology Finding: Data Leakage

### Original Test Set Contamination

| Severity | Count | Percentage | Description |
|----------|-------|------------|-------------|
| Severe (≥90%) | 7 | 47% | Near-identical to training questions |
| Moderate (70-90%) | 6 | 40% | Substantial overlap |
| Clean (<70%) | 2 | 13% | Adequately independent |

**Exact Matches Found (100% similarity):**
1. Weight gain concerns
2. Cardiovascular health effects
3. Relapse prevention strategies
4. Secondhand smoke dangers

### Impact of Leakage

| Test Set | Best Approach | Worst Approach |
|----------|---------------|----------------|
| **Original (leaked)** | Raw Sources | Baseline |
| **Independent (clean)** | Baseline | Raw Sources |

The ranking completely reversed, demonstrating that the original conclusions were artifacts of data contamination.

---

## Discussion

### Why Baseline Outperforms RAG

Several hypotheses explain why the no-retrieval baseline performs best:

1. **Domain Saturation:** Smoking cessation is well-documented in LLM training data. The model's parametric knowledge may already be comprehensive.

2. **Retrieval Noise:** RAG introduces potentially irrelevant context that can distract or mislead the model.

3. **Format Mismatch:** Retrieved Q&A pairs may not align well with test question formulations, especially after our independence validation.

4. **Context Dilution:** Adding retrieved context may dilute the signal compared to direct generation.

### Why AI-Generated Outperforms Human-Curated

1. **Volume Effect:** AI-generated has 5,936 pairs vs Human's 4,847, providing more retrieval candidates.

2. **Consistency:** AI-generated Q&A may have more consistent formatting that matches test questions better.

3. **Coverage:** Automatically generated content may cover more edge cases.

### Why Raw Sources Perform Worst

1. **No Semantic Structure:** Raw text lacks the question-answer structure that aids retrieval.

2. **Noise:** Web excerpts contain irrelevant boilerplate text.

3. **Retrieval Mismatch:** Embedding similarity between questions and raw text is inherently lower.

---

## Limitations

1. **Single Domain:** Results may not generalize beyond smoking cessation.

2. **Single LLM:** GPT-4o-mini; other models may show different patterns.

3. **Small Test Set:** 15 questions limits statistical power.

4. **Metric Limitations:** ROUGE/BLEU measure lexical overlap, not semantic accuracy.

5. **Domain Knowledge Saturation:** Smoking cessation is well-represented in LLM training.

---

## Recommendations

### For Publication

1. **Reframe the narrative:** Instead of "RAG improves performance," focus on "When does RAG help?"

2. **Emphasize methodology contribution:** The data leakage discovery is a significant methodological finding.

3. **Propose domain-dependency hypothesis:** RAG benefit may be inversely related to domain representation in LLM training.

### For Future Research

1. **Test on knowledge-sparse domains** where LLM parametric knowledge is limited.

2. **Evaluate with semantic metrics** like BERTScore or GPT-based evaluation.

3. **Analyze retrieval quality** directly - what documents are retrieved and why.

4. **Compare different retrieval strategies** (k values, similarity thresholds, reranking).

---

## Conclusion

This rigorous re-analysis reveals that:

1. **Data leakage invalidated previous conclusions** - a critical methodological warning for NLP researchers.

2. **RAG does not always improve performance** - especially in well-known domains.

3. **AI-generated knowledge bases can match or exceed human-curated ones** for retrieval purposes.

4. **Proper test set validation is essential** - fuzzy string matching should be standard practice.

The primary contribution shifts from "proving RAG superiority" to "demonstrating the importance of test set independence" - an arguably more valuable finding for the research community.

---

## Appendix: Raw Data

### Individual Run Scores (ROUGE-L)

| Run | Baseline | AI-RAG | Human-RAG | Raw-RAG |
|-----|----------|--------|-----------|---------|
| 1 | 0.2305 | 0.2228 | 0.2227 | 0.2027 |
| 2 | 0.2221 | 0.2171 | 0.2153 | 0.2082 |
| 3 | 0.2210 | 0.2238 | 0.2188 | 0.2051 |
| 4 | 0.2402 | 0.2323 | 0.2163 | 0.2120 |
| 5 | 0.2389 | 0.2263 | 0.2257 | 0.2134 |
| **Mean** | **0.2305** | **0.2245** | **0.2197** | **0.2083** |

---

*Report generated: January 10, 2026*
*Methodology: 5 independent runs, 15 test questions, all validated for <50% similarity to training data*
