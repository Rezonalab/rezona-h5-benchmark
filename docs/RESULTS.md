# Run results (generation phase), September 2026

Scope: 12 model configurations × 150 shared cases (`data/cases_150.json`), two prompt sets (Web zh, Mobile en).
Success = `project/dist/index.html` produced within 120 min. Costs recomputed from token usage (see PRICING.md).
Per-case CSVs (tokens, wall time, status) are in the result buckets' `meta/` folders; judge scores are produced by
`eval/run_eval.py` and are **not** included here.

## Web set (Chinese desktop prompts) — 150 cases

| model | agent | success | terminal failures | cost USD | USD/case | avg min |
|---|---|---|---|---|---|---|
| GPT-5.5 high | Codex | 150 | – | 242 | 1.62 | 6 |
| GPT-5.6-sol high | Codex | 150 | – | 111 | 0.74 | 6 |
| GPT-6 astra high | Codex | 150 | – | 1,159 | 7.72 | 27 |
| Opus 5 xhigh | Claude Code | 141 | 8 timeout, 1 safety block | 2,698 | 17.98 | 60 |
| Fable 5 xhigh | Claude Code | 148 | 2 refusal | 1,624 | 10.83 | 29 |
| Fable 5.1 xhigh | Claude Code | 148 | 2 refusal | 2,349 | 15.66 | 40 |
| DeepSeek-V4-Pro | Codex | 150 | – | 39 | 0.26 | 12 |
| DeepSeek-V4-Flash | Claude Code | 149 | 1 timeout | 77 | 0.51 | 33 |
| DeepSeek 4.1 Flash (`deepseek-flash`) | Claude Code | 149 | 1 no_dist | 78 | 0.52 | 23 |
| GLM-5.2 | Claude Code | 150 | – | n/a | n/a | 34 |
| GLM-5.3 | Claude Code | 143 | 7 timeout | n/a | n/a | 66 |
| Kimi-K3 | Claude Code | 150 | – | ~200 | ~1.3 | 25 |
| Seed evolving (run 1) | Claude Code | 142 | 4 timeout, 3 req-timeout, 1 no_dist | 78 | 0.52 | 47 |
| Seed evolving (rerun 09-10) | Claude Code | 129 | 15 timeout, 2 req-timeout, 2 no_dist | 94 | 0.63 | 63 |

The six overseas models and Seed evolving also completed the full 250-case set (`benchmark_merged.json`);
the 150 subset is what every model shares. Seed evolving was additionally rerun on the full 250 on 09-16
(217 success / 29 timeout / 3 req-timeout / 1 no_dist, $155) — kept locally, not uploaded.

## Mobile set (English prompts with a [Mobile] section) — 150 cases

| model | success | terminal failures | cost USD | USD/case | avg min |
|---|---|---|---|---|---|
| GPT-5.5 high | 150 | – | 248 | 1.66 | 6 |
| GPT-5.6-sol high | 150 | – | 107 | 0.72 | 5 |
| GPT-6 astra high | 150 | – | 1,132 | 7.55 | 27 |
| Opus 5 xhigh | 144 | 5 timeout, 1 safety block | 3,231 | 21.54 | 66 |
| Fable 5 xhigh | 146 | 3 refusal, 1 req-timeout | 1,974 | 13.16 | 33 |
| Fable 5.1 xhigh | 147 | 3 refusal | 2,464 | 16.43 | 39 |
| DeepSeek-V4-Pro | 150 | – | 46 | 0.31 | 14 |
| DeepSeek-V4-Flash | 149 | 1 timeout | 82 | 0.54 | 24 |
| DeepSeek 4.1 Flash | 149 | 1 timeout | 82 | 0.55 | 24 |
| GLM-5.2 | 150 | – | n/a | n/a | 38 |
| GLM-5.3 | 124 | 26 timeout | n/a | n/a | 84 |
| Kimi-K3 | 55 (incomplete) | 92 account-suspended, 2 no_project | 107 | – | 17 |
| Seed evolving | 128 | 18 timeout, 2 req-timeout, 1 no_dist, 1 no_project | 100 | 0.66 | 69 |

Kimi-K3 mobile stopped at 55 when the Moonshot account balance ran out; the remaining 95 were never rerun.

## Refusals / safety blocks

* `hard_rewrite_032` (mobile): refused by Fable 5, Fable 5.1 and blocked by Opus 5 safeguards.
* `v3_shooter_3d_001` (first-person air combat): Fable 5.1 refused on every attempt (web and mobile).
* `v3_turn_based_4x_2d_027` (mobile): refused by Fable 5 and Fable 5.1.

## Artifacts

* Web: `gs://rezonaai-benchmark-result/benchmark_lab/<model_key>.zip` (+ `cc_seed_evolving_rerun_20260910.zip`,
  `cc_seed_evolving_supplement_20260915.zip`), `meta/status_*.csv`, `meta/cases_150.json`.
* Mobile: `gs://rezonaai-benchmark-result/benchmark_lab_mobile/<model_key>.zip`, `meta/status_*.csv`.
* Playable index (public): `https://storage.googleapis.com/rezonaai-benchmark-play/index.html` (20 shared cases) and
  `…/mobile12/index.html` (12 hand-picked mobile cases).

Zip layout: `<model_key>/<task_id>/{project/ (src + dist, no node_modules), prompt.md, transcript.jsonl, stderr.log, meta.json}`.
