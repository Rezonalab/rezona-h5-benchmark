# Rezona H5 Benchmark

[中文](README_zh.md) · [Dataset card](data/README.md) · [Results](results/README.md) · [Reproduce](docs/reproduce.md)

**Can a coding agent build a complete, playable game from a design brief?** The Rezona H5 Benchmark has 180 HTML5
game-generation tasks. Each task gives an agent such as Claude Code or Codex a multi-system game design and checks
the built project against 10 falsifiable assertions: 6 public checklist items and 4 hidden probes the brief only
implies. That is 1,800 assertions in total.

* **180 tasks** in three tracks:
  * `main`: 75 desktop-web + 75 mobile tasks, rewritten from player game requests
  * `expert`: 10 tasks written by game designers
  * `repro`: 20 tasks that re-create existing commercial games
* **Coverage**: 2D and 3D; six game categories; eight capability dimensions, from core rules and AI behaviour to
  game feel and onboarding.
* **Scoring**: an LLM judge reads the generated source. A runnability gate comes first, then each item is scored
  pass/fail with a reason.
* **Released**: the tasks (Chinese original + English translation), the generation harness, the judge rubrics,
  per-item judge results for 13 models, and the scripts that rebuild every leaderboard number.

## Leaderboard (v1)

Public-checklist pass rate on 180 cases. Judge: `gpt-6-astra`. Agents ran with a 120-minute limit per case.

| # | Model | Agent | Cases | Public pass % | Hidden pass % | Runnable % |
|---|---|---|---|---|---|---|
| 1 | GPT-6 astra (high) | Codex | 180 | **57.1** | 49.3 | 86.7 |
| 2 | Fable 5.1 (xhigh) | Claude Code | 180 | **44.7** | 40.7 | 82.2 |
| 3 | Fable 5 (xhigh) | Claude Code | 180 | **39.0** | 39.3 | 78.9 |
| 4 | Opus 5 (xhigh) | Claude Code | 180 | **37.2** | 40.4 | 83.9 |
| 5 | GPT-5.6-sol (high) | Codex | 180 | **33.4** | 32.6 | 83.3 |
| 6 | Kimi-K3 | Claude Code | 105* | **31.9** | 28.6 | 78.1 |
| 7 | GLM-5.3 | Claude Code | 180 | **31.1** | 34.0 | 78.3 |
| 8 | GPT-5.5 (high) | Codex | 180 | **26.9** | 28.3 | 84.4 |
| 9 | DeepSeek 4.1 Flash | Claude Code | 180 | **25.9** | 28.9 | 79.4 |
| 10 | GLM-5.2 | Claude Code | 180 | **24.3** | 28.1 | 73.3 |
| 11 | DeepSeek V4-Flash | Claude Code | 180 | **23.5** | 28.5 | 73.3 |
| 12 | DeepSeek V4-Pro (high) | Codex | 180 | **22.2** | 27.5 | 77.2 |
| 13 | Seed evolving | Claude Code | 180 | **21.0** | 24.9 | 66.7 |

\* Kimi-K3 has no Mobile-75 results.

Notes on reading these numbers:

* **Strict judge.** Its absolute pass rates are about 30 points below human play-testers, but the model ranking
  agrees closely with theirs (Spearman ρ = 0.95, see [`docs/human_eval.md`](docs/human_eval.md)).
* **Self-preference risk.** The judge and the top model share a family. Human raters also rank GPT-6 astra first.
* Per-slice results (track, platform, 2D/3D, difficulty, category, capability) and costs are in
  [`results/`](results/README.md).

## Quick start

```bash
git clone https://github.com/Rezonalab/rezona-h5-benchmark.git && cd rezona-h5-benchmark
pip install -r requirements.txt

# 1. Look at the tasks
python3 -c "import json; c=[json.loads(l) for l in open('data/h5bench_180_en.jsonl')]; print(len(c), c[0]['prompt'][:300])"

# 2. Rebuild the leaderboard from the released judge results (no API key needed)
python3 scoring/leaderboard.py

# 3. Generate games for a few tasks with one agent, then judge them (needs API keys; see docs/reproduce.md)
python3 harness/run_bench.py run --models cc_opus_5 --cases data/h5bench_180_zh.jsonl --limit 3
python3 eval/run_eval.py --runs $HOME/bench/runs --cases data/h5bench_180_zh.jsonl --models cc_opus_5 --limit 3
```

## Repository layout

```
data/         h5bench_180_{zh,en}.jsonl — the 180 tasks (CC BY 4.0) · README.md dataset card
results/      leaderboard, per-case and per-item judge results, generation cost/time (v1, judge gpt-6-astra)
harness/      run_bench.py — runs Claude Code / Codex over the tasks, one isolated process per (model, task) · scripts/
llm-eval/     judge rubrics: {2D,3D}_eval.py (web), {2D,3D}_mobile_eval.py (mobile)
eval/         run_eval.py — batch judge over a runs directory
scoring/      leaderboard.py (rebuild results/) · aggregate.py (score your own runs: success, cost, pass rate)
playground/   build_play.py — static "click to play" index over generated games
utils/        judge plumbing: template filling, verdict validation, source collection, LLM invocation
configs/      model registry and prices, prompt templates, LiteLLM proxy config, keys.env.example
docs/         reproduce.md · human_eval.md · PRICING.md
```

## Task format

One JSON object per line. Abridged:

```json
{
  "task_id": "hard_action_rpg_3d_017",
  "track": "main", "platform": "web", "render": "3d", "category": "RPG", "level": "extreme",
  "prompt": "[Game] AI-Directed Dynamic Dungeon: an invisible director adjusts pressure ...",
  "checklist": ["Branch from the same seed ... the efficient branch actually encounters more enemies ...", "..."],
  "hidden_checklist": ["From the same initial combat state, compare leaving the healer alive with killing it ...", "..."],
  "checklist_capabilities": [["C2", "C5"], ...],
  "agent_ability": ["C1", "C2", "C3", "C5"]
}
```

See the [dataset card](data/README.md) for every field, the capability codes (C1–C8), and how difficulty levels
were assigned.

## Secrets

No credential is stored in this repository. `configs/keys.env` and `.env` are git-ignored, and the committed
`*.example` files hold placeholders only. `run_bench.py` passes each vendor key to its agent process through the
environment and never writes it to disk or into transcripts.

## License

Code (everything outside `data/`) is released under the [MIT License](LICENSE). The benchmark tasks in `data/` are
released under [CC BY 4.0](data/LICENSE). Game titles referenced by `repro` tasks are trademarks of their respective
owners; see [NOTICE.md](NOTICE.md) for third-party notices and the attribution format.

## Citation

See [`CITATION.cff`](CITATION.cff) (GitHub shows a "Cite this repository" button). A paper citation will be added
on publication.
