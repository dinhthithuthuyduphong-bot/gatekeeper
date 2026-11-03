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
import time
from pathlib import Path

RESULTS = Path("results/pilot")
GB_PER_TASK = 6.0  # SWE-bench images are 3.8-7.6 GB (xarray); layers are partly shared
DISK_RESERVE_GB = 4.0
EX_TEMPFAIL = 75  # run_pilot.py: task images could not be pulled, nothing was run
MIRROR = "mirror.gcr.io"  # same as run_pilot.MIRROR
EX_NOSPACE = 76  # run_pilot.py: task images do not fit on the disk, nothing was run


def pilot_spent_total(exclude_prefix: str | None = None) -> float:
    """Sum of spent_usd over every pilot result file (merged files excluded: no double count)."""
    total = 0.0
    for f in RESULTS.rglob("*.json"):
        d = json.loads(f.read_text())
        if d.get("merged_from") or "instances" not in d:  # merged files / analysis outputs
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


def session_start_epoch() -> float:
    """Start time of this process's session leader (the background job that runs a chain of
    stages), so a later stage in the same job sees the time already used. Falls back to now."""
    import os

    try:
        ticks = os.sysconf("SC_CLK_TCK")
        stat = Path(f"/proc/{os.getsid(0)}/stat").read_text()
        start = int(stat.rsplit(")", 1)[1].split()[19]) / ticks  # field 22: starttime
        uptime = float(Path("/proc/uptime").read_text().split()[0])
        return time.time() - (uptime - start)
    except (OSError, ValueError, IndexError):
        return time.time()


def done_tasks(parts: list[Path]) -> set[str]:
    """Tasks finished in earlier parts; a task with an infrastructure failure in ANY arm is not
    done (it is re-run, and merge() keeps the latest part's result for it)."""
    done: set[str] = set()
    for p in parts:
        d = json.loads(p.read_text())
        failed = {i for v in (d.get("infra_failures") or {}).values() for i in v}
        done |= set(d.get("instances", [])) - failed
        done -= failed
    return done


def merge(name: str, parts: list[Path]) -> dict:
    out: dict = {
        "name": name,
        "merged_from": [p.stem for p in parts],
        "skills": {},
        "usage": {},
        "infra_failures": {},
        "exit_status": {},
        "patch_apply_failed": {},
        "harness_test_timeout": {},
        "spent_usd": 0.0,
        "instances": [],
    }
    for p in parts:
        d = json.loads(p.read_text())
        out["spent_usd"] += float(d.get("spent_usd") or 0.0)
        out["instances"] += [i for i in d.get("instances", []) if i not in out["instances"]]
        for k in ("model", "dataset"):
            out.setdefault(k, d.get(k))
        rerun = set(d.get("instances", []))  # a task re-run in a later part replaces old data
        for sk in out["skills"].values():
            sk["pairs"] = [q for q in sk["pairs"] if q["instance_id"] not in rerun]
        for v in out["infra_failures"].values():
            for i in rerun & set(v):
                del v[i]
        for sk, v in d.get("skills", {}).items():
            out["skills"].setdefault(sk, {"pairs": []})["pairs"] += v["pairs"]
        for arm, v in (d.get("infra_failures") or {}).items():
            out["infra_failures"].setdefault(arm, {}).update(v)
        for arm, v in (d.get("exit_status") or {}).items():  # a re-run replaces older statuses
            out["exit_status"].setdefault(arm, {}).update(v)
        for key in ("patch_apply_failed", "harness_test_timeout"):  # agent outcomes (A37, A56)
            for arm in out[key]:  # a re-run task's old outcome goes, in EVERY arm
                out[key][arm] = [i for i in out[key][arm] if i not in rerun]
            for arm, ids in (d.get(key) or {}).items():
                out[key].setdefault(arm, []).extend(i for i in ids if i not in out[key][arm])
        for arm, u in (d.get("usage") or {}).items():
            agg = out["usage"].setdefault(arm, {"runs": 0, "usd": 0.0, "solved": 0, "scored": 0})
            n = u.get("runs") or 0
            agg["runs"] += n
            agg["usd"] += (u.get("usd_per_run") or 0.0) * n
            agg["solved"] += int(u.get("solved") or 0)
            agg["scored"] += int(u.get("scored") or 0)
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


