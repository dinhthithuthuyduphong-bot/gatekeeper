"""Section 30 analysis (docs/preregistration_main.md, registered before the runs). 0 USD.

  python scripts/s30_analysis.py --rows <swesmith_pallets__jinja.jsonl> [--prefix s30dry]

P30 (one-sided, alpha 0.025, scorer S): the skill learned in the single-commit environment > no
skill, both in the single-commit environment, exact sign test on the discordant pairs.
Descriptive: the history rule of section 29 (scripts/make_ablation.RULE) applied to the returned
skill and to every candidate of the learning run; Gatekeeper; scorer L; the gain against the
original skill in the same environment (section 25 step 3, another day); the returned skill as
shipped on the 34 tasks without a problem statement (resolved, git log / git show, "Bug Patch").
Writes results/<prefix>_analysis.json.
"""

from __future__ import annotations

import argparse
import gzip
import io
import json
import re
import sys
import tarfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import s25_ab as ab  # noqa: E402
from make_ablation import RULE  # noqa: E402
from s29_analysis import ALPHA, REPS, SEED, THETA, C, gain_diff  # noqa: E402


def load(p: str) -> dict:
    return json.loads(Path("results", p).read_text())


def history_lines(text: str) -> int:
    return sum(bool(RULE.search(line)) for line in text.splitlines())


def candidates(tar_path: Path) -> list[str]:
    with tarfile.open(tar_path) as tf:
        m = next(x for x in tf.getmembers() if x.name.endswith("/candidates.json"))
        data = json.load(io.TextIOWrapper(tf.extractfile(m), encoding="utf-8"))
    return [c["skills"] for c in data]


def trace_counts(path: Path) -> dict:
    recs = [json.loads(x) for x in gzip.open(path, "rt")]
    git = bug = 0
    for r in recs:
        ms = r.get("messages") or []
        cmd = " ".join(str(m.get("content", "")) for m in ms if m["role"] == "assistant")
        obs = [str(m.get("content", "")) for m in ms if m["role"] == "user"][1:]
        git += bool(re.search(r"git (log|show)", cmd))
        bug += any("Bug Patch" in o for o in obs)
    return {"runs": len(recs), "git_log_or_show": git, "bug_patch_seen": bug}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", required=True)
    ap.add_argument(
        "--prefix", default="s30", help="s30dry = the free dry run (pipeline test only)"
    )
    a = ap.parse_args()
    pre = a.prefix
    skill, none, ship = (load(f"{pre}_{x}.json") for x in ("skill", "none", "shipped34"))
    runs = skill["runs"] + none["runs"] + ship["runs"]
    lf = [r.get("leak_free_check") for r in skill["runs"] + none["runs"]]
    led = [
        load(f"{pre}_learn_ledger_h{h}.json")
        for h in (1, 2)
        if Path(f"results/{pre}_learn_ledger_h{h}.json").exists()
    ]
    cands = candidates(Path(f"results/{pre}_learn_run.tar.gz"))
    best = Path(f"results/{pre}_best_skills.txt").read_text(encoding="utf-8")
    pairs = ab.paired(skill, none)
    main_ = ab.analyse(pairs, ALPHA, THETA, C, REPS, SEED)
    orig = ab.paired(load("s25_leakfree_skill.json"), load("s25_leakfree_none.json"))
    out = {
        "checks": {
            "n": [len(skill["runs"]), len(none["runs"]), len(ship["runs"])],
            "infra_error": sum("infra_error" in r for r in runs),
            "crashed": sum(bool(r.get("crashed")) for r in runs),
            "capped": sum(r.get("cost_usd", 0) >= 0.30 for r in runs),
            "leak_free_checks_ok": sum(
                x == ["commits=1 refs=1 remotes=0 objects_with_bug_msg=0"] for x in lf
            ),
            "leak_free_checks": len(lf),
            "eval_spent_usd": skill["spent_usd"] + none["spent_usd"] + ship["spent_usd"],
            "learn_spent_usd": led[-1]["spent_total"] if led else None,
            "learn_rewrites_ok": sum(x.get("leak_free_rewrites_ok", 0) for x in led),
            "learn_leak_free": all(x.get("leak_free") for x in led) if led else None,
        },
        "skill_text": {
            "bytes": len(best.encode()),
            "history_lines_in_returned_skill": history_lines(best),
            "candidates": len(cands),
            "nonempty_candidates": sum(bool(c.strip()) for c in cands),
            "candidates_with_history_line": sum(history_lines(c) > 0 for c in cands),
        },
        "P30": {**main_["S"], "reject": main_["S"]["p_one_sided"] <= ALPHA},
        "L": main_["L"],
        "gatekeeper_admit_trial": main_["gatekeeper_admit_trial"],
        "vs_original_skill_single_commit": gain_diff(pairs, orig),
        "as_shipped_no_problem_statement": {
            "n": len(ship["runs"]),
            "resolved": sum(bool(r["S"]["resolved"]) for r in ship["runs"]),
            **trace_counts(Path(f"results/{pre}_shipped34.traces.jsonl.gz")),
        },
    }
    Path(f"results/{pre}_analysis.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
