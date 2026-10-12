# Runbook — how the 2026-09 runs were executed

## Machines and network

| machine | region | use | reachability |
|---|---|---|---|
| GCP Cloud Workstation `l5-runner-1` (n2d-highmem-96, 96C/755G) | asia-southeast1 | overseas models (Claude Code + Codex) | all vendors reachable |
| Volcengine ECS hfc2.28xlarge (112C/210G) | cn-guangzhou | domestic models | api.anthropic.com / api.openai.com return 403 / region-blocked; CN vendors fast |
| GCE `trace-merge-1` (asia-east2, Hong Kong) | — | rejected | OpenAI returns `unsupported_country_region_territory`, Anthropic 403 |

Anthropic and OpenAI reject requests from mainland China and Hong Kong; run those models from Singapore.
Domestic vendors (DeepSeek, Zhipu, Moonshot, Volcengine Ark) are reachable from both.

## Agent CLIs (pinned)

* `@anthropic-ai/claude-code@2.1.263`, `@openai/codex@0.147.0`, Node 24 (`npm i -g`; on CN machines use the npmmirror registry).
* Claude Code refuses `--dangerously-skip-permissions` as root → run the harness as an unprivileged user.
* Codex ≥0.147 no longer accepts `wire_api = "chat"`; every Codex provider must speak the Responses API
  (DeepSeek `/v1/responses` and Ark `/api/v3/responses` do).

## Per-model wiring (`configs/models.json`)

* `agent: claude` — Claude Code with `ANTHROPIC_BASE_URL` + `ANTHROPIC_MODEL` (+ `ANTHROPIC_AUTH_TOKEN` for third-party
  endpoints, `ANTHROPIC_API_KEY` for api.anthropic.com), `--effort <level>`, `CLAUDE_CODE_MAX_OUTPUT_TOKENS=64000`
  (default 32000 was hit by GLM-5.2 in a single turn). Each model gets its own `CLAUDE_CONFIG_DIR`.
* `agent: codex` — Codex with a private `CODEX_HOME` whose `config.toml` defines one `model_provider` (Responses API)
  and `model_reasoning_effort`.
* Endpoints that worked: DeepSeek `https://api.deepseek.com/anthropic` (model ids `deepseek-v4-pro`, `deepseek-v4-flash`,
  later `deepseek-flash`), Zhipu `https://open.bigmodel.cn/api/anthropic`, Moonshot `https://api.moonshot.cn/anthropic`.
* Seed evolving: the ordinary Ark key has no Anthropic-compatible endpoint (`/api/coding` needs a coding-plan key), so
  Claude Code talks to a local LiteLLM proxy (`configs/litellm_seed.yaml`, `harness/scripts/start_litellm.sh`).
  Use the `volcengine/` provider (chat completions) — `openai/` routes to Ark's Responses API which fails multi-turn
  tool calls with `missing input.status`. Set `additional_drop_params: ["user"]` and a long `timeout` (Seed's first
  turn can think > 10 min; LiteLLM's default 600 s cut requests off).

## Case sets (`data/`)

* `benchmark_merged.json` — 250 cases, Chinese desktop prompts (the full set; 6 overseas models + Seed ran all 250).
* `cases_150.json` — the paper's 150-case subset: stratified by category × 2D/3D × level proportionally to the 250,
  preferring cases the slower models had already finished (`harness/select150.py`).
* `cases_150_mobile_en.json` — same 150 task_ids, English prompts with a `[Mobile]` section (portrait/landscape lock,
  touch-only). Used with `configs/prompt_template_mobile_en.md`.
* `cases_pilot10.json` — 10-case cost pilot (one per category ± 2D/3D). `remake_selected_20.json` — 20 remake cases (not run).

## Procedure

```bash
export BENCH_HOME=$HOME/bench          # runs/, logs/, cc_home/, codex_home/ live here
mkdir -p $BENCH_HOME/configs && cp configs/* $BENCH_HOME/configs/ && cp configs/keys.env.example $BENCH_HOME/configs/keys.env
# fill keys.env, chmod 600
python3 harness/run_bench.py smoke --models all                       # hello.txt through every model with a key
harness/scripts/run_set.sh cc_opus_5 15 data/cases_150.json 120 opus5        # detached; one log per launch
harness/scripts/run_set.sh codex_gpt_5_5,codex_gpt_5_6_sol 8 data/cases_150.json
python3 harness/run_bench.py status                                   # → status.csv (tokens, recomputed cost, wall)
harness/scripts/zip_upload.sh gs://<bucket>/benchmark_lab cc_opus_5   # <model>/<task>/{project,prompt.md,transcript.jsonl,meta.json}
```

Runs are idempotent: a case whose `meta.json` says `success` or `refusal` is skipped, everything else is retried and
the previous attempt's logs move to `attempts/`. `node_modules` and build caches are deleted after each case; success
means `project/dist/index.html` exists. Timeout is 120 min per case for every model (timeouts are recorded as results,
not retried). `--task-ids a,b,c` reruns a hand-picked list.

Concurrency that held up: Opus 5 = 15, Fable 5/5.1 = 10, GPT-5.x = 8, GPT-6 = 10, DeepSeek = 10, Seed = 25,
GLM-5.2 = 10, GLM-5.3 = 20 (only after the Zhipu account tier was raised; at the default tier 3 streams already got
`1302` rate-limit 429s), Kimi = 8.

## Failure taxonomy (`status` in meta.json)

`success` (dist built) · `timeout` (killed at 120 min; source usually present, often with a dist) · `no_dist` (agent
stopped without a successful build, sometimes while claiming it built) · `no_project` (nothing written) ·
`agent_error` (CLI exited non-zero: API error, request timeout, credit exhaustion, rate limit) · `refusal`
(Anthropic safety refusal; terminal, never retried). Every case directory exists regardless of status.

## Things that bit us

* Account limits, not the machines, caused every interruption: Anthropic credit exhaustion, then a monthly spend
  cap; OpenAI credits twice; Zhipu balance + per-model rate tier; Moonshot balance twice; DeepSeek balance.
  Each stop wasted the in-flight cases (up to $20 each on Opus). Fund accounts before launching.
* Headless Chrome left behind by agents' Playwright self-tests can pin a dozen cores each; `reap_chrome.sh` runs
  from cron every 5 min and kills orphans / >30-min browsers.
* Refusals cluster on a few prompts (`hard_rewrite_032`, `v3_shooter_3d_001`, `v3_turn_based_4x_2d_027`): Fable 5 /
  5.1 and Opus 5 all refused `hard_rewrite_032` on the mobile set.
* Seed evolving and GLM-5.3 have the highest 120-min timeout rates (10–26 of 150 depending on the set); their
  timeout cases usually still contain a built `dist/`.
* Playground pages must be served from a **public** bucket via `storage.googleapis.com`; authenticated
  `storage.cloud.google.com` links render blank because module scripts fail behind the login redirect.