def image_names(ids: list[str], dataset_file: str) -> set[str]:
    """docker.io names of the task images of `ids` (same naming as run_pilot.image_name)."""
    sys.path.insert(0, str(Path(__file__).parent))
    from run_pilot import image_name  # noqa: PLC0415

    want = set(ids)
    out = set()
    for line in Path(dataset_file).read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            if r["instance_id"] in want:
                out.add(image_name(r).removesuffix(":latest") + ":latest")
    return out


def plan_images(local: set[str], needed: set[str], mirror: str) -> tuple[set[str], int]:
    """Keep-images mode (audit A54): which local task images to delete before a batch (those the
    batch does not need, including their mirror alias tags) and how many needed ones are missing
    (only those need new disk). Pure function: tested in tests/test_batched_pilot.py."""
    alias = {f"{mirror}/{n.removeprefix('docker.io/')}" for n in needed}
    canon = {n.removeprefix("docker.io/") for n in needed}
    keep = needed | alias | canon
    remove = {i for i in local if i not in keep and ("sweb.eval." in i)}
    missing = sum(1 for n in needed if n not in local and n.removeprefix("docker.io/") not in local)
    return remove, missing


def local_images() -> set[str]:
    out = subprocess.run(
        ["docker", "images", "--format", "{{.Repository}}:{{.Tag}}"], capture_output=True, text=True
    ).stdout
    return {x for x in out.split() if x and "<none>" not in x}


def arms_per_task(ids: list[str], skill_paths: list[str], task_sets: str | None) -> dict[str, int]:
    """Agent runs per task in one batch: the no-skill arm plus every skill whose task set holds the
    task (run_pilot.py runs a skill arm only on its set, intersected with I(x)). An upper bound of
    the real count, so a worst case built on it still never exceeds the cap (audit A65). Without a
    task-set file every skill arm may run on every task."""
    if not task_sets:
        return {i: 1 + len(skill_paths) for i in ids}
    from gatekeeper.skill import Skill  # noqa: PLC0415

    sets = json.loads(Path(task_sets).read_text())
    sids = [Skill.load(p).id for p in skill_paths]
    return {i: 1 + sum(1 for s in sids if s not in sets or i in sets[s]) for i in ids}


