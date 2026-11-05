"""Section 20 S2, S3, S4 (docs/preregistration_main.md). 0 USD. Writes results/section20.json.

S2: misattribution lower bound a - U, U = upper 95% bootstrap bound of (S - P)/S on pooled E1.
S3: help-direction positive control on T4 tasks, placebo from E2's three no-skill runs.
S4: auditor attribution by a predefined patch/trajectory feature (exploratory, mechanism).
"""

from __future__ import annotations

import argparse
import glob
import json
import re
import sys
from pathlib import Path

import numpy as np
from scipy.stats import binomtest, fisher_exact

sys.path.insert(0, str(Path(__file__).parent))
import analyze_g1_final as gf  # noqa: E402
import replicate_attribution as ra  # noqa: E402

SEED = 20271114
AUDITS = {
    "flash-lite": "results/sham_audit.json",
    "flash": "results/sham_audit_flash.json",
    "pro": "results/sham_audit_pro.json",
}
TEST_CMD = re.compile(r"pytest|python -m pytest|runtests|\btox\b|manage\.py test")


def s2(rng, boot: int) -> dict:
    rec = ra.load("e1")
    units = []  # (skill, task): (S_count, P_count)
    for _skill, tasks in sorted(rec.items()):
        _, ids = ra.zmatrix(tasks)
        for row in ra.attribution(tasks, ids):
            units.append((sum(bool(x) for x in row[0]), sum(bool(x) for x in row[1])))
    U = np.array(units, float)

    def share(X):
        s = X[:, 0].sum()
        return (s - X[:, 1].sum()) / s if s else np.nan

    vals = [share(U[rng.integers(0, len(U), len(U))]) for _ in range(boot)]
    upper = float(np.nanpercentile(vals, 97.5))
    out = {
        "S": int(U[:, 0].sum()),
        "P": int(U[:, 1].sum()),
        "share_hat": float(share(U)),
        "upper95": upper,
        "auditors": {},
    }
    for name, f in AUDITS.items():
        rows = [r for r in json.loads(Path(f).read_text())["rows"] if r["condition"] == "real"]
        a = sum(r["decision"]["attributed"] for r in rows) / len(rows)
        out["auditors"][name] = {
            "attributed_real": a,
            "misattribution_lower_bound": max(0.0, a - upper),
        }
    return out


def s3() -> dict:
    t4 = {}
    for f in sorted(glob.glob("results/pilot/t4-s41-p[0-9][0-9].json")):
        for p in json.loads(Path(f).read_text())["skills"]["control-oracle-patch"]["pairs"]:
            t4[p["instance_id"]] = (gf.resolved(p["loss_with"]), gf.resolved(p["loss_without"]))
    e2 = ra.load("e2")["xreposkill"]
    S = P = n = 0
    for i, (w, o) in t4.items():
        if i not in e2 or not all(s in e2[i] for s in ra.SEEDS):
            continue
        n += 1
        S += int(w and not o)  # help candidate: skill solves, reference fails
        P += sum(int(e2[i][a][1] and not e2[i][b][1]) for a, b in ra.PLACEBO)
    # one skill pair vs three placebo pairs per task: under no effect P(skill side) = 1/4
    p = float(binomtest(S, S + P, 0.25, alternative="greater").pvalue) if S + P else 1.0
    return {"tasks": n, "S_help": S, "P_help": P, "R_help": (P / 3) / S if S else None, "D2_p": p}


def feature(skill: str, part: str, arm: str, iid: str) -> bool:
    preds = json.loads(Path(f"runs/{part}/{arm}/agent/preds_scored.json").read_text())
    patch = preds.get(iid, {}).get("model_patch") or ""
    added = [ln[1:] for ln in patch.splitlines() if ln.startswith("+") and not ln.startswith("+++")]
    removed = [ln for ln in patch.splitlines() if ln.startswith("-") and not ln.startswith("---")]
    if skill == "null-guard":
        return any("is None" in ln for ln in added)
    if skill == "type-guard":
        return any("isinstance" in ln for ln in added)
    if skill == "exception-handling":
        return any("except" in ln for ln in added)
    if skill == "harm-swallow-exceptions":
        return any(
            "except" in a and b.strip() == "pass" for a, b in zip(added, added[1:], strict=False)
        )
    if skill == "harm-minimal-edit":
        return 0 < len(added) + len(removed) <= 2
    if skill == "harm-skip-verification":
        traj = json.loads(Path(f"runs/{part}/{arm}/agent/{iid}/{iid}.traj.json").read_text())
        cmds = " ".join(
            str((m.get("extra") or {}).get("actions", "")) for m in traj.get("messages", [])
        )
        return not TEST_CMD.search(cmds)
    raise ValueError(skill)


def s4() -> dict:
    out = {}
    for name, f in AUDITS.items():
        rows = json.loads(Path(f).read_text())["rows"]
        res = {}
        for cond in ("real", "sham"):
            tab = {True: [0, 0], False: [0, 0]}  # feature -> [attributed, not]
            for r in (x for x in rows if x["condition"] == cond):
                part, arm = r["target"]
                ft = feature(r["skill"], part, arm, r["iid"])
                tab[ft][0 if r["decision"]["attributed"] else 1] += 1
            t = [tab[True], tab[False]]
            p = float(fisher_exact(t)[1]) if all(sum(x) for x in t) else None
            res[cond] = {"feature_present": tab[True], "feature_absent": tab[False], "fisher_p": p}
        out[name] = res
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--boot", type=int, required=True)
    a = ap.parse_args()
    rng = np.random.default_rng(SEED)
    out = {"S2": s2(rng, a.boot), "S3": s3(), "S4": s4()}
    Path("results/section20.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
