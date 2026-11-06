"""Runs SWE-Skills-Bench cells with the adapter under a hard spend cap (sections 22, 23). Paid.

  python scripts/run_sskb.py --plan probe --model gemini-flash-lite --cap-usd 5.0 --out runs/sskb-p0
  python scripts/run_sskb.py --plan s23a --model gemini-flash --cap-usd 2.0 --out runs/sskb-s23a
  python scripts/run_sskb.py --plan s23b-screen --model gemini-flash-lite --cap-usd 5.0 \
      --out runs/sskb-s23b
  python scripts/run_sskb.py --plan s23b-confirm --model gemini-flash-lite --cap-usd 5.0 \
      --out runs/sskb-s23b

Cells are interleaved (seed, batch, skill, arm) so a stopped run stays balanced. Before each cell
the driver checks "spent + worst cell > cap" (worst cell = the agent cost_limit 1.0 USD) and stops
if so. Plans in the same cap group share one spend (s23b-screen and s23b-confirm: 5 USD in all).
Cost gate (sections 22, 23): after the first `gate_after` new cells, stop if the mean cost per cell
exceeds `gate_usd` (2 x the estimate). Writes results/sskb_<plan>.json, one row per cell.
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
S23B_SKILLS = [  # section 23b: Python/Go skills with |published effect| >= 6 pp, not in section 22
    "go-fx-di",
    "langsmith-fetch",
    "pandas-dataframe-patterns",
    "scipy-scientific-computing",
    "sympy-symbolic-math",
]
PLANS = {
    "probe": {
        "model": "gemini-flash-lite",
        "skills": ["viper-configuration", "asyncio-patterns"],
        "batches": list(range(1, 11)),
        "seeds": [41],
        "group": "probe",
        "gate_after": 4,
        "gate_usd": 0.16,
    },
    "s23a": {
        "model": "gemini-flash",
        "skills": ["viper-configuration", "asyncio-patterns"],
        "batches": list(range(1, 11)),
        "seeds": [41],
        "group": "s23a",
        "gate_after": 4,
        "gate_usd": 0.15,
    },
    "s23b-screen": {
        "model": "gemini-flash-lite",
        "skills": S23B_SKILLS,
        "batches": list(range(1, 11)),
        "seeds": [41],
        "group": "s23b",
        "gate_after": 4,
        "gate_usd": 0.052,
    },
    "s23a-pro": {  # D-M11: section 23a moved to gemini-pro, cap 3 USD
        "model": "gemini-pro",
        "skills": ["viper-configuration", "asyncio-patterns"],
        "batches": list(range(1, 11)),
        "seeds": [41],
        "group": "s23a-pro",
        "gate_after": 4,
        "gate_usd": 0.42,
    },
    "s23b-flash-screen": {  # D-M11: section 23b moved to gemini-flash, cap 7 USD for both steps
        "model": "gemini-flash",
        "skills": S23B_SKILLS,
        "batches": list(range(1, 7)),
        "seeds": [41],
        "group": "s23b-flash",
        "gate_after": 4,
        "gate_usd": 0.15,
    },
    "s23b-flash-confirm": {
        "model": "gemini-flash",
        "skills": None,
        "batches": list(range(1, 11)),
        "seeds": [51],
        "group": "s23b-flash",
        "gate_after": 0,
        "gate_usd": 0.0,
    },
    "s23b-confirm": {
        "model": "gemini-flash-lite",
        "skills": None,  # chosen by select_confirm() from the screen
        "batches": list(range(1, 11)),
        "seeds": [51, 61],
        "group": "s23b",
        "gate_after": 0,
        "gate_usd": 0.0,
    },
}


def cells(plan: dict) -> list[tuple[str, int, int, str]]:
    return [
        (sk, b, s, arm)
        for s in plan["seeds"]
        for b in plan["batches"]
        for sk in plan["skills"]
        for arm in ("none", "skill")
    ]


def skill_means(rows: list[dict]) -> dict[str, float]:
    """D per skill = mean of (skill pass rate - none pass rate) over complete pairs."""
    by: dict[tuple, dict[str, float]] = {}
    for r in rows:
        if r.get("pass_rate") is not None:
            by.setdefault((r["skill"], r["batch"], r["seed"]), {})[r["arm"]] = r["pass_rate"]
    d: dict[str, list[float]] = {}
    for (sk, _, _), v in by.items():
        if len(v) == 2:
            d.setdefault(sk, []).append(v["skill"] - v["none"])
    return {sk: sum(x) / len(x) for sk, x in d.items()}


def select_confirm(screen_rows: list[dict], skills: list[str], n_batches: int) -> tuple[str, int]:
    """Section 23b rule: the screened skill with the largest |D|; ties go to the first in `skills`.
    Requires the full screen (n_batches complete pairs per skill). Returns (skill, sign)."""
    by = {}
    for r in screen_rows:
        if r.get("pass_rate") is not None:
            by.setdefault((r["skill"], r["batch"]), set()).add(r["arm"])
    for sk in skills:
        n = sum(1 for (s, _), arms in by.items() if s == sk and arms == {"none", "skill"})
        if n != n_batches:
            raise SystemExit(f"screen incomplete for {sk}: {n}/{n_batches} pairs")
    d = skill_means(screen_rows)
    best = max(skills, key=lambda s: (abs(d[s]), -skills.index(s)))
    return best, (1 if d[best] > 0 else -1)


def health_stop(row: dict, new: int, infra_new: int) -> str | None:
    """Stop reasons checked after each new cell (section 23; A84)."""
    if "infra_error" not in row and (row.get("n_calls") or 0) > 0 and not row.get("cost_usd"):
        return "cost accounting: model calls with cost 0 (A84)"
    if row.get("exit_status") in ("APIConnectionError", "AuthenticationError"):
        return f"model unreachable: {row['exit_status']} (A84)"
    if new >= 4 and infra_new / new > 0.10:
        return f"infra errors {infra_new}/{new} > 10%"
    return None


def load_rows(plan: str) -> list[dict]:
    f = Path(f"results/sskb_{plan}.json")
    return json.loads(f.read_text())["rows"] if f.exists() else []


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
    plan = dict(PLANS[a.plan])
    if a.model != plan["model"]:
        raise SystemExit(f"plan {a.plan} is registered for {plan['model']}, not {a.model}")
    extra = {}
    if a.plan.endswith("-confirm"):
        screen = a.plan.replace("-confirm", "-screen")
        sk, sign = select_confirm(load_rows(screen), S23B_SKILLS, len(PLANS[screen]["batches"]))
        plan["skills"] = [sk]
        extra = {"selected": sk, "direction": sign}
        print(f"[select] {sk} direction {sign:+d}")
    out_file = Path(f"results/sskb_{a.plan}.json")
    rows = load_rows(a.plan)
    done = {(r["skill"], r["batch"], r["seed"], r["arm"]) for r in rows}
    group = [p for p, v in PLANS.items() if v["group"] == plan["group"]]
    spent = sum(r.get("cost_usd") or 0.0 for p in group for r in load_rows(p))
    if a.plan.endswith("-confirm"):  # D-M11: start only if the whole confirmation fits the cap
        costs = [r.get("cost_usd") or 0.0 for r in load_rows(screen)]
        need = len(cells(plan)) * sum(costs) / len(costs)
        if spent + need + WORST_CELL > a.cap_usd:
            print(f"[stop] confirmation needs ~{need:.2f} USD; spent {spent:.2f}, cap {a.cap_usd}")
            return 0
    new, new_cost, infra_new = 0, 0.0, 0
    for sk, b, s, arm in cells(plan):
        if (sk, b, s, arm) in done:
            continue
        if a.max_cells and new >= a.max_cells:
            print(f"[stop] --max-cells {a.max_cells}")
            break
        if plan["gate_after"] and new == plan["gate_after"]:
            if new_cost / new > plan["gate_usd"]:
                print(f"[stop] cost gate: {new_cost / new:.4f} USD/cell > {plan['gate_usd']}")
                break
        if spent + WORST_CELL > a.cap_usd:
            print(f"[stop] cap: spent {spent:.4f} + worst cell {WORST_CELL} > {a.cap_usd}")
            break
        new += 1
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
        new_cost += row.get("cost_usd") or 0.0
        out_file.write_text(
            json.dumps({"plan": a.plan, "model": a.model, **extra, "rows": rows}, indent=1) + "\n"
        )
        print(
            f"[cell] {sk} b{b} s{s} {arm}: cost={row.get('cost_usd')} spent={spent:.4f}"
            f"{' INFRA' if 'infra_error' in row else ''}",
            flush=True,
        )
        infra_new += "infra_error" in row
        if stop := health_stop(row, new, infra_new):
            print(f"[stop] {stop}")
            break
    print(f"[done] {len(rows)} cells, group spent {spent:.4f} USD")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
