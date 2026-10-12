#!/usr/bin/env python3
"""Batch LLM-judge evaluation over harness outputs.

Input : a runs directory laid out as <runs>/<model_key>/<task_id>/project/ (what run_bench.py
        writes, or an unzipped result zip), plus the case file that produced it.
Judge : llm-eval/{2D,3D}_eval.py (web) or {2D,3D}_mobile_eval.py (--mobile). 2D vs 3D is
        chosen per case from task_id ("_3d_") or a "render:3D" label.
Output: eval_results/<model_key>/<task_id>.json (judge verdict + meta) and
        eval_results/<model_key>.csv (one row per case: gate, items passed/total, aux dims).

    python eval/run_eval.py --runs ~/bench/runs --cases data/cases_150.json --models cc_opus_5,codex_gpt_5_5
    python eval/run_eval.py --runs ~/bench_mobile/runs --cases data/cases_150_mobile_en.json --mobile --concurrency 4

Judge credentials: ANTHROPIC_API_KEY in .env or the shell (see utils/llm_invoke.py). Verdicts that
already exist are skipped unless --force. A case with no project/ directory is recorded as
status=no_project and scored 0 without calling the judge.
"""
from __future__ import annotations
import argparse, csv, importlib.util, json, os, re, sys, threading, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
JUDGE_DIR = ROOT / "llm-eval"

def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, JUDGE_DIR / f"{name}.py")
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod

def is_3d(case: dict) -> bool:
    return "_3d_" in case["task_id"] or any("render:3D" in l for l in case.get("label", []))

def pick_judge(case: dict, mobile: bool):
    if mobile:
        return (_load("3D_mobile_eval").Eval3DMobileScenario if is_3d(case) else _load("2D_mobile_eval").Eval2DMobileScenario)()
    return (_load("3D_eval").Eval3DScenario if is_3d(case) else _load("2D_eval").Eval2DScenario)()

def parse_total(v: dict) -> tuple[int, int]:
    m = re.match(r"\s*(\d+)\s*/\s*(\d+)", str(v.get("total_score", "")))
    return (int(m.group(1)), int(m.group(2))) if m else (0, 0)

def aux(v: dict, key_sub: str) -> int | None:
    for k, val in v.items():
        if key_sub in k:
            m = re.match(r"\s*(\d+)", str(val)); return int(m.group(1)) if m else None
    return None

_lock = threading.Lock()
def log(msg): 
    with _lock: print(time.strftime("[%m-%d %H:%M:%S] ") + msg, flush=True)

def eval_one(model: str, case: dict, runs: Path, out_dir: Path, mobile: bool, force: bool) -> dict:
    tid = case["task_id"]; proj = runs / model / tid / "project"; out = out_dir / model / f"{tid}.json"
    if out.exists() and not force:
        return json.loads(out.read_text())
    meta_p = runs / model / tid / "meta.json"
    harness_status = json.loads(meta_p.read_text()).get("status") if meta_p.exists() else None
    rec = {"model_key": model, "task_id": tid, "harness_status": harness_status, "judge": "mobile" if mobile else "web",
           "render": "3D" if is_3d(case) else "2D", "checklist_n": len(case.get("checklist", []))}
    src_files = [p for p in proj.rglob("*") if p.is_file() and "node_modules" not in p.parts and "dist" not in p.parts] if proj.exists() else []
    if not src_files:
        rec.update(status="no_project", passed=0, total=rec["checklist_n"], verdict=None)
    else:
        try:
            base_info = {"prompt": case["prompt"], "checklist": case["checklist"], "attachment": case.get("attachment", [])}
            v = pick_judge(case, mobile).eval(base_info, str(proj))
            p, t = parse_total(v)
            rec.update(status="judged", passed=p, total=t, gate_failed=(p == 0 and any("代码无法运行" in str(x) for x in v.values())),
                       aux_levels=aux(v, "关卡"), aux_juice=aux(v, "Juice"), verdict=v)
        except Exception as e:  # noqa: BLE001
            rec.update(status="judge_error", passed=0, total=rec["checklist_n"], error=repr(e)[:500], verdict=None)
    out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(rec, ensure_ascii=False, indent=1))
    log(f"{model} {tid} {rec['status']} {rec.get('passed')}/{rec.get('total')}")
    return rec

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--runs", required=True, help="dir containing <model_key>/<task_id>/project")
    ap.add_argument("--cases", required=True)
    ap.add_argument("--models", default="all", help="comma list of model_key dirs under --runs")
    ap.add_argument("--mobile", action="store_true", help="use the mobile judges")
    ap.add_argument("--out", default=str(ROOT / "eval_results"))
    ap.add_argument("--concurrency", type=int, default=3)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    runs = Path(a.runs).expanduser(); out_dir = Path(a.out)
    cases = json.loads(Path(a.cases).read_text()); cases = cases if isinstance(cases, list) else cases["cases"]
    if a.limit: cases = cases[: a.limit]
    models = sorted(p.name for p in runs.iterdir() if p.is_dir()) if a.models == "all" else a.models.split(",")
    jobs = [(m, c) for m in models for c in cases]
    log(f"{len(models)} models × {len(cases)} cases = {len(jobs)} judgements, concurrency {a.concurrency}")
    results = []
    with ThreadPoolExecutor(max_workers=a.concurrency) as ex:
        for f in as_completed([ex.submit(eval_one, m, c, runs, out_dir, a.mobile, a.force) for m, c in jobs]):
            results.append(f.result())
    for m in models:
        rows = sorted((r for r in results if r["model_key"] == m), key=lambda r: r["task_id"])
        with open(out_dir / f"{m}.csv", "w", newline="") as fh:
            w = csv.writer(fh); w.writerow(["task_id", "render", "harness_status", "status", "passed", "total", "pass_ratio", "gate_failed", "aux_levels", "aux_juice"])
            for r in rows:
                w.writerow([r["task_id"], r["render"], r["harness_status"], r["status"], r.get("passed"), r.get("total"),
                            round(r["passed"] / r["total"], 4) if r.get("total") else 0, r.get("gate_failed"), r.get("aux_levels"), r.get("aux_juice")])
        judged = [r for r in rows if r.get("total")]
        mean = sum(r["passed"] / r["total"] for r in judged) / len(judged) if judged else 0
        log(f"SUMMARY {m}: {len(rows)} cases, judged {sum(r['status']=='judged' for r in rows)}, mean pass ratio {mean:.3f} -> {out_dir / (m + '.csv')}")

if __name__ == "__main__":
    main()