def plan_batch(
    todo: list[str], size: int, arms_of: dict[str, int], room: float, cost_limit: float
) -> tuple[list[str], float]:
    """Longest PREFIX of todo (at most size tasks; order kept, nothing skipped) whose worst case
    sum(arms x cost_limit) fits in room. At least one task is returned; the caller stops if even
    that one does not fit."""
    take: list[str] = []
    worst = 0.0
    for t in todo[:size]:
        w = arms_of[t] * cost_limit
        if take and worst + w > room:
            break
        take.append(t)
        worst += w
        if worst > room:
            break
    return take, worst


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
    ap.add_argument("--task-sets", default="", help="per-skill task sets (see run_pilot)")
    ap.add_argument("--arm-parallel", type=int, default=1, help="see run_pilot")
    ap.add_argument(
        "--keep-images",
        action="store_true",
        help="do not prune after a batch; before a batch delete only images it does not need "
        "(seeds interleaved on the same tasks reuse them; audit A54). REQUIRES EXCLUSIVE USE OF "
        "DOCKER: it deletes every task image the batch does not need, also another job's",
    )
    ap.add_argument("--harness-python", default="", help="see run_pilot (SWE-bench-Live)")
    ap.add_argument("--harness-namespace", default="", help="see run_pilot (SWE-bench-Live)")
    ap.add_argument("--pull-retries", type=int, default=6, help="waits on a registry limit")
    ap.add_argument("--pull-wait-min", type=float, default=30.0)
    ap.add_argument(
        "--stop-after-min",
        type=float,
        default=0.0,
        help="do not start a batch (or a registry wait) after this many minutes; 0 = no limit. "
        "Lets a time-limited host stop cleanly between batches instead of killing one mid-run",
    )
    ap.add_argument("--batch-min", type=float, default=25.0, help="expected minutes per batch")
    a = ap.parse_args()

    skills = [s for s in a.skills.split(",") if s]
    tasks = task_list(a.tasks_from, skills)
    arms_of = arms_per_task(tasks, skills, a.task_sets)
    # resume by TASK, not by part number: parts already written cover these instances
    parts = sorted(RESULTS.glob(f"{a.name}-p[0-9][0-9].json"))
    done = done_tasks(parts)
    todo = [t for t in tasks if t not in done]
    print(f"{len(done)} tasks already done in {len(parts)} parts; {len(todo)} to go", flush=True)
    k = len(parts)
    n_batches = 0
    pull_waits = 0
    max_size = a.batch
    started = session_start_epoch()  # the whole background job's clock, not this process's

    def minutes_left() -> float:
        return a.stop_after_min - (time.time() - started) / 60 if a.stop_after_min else 1e9

    while todo:
        if a.max_batches and n_batches >= a.max_batches:
            break
        if minutes_left() < a.batch_min:
            print(
                f"[stop] time: {minutes_left():.0f} min left < one batch; rerun to resume",
                flush=True,
            )
            break
        free_gb = shutil.disk_usage("/").free / 1e9
        if a.keep_images:  # images of the next tasks may already be local (previous seed)
            cand = todo[: min(a.batch, max_size)]
            remove, missing = plan_images(local_images(), image_names(cand, a.dataset_file), MIRROR)
            if remove:
                subprocess.run(["docker", "rmi", "-f", *sorted(remove)], capture_output=True)
                subprocess.run(["docker", "image", "prune", "-f"], capture_output=True)
            free_gb = shutil.disk_usage("/").free / 1e9
            fits = int((free_gb - DISK_RESERVE_GB) // GB_PER_TASK)
            size = len(cand) if missing <= fits else max(1, len(cand) - (missing - fits))
            if missing and fits < 1:
                print(f"[stop] only {free_gb:.1f} GB free", flush=True)
                break
        else:
            size = max(1, min(a.batch, max_size, int((free_gb - DISK_RESERVE_GB) // GB_PER_TASK)))
            if free_gb < DISK_RESERVE_GB + GB_PER_TASK:
                print(f"[stop] only {free_gb:.1f} GB free", flush=True)
                break
        spent = pilot_spent_total()
        # shrink the batch near the cap instead of stopping while a smaller batch still fits; the
        # worst case counts only the arms that really run on each task (A65)
        ids, worst = plan_batch(todo, size, arms_of, a.cap_usd - spent, a.cost_limit)
        todo = todo[len(ids) :]
        part = f"{a.name}-p{k:02d}"
        f = RESULTS / f"{part}.json"
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
        if a.task_sets:
            cmd += ["--task-sets", a.task_sets]
        if a.arm_parallel > 1:
            cmd += ["--arm-parallel", str(a.arm_parallel)]
        if a.harness_python:
            cmd += ["--harness-python", a.harness_python]
        if a.harness_namespace:
            cmd += ["--harness-namespace", a.harness_namespace]
        rc = subprocess.run(cmd, check=False).returncode
        if rc == EX_NOSPACE and len(ids) > 1:  # large images (e.g. matplotlib ~10 GB): halve
            subprocess.run(["docker", "image", "prune", "-af"], capture_output=True, check=False)
            half = len(ids) // 2
            print(f"[shrink] images do not fit: retrying with {half} tasks", flush=True)
            todo = ids + todo
            max_size = half
            continue
        if rc == EX_TEMPFAIL and minutes_left() < a.pull_wait_min + a.batch_min:
            print("[stop] registry limit and not enough time to wait; rerun to resume", flush=True)
            break
        if rc == EX_TEMPFAIL and pull_waits < a.pull_retries:  # registry limit: nothing ran
            pull_waits += 1
            print(
                f"[wait] images not pullable; retry {pull_waits} in {a.pull_wait_min} min",
                flush=True,
            )
            time.sleep(a.pull_wait_min * 60)
            todo = ids + todo
            continue
        if not a.keep_images:  # keep-images: unneeded images are removed before the next batch
            subprocess.run(["docker", "image", "prune", "-af"], capture_output=True, check=False)
        subprocess.run(["docker", "container", "prune", "-f"], capture_output=True, check=False)
        if rc != 0 or not f.exists():
            print(f"[error] {part} exited {rc}; stopping (rerun to resume)", flush=True)
            break
        parts.append(f)
        pull_waits = 0  # the retry allowance is per batch, not per stage
        max_size = a.batch
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
