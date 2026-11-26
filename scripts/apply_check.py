#!/usr/bin/env python3
"""Could SWE-smith's patch-apply fallback (issue 256) have touched our grades? (R-108; 0 USD)

SWE-smith grades a patch on the task branch's HEAD~1 (the "Bug Patch" commit, since every branch
we use ends with "Remove F2P Tests") and applies it with a chain of commands; only when the first,
`git apply --verbose`, fails does the chain fall back to `git apply --reject` and then
`patch --fuzz`, the step issue 256 reports can undo hunks. This script checks every saved patch of
the twelve decisions of Table 2 with `git apply --check` against that commit, in a temporary index
of the bare mirror (no checkout, no container). A patch that passes the check is applied by the
first command, so the fallback never runs for it.

  python scripts/apply_check.py --mirrors <dir of <repo>.git mirrors> --trial <trial worktree> \
      --out results/apply_check.json
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
from collections import Counter
from pathlib import Path

MIRRORS = {
    "pallets__jinja.ada0a9a6": "pallets__jinja.ada0a9a6.git",
    "blevesearch__bleve.f2876b5e": "blevesearch__bleve.f2876b5e.git",
    "pygments__pygments.27649ebb": "pygments__pygments.27649ebb.git",
}


def arm_file(name: str, trial: Path) -> Path:
    for base in (Path("results"), trial / "results"):
        p = base / f"{name}.json"
        if p.exists():
            return p
    raise FileNotFoundError(name)


def bug_commit(mirror: Path, iid: str) -> str:
    """The commit SWE-smith grades on: HEAD~1 of the task branch, checked to be "Bug Patch"."""
    out = subprocess.run(
        ["git", "-C", str(mirror), "log", "-2", "--format=%H%x09%s", f"refs/heads/{iid}"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()
    (tip, tip_msg), (parent, parent_msg) = (x.split("\t", 1) for x in out)
    assert tip_msg == "Remove F2P Tests" and parent_msg == "Bug Patch", (iid, out)
    return parent


def check(mirror: Path, commit: str, patch: str) -> bool:
    with tempfile.TemporaryDirectory() as d:
        env = dict(os.environ, GIT_INDEX_FILE=str(Path(d) / "index"))
        subprocess.run(["git", "-C", str(mirror), "read-tree", commit], env=env, check=True)
        r = subprocess.run(
            ["git", "-C", str(mirror), "apply", "--cached", "--check", "-"],
            input=patch,
            text=True,
            capture_output=True,
            env=env,
        )
        return r.returncode == 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mirrors", type=Path, required=True)
    ap.add_argument("--trial", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    decisions = json.loads(Path("results/s42_end_of_pool.json").read_text())["decisions"]
    arms = sorted({arm for d in decisions.values() for arm in d["run_structure"]["arms"]})
    per_arm, failed = {}, []
    for arm in arms:
        runs = json.loads(arm_file(arm, a.trial).read_text())["runs"]
        c = Counter()
        for r in runs:
            patch = r.get("patch") or ""
            if not patch.strip():
                c["empty"] += 1
                # issue 252's symptom: an empty patch graded resolved
                c["empty_resolved"] += bool((r.get("S") or {}).get("resolved"))
                continue
            repo = next(k for k in MIRRORS if r["instance_id"].startswith(k))
            mirror = a.mirrors / MIRRORS[repo]
            ok = check(mirror, bug_commit(mirror, r["instance_id"]), patch)
            resolved = bool((r.get("S") or {}).get("resolved"))
            c["applies" if ok else "needs_fallback"] += 1
            if not ok:
                failed.append({"arm": arm, "instance_id": r["instance_id"], "resolved_S": resolved})
        per_arm[arm] = dict(c)
    total = Counter()
    for c in per_arm.values():
        total.update(c)
    out = {"per_arm": per_arm, "total": dict(total), "needs_fallback": failed}
    a.out.write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({"total": out["total"], "needs_fallback": len(failed)}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
