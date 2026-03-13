# Statistical Significance Tests

**Generated:** 2026-03-13T01:54:59.120959
**Test:** Wilcoxon signed-rank (two-sided, paired)
**Effect size:** Cliff's delta
**Confidence intervals:** Bootstrap 95% (10,000 samples)

## Bootstrap 95% Confidence Intervals

| Config | Metric | Mean | 95% CI | n |
|---|---|---|---|---|
| baseline | answer_relevancy | 0.8411 | [0.7843, 0.8915] | 100 |
| baseline | bertscore_f1 | 0.8977 | [0.8938, 0.9016] | 100 |
| ai_rag | faithfulness | 0.7237 | [0.6503, 0.7970] | 100 |
| ai_rag | answer_relevancy | 0.5635 | [0.4789, 0.6465] | 100 |
| ai_rag | context_precision | 0.4808 | [0.3867, 0.5717] | 100 |
| ai_rag | context_recall | 0.2590 | [0.1947, 0.3260] | 100 |
| ai_rag | bertscore_f1 | 0.8848 | [0.8809, 0.8887] | 100 |
| human_rag | faithfulness | 0.7888 | [0.7183, 0.8555] | 100 |
| human_rag | answer_relevancy | 0.7075 | [0.6334, 0.7786] | 100 |
| human_rag | context_recall | 0.4231 | [0.3508, 0.4973] | 100 |
| human_rag | bertscore_f1 | 0.8891 | [0.8850, 0.8930] | 100 |
| web_rag | faithfulness | 0.7187 | [0.6420, 0.7910] | 100 |
| web_rag | answer_relevancy | 0.5260 | [0.4403, 0.6086] | 100 |
| web_rag | context_recall | 0.3054 | [0.2342, 0.3780] | 100 |
| web_rag | bertscore_f1 | 0.8831 | [0.8791, 0.8872] | 100 |

## Pairwise Comparisons


### faithfulness

| Comparison | p-value | Significant? | Cliff's d | Effect Size |
|---|---|---|---|---|
| baseline vs ai_rag | N/A | ns | N/A | insufficient data |
| baseline vs human_rag | N/A | ns | N/A | insufficient data |
| baseline vs web_rag | N/A | ns | N/A | insufficient data |
| ai_rag vs human_rag | 0.115632 | ns | -0.1200 | negligible |
| ai_rag vs web_rag | 0.914128 | ns | -0.0400 | negligible |
| human_rag vs web_rag | 0.070611 | ns | 0.1300 | negligible |

### answer_relevancy

| Comparison | p-value | Significant? | Cliff's d | Effect Size |
|---|---|---|---|---|
| baseline vs ai_rag | 0.000000 | p<0.01 | 0.4000 | medium |
| baseline vs human_rag | 0.003369 | p<0.01 | 0.1800 | small |
| baseline vs web_rag | 0.000000 | p<0.01 | 0.4100 | medium |
| ai_rag vs human_rag | 0.003768 | p<0.01 | -0.2000 | small |
| ai_rag vs web_rag | 0.406084 | ns | 0.0500 | negligible |
| human_rag vs web_rag | 0.000049 | p<0.01 | 0.3000 | small |

### context_precision

| Comparison | p-value | Significant? | Cliff's d | Effect Size |
|---|---|---|---|---|
| baseline vs ai_rag | N/A | ns | N/A | insufficient data |
| baseline vs human_rag | N/A | ns | N/A | insufficient data |
| baseline vs web_rag | N/A | ns | N/A | insufficient data |
| ai_rag vs human_rag | N/A | ns | N/A | insufficient data |
| ai_rag vs web_rag | N/A | ns | N/A | insufficient data |
| human_rag vs web_rag | N/A | ns | N/A | insufficient data |

### context_recall

| Comparison | p-value | Significant? | Cliff's d | Effect Size |
|---|---|---|---|---|
| baseline vs ai_rag | N/A | ns | N/A | insufficient data |
| baseline vs human_rag | N/A | ns | N/A | insufficient data |
| baseline vs web_rag | N/A | ns | N/A | insufficient data |
| ai_rag vs human_rag | 0.000008 | p<0.01 | -0.3100 | small |
| ai_rag vs web_rag | 0.215839 | ns | -0.0600 | negligible |
| human_rag vs web_rag | 0.000648 | p<0.01 | 0.2100 | small |

### bertscore_f1

| Comparison | p-value | Significant? | Cliff's d | Effect Size |
|---|---|---|---|---|
| baseline vs ai_rag | 0.000000 | p<0.01 | 0.5400 | large |
| baseline vs human_rag | 0.000000 | p<0.01 | 0.4800 | large |
| baseline vs web_rag | 0.000000 | p<0.01 | 0.5800 | large |
| ai_rag vs human_rag | 0.094717 | ns | -0.1200 | negligible |
| ai_rag vs web_rag | 0.138874 | ns | 0.2000 | small |
| human_rag vs web_rag | 0.007427 | p<0.01 | 0.2500 | small |

## Interpretation Guide

**Significance levels:** * p<0.05, ** p<0.01, ns = not significant

**Cliff's delta magnitudes:** |d|<0.147 negligible, <0.33 small, <0.474 medium, ≥0.474 large
