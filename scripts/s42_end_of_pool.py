"""Section 42 (docs/preregistration_main.md; specified before this script ran; post hoc; 0 USD).

The end-of-pool test of docs/method_end_of_pool.md on the 12 decisions of section 36a, from the
raw paired data, with the run structure of every comparison (B0) and descriptive independence
diagnostics (B6).

  python scripts/s42_end_of_pool.py --trial <worktree of origin/trial> --rows <rows dir> \
      --out results/s42_end_of_pool.json
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

import numpy as np
from scipy.stats import kendalltau

sys.path.insert(0, str(Path(__file__).parent))
import s25_ab as ab  # noqa: E402

from gatekeeper.eprocess import BettingEProcess, end_of_pool_log_e  # noqa: E402

LAM, THETA, ALPHA, C = 0.5, 0.0, 0.025, 0.5  # registered (section 25); lam = c / (1 + theta)
K_FAMILY = 12  # section 36a
PERMS, SEED = 10000, 4201
R = Path("results")


def load(p: Path) -> dict:
    return json.loads(p.read_text())


def published(stem: str) -> dict:
    """First publication of results/<stem>.json on pilot-snapshots: time and run id.

    s30_*_run1.json are the files first published as s30_skill.json / s30_none.json (run
    42808049387), renamed when the re-run part was merged; a later dry run (43134720345)
    re-published them under the new name, so the original name is the one that dates them."""
    stem = stem.removesuffix("_run1")
    out = subprocess.run(
        [
            "git",
            "log",
            "--reverse",
            "--format=%aI|%s",
            "origin/pilot-snapshots",
            "--",
            f"results/{stem}.json",
        ],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()
    if not out:
        return {"time": None, "run": None}
    t, msg = out[0].split("|", 1)
    m = re.search(r"run (\d+)", msg)
    return {"time": t, "run": m.group(1) if m else None}


def sources(path: Path) -> dict[str, str]:
    """task -> stem of the file its run came from (merged files: the last component holding it)."""
    d = load(path)
    comps = [c.split()[0] for c in d.get("merged_from") or [path.name]]  # "file.json (note)"
    base = path.parent / path.name.replace("_all.json", ".json")
    if not d.get("merged_from") and path.name.endswith("_all.json") and base.exists():
        comps = [base.name]  # same runs, infrastructure errors re-scored only (s27pyg_none_all)
    out: dict[str, str] = {}
    for c in comps:
        for r in load(path.parent / c)["runs"]:
            out[r["instance_id"]] = c.removesuffix(".json")
    return out


def z_pairs(skill: Path, other: Path) -> tuple[list[str], dict[str, float], list[dict]]:
    pairs = ab.paired(load(skill), load(other))
    z = {i: float(not ab.passed(a, "S")) - float(not ab.passed(b, "S")) for i, a, b in pairs}
    return [i for i, _, _ in pairs], z, [x for _, a, b in pairs for x in (a, b)]


def sequential_first(seq: list[float]) -> int | None:
    ep = BettingEProcess(theta=THETA, alpha=ALPHA, c=C)
    for k, x in enumerate(seq, 1):
        ep.update(x)
        if ep.crossed:
            return k
    return None


def structure(files: list[Path], tasks: list[str]) -> dict:
    """B0, per task: did every arm of this task come from the same run (job)?"""
    pub: dict[str, dict] = {}
    per_task: dict[str, list[dict]] = {i: [] for i in tasks}
    arms = {}
    for f in files:
        src = sources(f)
        for stem in set(src.values()):
            pub.setdefault(stem, published(stem))
        arms[f.stem] = {s: {"tasks": n, **pub[s]} for s, n in Counter(src.values()).items()}
        for i in tasks:
            if i in src:  # the 70 tasks of P35 come from two jobs: each file holds one part
                per_task[i].append(pub[src[i]])
    same_job = sum(len({p["run"] for p in v}) == 1 for v in per_task.values())
    same_day = sum(len({(p["time"] or "")[:10] for p in v}) == 1 for v in per_task.values())
    n = len(tasks)
    if same_job == n:
        verdict = "every task: all arms in the same job"
    elif same_day == n:
        verdict = f"all arms the same day; same job for {same_job} of {n} tasks"
    else:
        verdict = f"same job for {same_job}, same day for {same_day}, of {n} tasks"
    return {
        "arms": arms,
        "tasks_same_job": same_job,
        "tasks_same_day": same_day,
        "verdict": verdict,
    }


def diagnostics(seq: list[float], runs: list[dict], seed: int) -> dict:
    crashed = [r for r in runs if r.get("crashed")]
    rate = [r for r in crashed if "RateLimitError" in str(r.get("crash_head"))]
    x = np.arange(len(seq))
    y = np.asarray(seq, dtype=float)
    if np.all(y == y[0]):
        return {"crashed": len(crashed), "rate_limit_crashes": len(rate), "kendall_tau": None}
    tau = kendalltau(x, y).statistic
    rng = np.random.default_rng(seed)
    hits = sum(abs(kendalltau(x, rng.permutation(y)).statistic) >= abs(tau) for _ in range(PERMS))
    return {
        "crashed": len(crashed),
        "rate_limit_crashes": len(rate),
        "kendall_tau": float(tau),
        "kendall_p_two_sided_perm": (hits + 1) / (PERMS + 1),
    }


def decision(
    name: str, seq: list[float], files: list[Path], runs: list[dict], k: int, tasks: list[str]
) -> dict:
    log_e = end_of_pool_log_e(seq, lam=LAM, theta=THETA)
    return {
        "n": len(seq),
        "values": {str(v): c for v, c in sorted(Counter(seq).items())},
        "log10_E": log_e / np.log(10),
        "E": float(np.exp(log_e)),
        "reject_at_40": bool(log_e >= np.log(1 / ALPHA)),
        "reject_at_480": bool(log_e >= np.log(K_FAMILY / ALPHA)),
        "sequential_first_crossing_at_40": sequential_first(seq),
        "run_structure": structure(files, tasks),
        "diagnostics": diagnostics(seq, runs, SEED + k),
    }


def empty_tasks(rows: Path) -> set[str]:
    out = set()
    for n in ("swesmith_pallets__jinja.jsonl", "extra36.jsonl"):
        for x in (rows / n).read_text().splitlines():
            if x.strip():
                r = json.loads(x)
                if not (r.get("problem_statement") or "").strip():
                    out.add(r["instance_id"])
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--trial", type=Path, required=True)
    ap.add_argument("--rows", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    t = a.trial / "results"
    pairs = [
        ("1 jinja_as_shipped", t / "f1_skill_probe.json", t / "f1_probe.json"),
        ("2 jinja_single_commit", t / "s25_leakfree_skill.json", t / "s25_leakfree_none.json"),
        ("3 bleve_as_shipped", t / "s25bleve_skill_probe.json", t / "s25bleve_f1_probe.json"),
        (
            "4 bleve_single_commit",
            t / "s25bleve_leakfree_skill_all.json",
            t / "s25bleve_leakfree_none.json",
        ),
        ("5 jinja_content_vs_placebo", t / "f1_skill_probe.json", t / "s27_placebo.json"),
        ("6 jinja_no_history_instruction", R / "s29_ablate.json", R / "s29_none.json"),
        ("7 jinja_relearned_single_commit", R / "s30_skill.json", R / "s30_none.json"),
        ("8 pygments_reuse", t / "s27pyg_skill_all.json", t / "s27pyg_none_all.json"),
        ("9 seed51_as_shipped", R / "s33_ship_skill.json", R / "s33_ship_none.json"),
        ("10 seed51_single_commit", R / "s33_lf_skill.json", R / "s33_lf_none.json"),
    ]
    out: dict = {
        "parameters": {"lam": LAM, "theta": THETA, "alpha": ALPHA, "family": K_FAMILY},
        "decisions": {},
    }
    for k, (name, s, o) in enumerate(pairs, 1):
        order, z, runs = z_pairs(s, o)
        out["decisions"][name] = decision(name, [z[i] for i in order], [s, o], runs, k, order)
    empty = empty_tasks(a.rows)
    for k, (name, pres, keep) in enumerate(
        [
            ("11 P33c_environment_contrast", ["s33"], lambda i: True),
            ("12 P35_environment_contrast_unseen", ["s33", "s35"], None),
        ],
        11,
    ):
        seq, files, runs, tasks = [], [], [], []
        for pre in pres:
            o1, zs, r1 = z_pairs(R / f"{pre}_ship_skill.json", R / f"{pre}_ship_none.json")
            _, zl, r2 = z_pairs(R / f"{pre}_lf_skill.json", R / f"{pre}_lf_none.json")
            ok = keep or ((lambda i: i in empty) if pre == "s33" else (lambda i: True))
            sel = [i for i in o1 if i in zl and ok(i)]
            seq += [(zs[i] - zl[i]) / 2 for i in sel]
            tasks += sel
            files += [R / f"{pre}_{x}.json" for x in ("ship_skill", "ship_none", "lf_skill")]
            files += [R / f"{pre}_lf_none.json"]
            runs += [r for r in r1 + r2 if r["instance_id"] in set(sel)]
        out["decisions"][name] = decision(name, seq, files, runs, k, tasks)
    a.out.write_text(json.dumps(out, indent=1) + "\n")
    for name, d in out["decisions"].items():
        dg = d["diagnostics"]
        print(
            f"{name:36s} n={d['n']:3d} E={d['E']:.4g} >40={d['reject_at_40']!s:5s} "
            f">480={d['reject_at_480']!s:5s} seq={d['sequential_first_crossing_at_40']} "
            f"| {d['run_structure']['verdict']} | crashed={dg['crashed']} "
            f"rate={dg['rate_limit_crashes']} tau={dg.get('kendall_tau')} "
            f"p={dg.get('kendall_p_two_sided_perm')}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
