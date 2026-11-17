"""Run manifest for the replication package (F2 of docs/todo_ease_revision.md; 0 USD).

  python scripts/package_manifest.py --out results/package_manifest.json

For every run file results/*.json that holds a "runs" list: the model string recorded by the
runner, seed, number of task runs, sha256 of the sorted task ids, sha256 of the file, and the
first time the file was published on branch pilot-snapshots (author date; absent if the file was
never published there). For every skill text (docs/skills/**, results/*best_skills*.txt): sha256.
The grading results of each task run are in its record: "S" (strict grader, field "resolved")
and "L" (lenient grader, field "passed"), read by passed() in scripts/s25_ab.py.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def first_published(path: str) -> str | None:
    out = subprocess.run(
        [
            "git",
            "log",
            "--reverse",
            "--diff-filter=A",
            "--format=%aI",
            "origin/pilot-snapshots",
            "--",
            path,
        ],
        capture_output=True,
        text=True,
        check=False,
    ).stdout.split()
    return out[0] if out else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    runs = []
    for p in sorted(Path("results").glob("*.json")):
        try:
            d = json.loads(p.read_text())
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        if not isinstance(d, dict) or not isinstance(d.get("runs"), list):
            continue
        ids = sorted(str(r.get("instance_id")) for r in d["runs"] if isinstance(r, dict))
        runs.append(
            {
                "file": str(p),
                "model": d.get("model"),
                "seed": d.get("seed"),
                "n_task_runs": len(ids),
                "task_ids_sha256": sha("\n".join(ids).encode()),
                "skills_chars": d.get("skills_chars"),
                "file_sha256": sha(p.read_bytes()),
                "first_published_utc": first_published(str(p)),
            }
        )
    skills = [
        {"file": str(p), "sha256": sha(p.read_bytes())}
        for p in sorted(
            [*Path("docs/skills").rglob("*"), *Path("results").glob("*best_skills*.txt")]
        )
        if p.is_file()
    ]
    a.out.write_text(json.dumps({"runs": runs, "skills": skills}, indent=1) + "\n")
    print(f"{len(runs)} run files, {len(skills)} skill files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
