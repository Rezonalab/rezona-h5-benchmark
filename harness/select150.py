#!/usr/bin/env python3
"""Pick a fixed N-case subset of a case file, stratified by (category × 2D/3D × level) proportionally to
the full set. Inside each stratum, cases the "lagging" models have already finished are preferred, so the
subset costs the least extra compute. This produced data/cases_150.json from data/benchmark_merged.json.

    python harness/select150.py --cases data/benchmark_merged.json --n 150 --out data/cases_150.json \
        --runs ~/bench/runs --prefer cc_glm_5_3,cc_deepseek_v4_flash,cc_kimi_k3
"""
import argparse, json, collections, glob
from pathlib import Path

def render(c): return "3D" if "_3d_" in c["task_id"] or any("render:3D" in l for l in c.get("label", [])) else "2D"

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--cases", required=True); ap.add_argument("--n", type=int, default=150); ap.add_argument("--out", required=True)
ap.add_argument("--runs", default=None, help="runs dir; successes of --prefer models are favoured inside each stratum")
ap.add_argument("--prefer", default="", help="comma list of model_keys")
a = ap.parse_args()
cases = json.load(open(a.cases)); done = collections.Counter()
for m in filter(None, a.prefer.split(",")):
    for p in glob.glob(f"{a.runs}/{m}/*/meta.json") if a.runs else []:
        try:
            if json.load(open(p)).get("status") == "success": done[Path(p).parent.name] += 1
        except Exception: pass
strata = collections.defaultdict(list)
for c in cases: strata[(c["category"], render(c), c["level"])].append(c)
alloc = {k: len(v) * a.n / len(cases) for k, v in strata.items()}
base = {k: int(x) for k, x in alloc.items()}
for k in sorted(alloc, key=lambda k: alloc[k] - base[k], reverse=True)[: a.n - sum(base.values())]: base[k] += 1
sel = []
for k, v in strata.items():
    sel += sorted(v, key=lambda c: (-done[c["task_id"]], c["task_id"]))[: base[k]]
sel.sort(key=lambda c: c["task_id"])
json.dump(sel, open(a.out, "w"), ensure_ascii=False, indent=1)
print(f"{'stratum':44} {'full':>5} {'sel':>4}")
for k in sorted(strata): print(f"{' / '.join(k):44} {len(strata[k]):5d} {base[k]:4d}")
print("levels:", dict(collections.Counter(c["level"] for c in sel)), "->", a.out)
