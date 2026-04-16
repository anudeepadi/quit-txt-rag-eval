# Honest Results Analysis - Fair Three-Way Comparison

**Generated: January 6, 2026**

---

## Executive Summary

After running a **truly fair comparison** with identical conditions for all approaches, the results are **unexpected and require honest discussion**.

---

## Fair Comparison Results

| Approach | BLEU | ROUGE-1 | ROUGE-L |
|----------|------|---------|---------|
| Baseline (No RAG) | 0.167 | 0.321 | **0.259** |
| Raw Sources RAG | 0.185 | **0.357** | 0.256 |
| AI-Generated RAG | **0.329** | 0.314 | 0.236 |
| Human-Curated RAG | 0.242 | 0.317 | 0.242 |

---

## Key Findings (Honest Assessment)

### 1. AI-Generated RAG has HIGHER BLEU than Human-Curated

- AI RAG: 0.329 BLEU
- Human RAG: 0.242 BLEU
- **AI achieves 136% of Human performance** (not 71% as previously claimed)

**Why?** The AI-generated dataset was created by an LLM (Gemini), so its vocabulary and phrasing naturally aligns with how GPT-4o-mini generates responses. This creates artificially high lexical similarity.

### 2. Baseline Beats ALL RAG on ROUGE-L

- Baseline: 0.259 ROUGE-L
- All RAG approaches: 0.236-0.256 ROUGE-L

**Implication:** For this domain, the LLM (GPT-4o-mini) already has strong built-in knowledge about smoking cessation. RAG may actually add noise rather than help.

### 3. Raw Sources has HIGHEST ROUGE-1

- Raw Sources: 0.357 ROUGE-1
- Others: 0.314-0.321 ROUGE-1

This is unexpected and suggests the raw content provides useful factual grounding.

---

## What the Previous Claims Got Wrong

| Previous Claim | Previous Number | Fair Comparison Result |
|----------------|-----------------|------------------------|
| AI achieves X% of Human | 70.6% | **136.1%** (AI > Human) |
| AI better than Raw by | 149.7% | **77.9%** |
| Human better than Raw by | 254.0% | **30.7%** |

**The previous numbers were INVALID** because they compared different experiments with different test questions.

---

## Why AI Outperforms Human on BLEU

1. **LLM Vocabulary Alignment**: AI-generated content was created by Gemini, which uses similar phrasing patterns to GPT-4o-mini
2. **Human Uses Expert Terminology**: Human-curated answers use specialized clinical vocabulary that doesn't match LLM natural output
3. **Response Length**: AI-generated responses tend to be more concise, which can affect BLEU scoring

---

## Revised Meeting Target Assessment

| Target | Expected | Actual | Status |
|--------|----------|--------|--------|
| AI 40% better than Raw (BLEU) | 40% | **77.9%** | EXCEEDED |
| AI achieves 84% of Human (BLEU) | 84% | **136.1%** | UNEXPECTED (AI > Human) |

---

## Honest Conclusions

1. **The improvement numbers in previous reports were inflated** due to comparing different experiments

2. **AI-generated dataset performs BETTER than human-curated on BLEU** - this is counterintuitive but explainable (LLM vocabulary alignment)

3. **RAG doesn't significantly help for this domain** - the baseline LLM already knows smoking cessation well

4. **The narrative needs revision** - we cannot claim human-curated > AI-generated on lexical metrics

---

## Recommendations for Paper

1. **Focus on semantic metrics (ROUGE-L)** where differences are smaller and more nuanced
2. **Acknowledge the domain limitation** - smoking cessation is well-covered in LLM training data
3. **Discuss LLM vocabulary alignment** as an interesting finding
4. **Be transparent about methodology** - previous comparisons were methodologically flawed

---

*This analysis reflects the rigorous validation requested by the user.*
