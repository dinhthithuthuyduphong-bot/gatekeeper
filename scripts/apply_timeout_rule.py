"""Apply execution note 7 (docs/preregistration_e1.md; audit A56) to batch files written by code
older than that note (audit A57): a harness test timeout on the FIRST scoring is the agent's
outcome "not resolved" (SWE-bench: error_ids, never resolved_ids), never re-scored and never an
infrastructure failure. Code before the note re-scored such tasks, and after a second timeout
called them infrastructure failures, so the task would have been re-run.

  python scripts/apply_timeout_rule.py g1-e1-s41-p25 [--dry-run]

Only files WITHOUT a "harness_test_timeout" field (old code) are changed; the evidence is the
harness's own log of the first scoring (logs/run_evaluation/<part>-<arm>-<UTC>-<pid>). Losses of
the affected tasks are re-read from the harness reports; pairs, mean Z and variance components of
the affected skills are rebuilt. runs/<part>/trials.jsonl is left as the old code wrote it (raw).
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
from pathlib import Path

from gatekeeper.analysis import variance_components
from gatekeeper.harness import eval_timed_out, loss_of, patch_apply_failed, read_report

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("run_pilot", ROOT / "scripts" / "run_pilot.py")
_rp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_rp)
TEST_TIMED_OUT, PATCH_NOT_APPLIED = _rp.TEST_TIMED_OUT, _rp.PATCH_NOT_APPLIED
NO_REPORT = "harness: no report for a non-empty patch"


def first_run_id(part: str, arm: str, logs: Path) -> str:
    pat = re.compile(rf"^{re.escape(part)}-{re.escape(arm)}-\d{{8}}T\d{{6}}-\d+$")
    hits = [p.name for p in logs.iterdir() if pat.match(p.name)]
    if len(hits) != 1:
        raise SystemExit(f"{part}/{arm}: expected one first-scoring log dir, found {hits}")
    return hits[0]


def arm_loss(rid: str, iid: str, logs: Path) -> float:
    """Loss as the CURRENT code scores it (run_pilot.score_arm), from the reports on disk."""
    if eval_timed_out(rid, iid, logs):
        return loss_of(dict(TEST_TIMED_OUT))[0]
    rep = read_report(rid, "", iid, logs)
    if rep is None and (logs / f"{rid}-r1").exists():  # legitimate re-score of a missing report
        rep = read_report(f"{rid}-r1", "", iid, logs)
    if rep is None and (
        patch_apply_failed(rid, iid, logs) or patch_apply_failed(f"{rid}-r1", iid, logs)
    ):
        rep = dict(PATCH_NOT_APPLIED)
    return loss_of(rep)[0]


def apply(d: dict, logs: Path) -> dict[str, list[str]]:
    """Changes d in place; returns the timeouts per arm (empty: nothing changed)."""
    if d.get("harness_test_timeout") is not None:
        return {}
    part, ids = d["name"], d["instances"]
    rid = {arm: first_run_id(part, arm, logs) for arm in d["exit_status"]}
    timeouts = {a: [i for i in ids if eval_timed_out(r, i, logs)] for a, r in rid.items()}
    timeouts = {a: v for a, v in timeouts.items() if v}
    if not timeouts:
        return {}
    infra = d.setdefault("infra_failures", {})
    for arm, v in timeouts.items():
        for i in v:
            reason = (infra.get(arm) or {}).get(i)
            if reason is not None and reason != NO_REPORT:
                raise SystemExit(f"{part}/{arm}/{i}: infra reason {reason!r} with a timeout log")
            (infra.get(arm) or {}).pop(i, None)
    d["infra_failures"] = {a: v for a, v in infra.items() if v}
    affected = sorted({i for v in timeouts.values() for i in v})
    bad = lambda arm, i: i in (d["infra_failures"].get(arm) or {})  # noqa: E731
    for sk, v in d["skills"].items():
        keep = [p for p in v["pairs"] if p["instance_id"] not in affected]
        for i in affected:
            if not bad("none", i) and not bad(sk, i):
                keep.append(
                    {
                        "instance_id": i,
                        "loss_with": arm_loss(rid[sk], i, logs),
                        "loss_without": arm_loss(rid["none"], i, logs),
                    }
                )
        keep.sort(key=lambda p: p["instance_id"])
        pairs = [(p["instance_id"], p["loss_with"], p["loss_without"]) for p in keep]
        z = [lw - lo for _, lw, lo in pairs]
        v["pairs"] = keep
        v["mean_Z"] = sum(z) / len(z) if z else None
        v["variance_components"] = variance_components(pairs) if len(pairs) >= 3 else None
    d["harness_test_timeout"] = timeouts
    d["timeout_rule_applied"] = {
        "by": "scripts/apply_timeout_rule.py",
        "rule": "docs/preregistration_e1.md execution note 7 (audit A56, A57)",
        "first_scoring_runs": rid,
    }
    return timeouts


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("parts", nargs="+")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--logs", type=Path, default=Path("logs/run_evaluation"))
    a = ap.parse_args()
    for part in a.parts:
        f = Path("results/pilot") / f"{part}.json"
        d = json.loads(f.read_text())
        t = apply(d, a.logs)
        print(f"{part}: {'no change' if not t else t}")
        if t and not a.dry_run:
            f.write_text(json.dumps(d, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
