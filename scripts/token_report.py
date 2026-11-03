"""Token usage per pilot stage, from the agent trajectories (runs/<part>/<arm>/agent/*/*.traj.json).

Reports use tokens (input, of which cached, output) so that stages, arms and models can be
compared independently of price lists; USD is only used to control the budget.
Writes results/token_usage.json.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

from gatekeeper.pilot import traj_usage

STAGES = {
    "A (model choice)": r"^g1-a-(lite2|flash)$",
    "B1 (invalid, seed 0)": r"^g1-b-p\d\d$",
    "B2": r"^g1-b2-p\d\d$",
    "B3": r"^g1-b3-p\d\d$",
    "C (screening)": r"^g1-c-p\d\d$",
    "Confirmation (seeds 11/21/31)": r"^g1-c-s(11|21|31)-p\d\d$",
}


def main() -> int:
    out: dict = {}
    for stage, pat in STAGES.items():
        agg = defaultdict(lambda: {"runs": 0, "tokens_in": 0, "tokens_cached": 0, "tokens_out": 0})
        for part in sorted(Path("runs").glob("*")):
            if not re.match(pat, part.name):
                continue
            for traj in part.glob("*/agent/*/*.traj.json"):
                arm = traj.parts[2]
                try:
                    u = traj_usage(json.loads(traj.read_text()))
                except (OSError, ValueError):
                    continue
                a = agg[arm]
                a["runs"] += 1
                for k in ("tokens_in", "tokens_cached", "tokens_out"):
                    a[k] += int(u.get(k, 0) or 0)
        tot = {"runs": 0, "tokens_in": 0, "tokens_cached": 0, "tokens_out": 0}
        for a in agg.values():
            for k in tot:
                tot[k] += a[k]
        for a in [*agg.values(), tot]:
            n = a["runs"] or 1
            a["in_per_run"] = round(a["tokens_in"] / n)
            a["out_per_run"] = round(a["tokens_out"] / n)
            a["cached_share"] = (
                round(a["tokens_cached"] / a["tokens_in"], 3) if a["tokens_in"] else None
            )
        out[stage] = {"total": tot, "per_arm": dict(agg)}
    Path("results/token_usage.json").write_text(json.dumps(out, indent=1) + "\n")
    for stage, v in out.items():
        t = v["total"]
        print(
            f"{stage:32s} runs {t['runs']:4d}  in {t['tokens_in'] / 1e6:7.2f}M "
            f"(cached {t['cached_share']})  out {t['tokens_out'] / 1e6:5.2f}M  "
            f"per run in {t['in_per_run'] / 1e3:.0f}k out {t['out_per_run'] / 1e3:.1f}k"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
