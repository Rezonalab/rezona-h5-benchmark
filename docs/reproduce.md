# Reproducing the generation runs

This is how the v1 results were generated, with the pitfalls we hit along the way. Running all 13 models on 180 cases
costs several thousand USD (see [`results/generation.csv`](../results/generation.csv)). Start with `--limit` and one
model.

## Requirements

* Python ≥ 3.10, Node 24, `zip`.
* Agent CLIs, pinned to the versions used for v1:
  `npm i -g @anthropic-ai/claude-code@2.1.263 @openai/codex@0.147.0`.
  Set `BENCH_TOOLS_BIN=<dir>` to make the runner use a specific install.
* Claude Code refuses `--dangerously-skip-permissions` as root, so run the harness as an unprivileged user.
* Codex ≥ 0.147 only speaks the Responses API (`wire_api = "responses"`). Every Codex provider in
  `configs/models.json` must offer `/responses`.
* Region: Anthropic and OpenAI reject requests from mainland China and Hong Kong. We ran those models from Singapore.
  The Chinese vendors (DeepSeek, Zhipu, Moonshot, Volcengine Ark) are reachable from both regions.
* Agents run their own headless-browser self-tests. Give the machine plenty of cores and RAM, or lower the
  concurrency.

## Setup

```bash
export BENCH_HOME=$HOME/bench                      # runs/, logs/, per-model CLI homes live here
mkdir -p $BENCH_HOME/configs
cp configs/models.json $BENCH_HOME/configs/
cp configs/prompt_template_web_zh.md    $BENCH_HOME/configs/prompt_template.md          # web cases
cp configs/prompt_template_mobile_zh.md $BENCH_HOME/configs/prompt_template_mobile.md   # cases with platform=mobile
cp configs/keys.env.example $BENCH_HOME/configs/keys.env && chmod 600 $BENCH_HOME/configs/keys.env   # fill in your keys
```

The runner wraps each case's `prompt` in `prompt_template.md`, or in `prompt_template_mobile.md` when the case has
`platform: mobile` and that file exists. In the v1 results, PC-75 and Final-30 used the Chinese templates and
Chinese prompts. Mobile-75 used `prompt_template_mobile_en.md` with an English prompt variant that has a `[Mobile]`
section (not in this release; see [`data/README.md`](../data/README.md)).

## Run

```bash
python3 harness/run_bench.py smoke --models all                                    # hello-world through every model with a key
python3 harness/run_bench.py run --models cc_opus_5 --cases data/octave_180_zh.jsonl --limit 3
harness/scripts/run_set.sh cc_opus_5 15 data/octave_180_zh.jsonl 120 opus5       # detached full run, log in $BENCH_HOME/logs
python3 harness/run_bench.py status --models cc_opus_5                             # → $BENCH_HOME/status.csv
```

Output for each case: `$BENCH_HOME/runs/<model_key>/<task_id>/{project/, prompt.md, transcript.jsonl, stderr.log, meta.json}`.

* **Runs are idempotent.** A case whose `meta.json` says `success` or `refusal` is skipped. Any other status is
  retried, and the previous attempt's logs move to `attempts/`. `--task-ids a,b,c` reruns a hand-picked list.
* **Success** means `project/dist/index.html` exists. `node_modules` and build caches are deleted after each case.
* **Time limit**: 120 minutes per case for every model. Timeouts are recorded as results and not retried.

### Status values (`meta.json.status`)

| Status | Meaning |
|---|---|
| `success` | `dist/` was built |
| `timeout` | Killed at 120 min. Source is usually present, often with a `dist/` |
| `no_dist` | The agent stopped without a successful build, sometimes while claiming it had built |
| `no_project` | Nothing was written |
| `agent_error` | The CLI exited non-zero: API error, request timeout, out of credit, rate limit |
| `refusal` | Safety refusal. Terminal, never retried |

## Per-model wiring (`configs/models.json`)

* **`agent: claude`** runs Claude Code with `ANTHROPIC_BASE_URL` and `ANTHROPIC_MODEL`.
  * Third-party endpoints get `ANTHROPIC_AUTH_TOKEN`; api.anthropic.com gets `ANTHROPIC_API_KEY`.
  * Optional `--effort` from `effort`.
  * `CLAUDE_CODE_MAX_OUTPUT_TOKENS=64000`: the default 32000 was hit in a single turn.
  * Each model gets its own `CLAUDE_CONFIG_DIR`.
* **`agent: codex`** runs Codex with a private `CODEX_HOME` whose `config.toml` defines one `model_provider`
  (Responses API) and `model_reasoning_effort`.
* **Anthropic-compatible endpoints that worked**:
  * DeepSeek `https://api.deepseek.com/anthropic`
  * Zhipu `https://open.bigmodel.cn/api/anthropic`
  * Moonshot `https://api.moonshot.cn/anthropic`
* **Seed evolving** goes through a local LiteLLM proxy (`configs/litellm_seed.yaml`,
  `harness/scripts/start_litellm.sh`, listening on 127.0.0.1:4000). A regular Ark key has no Anthropic-compatible
  endpoint. Proxy settings that matter:
  * Use the `volcengine/` provider (chat completions). The `openai/` provider routes to Ark's Responses API, which
    fails multi-turn tool calls.
  * Keep `additional_drop_params: ["user"]`.
  * Keep a long `timeout`: Seed's first turn can think for more than 10 minutes.
* **`custom_headers_env`** (optional) names a variable in `keys.env` whose value is passed to Claude Code as
  `ANTHROPIC_CUSTOM_HEADERS`.

## Judge and score

```bash
cp .env.example .env    # judge credentials (see below)
python3 eval/run_eval.py --runs $BENCH_HOME/runs --cases data/octave_180_zh.jsonl --models cc_opus_5 --concurrency 4
python3 scoring/aggregate.py --status $BENCH_HOME/status.csv --eval-dir eval_results --subset data/octave_180_zh.jsonl
```

`eval/run_eval.py` picks the rubric per case: 2D or 3D from `render`, web or mobile from `platform`. It scores the 6
checklist items and the 4 hidden probes separately.

> The v1 results were judged with **gpt-6-astra**. The `utils/llm_invoke.py` backend in this repo currently calls
> Anthropic models (default `claude-opus-5`, or the `claude -p` fallback with `EVAL_ALLOW_CC_FALLBACK=1`). Scores
> from a different judge model are not directly comparable with `results/`.

## Things that bit us

* **Account limits, not machines, caused every interruption**: credit exhaustion, monthly spend caps, per-model rate
  tiers. Each stop wastes the cases in flight (up to $20 each for the most expensive models). Fund the accounts
  before launching.
* **Orphan browsers.** Headless Chrome left behind by agents' Playwright self-tests can each pin a dozen cores.
  `harness/scripts/reap_chrome.sh` (run it from cron every 5 min) kills orphans and browsers older than 30 min.
* **Refusals cluster on a few prompts** (`hard_rewrite_032`, `v3_shooter_3d_001`, `v3_turn_based_4x_2d_027`).
* **Hosting built games.** If you host them on GCS, serve them from a public bucket via `storage.googleapis.com`.
  Authenticated `storage.cloud.google.com` links render blank because module scripts fail behind the login redirect.
  `playground/build_play.py` builds a static "click to play" index and rewrites absolute asset paths.
