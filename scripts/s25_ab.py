"""Section 25 decision rule for a skill arm against its no-skill arm (registered, step 2 and 4c).

For each scorer X in {S, L}: exact one-sided sign test on discordant task pairs (b = only the skill
arm passes, c = only the no-skill arm passes), Holm over the two tests at family alpha; outcome
A (S rejects), B (L only), C (neither). Gatekeeper: BettingEProcess on Z_S = 1[skill fails] -
1[none fails] in task order (theta, c, alpha as registered). Also the problem-statement subgroups.

  python scripts/s25_ab.py --skill results/f1_skill_probe.json --none results/f1_probe.json \
      --rows swesmith_pallets__jinja.jsonl --alpha 0.025 --theta 0 --c 0.5 --reps 10000 --seed 1
"""

from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path

import numpy as np
from scipy.stats import binomtest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


def passed(run: dict, scorer: str) -> bool:
    r = run.get(scorer) or {}
    return bool(r.get("resolved") if scorer == "S" else r.get("passed"))


def paired(skill: dict, none: dict) -> list[tuple[str, dict, dict]]:
    a = {r["instance_id"]: r for r in skill["runs"]}
    b = {r["instance_id"]: r for r in none["runs"]}
    order = [r["instance_id"] for r in sorted(skill["runs"], key=lambda r: r["order"])]
    bad = [i for i in order if "infra_error" in a[i] or "infra_error" in b.get(i, {})]
    if set(a) != set(b) or bad:
        raise SystemExit(f"task sets differ or infrastructure errors: {bad[:5]}")
    return [(i, a[i], b[i]) for i in order]


def analyse(pairs, alpha: float, theta: float, c: float, reps: int, seed: int) -> dict:
    from gatekeeper.eprocess import BettingEProcess

    out: dict = {"n": len(pairs)}
    ps = {}
    for x in ("S", "L"):
        s = np.array([passed(p[1], x) for p in pairs], dtype=float)
        n = np.array([passed(p[2], x) for p in pairs], dtype=float)
        b, cc = int(((s == 1) & (n == 0)).sum()), int(((s == 0) & (n == 1)).sum())
        p = binomtest(b, b + cc, 0.5, alternative="greater").pvalue if b + cc else 1.0
        rng = np.random.default_rng(seed)
        idx = rng.integers(0, len(s), size=(reps, len(s)))
        boot = (s[idx] - n[idx]).mean(axis=1)
        out[x] = {
            "skill": int(s.sum()),
            "none": int(n.sum()),
            "b": b,
            "c": cc,
            "p_one_sided": float(p),
            "gain": float((s - n).mean()),
            "boot95": [float(np.quantile(boot, 0.025)), float(np.quantile(boot, 0.975))],
        }
        ps[x] = p
    first, second = sorted(ps, key=ps.get)
    rej = {first: bool(ps[first] <= alpha / 2), second: False}
    rej[second] = bool(rej[first] and ps[second] <= alpha)
    out["holm_reject"] = rej
    out["outcome"] = "A" if rej["S"] else ("B" if rej["L"] else "C")
    ep = BettingEProcess(theta=theta, alpha=alpha, c=c)
    admit = None
    for k, (_, a, b) in enumerate(pairs, 1):
        ep.update(float(not passed(a, "S")) - float(not passed(b, "S")))
        if admit is None and ep.crossed:
            admit = k
    out["gatekeeper_admit_trial"] = admit
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    for k in ("--skill", "--none", "--rows"):
        ap.add_argument(k, required=True)
    for k in ("--alpha", "--theta", "--c"):
        ap.add_argument(k, required=True, type=float)
    ap.add_argument("--reps", required=True, type=int)
    ap.add_argument("--seed", required=True, type=int)
    ap.add_argument("--out")
    a = ap.parse_args()
    raw = Path(a.rows).read_bytes()
    text = (gzip.decompress(raw) if a.rows.endswith(".gz") else raw).decode()
    ps_empty = {
        r["instance_id"]: not (r.get("problem_statement") or "").strip()
        for r in (json.loads(x) for x in text.splitlines() if x.strip())
    }
    pairs = paired(json.loads(Path(a.skill).read_text()), json.loads(Path(a.none).read_text()))
    res = {"all": analyse(pairs, a.alpha, a.theta, a.c, a.reps, a.seed)}
    for name, keep in (("no_problem_statement", True), ("with_problem_statement", False)):
        sub = [p for p in pairs if ps_empty[p[0]] == keep]
        if sub:
            r = analyse(sub, a.alpha, a.theta, a.c, a.reps, a.seed)
            res[name] = {k: r[k] for k in ("n", "S")}
    js = json.dumps(res, indent=1)
    if a.out:
        Path(a.out).write_text(js + "\n")
    print(js)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
