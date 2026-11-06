"""Runs SWE-Skills-Bench cells with the adapter under a hard spend cap (section 22). Paid.

  python scripts/run_sskb.py --plan probe --model gemini-flash-lite --cap-usd 5.0 --out runs/sskb-p0

The probe plan: skills viper-configuration and asyncio-patterns, batches 1-10, seed 41, both arms,
interleaved (batch, skill, arm) so a stopped run stays balanced. Before each cell the driver checks
"spent + worst cell > cap" (worst cell = the agent cost_limit 1.0 USD) and stops if so. Writes
results/sskb_<plan>.json with one row per cell (no trajectory text).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

S = Path("/tmp/claude-0/-home-user-gatekeeper/cfb16e31-7b52-5c1a-8071-d03b24bd210f/scratchpad")
SSKB = S / "ext/sskb"
AGENT_PY = S / "pilotenv/bin/python"
WORST_CELL = 1.0  # agent cost_limit per run (E1 setting)
PLANS = {
    "probe": {
        "skills": ["viper-configuration", "asyncio-patterns"],
        "batches": list(range(1, 11)),
        "seeds": [41],
    }
}


def cells(plan: dict) -> list[tuple[str, int, int, str]]:
    return [
        (sk, b, s, arm)
        for s in plan["seeds"]
        for b in plan["batches"]
        for sk in plan["skills"]
        for arm in ("none", "skill")
    ]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", choices=sorted(PLANS), required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--cap-usd", type=float, required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-cells", type=int, default=0, help="stop after N new cells (cost check)")
    a = ap.parse_args()
    if subprocess.run(
        [sys.executable, "scripts/preflight.py", "--ci"], capture_output=True
    ).returncode:
        raise SystemExit(7)  # gate (CLAUDE.md)
    out_file = Path(f"results/sskb_{a.plan}.json")
    rows = json.loads(out_file.read_text())["rows"] if out_file.exists() else []
    done = {(r["skill"], r["batch"], r["seed"], r["arm"]) for r in rows}
    spent = sum(r.get("cost_usd") or 0.0 for r in rows)
    new = 0
    for sk, b, s, arm in cells(PLANS[a.plan]):
        if (sk, b, s, arm) in done:
            continue
        if a.max_cells and new >= a.max_cells:
            print(f"[stop] --max-cells {a.max_cells}")
            break
        new += 1
        if spent + WORST_CELL > a.cap_usd:
            print(f"[stop] cap: spent {spent:.4f} + worst cell {WORST_CELL} > {a.cap_usd}")
            break
        cmd = [
            str(AGENT_PY),
            "scripts/sskb_adapter.py",
            "run",
            "--sskb",
            str(SSKB),
            "--skill",
            sk,
            "--batch",
            str(b),
            "--arm",
            arm,
            "--seed",
            str(s),
            "--model",
            a.model,
            "--out",
            a.out,
        ]
        p = subprocess.run(cmd, capture_output=True, text=True)
        line = next((ln for ln in reversed(p.stdout.splitlines()) if ln.startswith("{")), None)
        if p.returncode or line is None:
            row = {"skill": sk, "batch": b, "seed": s, "arm": arm, "infra_error": p.stderr[-1500:]}
        else:
            row = json.loads(line)
        rows.append(row)
        spent += row.get("cost_usd") or 0.0
        out_file.write_text(
            json.dumps({"plan": a.plan, "model": a.model, "rows": rows}, indent=1) + "\n"
        )
        print(
            f"[cell] {sk} b{b} s{s} {arm}: pass_rate={row.get('pass_rate')} "
            f"cost={row.get('cost_usd')} spent={spent:.4f}",
            flush=True,
        )
    print(f"[done] {len(rows)} cells, spent {spent:.4f} USD")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
