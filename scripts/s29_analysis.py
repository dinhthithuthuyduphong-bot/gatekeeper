"""Section 29 analysis (docs/preregistration_main.md, registered before the run). 0 USD.

  python scripts/s29_analysis.py --rows <swesmith_pallets__jinja.jsonl>

P29 (one-sided, alpha 0.025, scorer S): ablated skill > no skill, exact sign test on the
discordant pairs.
Descriptive: Gatekeeper (theta 0, c 0.5, alpha 0.025); scorer L; the 34 tasks without a problem
statement; the gain against the full skill in the single-commit environment (section 25 step 3) and
against the full skill as shipped (06/11); traces (git log / git show, "Bug Patch").
Writes results/s29_analysis.json.
"""

from __future__ import annotations

import argparse
import gzip
import json
import re
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import s25_ab as ab  # noqa: E402

ALPHA, THETA, C, REPS, SEED = 0.025, 0.0, 0.5, 10000, 1  # as section 25


def load(p: str) -> dict:
    return json.loads(Path("results", p).read_text())


def gain_diff(pa, pb) -> dict:
    """(gain of pairs a) - (gain of pairs b), joint task-level bootstrap on shared tasks."""
    a = {i: (s, n) for i, s, n in pa}
    b = {i: (s, n) for i, s, n in pb}
    ids = sorted(set(a) & set(b))
    v = np.array(
        [
            (ab.passed(a[i][0], "S") - ab.passed(a[i][1], "S"))
            - (ab.passed(b[i][0], "S") - ab.passed(b[i][1], "S"))
            for i in ids
        ],
        float,
    )
    rng = np.random.default_rng(SEED)
    boot = v[rng.integers(0, v.size, size=(REPS, v.size))].mean(1)
    return {
        "n": len(ids),
        "d": float(v.mean()),
        "ci95": [float(np.quantile(boot, q)) for q in (0.025, 0.975)],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", required=True)
    ap.add_argument(
        "--prefix", default="s29", help="s29dry = the free dry run (pipeline test only)"
    )
    a = ap.parse_args()
    op = gzip.open if a.rows.endswith(".gz") else open
    empty = {
        r["instance_id"]: not (r.get("problem_statement") or "").strip()
        for r in (json.loads(x) for x in op(a.rows, "rt") if x.strip())
    }
    abl, none = load(f"{a.prefix}_ablate.json"), load(f"{a.prefix}_none.json")
    checks = {
        "n": (len(abl["runs"]), len(none["runs"])),
        "infra_error": sum("infra_error" in r for r in abl["runs"] + none["runs"]),
        "crashed": sum(bool(r.get("crashed")) for r in abl["runs"] + none["runs"]),
        "capped": sum(r.get("cost_usd", 0) >= 0.30 for r in abl["runs"] + none["runs"]),
        "spent_usd": abl["spent_usd"] + none["spent_usd"],
    }
    pairs = ab.paired(abl, none)
    main_ = ab.analyse(pairs, ALPHA, THETA, C, REPS, SEED)
    nops = [p for p in pairs if empty[p[0]]]
    sub = ab.analyse(nops, ALPHA, THETA, C, REPS, SEED)["S"]
    lf = ab.paired(load("s25_leakfree_skill.json"), load("s25_leakfree_none.json"))
    full = ab.paired(load("f1_skill_probe.json"), load("f1_probe.json"))
    recs = [json.loads(x) for x in gzip.open(f"results/{a.prefix}_ablate.traces.jsonl.gz", "rt")]
    git = bug = 0
    for r in recs:
        ms = r.get("messages") or []
        cmd = " ".join(str(m.get("content", "")) for m in ms if m["role"] == "assistant")
        obs = [str(m.get("content", "")) for m in ms if m["role"] == "user"][1:]
        git += bool(re.search(r"git (log|show)", cmd))
        bug += any("Bug Patch" in o for o in obs)
    out = {
        "checks": checks,
        "P29": {**main_["S"], "reject": main_["S"]["p_one_sided"] <= ALPHA},
        "L": main_["L"],
        "gatekeeper_admit_trial": main_["gatekeeper_admit_trial"],
        "no_problem_statement": {**sub, "n": len(nops)},
        "vs_full_single_commit": gain_diff(pairs, lf),
        "vs_full_as_shipped": gain_diff(pairs, full),
        "traces": {"runs": len(recs), "git_log_or_show": git, "bug_patch_seen": bug},
    }
    Path(f"results/{a.prefix}_analysis.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
