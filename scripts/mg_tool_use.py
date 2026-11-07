"""MemGovern cell, manipulation check: did the agent call the memory tools? (0 USD)

  python scripts/mg_tool_use.py --runs <dir with runs/mg*-s41-*/memgovern/agent/*/*.traj.json>

Counts, per memgovern-arm trajectory (arm versions 1 and 2, branch `trial`, note M-4), whether
any ASSISTANT message - its text or its tool calls - contains `exp_search` or `exp_read`. System and
user messages are excluded, because the instructions themselves name the tools. Writes
results/mg_tool_use.json.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

TOOLS = ("exp_search", "exp_read")


def used(traj: dict) -> bool:
    for m in traj.get("messages", []):
        if m.get("role") != "assistant":
            continue
        blob = json.dumps({k: v for k, v in m.items() if k != "role"})
        if any(t in blob for t in TOOLS):
            return True
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=Path, required=True)
    a = ap.parse_args()
    out = {}
    for f in sorted(a.runs.glob("runs/mg*-s41-*/memgovern/agent/*/*.traj.json")):
        version = "v2" if f.parts[-5].startswith("mg2-") else "v1"
        out.setdefault(version, {})[f.stem.removesuffix(".traj")] = used(json.loads(f.read_text()))
    summary = {v: {"tasks": len(d), "used": sum(d.values())} for v, d in out.items()}
    Path("results/mg_tool_use.json").write_text(
        json.dumps({"summary": summary, "per_task": out}, indent=1) + "\n"
    )
    print(json.dumps(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
