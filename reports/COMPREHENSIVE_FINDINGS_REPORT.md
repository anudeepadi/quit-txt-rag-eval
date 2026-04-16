# Comprehensive Findings Report
## RAG Comparison for Smoking Cessation Counseling

**Date:** January 10, 2026
**Principal Investigator:** Research Team
**Project:** QuitTxt Smoking Cessation System

---

## Executive Summary

This study conducted a rigorous comparison of Retrieval-Augmented Generation (RAG) approaches for smoking cessation counseling. Our analysis revealed a **critical methodological issue** in the original evaluation: severe data leakage contaminated 47% of test questions. After creating an independent test set, results showed that **baseline LLM performance exceeds all RAG variants** for this well-documented domain.

### Key Takeaways

1. **Data leakage invalidated previous conclusions** - 7/15 original test questions had ≥90% similarity to training data
2. **Baseline outperforms RAG** - No retrieval needed for well-known domains
3. **AI-generated matches human-curated** - 102.1% relative performance
4. **Professor's Target 1: MET** - AI achieves 102% of Human (target was 84%)
5. **Professor's Target 2: NOT MET** - AI only +7.8% vs Raw (target was +40%)

---

## 1. Methodology

### 1.1 Data Audit

| Dataset | Records | Duplicates | Quality |
|---------|---------|------------|---------|
| Human-Curated Q&A | 4,847 | 505 (10.4%) | Good |
| AI-Generated Q&A | 5,936 | 0 (0%) | Excellent |

### 1.2 Critical Discovery: Data Leakage

During our audit, we discovered the original test set was contaminated:

| Severity Level | Count | Percentage |
|----------------|-------|------------|
| **Severe (≥90% similarity)** | 7 | 47% |
| Moderate (70-90%) | 6 | 40% |
| Clean (<70%) | 2 | 13% |

**Exact Matches Found (100% similarity):**
- "How can I manage weight gain after quitting smoking?"
- "What are the cardiovascular benefits of quitting smoking?"
- "How can I prevent relapse after quitting smoking?"
- "What are the dangers of secondhand smoke?"

### 1.3 Independent Test Set Creation

We created 15 new questions with:
- Maximum 50% similarity to any training question
- Coverage of all original topics
- Validated using SequenceMatcher fuzzy matching
- Expert-reviewed reference answers

### 1.4 Experimental Protocol

| Parameter | Value |
|-----------|-------|
| Model | GPT-4o-mini |
| Temperature | 0.3 |
| Max Tokens | 200 |
| Retrieval | ChromaDB, k=3 |
| Runs | 5 independent trials |
| Test Questions | 15 |

---

## 2. Results

### 2.1 Primary Metric: ROUGE-L

| Rank | Approach | Mean | Std | 95% CI |
|------|----------|------|-----|--------|
| 1 | **Baseline (No RAG)** | **0.2305** | 0.0090 | ±0.0079 |
| 2 | AI-Generated RAG | 0.2245 | 0.0055 | ±0.0049 |
| 3 | Human-Curated RAG | 0.2197 | 0.0044 | ±0.0038 |
| 4 | Raw Sources RAG | 0.2083 | 0.0045 | ±0.0039 |

### 2.2 All Metrics Comparison

| Approach | ROUGE-L | ROUGE-1 | ROUGE-2 | BLEU | METEOR |
|----------|---------|---------|---------|------|--------|
| Baseline | **0.231** | **0.342** | **0.097** | 0.054 | **0.310** |
| AI-Generated | 0.224 | 0.325 | 0.086 | **0.057** | 0.290 |
| Human-Curated | 0.220 | 0.334 | 0.079 | 0.045 | 0.296 |
| Raw Sources | 0.208 | 0.316 | 0.068 | 0.039 | 0.275 |

### 2.3 Statistical Significance

| Comparison | Difference | Cohen's d | p-value | Significant |
|------------|------------|-----------|---------|-------------|
| AI vs Human | +2.1% | 0.72 | 0.184 | No |
| **AI vs Raw** | **+7.8%** | **3.19** | **0.002** | **Yes (p<0.01)** |
| **Human vs Raw** | **+5.5%** | **1.89** | **0.014** | **Yes (p<0.05)** |
| AI vs Baseline | -2.6% | -1.07 | 0.074 | No |
| **Raw vs Baseline** | **-9.7%** | **-3.25** | **0.002** | **Yes (p<0.01)** |

### 2.4 Professor's Research Targets

| Target | Expected | Actual | Status |
|--------|----------|--------|--------|
| AI achieves ≥84% of Human performance | ≥84% | **102.1%** | ✅ **MET** |
| AI is 40% better than Raw sources | ≥+40% | +7.8% | ❌ **NOT MET** |

---

## 3. Deep Investigation: Why Baseline > RAG?

### 3.1 Hypothesis Testing

We investigated three hypotheses to explain the unexpected result:

#### H1: Domain Saturation ✅ CONFIRMED

GPT-4o-mini's training data extensively covers smoking cessation.

**Evidence:**
- Baseline responses average 991 characters vs 902-927 for RAG
- Baseline includes accurate medical timelines and statistics
- No factual errors observed in baseline responses

