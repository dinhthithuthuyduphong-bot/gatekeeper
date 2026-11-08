"""Section 26m: harness audit - environment-broken PASS_TO_PASS tests (0 USD, no LLM).

  python scripts/harness_audit.py --e2-logs <dir with logs/run_evaluation from raw-archive>

Every registered pair (results/pilot/<run>.json, "skills" -> pairs) is linked to the harness report
that produced it: same seed and arm, same instance, and loss_of(report) equal to the registered
loss (the link is exact; unlinked pairs are counted and reported). Three endpoints per pair:
  S  harness "resolved" (registered endpoint; must reproduce the registered numbers),
  F  patch applied, tests ran, every FAIL_TO_PASS passed,
  B  as S after dropping PASS_TO_PASS tests that fail in EVERY scored run of the instance (all
     arms, all seeds; instances with >= 3 scored runs only). Arm-independent by construction.
Effect = mean over tasks (present in every seed) of the mean over seeds of (resolved with skill -
resolved without) = -mean_z_resolved of the registered analysis; task-level bootstrap 95% CI
(10,000 resamples). Writes results/harness_audit.json and
results/harness_gold_targets.json (instances for the gold-patch rescoring step).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gatekeeper.harness import loss_of  # noqa: E402

RUN_RE = re.compile(r"^(?P<name>.+?-p\d+)-(?P<arm>.+?)-\d{8}T\d{6}-\d+(?:-r\d+)?$")
SEED_RE = re.compile(r"-s(\d+)-")
EXPERIMENTS = {  # registered pair files (analyze_g1_final verdict --confirm ...)
    "E1": ["g1-e1all-s41", "g1-e1all-s51", "g1-e1all-s61"],
    "E2": ["g2-e2-s41", "g2-e2-s51", "g2-e2-s61"],
    "T4": ["t4-s41"],
}
PREFIX = {"E1": ("g1-e1-", "g1-e1x-"), "E2": ("g2-e2-",), "T4": ("t4-s41-",)}
N_BOOT = 10_000
SEED = 2026
MIN_RUNS_B = 3
NO_REPORT = loss_of(None)[0]


def load_reports(roots: list[Path]) -> list[dict]:
    out = []
    for root in roots:
        for f in root.glob("*/*/*/report.json"):
            run, iid = f.parts[-4], f.parts[-2]
            m = RUN_RE.match(run)
            if not m:
                continue
            try:
                rep = json.loads(f.read_text())[iid]
            except (KeyError, ValueError):
                continue
            s = SEED_RE.search(m["name"] + "-")
            out.append(
                {
                    "run": run,
                    "name": m["name"],
                    "arm": m["arm"],
                    "seed": int(s.group(1)) if s else None,
                    "iid": iid,
                    "rep": rep,
                    "loss": loss_of(rep)[0],
                }
            )
    return out


def p2p_fail(rep: dict) -> set[str]:
    return set(((rep.get("tests_status") or {}).get("PASS_TO_PASS") or {}).get("failure") or [])


def broken_tests(reports: list[dict]) -> dict[str, set[str]]:
    by = defaultdict(list)
    for r in reports:
        by[r["iid"]].append(p2p_fail(r["rep"]))
    return {
        iid: set.intersection(*fs)
        for iid, fs in by.items()
        if len(fs) >= MIN_RUNS_B and set.intersection(*fs)
    }


def endpoints(rep: dict | None, broken: set[str]) -> dict[str, bool]:
    if rep is None or "tests_status" not in rep:
        return {"S": False, "F": False, "B": False}
    ts = rep["tests_status"]
    f2p = ts.get("FAIL_TO_PASS") or {}
    f_ok = not f2p.get("failure")
    s = bool(rep.get("resolved"))
    b = s or (f_ok and not (p2p_fail(rep) - broken) and rep.get("patch_successfully_applied", True))
    return {"S": s, "F": f_ok, "B": bool(b)}


def link(pair_loss: float, cands: list[dict]) -> dict | None:
    hit = [c for c in cands if abs(c["loss"] - pair_loss) < 1e-9]
    return hit[-1] if hit else None


def boot_ci(x: np.ndarray, rng: np.random.Generator) -> list[float]:
    idx = rng.integers(0, x.size, size=(N_BOOT, x.size))
    m = x[idx].mean(1)
    return [float(np.quantile(m, 0.025)), float(np.quantile(m, 0.975))]


def analyse(exp: str, reports: list[dict], rng: np.random.Generator) -> dict:
    mine = [r for r in reports if r["name"].startswith(PREFIX[exp])]
    broken = broken_tests(mine)
    idx = defaultdict(list)
    for r in mine:
        idx[(r["seed"], r["arm"], r["iid"])].append(r)
    out, unlinked, n_pairs = {}, 0, 0
    for f in EXPERIMENTS[exp]:
        run = json.loads(Path(f"results/pilot/{f}.json").read_text())
        seed = int(SEED_RE.search(f + "-").group(1))
        for skill, v in run["skills"].items():
            acc = out.setdefault(skill, defaultdict(lambda: defaultdict(list)))
            for p in v["pairs"]:
                n_pairs += 1
                iid = p["instance_id"]
                rw = link(p["loss_with"], idx[(seed, skill, iid)])
                ro = link(p["loss_without"], idx[(seed, "none", iid)])
                # no report = no submission / patch not applied / timed out: the registered
                # loss is then loss_of(None) = 2/3 (F = 1, R = 0) and every endpoint is "unresolved"
                if (rw is None and abs(p["loss_with"] - NO_REPORT) > 1e-9) or (
                    ro is None and abs(p["loss_without"] - NO_REPORT) > 1e-9
                ):
                    unlinked += 1
                    continue
                ew = endpoints(rw["rep"] if rw else None, broken.get(iid, set()))
                eo = endpoints(ro["rep"] if ro else None, broken.get(iid, set()))
                for e in "SFB":
                    acc[e][iid].append(float(ew[e]) - float(eo[e]))
    res = {}
    for skill, acc in out.items():
        res[skill] = {}
        for e in "SFB":
            need = len(EXPERIMENTS[exp])  # as analyze_g1_final.per_task_mean: all seeds present
            x = np.array([np.mean(v) for v in acc[e].values() if len(v) == need])
            res[skill][e] = {
                "n_tasks": int(x.size),
                "effect": float(x.mean()),
                "ci": boot_ci(x, rng),
            }
    return {
        "skills": res,
        "n_pairs": n_pairs,
        "unlinked_pairs": unlinked,
        "n_reports": len(mine),
        "broken_instances": {k: sorted(v) for k, v in broken.items()},
    }


def gold_targets(reports: list[dict]) -> list[str]:
    tgt = set()
    for r in reports:
        e = endpoints(r["rep"], set())
        if e["F"] and not e["S"]:
            tgt.add(r["iid"])
    tgt |= set(broken_tests(reports))
    return sorted(tgt)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--e2-logs", type=Path, required=True)
    a = ap.parse_args()
    reports = load_reports([Path("logs/run_evaluation"), a.e2_logs / "logs/run_evaluation"])
    rng = np.random.default_rng(SEED)
    res = {e: analyse(e, reports, rng) for e in EXPERIMENTS}
    res["registered_check"] = {
        e: json.loads(Path(f"results/{e.lower()}_final.json").read_text())["skills"]
        for e in ("E1", "E2")
    }
    Path("results/harness_audit.json").write_text(json.dumps(res, indent=1, default=str) + "\n")
    Path("results/harness_gold_targets.json").write_text(
        json.dumps(gold_targets(reports), indent=1) + "\n"
    )
    for e in EXPERIMENTS:
        print(e, "pairs", res[e]["n_pairs"], "unlinked", res[e]["unlinked_pairs"])
        print("  broken instances", len(res[e]["broken_instances"]))
        for sk, v in res[e]["skills"].items():
            line = "; ".join(
                f"{k} {v[k]['effect']:+.3f} [{v[k]['ci'][0]:+.3f},{v[k]['ci'][1]:+.3f}]"
                for k in "SFB"
            )
            print(f"  {sk} (n={v['S']['n_tasks']}): {line}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
