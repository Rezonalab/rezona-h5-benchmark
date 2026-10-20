# Human evaluation vs. the LLM judge

We checked the primary judge (`gpt-6-astra`, static code reading) against human play-testing. This page gives
aggregate results only. Per-item annotations are not released.

## Setup

* **Human raters** played each generated game in a browser and marked every checklist item as pass, fail, or
  "cannot judge". Each game was rated by one rater, so there is no inter-rater agreement figure.
* **Strictly comparable sample**: we kept only items where the human and the judge saw the same case, platform,
  model and checklist wording. That leaves 8 Mobile-75 cases × 11 models (75 games) and 344 items, 266 of them
  decided by the human (78 marked "cannot judge", 23%).
* Agreement is measured on those 266 items.

## Item-level agreement

| Subset | Items | Human pass | Judge pass | Agreement | Cohen's κ |
|---|---|---|---|---|---|
| All items | 266 | 76.3% | 46.2% | 61.7% | 0.26 |
| Public checklist | 165 | 84.8% | 46.1% | 56.4% | 0.17 |
| Hidden probes | 101 | 62.4% | 46.5% | 70.3% | 0.42 |
| Excluding gate-failed games | 255 | 78.8% | 48.2% | 60.8% | 0.23 |

Disagreements almost all go one way: in 91 items the human passed what the judge failed, and in only 11 items the
judge passed what the human failed. Just 2 of those 91 come from a whole game being zeroed by the runnability gate.
On a looser sample that also includes items whose wording was later revised (368 decided items), κ = 0.21.

## Model-level agreement

The ranking matters more for a benchmark than the absolute pass rate. Below are the 9 models with at least 20 decided
items:

| Model | Decided items | Human pass | Judge pass |
|---|---|---|---|
| GPT-6 astra | 34 | 94.1% | 61.8% |
| Opus 5 | 31 | 90.3% | 58.1% |
| Fable 5.1 | 33 | 84.8% | 60.6% |
| GPT-5.6-sol | 24 | 83.3% | 50.0% |
| DeepSeek 4.1 Flash | 22 | 81.8% | 40.9% |
| GPT-5.5 | 25 | 80.0% | 48.0% |
| Seed evolving | 25 | 80.0% | 40.0% |
| GLM-5.3 | 33 | 57.6% | 33.3% |
| Fable 5 | 28 | 42.9% | 32.1% |

Spearman ρ between the human and judge per-model pass rates is **0.95**.

## Takeaways

* **Strict but order-preserving.** The judge's absolute pass rates are about 30 percentage points below the human
  ones, but it ranks models almost the same way. Read leaderboard numbers as relative, not as "share of features
  that work for a player".
* **Self-preference risk.** The judge and the top-ranked model are from the same family. Human raters also put
  GPT-6 astra first (94.1% on the comparable items above), which is independent evidence that its rank is not just a
  judge artifact.

## Limitations

* Coverage is narrow: 8 cases, all from Mobile-75.
* Gate-failure rate in the human sample (about 2%) is much lower than in the full results (about 20%), so "humans
  are more lenient" should not be extrapolated to gate-failed games.
* Every game was rated once, so there is no inter-rater agreement estimate.
