"""Combine the pairs of several stages of the SAME seed into one run file for the analysis
(E1 + its extension: python scripts/combine_runs.py g1-e1all-s41 g1-e1-s41 g1-e1x-s41).

Each pair keeps the exit statuses of ITS OWN stage ("status_with", "status_without"), because a
task can have a no-skill run in both stages (audit A40). A (skill, task) pair may appear in only
one stage: a duplicate stops the script. Writes results/pilot/<out>.json."""

from __future__ import annotations

import json
import sys
from pathlib import Path

RESULTS = Path("results/pilot")


def combine(runs: list[dict]) -> dict:
    names = [r.get("name") for r in runs]
    # merged_from: never counted as spending by the batch driver (pilot_spent_total)
    out: dict = {"combined_from": names, "merged_from": names, "skills": {}, "instances": []}
    seen: set[tuple[str, str]] = set()
    for r in runs:
        st = r.get("exit_status") or {}
        for sk, v in r.get("skills", {}).items():
            dst = out["skills"].setdefault(sk, {"pairs": []})
            for p in v["pairs"]:
                key = (sk, p["instance_id"])
                if key in seen:
                    raise SystemExit(f"pair {key} appears in two stages")
                seen.add(key)
                q = dict(p)
                q["status_with"] = (st.get(sk) or {}).get(p["instance_id"])
                q["status_without"] = (st.get("none") or {}).get(p["instance_id"])
                q["stage"] = r.get("name")
                tt = r.get("harness_test_timeout") or {}
                q["timeout_with"] = p["instance_id"] in tt.get(sk, [])
                q["timeout_without"] = p["instance_id"] in tt.get("none", [])
                dst["pairs"].append(q)
        out["instances"] += [i for i in r.get("instances", []) if i not in out["instances"]]
    out["pair_level_exit_status"] = True
    return out


def main() -> int:
    name, *parts = sys.argv[1:]
    runs = [json.loads((RESULTS / f"{p}.json").read_text()) for p in parts]
    out = combine(runs)
    out["name"] = name
    (RESULTS / f"{name}.json").write_text(json.dumps(out, indent=2) + "\n")
    print({sk: len(v["pairs"]) for sk, v in out["skills"].items()})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
