"""'Model unchanged' check before pairing new skill runs with E2's no-skill runs
(docs/preregistration_main.md sections 5 and 11). Paid (small): two first-turn calls per
(task, seed).

For every E2 no-skill trajectory: replay the agent's FIRST call (system + instance message, same
model config and seed, through mini-swe-agent's own LitellmModel, so the request incl. the bash
tool is identical), twice. A seed passes only if, for EVERY task, both replays equal the recorded
first answer (content and actions) and the API reports the same model name.

  python scripts/stationarity_check.py --trajs <dir with E2 none-arm .traj.json> --cap-usd 1.0
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

PRICES = json.loads(Path("configs/models/vertex_gemini.json").read_text())["models"]


def first_turn(traj: dict) -> tuple[list[dict], dict]:
    msgs = traj["messages"]
    assert (
        msgs[0]["role"] == "system" and msgs[1]["role"] == "user" and msgs[2]["role"] == "assistant"
    )
    return msgs[:2], msgs[2]


def signature(msg: dict) -> tuple[str, tuple[str, ...], str]:
    ex = msg.get("extra", {})
    acts = tuple(str(a.get("command", a)) for a in ex.get("actions", []))
    return (msg.get("content") or "", acts, (ex.get("response") or {}).get("model", ""))


def cost(usage: dict, spec: dict) -> float:
    return (
        usage.get("prompt_tokens", 0) * spec["usd_per_mtok_in"]
        + usage.get("completion_tokens", 0) * spec["usd_per_mtok_out"]
    ) / 1e6


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--trajs", type=Path, required=True)
    ap.add_argument("--cap-usd", type=float, required=True)
    ap.add_argument("--dry", action="store_true", help="reconstruct only, no model call")
    a = ap.parse_args()
    if subprocess.run(
        [sys.executable, "scripts/preflight.py", "--ci"], capture_output=True
    ).returncode:
        raise SystemExit(7)  # gate (CLAUDE.md)
    from minisweagent.models import get_model

    files = sorted(a.trajs.rglob("*.traj.json"))
    spec = next(v for v in PRICES.values() if v["litellm_name"].endswith("flash-lite"))
    spent, rows = 0.0, []
    for f in files:
        seed = int(re.search(r"g2-e2-s(\d+)-", str(f)).group(1))
        traj = json.loads(f.read_text())
        msgs, rec = first_turn(traj)
        row = {
            "instance_id": traj["instance_id"],
            "seed": seed,
            "recorded_model": signature(rec)[2],
        }
        if a.dry:
            rows.append(row)
            continue
        cfg = dict(traj["info"]["config"]["model"])
        cfg["litellm_model_registry"] = None
        cfg["cost_tracking"] = "ignore_errors"
        model = get_model(config=cfg)
        sigs = []
        for _ in range(2):
            if spent >= a.cap_usd:
                raise SystemExit(f"cap {a.cap_usd} USD reached after {len(rows)} tasks")
            out = model.query(msgs)
            spent += cost(out["extra"]["response"].get("usage") or {}, spec)
            sigs.append(signature(out))
        row.update(
            {
                "replays_identical": sigs[0][:2] == sigs[1][:2],
                "equals_recorded": all(s[:2] == signature(rec)[:2] for s in sigs),
                "model_same": all(s[2] == row["recorded_model"] for s in sigs),
            }
        )
        rows.append(row)
    by_seed = defaultdict(list)
    for r in rows:
        by_seed[r["seed"]].append(r)
    verdict = {
        s: (
            None
            if a.dry
            else all(
                r["replays_identical"] and r["equals_recorded"] and r["model_same"] for r in rs
            )
        )
        for s, rs in sorted(by_seed.items())
    }
    out = {
        "n": len(rows),
        "spent_usd_estimate": round(spent, 4),
        "seed_passes": verdict,
        "rows": rows,
    }
    name = "stationarity_e2_dry.json" if a.dry else "stationarity_e2.json"
    Path("results", name).write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "rows"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
