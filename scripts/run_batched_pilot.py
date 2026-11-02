"""Run a pilot stage in small task batches with a hard cumulative spending cap.

* Batches of --batch tasks (default 4): each batch is a separate run_pilot.py call named
  <name>-pNN, so a crash or container restart loses at most one batch (finished batches are skipped
  on rerun).
* Docker images are pruned after each batch: SWE-bench images are 2-4 GB each and the disk cannot
  hold a whole pool (a full disk makes later containers fail -> infrastructure errors).
* Cumulative cap: before every batch, total pilot spend (every results/pilot/**/*.json, invalid runs
  included, because that money was spent) plus the batch's worst case must stay <= --cap-usd.
* At the end the batch files are merged into results/pilot/<name>.json for analyze_g1.py.

Usage: python scripts/run_batched_pilot.py --name g1-b --model gemini-flash-lite \
         --skills a.json,b.json --tasks-from results/pool_validation/default/summary.json \
         --dataset-file rows.jsonl --cap-usd 20 --cost-limit 0.1
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

RESULTS = Path("results/pilot")
GB_PER_TASK = 6.0  # SWE-bench images are 3.8-7.6 GB (xarray); layers are partly shared
DISK_RESERVE_GB = 4.0


def pilot_spent_total(exclude_prefix: str | None = None) -> float:
    """Sum of spent_usd over every pilot result file (merged files excluded: no double count)."""
    total = 0.0
    for f in RESULTS.rglob("*.json"):
        d = json.loads(f.read_text())
        if d.get("merged_from"):
            continue
        if exclude_prefix and f.stem == exclude_prefix:
            continue
        total += float(d.get("spent_usd") or 0.0)
    return round(total, 4)


def task_list(path: str, skills: list[str]) -> list[str]:
    d = json.loads(Path(path).read_text())
    if "usable" in d:
        return list(d["usable"])
    return list(d["instances"])


def merge(name: str, parts: list[Path]) -> dict:
    out: dict = {
        "name": name,
        "merged_from": [p.stem for p in parts],
        "skills": {},
        "usage": {},
        "infra_failures": {},
        "spent_usd": 0.0,
        "instances": [],
    }
    for p in parts:
        d = json.loads(p.read_text())
        out["spent_usd"] += float(d.get("spent_usd") or 0.0)
        out["instances"] += d.get("instances", [])
        for k in ("model", "dataset", "theta", "alpha"):
            out.setdefault(k, d.get(k))
        for sk, v in d.get("skills", {}).items():
            out["skills"].setdefault(sk, {"pairs": []})["pairs"] += v["pairs"]
        for arm, v in (d.get("infra_failures") or {}).items():
            out["infra_failures"].setdefault(arm, {}).update(v)
        for arm, u in (d.get("usage") or {}).items():
            agg = out["usage"].setdefault(arm, {"runs": 0, "usd": 0.0, "solved": 0, "scored": 0})
            n = u.get("runs") or 0
            agg["runs"] += n
            agg["usd"] += (u.get("usd_per_run") or 0.0) * n
    for agg in out["usage"].values():
        agg["usd_per_run"] = agg["usd"] / agg["runs"] if agg["runs"] else None
    # solve rates recomputed from pairs (no-skill arm = loss_without)
    for v in out["skills"].values():
        z = [p["loss_with"] - p["loss_without"] for p in v["pairs"]]
        v["mean_Z"] = sum(z) / len(z) if z else None
        v["n"] = len(z)
        v["solve_rate_with"] = sum(p["loss_with"] == 0 for p in v["pairs"]) / len(z) if z else None
        v["solve_rate_without"] = (
            sum(p["loss_without"] == 0 for p in v["pairs"]) / len(z) if z else None
        )
    out["spent_usd"] = round(out["spent_usd"], 4)
    (RESULTS / f"{name}.json").write_text(json.dumps(out, indent=2) + "\n")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--skills", required=True)
    ap.add_argument("--tasks-from", required=True, help="pool summary (usable) or pool file")
    ap.add_argument("--dataset-file", required=True)
    ap.add_argument("--batch", type=int, default=4)
    ap.add_argument("--cap-usd", type=float, default=20.0, help="cumulative pilot spending cap")
    ap.add_argument("--cost-limit", type=float, default=0.1)
    ap.add_argument("--step-limit", type=int, default=60)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--max-batches", type=int, default=0)
    ap.add_argument("--model-seed", type=int, default=None, help="replicate seed (see run_pilot)")
    a = ap.parse_args()

    skills = [s for s in a.skills.split(",") if s]
    tasks = task_list(a.tasks_from, skills)
    arms = 1 + len(skills)
    # resume by TASK, not by part number: parts already written cover these instances
    parts = sorted(RESULTS.glob(f"{a.name}-p[0-9][0-9].json"))
    done = {i for p in parts for i in json.loads(p.read_text()).get("instances", [])}
    todo = [t for t in tasks if t not in done]
    print(f"{len(done)} tasks already done in {len(parts)} parts; {len(todo)} to go", flush=True)
    k = len(parts)
    n_batches = 0
    while todo:
        if a.max_batches and n_batches >= a.max_batches:
            break
        free_gb = shutil.disk_usage("/").free / 1e9
        size = max(1, min(a.batch, int((free_gb - DISK_RESERVE_GB) // GB_PER_TASK)))
        if free_gb < DISK_RESERVE_GB + GB_PER_TASK:
            print(f"[stop] only {free_gb:.1f} GB free", flush=True)
            break
        ids, todo = todo[:size], todo[size:]
        part = f"{a.name}-p{k:02d}"
        f = RESULTS / f"{part}.json"
        spent = pilot_spent_total()
        worst = arms * len(ids) * a.cost_limit
        if spent + worst > a.cap_usd:
            print(
                f"[stop] cap: spent {spent:.2f} + worst batch {worst:.2f} > cap {a.cap_usd:.2f}",
                flush=True,
            )
            break
        print(
            f"[run] {part}: {len(ids)} tasks ({free_gb:.0f} GB free), spent so far {spent:.2f} USD",
            flush=True,
        )
        cmd = [
            sys.executable,
            "scripts/run_pilot.py",
            "--name",
            part,
            "--model",
            a.model,
            "--skills",
            a.skills,
            "--instances",
            ",".join(ids),
            "--dataset-file",
            a.dataset_file,
            "--workers",
            str(a.workers),
            "--step-limit",
            str(a.step_limit),
            "--cost-limit",
            str(a.cost_limit),
            "--budget-usd",
            str(round(a.cap_usd - spent, 4)),
        ]
        if a.model_seed is not None:
            cmd += ["--model-seed", str(a.model_seed)]
        rc = subprocess.run(cmd, check=False).returncode
        subprocess.run(["docker", "image", "prune", "-af"], capture_output=True, check=False)
        subprocess.run(["docker", "container", "prune", "-f"], capture_output=True, check=False)
        if rc != 0 or not f.exists():
            print(f"[error] {part} exited {rc}; stopping (rerun to resume)", flush=True)
            break
        parts.append(f)
        k += 1
        n_batches += 1
    if parts:
        m = merge(a.name, parts)
        print(
            f"[merged] {a.name}: {len(m['instances'])} tasks, {m['spent_usd']:.2f} USD; "
            f"total pilot spend {pilot_spent_total():.2f} USD",
            flush=True,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
