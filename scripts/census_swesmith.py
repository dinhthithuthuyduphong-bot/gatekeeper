"""Section 25 census (0 USD): SWE-smith task counts per repository, from committed metadata.

Reads data/benchmarks/summary.json (Data snapshots workflow) and the benchmark CSVs; counts how
many SWE-smith tasks each repository has, how many repositories reach given task counts, and
which repositories also have natural tasks (SWE-bench, SWE-bench-Live, SWE-Gym). No outcome of
any agent run is read. Output: results/swesmith_census.json.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

BENCH = Path("data/benchmarks")
OUT = Path("results/swesmith_census.json")
csv.field_size_limit(2**31 - 1)


def smith_repo(key: str) -> str:
    """'swesmith/owner__name.hash' -> 'owner/name'."""
    name = key.split("/", 1)[1].rsplit(".", 1)[0]
    return name.replace("__", "/", 1)


def natural_counts(name: str) -> Counter:
    c: Counter = Counter()
    with (BENCH / f"{name}.csv").open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            c[r["repo"]] += 1
    return c


def census(smith: dict[str, int], natural: dict[str, Counter], thresholds: list[int]) -> dict:
    per_repo = Counter()
    for k, v in smith.items():
        per_repo[smith_repo(k)] += v
    vals = sorted(per_repo.values())
    out = {
        "n_tasks": sum(vals),
        "n_repos": len(vals),
        "median_tasks_per_repo": vals[len(vals) // 2]
        if len(vals) % 2
        else (vals[len(vals) // 2 - 1] + vals[len(vals) // 2]) / 2,
        "repos_with_at_least": {str(t): sum(v >= t for v in vals) for t in thresholds},
        "overlap_with_natural": {},
    }
    for name, c in natural.items():
        out["overlap_with_natural"][name] = sorted(
            (
                {"repo": r, "smith_tasks": per_repo[r], "natural_tasks": n}
                for r, n in c.items()
                if r in per_repo
            ),
            key=lambda x: -x["natural_tasks"],
        )
    return out


def main() -> int:
    summary = json.loads((BENCH / "summary.json").read_text())
    smith = summary["swe-smith"]
    natural = {n: natural_counts(n) for n in ("swe-bench", "swe-bench-live", "swe-gym")}
    # thresholds are the registered n_min values of section 24 (K = 1, 100, 3991) and 100/300 for
    # description only
    res = census(smith["tasks_per_repo"], natural, thresholds=[11, 22, 31, 100, 300])
    res["source"] = {k: smith[k] for k in ("hf_id", "split", "fingerprint", "n_tasks", "n_repos")}
    OUT.write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps({k: res[k] for k in ("n_tasks", "n_repos", "repos_with_at_least")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
