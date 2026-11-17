"""Registration timeline (F1 of docs/todo_ease_revision.md; 0 USD).

  python scripts/registration_timeline.py --out results/registration_timeline.json

For every section of docs/preregistration_main.md ("## NN. ...") and every execution note in it
("Ghi chú thực thi NN-M"), the first commit that added the heading line (git log -S), and, for the
sections whose runs published result files results/sNN*.json on the pilot-snapshots branch, the
first publication of such a file. A reader can check that each rule was committed before the data
it applies to. Commit hashes are kept; author names and messages are not.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

DOC = "docs/preregistration_main.md"


def git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout


def first_commit_with(line: str) -> dict | None:
    out = git("log", "--reverse", "--format=%H %cI", f"-S{line}", "--", DOC).splitlines()
    if not out:
        return None
    sha, t = out[0].split()
    return {"commit": sha[:12], "time_utc": t}


def first_result(sec: int) -> dict | None:
    """First addition of a non-dry-run result file of the section on pilot-snapshots (author date:
    the committer dates were reset when the branch was rewritten)."""
    specs = [f"results/s{sec}_*.json", f"results/s{sec}bleve_*.json", f"results/s{sec}pyg*.json"]
    out = git(
        "log",
        "--reverse",
        "--diff-filter=A",
        "--format=@%aI",
        "--name-only",
        "origin/pilot-snapshots",
        "--",
        *specs,
    )
    t = None
    for line in out.splitlines():
        if line.startswith("@"):
            t = line[1:]
        elif line.strip() and "dry" not in line:
            return {"file": line.strip(), "time_utc": t}
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    text = Path(DOC).read_text()
    rows = []
    for line in text.splitlines():
        m = re.match(r"^## (\d+)\. ", line)
        n = re.search(r"Ghi chú thực thi (\d+)-(\d+)", line)
        if m:
            sec = int(m.group(1))
            rows.append(
                {
                    "kind": "section",
                    "id": f"§{sec}",
                    "heading": line[3:90],
                    "registered": first_commit_with(line),
                    "first_result_published": first_result(sec) if sec >= 25 else None,
                }
            )
        elif n and (line.startswith("**Ghi chú") or line.startswith("### Ghi chú")):
            rows.append(
                {
                    "kind": "execution note",
                    "id": f"{n.group(1)}-{n.group(2)}",
                    "heading": line.strip("*# ")[:90],
                    "registered": first_commit_with(line),
                }
            )
    bad = [
        r["id"]
        for r in rows
        if r.get("first_result_published")
        and r["registered"]
        and r["first_result_published"]["time_utc"] < r["registered"]["time_utc"]
    ]
    out = {"rows": rows, "sections_with_results_before_registration": bad}
    a.out.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")
    print(f"{len(rows)} rows; results published before registration: {bad}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
