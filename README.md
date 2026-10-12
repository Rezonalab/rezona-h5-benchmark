# h5-benchmark

End-to-end pipeline for the H5 game-generation benchmark: drive coding agents (Claude Code, Codex) over a case
set with per-model credentials, collect the generated projects, judge them with a static-code LLM rubric, and
aggregate cost / success / score tables. Everything that produced the September 2026 runs lives here.

```
configs/    models.json (model registry + prices), prompt templates (web zh / mobile en), LiteLLM proxy config,
            keys.env.example (placeholders — real keys never enter this repo)
data/       benchmark_merged.json (250 cases) · cases_150.json (paper subset) · cases_150_mobile_en.json ·
            cases_pilot10.json · remake_selected_20.json
harness/    run_bench.py (the runner) · select150.py (subset sampler) · inspect_runs.py / failed_detail.py ·
            scripts/ run_set.sh · start_litellm.sh · zip_upload.sh · reap_chrome.sh
llm-eval/   2D_eval.py 3D_eval.py 2D_mobile_eval.py 3D_mobile_eval.py — judge rubrics (Stage A runnability gate,
            Stage B per-checklist-item binary scoring, two auxiliary 0–5 dimensions)
utils/      static_eval.py (template fill + verdict validation), llm_invoke.py (Anthropic SDK / `claude -p`
            fallback), eval_json.py, tools.py (source collection)
eval/       run_eval.py — batch judge over a runs directory → eval_results/<model>/<task>.json + <model>.csv
scoring/    aggregate.py — status.csv + eval CSVs → per-model markdown table (success, cost, pass ratio)
playground/ build_play.py — extract dists from result zips, fix asset paths, build a public "▶ play" index
docs/       RUNBOOK.md (machines, wiring, pitfalls) · RESULTS.md (generation-phase numbers) · PRICING.md
```

## 1. Generate

```bash
pip install -r requirements.txt            # anthropic (judge); litellm[proxy] only for Seed evolving
npm i -g @anthropic-ai/claude-code@2.1.263 @openai/codex@0.147.0

export BENCH_HOME=$HOME/bench
mkdir -p $BENCH_HOME/configs && cp configs/models.json configs/prompt_template_web_zh.md $BENCH_HOME/configs/
cp configs/prompt_template_web_zh.md $BENCH_HOME/configs/prompt_template.md   # runner reads this name
cp configs/keys.env.example $BENCH_HOME/configs/keys.env && chmod 600 $BENCH_HOME/configs/keys.env   # fill in

python3 harness/run_bench.py smoke --models all                                   # one hello.txt per model
harness/scripts/run_set.sh cc_opus_5 15 data/cases_150.json 120 opus5             # detached run, log in $BENCH_HOME/logs
python3 harness/run_bench.py status --models cc_opus_5                            # → $BENCH_HOME/status.csv
harness/scripts/zip_upload.sh gs://<bucket>/benchmark_lab cc_opus_5
```

Mobile set: point a second `BENCH_HOME` at a directory whose `configs/prompt_template.md` is
`configs/prompt_template_mobile_en.md` and pass `data/cases_150_mobile_en.json`.
Seed evolving needs the LiteLLM proxy (`harness/scripts/start_litellm.sh`) running on 127.0.0.1:4000.

Output per case: `$BENCH_HOME/runs/<model_key>/<task_id>/{project/,prompt.md,transcript.jsonl,stderr.log,meta.json}`.
`meta.json.status` ∈ success · timeout · no_dist · no_project · agent_error · refusal (see docs/RUNBOOK.md).

## 2. Judge

```bash
cp .env.example .env                       # ANTHROPIC_API_KEY for the judge (or EVAL_ALLOW_CC_FALLBACK=1 to use `claude -p`)
python3 eval/run_eval.py --runs $BENCH_HOME/runs --cases data/cases_150.json --models cc_opus_5,codex_gpt_5_5 --concurrency 4
python3 eval/run_eval.py --runs $HOME/bench_mobile/runs --cases data/cases_150_mobile_en.json --mobile
```

The judge picks `2D_*` or `3D_*` per case (`_3d_` in task_id or a `render:3D` label). Verdict JSON keeps each
checklist item's verbatim wording as key with `"1, "` / `"0, <reason>"`, plus `total_score = "passed/N"` and the two
auxiliary dimensions. Unzipped result zips work directly as `--runs` (same layout).

## 3. Score

```bash
python3 scoring/aggregate.py --status status_web.csv --eval-dir eval_results --subset data/cases_150.json --out results_web.md
```

## 4. Playground

```bash
python3 playground/build_play.py --zips-dir /path/to/zips --cases data/cases_150.json \
    --mobile-cases data/cases_150_mobile_en.json --n 20 --bucket gs://<public-bucket>
```

## Secrets

No credential is stored in this repository. `configs/keys.env` and `.env` are git-ignored; the committed
`*.example` files hold placeholders only. `run_bench.py` passes each vendor key to its agent process through the
environment and never writes it to disk or transcripts.
