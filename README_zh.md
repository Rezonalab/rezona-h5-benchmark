# OCTAVE

**A Capability-Resolved Benchmark for Complete HTML5 Game Generation**

[English](README.md) · [数据集说明](data/README.md) · [结果](results/README.md) · [复现](docs/reproduce.md)

**编程 agent 能否根据一份设计说明，做出一个完整可玩的游戏？** OCTAVE 包含 180 道 HTML5 游戏生成题。每道题把一份多系统耦合的游戏设计交给 Claude Code、Codex 等 agent，再用 10 条可证伪的断言检查生成的项目：6 条公开检查项，加 4 条题面只隐含、没有明说的隐藏探针。全集共 1,800 条断言。

- **180 道题，分三个赛道**：
  - `main`：桌面 Web 75 道 + 移动端 75 道，由玩家的游戏需求改写扩写而来
  - `expert`：游戏设计师出的 10 道
  - `repro`：复刻现有商业游戏的 20 道
- **覆盖范围**：2D / 3D；6 个游戏大类；8 个能力维度，从核心规则、AI 行为到打击感与引导。
- **判分方式**：LLM 判官读取生成的源码，先过可运行门槛，再逐条判定通过或不通过，并给出理由。
- **公开内容**：题目（中文原文 + 英文译文）、生成 harness、判分 rubric、13 个模型的逐条判分结果，以及能复算全部排行榜数字的脚本。

## 排行榜（v1）

指标是 180 题上的公开检查项通过率。判官为 `gpt-6-astra`，每题时限 120 分钟。

| # | 模型 | Agent | 题数 | 公开通过率 % | 隐藏通过率 % | 可运行率 % |
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

\* Kimi-K3 缺移动端 75 题的结果。

看这些数字时请注意：

- **判官偏严**：它给出的绝对通过率比人工试玩低约 30 个百分点，但模型排名和人工高度一致（Spearman ρ = 0.95，见 [`docs/human_eval.md`](docs/human_eval.md)）。
- **自评偏好风险**：判官和第一名模型同源。不过人工评测同样把 GPT-6 astra 排在第一。
- 按赛道、平台、2D/3D、难度、类别、能力维度的切片结果和成本，见 [`results/`](results/README.md)。

## 快速开始

```bash
git clone https://github.com/Rezonalab/octave-bench.git && cd octave-bench
pip install -r requirements.txt

# 1. 查看题目
python3 -c "import json; c=[json.loads(l) for l in open('data/octave_180_zh.jsonl')]; print(len(c), c[0]['prompt'][:200])"

# 2. 用公开的判分结果复算排行榜（不需要 API key）
python3 scoring/leaderboard.py

# 3. 用一个 agent 生成几道题，再判分（需要 API key，见 docs/reproduce.md）
python3 harness/run_bench.py run --models cc_opus_5 --cases data/octave_180_zh.jsonl --limit 3
python3 eval/run_eval.py --runs $HOME/bench/runs --cases data/octave_180_zh.jsonl --models cc_opus_5 --limit 3
```

目录结构、题目字段和能力编号（C1 核心规则 / C2 AI 与 NPC 行为 / C3 数值设计与平衡 / C4 交互与输入 / C5 关卡与场景 / C6 动画与渲染 / C7 反馈与打击感 / C8 引导与元 UI）的完整说明见 [README.md](README.md) 和 [数据集说明](data/README.md)。

## 许可证

代码（`data/` 以外的所有内容）采用 [MIT](LICENSE)，`data/` 中的题目采用 [CC BY 4.0](data/LICENSE)。repro 题中提到的游戏名称和商标归各自权利人所有，详见 [NOTICE.md](NOTICE.md)。

## 引用

见 [`CITATION.cff`](CITATION.cff)。论文发表后会补充论文的引用信息。