#### H2: Retrieval Noise ✅ CONFIRMED

Retrieved documents are related but not precisely targeted.

**Evidence:**
- Average retrieval distance: 0.40-0.41 (borderline acceptable)
- Optimal retrieval would show distances < 0.30
- Some retrieved Q&A pairs answer slightly different questions

#### H3: Context Constraint ✅ CONFIRMED

RAG prompts limit the model's fuller knowledge.

**Evidence:**
- RAG prompt: "Use the following information to answer..."
- This constrains the model to retrieved context
- Baseline freely uses parametric knowledge

### 3.2 Response Length Analysis

| Approach | Avg Length (chars) | vs Reference |
|----------|-------------------|--------------|
| Baseline | 991 | 3.8x longer |
| Human RAG | 902 | 3.5x longer |
| AI RAG | 927 | 3.6x longer |
| Reference | 259 | - |

Longer responses provide more tokens for ROUGE matching, potentially inflating baseline scores.

---

## 4. Impact of Data Leakage

### 4.1 Ranking Reversal

| Rank | Original (Leaked) | Independent (Clean) |
|------|-------------------|---------------------|
| 1 | Raw Sources | **Baseline** |
| 2 | Human-Curated | AI-Generated |
| 3 | AI-Generated | Human-Curated |
| 4 | Baseline | Raw Sources |

**The rankings completely reversed**, demonstrating that data leakage fundamentally corrupted the original evaluation.

### 4.2 Implications

1. Previous claims about RAG superiority were artifacts of data contamination
2. Test set validation is critical for NLP research
3. Fuzzy string matching should be standard practice

---

## 5. Discussion

### 5.1 When RAG Helps vs Doesn't Help

| RAG Benefits | RAG May Not Help |
|--------------|------------------|
| Knowledge-sparse domains | Well-documented topics |
| Rapidly changing information | Stable knowledge |
| Specialized technical areas | Common knowledge |
| Custom organizational data | Public health info |

### 5.2 Practical Recommendations

1. **Always test baseline first** before implementing RAG
2. **Validate test set independence** using fuzzy matching
3. **Consider domain saturation** in LLM training data
4. **Use retrieval quality metrics** (aim for distance < 0.30)
5. **Allow hybrid prompts** that combine retrieved + parametric knowledge

### 5.3 Limitations

- Single domain (smoking cessation)
- Single LLM (GPT-4o-mini)
- Small test set (15 questions)
- Lexical metrics only (no semantic evaluation)
- Well-represented domain in training data

---

## 6. Conclusions

### 6.1 Primary Findings

1. **Methodological Contribution:** Discovered severe data leakage (47%) that invalidated previous conclusions

2. **Empirical Finding:** Baseline LLM outperforms all RAG variants for smoking cessation counseling

3. **Comparative Finding:** AI-generated knowledge bases perform comparably to human-curated ones (102% relative performance)

4. **Research Target Assessment:**
   - Target 1 (AI ≥84% Human): MET
   - Target 2 (AI +40% vs Raw): NOT MET

### 6.2 Reframed Narrative

The research question shifts from:
> "Does RAG improve performance?"

To the more nuanced:
> "When and why does RAG improve performance?"

This is arguably a more valuable contribution to the field.

---

## 7. Deliverables

### Documentation
- `COMPREHENSIVE_FINDINGS_REPORT.md` (this document)
- `DEEP_INVESTIGATION_SUMMARY.md`
- `CRITICAL_DATA_LEAKAGE_FINDING.md`

### Data
- `comprehensive_results.json` - Complete metrics
- `FINAL_independent_test_set.json` - 15 validated questions
- `deep_investigation_results.json` - Response comparisons

### Visualizations
- `fig1_main_results.pdf` - Metrics comparison
- `fig2_statistical_comparison.pdf` - Significance testing
- `fig3_data_leakage_impact.pdf` - Ranking reversal
- `fig4_metrics_table.pdf` - Complete metrics
- `fig5_targets_assessment.pdf` - Target evaluation

### Publication
- `publication_materials_FINAL.tex` - LaTeX document
- `RAG_Comparison_Paper.pdf` - Compiled paper

---

## Appendix A: Individual Run Data (ROUGE-L)

| Run | Baseline | AI-RAG | Human-RAG | Raw-RAG |
|-----|----------|--------|-----------|---------|
| 1 | 0.2305 | 0.2228 | 0.2227 | 0.2027 |
| 2 | 0.2221 | 0.2171 | 0.2153 | 0.2082 |
| 3 | 0.2210 | 0.2238 | 0.2188 | 0.2051 |
| 4 | 0.2402 | 0.2323 | 0.2163 | 0.2120 |
| 5 | 0.2389 | 0.2263 | 0.2257 | 0.2134 |

## Appendix B: Effect Size Interpretation

| Cohen's d | Interpretation |
|-----------|----------------|
| < 0.2 | Negligible |
| 0.2 - 0.5 | Small |
| 0.5 - 0.8 | Medium |
| ≥ 0.8 | Large |

---

*Report generated: January 10, 2026*
*Methodology: Comprehensive RAG evaluation with independent test set validation*
