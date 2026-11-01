"""Cost ranges for Gemini on Vertex AI (TODO.md Phase 2-3; docs/preregistration.md §8).

Tokens per agent run are NOT measured yet: the table spans an assumed range and must be replaced
by measured values (runlog.CostSummary) after the first paid pilot. Prices come from
configs/models/vertex_gemini.json (unverified placeholders until `_verified` is true).
Writes results/cost_estimate.json.
"""

from __future__ import annotations

import json
from pathlib import Path

from gatekeeper.pilot import estimate_cost_usd, load_model_specs

# (label, input tokens per agent run, output tokens per agent run) — assumptions
TOKEN_SCENARIOS = [
    ("light", 150_000, 8_000),
    ("typical", 500_000, 20_000),
    ("heavy", 1_500_000, 50_000),
]
# number of agent runs (1 paired trial = 2 runs)
WORKLOADS = {
    "G1 mini-pilot: 4 skills x 30 pairs (+ shared none arm)": (4 + 1) * 30,
    "Phase 3 pilot (preregistration §8)": 3_900,
    "Phase 6 study: 180 pairs x 8 systems x 3 runs x 2 backends (rough)": 180 * 2 * 8 * 3,
}


def main() -> None:
    cfg = json.loads(Path("configs/models/vertex_gemini.json").read_text())
    specs = load_model_specs("configs/models/vertex_gemini.json")
    rows = []
    for wname, runs in WORKLOADS.items():
        for mkey, spec in specs.items():
            for label, tin, tout in TOKEN_SCENARIOS:
                per_run = estimate_cost_usd(spec, tin, tout)
                rows.append(
                    {
                        "workload": wname,
                        "agent_runs": runs,
                        "model": mkey,
                        "scenario": label,
                        "usd_per_run": round(per_run, 4),
                        "usd_total": round(per_run * runs, 2),
                    }
                )
                print(
                    f"{wname[:40]:<40} {mkey:<12} {label:<8} {per_run:7.3f}/run "
                    f"{per_run * runs:10.2f} USD"
                )
    out = {
        "prices_verified": cfg.get("_verified", False),
        "token_scenarios": TOKEN_SCENARIOS,
        "rows": rows,
    }
    Path("results").mkdir(exist_ok=True)
    Path("results/cost_estimate.json").write_text(json.dumps(out, indent=2) + "\n")


if __name__ == "__main__":
    main()
