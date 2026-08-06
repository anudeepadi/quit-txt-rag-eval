# Statistical Significance Tests

**Generated:** 2026-08-04T21:11:15.684174
**Test:** Wilcoxon signed-rank (two-sided, paired)
**Effect size:** Cliff's delta
**Confidence intervals:** Bootstrap 95% (10,000 samples)

## Bootstrap 95% Confidence Intervals

| Config | Metric | Mean | 95% CI | n |
|---|---|---|---|---|
| ai_rag | faithfulness | 0.8167 | [0.7535, 0.8756] | 100 |
| human_rag | faithfulness | 0.7707 | [0.7046, 0.8322] | 100 |

## Pairwise Comparisons


### faithfulness

| Comparison | p-value | Significant? | Cliff's d | Effect Size |
|---|---|---|---|---|
| ai_rag vs human_rag | 0.099140 | ns | 0.1100 | negligible |

## Non-Inferiority vs `human_rag` (margin = 0.05)

The two-sided Wilcoxon above can only fail to detect a difference; it cannot establish parity. These tests reject the null that the candidate arm is worse than `human_rag` by at least 0.05.


### faithfulness

| Comparison | Mean diff | 95% CI | One-sided LB | p (non-inf) | p (equiv) | Non-inferior? | Equivalent? | n |
|---|---|---|---|---|---|---|---|---|
| ai_rag vs human_rag | 0.0460 | [-0.0152, 0.1051] | -0.0051 | 0.000000 | 0.030113 | True | True | 100 |

## Interpretation Guide

**Significance levels:** * p<0.05, ** p<0.01, ns = not significant

**Cliff's delta magnitudes:** |d|<0.147 negligible, <0.33 small, <0.474 medium, ≥0.474 large

**Non-inferiority:** the candidate is declared non-inferior when the one-sided 95% lower bound on (candidate − human_rag) sits above −0.05 and the paired Wilcoxon shifted by +0.05 rejects at p<0.05. **Equivalence** additionally requires the upper one-sided test to reject (TOST), i.e. the difference is bounded inside ±0.05 in both directions.

**Margin justification:** 0.05 faithfulness is ~1.7x the measured run-to-run noise floor (sd 0.0115, minimum detectable effect ~0.03). The margin is pre-registered — it must not be revised after the frozen test set is unblinded.
