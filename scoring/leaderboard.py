#!/usr/bin/env python3
"""Recompute the leaderboard and per-slice breakdowns from the released judge results.

Input : results/case_scores.csv (one row per model × case) and results/item_scores.csv.gz (one row per judged item).
Output: results/leaderboard.csv, results/leaderboard.md and results/breakdowns.json.

    python scoring/leaderboard.py                       # writes into results/
    python scoring/leaderboard.py --results my_results  # same layout, another directory

Metrics (per model, averaged over cases with equal weight):
  public_rate            share of the 6 public checklist items passed (the ranking metric)
  hidden_rate            share of the 4 hidden probes passed (reported separately, not part of the ranking)
  all10_rate             share of all 10 items passed
  runnable_rate          share of cases whose project built and passed the judge's runnability gate
  functional_public_rate public_rate over runnable cases only
A case whose gate failed (or that produced no artifact) scores 0 on every item.
"""
from __future__ import annotations
import argparse, csv, gzip, json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CAPABILITIES = {"C1": "Core rules", "C2": "AI & NPC behavior", "C3": "Numeric design & balance", "C4": "Interaction & input",
                "C5": "Levels & scenes", "C6": "Animation & rendering", "C7": "Feedback & game feel", "C8": "Onboarding & meta UI"}


def summarize(rows: list[dict]) -> dict:
    n = len(rows)
    runnable = [r for r in rows if r["gate_failed"] != "True"]
    mean = lambda xs: round(sum(xs) / len(xs), 4) if xs else None
    return {"n_cases": n,
            "public_rate": mean([float(r["public_rate"]) for r in rows]),
            "hidden_rate": mean([float(r["hidden_rate"]) for r in rows]),
            "all10_rate": mean([float(r["all10_rate"]) for r in rows]),
            "runnable_rate": round(len(runnable) / n, 4) if n else None,
            "functional_public_rate": mean([float(r["public_rate"]) for r in runnable])}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--results", default=str(ROOT / "results"))
    a = ap.parse_args()
    res = Path(a.results)
    cases = list(csv.DictReader(open(res / "case_scores.csv", encoding="utf-8")))
    names = {r["model"]: r["model_name"] for r in cases}
    by_model = defaultdict(list)
    for r in cases:
        by_model[r["model"]].append(r)

    board = sorted(({"model": m, "model_name": names[m], **summarize(rs)} for m, rs in by_model.items()),
                   key=lambda x: -x["public_rate"])
    for i, b in enumerate(board, 1):
        b["rank"] = i
    cols = ["rank", "model", "model_name", "n_cases", "public_rate", "hidden_rate", "all10_rate", "runnable_rate", "functional_public_rate"]
    with open(res / "leaderboard.csv", "w", newline="") as f:
        w = csv.DictWriter(f, cols); w.writeheader(); w.writerows({k: b[k] for k in cols} for b in board)
    pct = lambda v: f"{v * 100:.1f}" if v is not None else "–"
    md = ["| # | Model | Cases | Public pass % | Hidden pass % | All-10 % | Runnable % |", "|---|---|---|---|---|---|---|"]
    md += [f"| {b['rank']} | {b['model_name']} | {b['n_cases']} | **{pct(b['public_rate'])}** | {pct(b['hidden_rate'])} | "
           f"{pct(b['all10_rate'])} | {pct(b['runnable_rate'])} |" for b in board]
    (res / "leaderboard.md").write_text("\n".join(md) + "\n")

    breakdowns = {}
    for dim in ["track", "platform", "render", "level", "category", "incentive", "judge_batch"]:
        out = {}
        for m, rs in by_model.items():
            groups = defaultdict(list)
            for r in rs:
                groups[r[dim]].append(r)
            out[m] = {g: summarize(v) for g, v in sorted(groups.items())}
        breakdowns[f"by_{dim}"] = out

    cap = defaultdict(lambda: [0, 0])
    with gzip.open(res / "item_scores.csv.gz", "rt", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            for c in r["capabilities"].split("|"):
                k = cap[(r["model"], c, r["kind"])]
                k[0] += int(r["passed"]); k[1] += 1
    breakdowns["capability_by_model"] = {
        m: {f"{c}|{kind}": {"name": CAPABILITIES[c], "n": t, "rate": round(p / t, 4)}
            for (mm, c, kind), (p, t) in sorted(cap.items()) if mm == m}
        for m in sorted(by_model)}
    (res / "breakdowns.json").write_text(json.dumps({"leaderboard": board, **breakdowns}, ensure_ascii=False, indent=1))
    print("\n".join(md))


if __name__ == "__main__":
    main()
