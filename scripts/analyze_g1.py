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


def z_of(run: dict, skill: str) -> list[float]:
    s = run.get("skills", {}).get(skill)
    return [p["loss_with"] - p["loss_without"] for p in s["pairs"]] if s else []


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage-b", required=True)
    ap.add_argument("--stage-c", default="")
    ap.add_argument("--effect", type=float, default=0.10)
    a = ap.parse_args()
    b = json.loads(Path(f"results/pilot/{a.stage_b}.json").read_text())
    c = json.loads(Path(f"results/pilot/{a.stage_c}.json").read_text()) if a.stage_c else {}
    skills = {k: z_of(c, k) for k in c.get("skills", {}) if not k.startswith("control-")}
    d = g1_decision(skills, z_of(b, NOISE), z_of(b, POSITIVE), effect=a.effect)
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
