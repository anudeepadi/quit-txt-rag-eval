# Synthetic onboarding result — NOT study findings

These scores are hand-authored fixtures, not generated or judged answers.
The run exercises the repository's actual loader, split guard, summary, and paired tests.

Split: 61 invented rows → 1 flagged row removed → 50 dev / 10 held out.
Optimization guard: PASS. Dev/test overlap: 0.

| Fixture | n | Mean | SD | Descriptive 95% interval |
| --- | ---: | ---: | ---: | --- |
| AI RAG fixture | 10 | 0.8060 | 0.0896 | 0.7505–0.8615 |
| Human RAG fixture | 10 | 0.8130 | 0.0673 | 0.7713–0.8547 |

Intervals above use the existing helper's normal approximation; n=10 is only a fixture.

Paired mean difference (AI − human): -0.0070.
Illustrative margin: 0.05; non-inferiority p=0.000361; TOST p=0.000361.
These calculations do not establish model parity or clinical effectiveness.
The study's 50/77 split and recorded manifest are not changed by this example.
