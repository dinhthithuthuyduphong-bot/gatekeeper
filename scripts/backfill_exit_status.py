"""Add the agent exit status per arm and task to batch result files written before run_pilot.py
recorded it (needed for the intercurrent-event analyses of preregistration_e1.md section 3).

  python scripts/backfill_exit_status.py g1-e1-s41

Reads runs/<part>/<arm>/agent/<iid>/<iid>.traj.json (the trajectories themselves, unchanged).
A part whose trajectory for some (arm, task) is missing is left untouched and reported."""

from __future__ import annotations

import json
import sys
from pathlib import Path

RESULTS = Path("results/pilot")


def statuses(part: str, d: dict) -> dict[str, dict[str, str | None]] | None:
    arms = ["none", *d.get("skills", {}).keys()]
    out: dict[str, dict[str, str | None]] = {}
    for arm in arms:
        agent = Path("runs") / part / arm / "agent"
        if not agent.is_dir():
            continue
        for tdir in sorted(p for p in agent.iterdir() if p.is_dir()):
            traj = tdir / f"{tdir.name}.traj.json"
            if not traj.exists():
                return None
            info = json.loads(traj.read_text()).get("info") or {}
            out.setdefault(arm, {})[tdir.name] = info.get("exit_status")
    # every scored pair must have both statuses
    for sk, v in d.get("skills", {}).items():
        for p in v["pairs"]:
            if p["instance_id"] not in out.get(sk, {}) or p["instance_id"] not in out.get(
                "none", {}
            ):
                return None
    return out


def main() -> int:
    name = sys.argv[1]
    for f in sorted(RESULTS.glob(f"{name}-p[0-9][0-9].json")):
        d = json.loads(f.read_text())
        if "exit_status" in d:
            continue
        st = statuses(f.stem, d)
        if st is None:
            print(f"{f.stem}: trajectories incomplete, left unchanged")
            continue
        d["exit_status"] = st
        d["exit_status_backfilled_from"] = f"runs/{f.stem}/*/agent/*/*.traj.json"
        f.write_text(json.dumps(d, indent=2) + "\n")
        n = sum(len(v) for v in st.values())
        print(f"{f.stem}: {n} statuses added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
