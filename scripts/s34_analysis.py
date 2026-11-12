"""Section 34 analysis (docs/preregistration_main.md, registered before the run; descriptive).

0 USD.
  python scripts/s34_analysis.py [--prefix s34dry]

Second agent model on the 34 jinja test tasks without a problem statement, environment as shipped,
two arms (no skill, original skill). Reports, per arm: tasks run, resolved under the benchmark's
scorer S, runs with the flags M1 (history command) and M2 ("Bug Patch" in an observation) of
section 32a, and the resolved count among flagged runs. No test is run (n = 34, base rate near 0).
The pilot (first 5 tasks) and the rest are one stream. Writes results/<prefix>_analysis.json.
"""

from __future__ import annotations

import argparse
import gzip
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from s32_analysis import flags  # noqa: E402

R = Path("results")
PARTS = ("pilot", "rest")
# Exploratory, added after the results were seen (not registered; reported as such):
# commands that display the content of a commit rather than only its message.
OPEN_COMMIT = re.compile(
    r"git\s+(show|diff\s+\S*(HEAD~|HEAD\^|[0-9a-f]{7})|revert|checkout\s+HEAD~|log\s+-p"
    r"|log\s+.*--patch|format-patch)"
)
CMD = re.compile(r"```(?:bash|mswea_bash_command)?\n(.*?)```", re.S)


def commands(msgs: list) -> list[str]:
    """Last fenced command of each assistant message, in order."""
    out = []
    for m in msgs:
        if m.get("role") != "assistant":
            continue
        c = m.get("content")
        if isinstance(c, list):
            c = " ".join(x.get("text", "") for x in c if isinstance(x, dict))
        found = CMD.findall(str(c))
        out += found[-1:]
    return out


def arm(prefix: str, name: str) -> dict:
    runs, traces, stopped, spent = [], {}, {}, 0.0
    for part in PARTS:
        f = R / f"{prefix}_{name}_{part}.json"
        if not f.exists():
            continue
        d = json.loads(f.read_text())
        runs += d["runs"]
        spent += d.get("spent_usd", 0.0)
        if d.get("stopped"):
            stopped[part] = d["stopped"]
        t = f.with_suffix(".traces.jsonl.gz")
        if t.exists():
            for line in gzip.open(t, "rt"):
                rec = json.loads(line)
                traces[rec["instance_id"]] = rec.get("messages")
    ids = [r["instance_id"] for r in runs]
    if len(ids) != len(set(ids)):
        raise SystemExit(f"{name}: a task appears in both parts")
    out = {
        "runs": len(runs),
        "infra_error": sum("infra_error" in r for r in runs),
        "crashed": sum(bool(r.get("crashed")) for r in runs),
        "stopped": stopped,
        "spent_usd": spent,
        "resolved": 0,
        "M1": 0,
        "M2": 0,
        "resolved_with_M2": 0,
        "runs_without_trace": 0,
        "exploratory_first_command_git_log": 0,
        "exploratory_opened_commit_content": 0,
    }
    for r in runs:
        ok = bool((r.get("S") or {}).get("resolved"))
        out["resolved"] += ok
        msgs = traces.get(r["instance_id"])
        if not msgs:
            out["runs_without_trace"] += 1
            continue
        m1, m2 = flags(msgs)
        out["M1"] += bool(m1)
        out["M2"] += bool(m2)
        out["resolved_with_M2"] += bool(m2) and ok
        cmds = commands(msgs)
        out["exploratory_first_command_git_log"] += bool(cmds) and bool(
            re.search(r"git\s+log", cmds[0])
        )
        out["exploratory_opened_commit_content"] += any(OPEN_COMMIT.search(c) for c in cmds)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prefix", default="s34")
    a = ap.parse_args()
    out = {"none": arm(a.prefix, "none"), "skill": arm(a.prefix, "skill")}
    out["reference_agent_of_the_study"] = {"skill_resolved": "15/34", "skill_M2": "34/34"}
    (R / f"{a.prefix}_analysis.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
