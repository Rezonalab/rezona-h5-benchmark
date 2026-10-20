# Results (v1, judge: gpt-6-astra)

Judge results for 13 models on the 180 cases in [`data/`](../data). Every number in the main leaderboard can be
recomputed with:

```bash
python scoring/leaderboard.py   # rewrites leaderboard.csv, leaderboard.md and breakdowns.json from the two score files
```

| File | Rows | Content |
|---|---|---|
| `leaderboard.csv` / `leaderboard.md` | 13 | One row per model, ranked by public pass rate |
| `breakdowns.json` | — | Same metrics sliced by track, platform, render, level, category, incentive, judge batch, and capability (C1–C8) |
| `case_scores.csv` | 2,265 | One row per model × case |
| `item_scores.csv.gz` | 22,650 | One row per judged item (6 public + 4 hidden per case), with the judge's reason |
| `generation.csv` | 2,340 | Generation side per model × case: agent status, wall time, tokens, cost (USD) |

Kimi-K3 has no Mobile-75 results, so it is scored on 105 cases. Its row is not directly comparable with the 180-case
rows.

## Metrics

* **public_rate** (ranking metric): share of the 6 public checklist items passed, averaged over cases.
* **hidden_rate**: share of the 4 hidden probes passed. Reported separately and not part of the ranking.
* **all10_rate**: all 10 items.
* **runnable_rate**: share of cases that built and passed the judge's runnability / platform / render gate. A
  gate-failed case scores 0 on every item (2 cases with no artifact at all are also counted as gate-failed).
* **functional_public_rate**: public_rate over runnable cases only. This separates "did not build" from "built but
  missing features".
* **aux_levels / aux_juice** (in `case_scores.csv`): the judge's two auxiliary 0–5 ratings (level design and game
  feel). They are not used in any ranking.

## Columns

`case_scores.csv`: `model, model_name, task_id, judge_batch, track, platform, render, category, subtype, incentive,
level, public_passed, public_total, public_rate, hidden_passed, hidden_total, hidden_rate, all10_rate, gate_failed,
artifact_present, aux_levels, aux_juice`

`item_scores.csv.gz`: `model, task_id, kind (public|hidden), item_index (0-based position in checklist /
hidden_checklist), passed (0|1), capabilities (C-codes, "|"-separated), reason`

`generation.csv`: `model, task_id, judge_batch, gen_status (success|timeout|no_dist|no_project|agent_error|refusal),
wall_min, in_tok, out_tok, cache_read_tok, cache_write_tok, cost_usd, turns`

## How the results were produced

* **Generation**: each model ran inside its agent CLI (Claude Code or Codex, see `configs/models.json`) with a
  120-minute limit per case. Prompt language: Chinese for PC-75 and Final-30. For Mobile-75, an English variant
  with an extra `[Mobile]` section. Costs are recomputed from token usage with the prices in
  [`docs/PRICING.md`](../docs/PRICING.md).
* **Judging**: `gpt-6-astra` reads the generated project's source and fills the rubric in `llm-eval/` (2D / 3D ×
  web / mobile; the variant is picked from the case's `render` and `platform`). The judge first applies a
  runnability gate and then scores each item as pass/fail with a reason.
* **Judge batches** (`judge_batch`): `PC-75` (main / web), `Mobile-75` (main / mobile), `Final-30` (expert +
  repro). Average pass rates differ a lot across batches (PC-75 is the hardest). Part of that gap may come from the
  different rubric variants, so compare models within a batch when in doubt.
* **Expert cases** were judged against their full original checklists (11–32 items). The scores here are recomputed
  on the released 6 + 4 items, which were selected before judging and match the judged items verbatim.

## Known issues

* **Self-preference risk.** The judge `gpt-6-astra` and the top model `GPT-6 astra` share a family. Human
  play-testing also ranks GPT-6 astra first, see [`docs/human_eval.md`](../docs/human_eval.md).
* **Strict judge.** The judge's absolute pass rates are about 30 percentage points below human ratings, but it
  preserves the model ranking (Spearman ρ = 0.95). See [`docs/human_eval.md`](../docs/human_eval.md).
* **GLM pricing.** GLM-5.2 / GLM-5.3 have no captured unit price, so their cost columns are empty. Fable 5.1 is
  priced as Fable 5.
