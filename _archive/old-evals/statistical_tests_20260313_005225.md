# Statistical Significance Tests

**Generated:** 2026-03-13T00:52:31.969342
**Test:** Wilcoxon signed-rank (two-sided, paired)
**Effect size:** Cliff's delta
**Confidence intervals:** Bootstrap 95% (10,000 samples)

## Bootstrap 95% Confidence Intervals

| Config | Metric | Mean | 95% CI | n |
|---|---|---|---|---|
| baseline | faithfulness | 0.1475 | [0.0850, 0.2175] | 100 |
| baseline | answer_relevancy | 0.8320 | [0.7737, 0.8847] | 100 |
| baseline | bertscore_f1 | 0.8977 | [0.8938, 0.9016] | 100 |
| ai_rag | bertscore_f1 | 0.8848 | [0.8809, 0.8887] | 100 |
| human_rag | bertscore_f1 | 0.8891 | [0.8850, 0.8930] | 100 |
| web_rag | bertscore_f1 | 0.8831 | [0.8791, 0.8872] | 100 |

## Pairwise Comparisons


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
