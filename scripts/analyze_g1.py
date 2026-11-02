"""Apply the pre-registered G1 rules (gatekeeper.analysis.g1_decision) to pilot results.

Usage: python scripts/analyze_g1.py --stage-b g1-b [--stage-c g1-c]
Reads results/pilot/<name>.json, writes results/g1_decision.json.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from gatekeeper.analysis import g1_decision

NOISE, POSITIVE = "control-none-seed1", "control-oracle-files"
POSITIVE_V2 = "control-oracle-tests"


def z_vs(run: dict, skill: str, ref: str) -> list[float]:
    """Per-task loss(skill) - loss(ref), both arms run independently on the same task (v2)."""
    s, r = run.get("skills", {}).get(skill), run.get("skills", {}).get(ref)
    if not s or not r:
        return []
    ref_loss = {p["instance_id"]: p["loss_with"] for p in r["pairs"]}
    return [
        p["loss_with"] - ref_loss[p["instance_id"]]
        for p in s["pairs"]
        if p["instance_id"] in ref_loss
    ]


def z_of(run: dict, skill: str, only_failed_baseline: bool = False) -> list[float]:
    s = run.get("skills", {}).get(skill)
    if not s:
        return []
    pairs = [p for p in s["pairs"] if not only_failed_baseline or p["loss_without"] > 0]
    return [p["loss_with"] - p["loss_without"] for p in pairs]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage-b", required=True)
    ap.add_argument("--stage-c", default="")
    ap.add_argument("--effect", type=float, default=0.10)
    ap.add_argument("--rule", choices=["v1", "v2"], default="v2", help="see preregistration_g1_v2")
    a = ap.parse_args()
    b = json.loads(Path(f"results/pilot/{a.stage_b}.json").read_text())
    c = json.loads(Path(f"results/pilot/{a.stage_c}.json").read_text()) if a.stage_c else {}
    skills = {k: z_of(c, k) for k in c.get("skills", {}) if not k.startswith("control-")}
    if a.rule == "v2":
        pos = z_vs(b, POSITIVE_V2, NOISE)
    else:
        pos = z_of(b, POSITIVE, only_failed_baseline=True)
    d = g1_decision(skills, z_of(b, NOISE), pos, effect=a.effect, rule=a.rule)
    d["rule"] = a.rule
    d["stage_b"], d["stage_c"] = a.stage_b, a.stage_c or None
    d["usage"] = {"stage_b": b.get("usage"), "stage_c": c.get("usage")}
    d["spent_usd"] = round(
        float(b.get("spent_usd", 0)) + float(c.get("spent_usd", 0) if c else 0), 2
    )
    Path("results").mkdir(exist_ok=True)
    Path("results/g1_decision.json").write_text(json.dumps(d, indent=2) + "\n")
    print(json.dumps({k: d[k] for k in ("verdict", "spent_usd")}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
