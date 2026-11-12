"""Section 33 analysis (docs/preregistration_main.md, registered before the run). 0 USD.

  python scripts/s33_analysis.py --rows <swesmith_pallets__jinja.jsonl> [--prefix s33dry]

Confirmatory, Holm at family level 0.025 over three tests on the seed-51 runs:
  P33a  skill > none as shipped (exact one-sided sign test);
  P33b  skill > none with the single-commit history (same test);
  P33c  environment share > 0: the e-process of section 32c on D_i = (Z_ship - Z_lf) / 2, with the
        anytime-valid p-value p = min(1, 1 / max_n E_n).
Descriptive: Gatekeeper per environment; Delta_leak of seed 51 and of seed 41; both seeds pooled;
the 34 tasks without a problem statement; agreement between seeds; note 33-1 (e-process on the
mean of the two seeds' D_i). Writes results/<prefix>_analysis.json.
"""

from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import s25_ab as ab  # noqa: E402

from gatekeeper.eprocess import BettingEProcess  # noqa: E402

ALPHA, THETA, C, REPS, SEED = 0.025, 0.0, 0.5, 10000, 1  # as sections 25 and 32c
R = Path("results")
OK = ["commits=1 refs=1 remotes=0 objects_with_bug_msg=0"]


def load(name: str) -> dict:
    return json.loads((R / name).read_text())


def z_of(skill: dict, none: dict) -> tuple[list[str], dict[str, float]]:
    pairs = ab.paired(skill, none)
    return [i for i, _, _ in pairs], {
        i: float(not ab.passed(a, "S")) - float(not ab.passed(b, "S")) for i, a, b in pairs
    }


def eproc(seq: list[float]) -> dict:
    ep = BettingEProcess(theta=THETA, alpha=ALPHA, c=C)
    best, first = 0.0, None
    for k, x in enumerate(seq, 1):
        ep.update(x)
        best = max(best, ep.log_e)
        if first is None and ep.crossed:
            first = k
    return {"first_crossing_at_40": first, "p_anytime": float(min(1.0, np.exp(-best)))}


def holm(ps: dict[str, float], alpha: float) -> dict[str, bool]:
    rej, ok = {}, True
    for rank, k in enumerate(sorted(ps, key=ps.get)):
        ok = ok and ps[k] <= alpha / (len(ps) - rank)
        rej[k] = ok
    return rej


def boot(v: np.ndarray) -> list[float]:
    rng = np.random.default_rng(SEED)
    b = v[rng.integers(0, v.size, size=(REPS, v.size))].mean(1)
    return [float(np.quantile(b, 0.025)), float(np.quantile(b, 0.975))]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", required=True)
    ap.add_argument("--prefix", default="s33")
    a = ap.parse_args()
    pre = a.prefix
    op = gzip.open if a.rows.endswith(".gz") else open
    empty = {
        r["instance_id"]: not (r.get("problem_statement") or "").strip()
        for r in (json.loads(x) for x in op(a.rows, "rt") if x.strip())
    }
    arms = {k: load(f"{pre}_{k}.json") for k in ("ship_none", "ship_skill", "lf_none", "lf_skill")}
    runs = [r for d in arms.values() for r in d["runs"]]
    lf = [r.get("leak_free_check") for k in ("lf_none", "lf_skill") for r in arms[k]["runs"]]
    checks = {
        "n": {k: len(d["runs"]) for k, d in arms.items()},
        "infra_error": sum("infra_error" in r for r in runs),
        "crashed": sum(bool(r.get("crashed")) for r in runs),
        "capped": sum(r.get("cost_usd", 0) >= 0.30 for r in runs),
        "leak_free_checks_ok": f"{sum(x == OK for x in lf)}/{len(lf)}",
        "stopped": {k: d.get("stopped") for k, d in arms.items() if d.get("stopped")},
        "spent_usd": sum(d["spent_usd"] for d in arms.values()),
    }
    ship = ab.analyse(ab.paired(arms["ship_skill"], arms["ship_none"]), ALPHA, THETA, C, REPS, SEED)
    lfa = ab.analyse(ab.paired(arms["lf_skill"], arms["lf_none"]), ALPHA, THETA, C, REPS, SEED)
    order, zs = z_of(arms["ship_skill"], arms["ship_none"])
    _, zl = z_of(arms["lf_skill"], arms["lf_none"])
    ids = [i for i in order if i in zl]
    d51 = np.array([(zs[i] - zl[i]) / 2 for i in ids])
    c33 = eproc(list(d51))
    ps = {
        "P33a": ship["S"]["p_one_sided"],
        "P33b": lfa["S"]["p_one_sided"],
        "P33c": c33["p_anytime"],
    }
    # seed 41 (sections 25): same tasks
    _, zs41 = z_of(load("f1_skill_probe.json"), load("f1_probe.json"))
    _, zl41 = z_of(load("s25_leakfree_skill.json"), load("s25_leakfree_none.json"))
    both = [i for i in ids if i in zs41 and i in zl41]
    d41 = np.array([(zs41[i] - zl41[i]) / 2 for i in both])
    d51b = np.array([(zs[i] - zl[i]) / 2 for i in both])
    pooled = (d41 + d51b) / 2

    def res(name: str) -> dict[str, bool]:
        return {r["instance_id"]: bool(r["S"]["resolved"]) for r in load(name)["runs"]}

    agree = {}
    for k, old in (
        ("ship_none", "f1_probe.json"),
        ("ship_skill", "f1_skill_probe.json"),
        ("lf_none", "s25_leakfree_none.json"),
        ("lf_skill", "s25_leakfree_skill.json"),
    ):
        o, n = res(old), {r["instance_id"]: bool(r["S"]["resolved"]) for r in arms[k]["runs"]}
        agree[k] = f"{sum(o[i] == n[i] for i in n if i in o)}/{sum(i in o for i in n)}"
    out = {
        "checks": checks,
        "P33a": ship["S"],
        "P33b": lfa["S"],
        "P33c": {**c33, "mean_D": float(d51.mean()), "n": int(d51.size)},
        "holm_reject": holm(ps, ALPHA),
        "gatekeeper_admit_trial": {
            "shipped": ship["gatekeeper_admit_trial"],
            "single_commit": lfa["gatekeeper_admit_trial"],
        },
        "delta_leak_seed51": {
            "d": float(-2 * d51.mean()),
            "ci95": sorted(-2 * x for x in boot(d51)),
        },
        "delta_leak_seed41": {
            "d": float(-2 * d41.mean()),
            "ci95": sorted(-2 * x for x in boot(d41)),
        },
        "delta_leak_pooled": {
            "d": float(-2 * pooled.mean()),
            "ci95": sorted(-2 * x for x in boot(pooled)),
            "n": int(pooled.size),
        },
        "note_33_1_eprocess_on_pooled_D": eproc(list(pooled)),
        "no_problem_statement": {
            k: sum(bool(r["S"]["resolved"]) for r in d["runs"] if empty[r["instance_id"]])
            for k, d in arms.items()
        },
        "same_outcome_as_seed41": agree,
    }
    (R / f"{pre}_analysis.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
