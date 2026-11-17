"""Commit dates of the third-party commits cited in paper/refs.bib (0 USD).

  python scripts/commit_dates.py --out data/commit_dates.json

For every raw.githubusercontent.com URL pinned to a full commit hash in configs/sources.json, fetch
that one commit object (depth 1) from the public repository into a temporary bare repository and
record its committer date. scripts/make_bib.py takes the year of a pinned source file from here.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import tempfile
from pathlib import Path

PIN = re.compile(r"https://raw\.githubusercontent\.com/([^/]+/[^/]+)/([0-9a-f]{40})/")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    src = json.loads(Path("configs/sources.json").read_text())["sources"]
    pins = sorted({m.groups() for s in src for u in s["urls"] for m in [PIN.match(u)] if m})
    out = {}
    for repo, sha in pins:
        with tempfile.TemporaryDirectory() as d:
            subprocess.run(["git", "init", "-q", "--bare", d], check=True)
            url = f"https://github.com/{repo}.git"
            subprocess.run(["git", "-C", d, "fetch", "-q", "--depth", "1", url, sha], check=True)
            date = subprocess.run(
                ["git", "-C", d, "log", "-1", "--format=%cI", sha],
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()
        out[sha] = {"repository": repo, "committer_date": date}
        print(repo, sha[:7], date)
    a.out.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
