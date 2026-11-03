"""Check the raw-evidence branch against the results on main (docs/raw_archive.md).

  python scripts/verify_archive.py

For every archived batch: (1) the archive's SHA-256 equals the manifest; (2) its number of agent
trajectories equals the number of agent runs in results/pilot/<part>.json; (3) the result file on
this checkout still has the SHA-256 recorded when it was archived (a later edit is reported).
Withheld batches (unlicensed third-party text) are listed. Exit code 1 on a mismatch of (1) or (2).
"""

from __future__ import annotations

import hashlib
import io
import json
import subprocess
import sys
import tarfile
from pathlib import Path

BRANCH = "raw-archive"


def main() -> int:
    subprocess.run(["git", "fetch", "-q", "origin", BRANCH], check=True)

    def show(path: str) -> bytes:
        cmd = ["git", "show", f"origin/{BRANCH}:{path}"]
        return subprocess.run(cmd, check=True, capture_output=True).stdout

    manifest = json.loads(show("archive/MANIFEST.json"))
    bad, notes = [], []
    for part, e in sorted(manifest["batches"].items()):
        if "withheld" in e:
            notes.append(f"{part}: withheld ({e['withheld']})")
            continue
        blob = show(e["path"])
        if hashlib.sha256(blob).hexdigest() != e["sha256"]:
            bad.append(f"{part}: archive SHA-256 differs from the manifest")
            continue
        with tarfile.open(fileobj=io.BytesIO(blob), mode="r:gz") as tar:
            n_traj = sum(1 for m in tar.getmembers() if m.name.endswith(".traj.json"))
        if not e.get("result_file"):
            notes.append(f"{part}: {e.get('result_status')} ({n_traj} trajectories archived)")
            continue
        res = Path(e["result_file"])
        if res.exists():
            d = json.loads(res.read_text())
            runs = sum((u.get("runs") or 0) for u in (d.get("usage") or {}).values())
            if runs and n_traj != runs:
                bad.append(f"{part}: {n_traj} trajectories archived, {runs} runs in {res}")
            if hashlib.sha256(res.read_bytes()).hexdigest() != e["result_sha256"]:
                notes.append(f"{part}: {res} changed after archiving")
        else:
            notes.append(f"{part}: {res} not in this checkout")
    n = len(manifest["batches"])
    print(f"{n} batches; {len(bad)} mismatches; {len(notes)} notes")
    for x in notes:
        print("  note:", x)
    for x in bad:
        print("  FAIL:", x)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
