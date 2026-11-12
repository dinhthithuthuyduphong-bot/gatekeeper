"""Fetch metadata of the standard benchmarks (TODO.md section 6.1, Phase 4 'Chon du lieu').

Runs in GitHub Actions (HuggingFace is not reachable from every dev machine). Only metadata is
kept: instance_id, repo, version, created_at and test counts; no code or patches.

Outputs:
  data/benchmarks/<name>.csv     one row per task (slim)
  data/benchmarks/summary.json   per-benchmark and per-(repo, version) counts, repo overlaps
"""

from __future__ import annotations

import csv
import json
import sys
import traceback
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from gatekeeper.patches import edit_patterns, parse_patch

OUT = Path("data/benchmarks")

# name -> list of (hf_dataset_id, split) candidates, first that loads wins
SOURCES = {
    "swe-bench": [("princeton-nlp/SWE-bench", "test"), ("SWE-bench/SWE-bench", "test")],
    "swe-bench-verified": [
        ("princeton-nlp/SWE-bench_Verified", "test"),
        ("SWE-bench/SWE-bench_Verified", "test"),
    ],
    "swe-gym": [("SWE-Gym/SWE-Gym", "train")],
    "swe-bench-live": [
        ("SWE-bench-Live/SWE-bench-Live", "full"),
        ("SWE-bench-Live/SWE-bench-Live", "test"),
        ("SWE-bench-Live/SWE-bench-Live", "verified"),
        ("SWE-bench-Live/SWE-bench-Live", "lite"),
    ],
    "swe-smith": [("SWE-bench/SWE-smith", "train")],
}
KEEP_ROWS = {"swe-bench", "swe-bench-verified", "swe-gym", "swe-bench-live"}  # smith: summary only


def _count_tests(v) -> int:
    if v is None:
        return 0
    if isinstance(v, str):
        try:
            v = json.loads(v)
        except json.JSONDecodeError:
            return 0
    return len(v) if isinstance(v, (list, tuple)) else 0


def load(name: str):
    from datasets import load_dataset

    errors = []
    for ds_id, split in SOURCES[name]:
        try:
            ds = load_dataset(ds_id, split=split)
            return ds_id, split, ds, errors
        except Exception as exc:  # noqa: BLE001 - record and try the next candidate
            errors.append(f"{ds_id}:{split}: {type(exc).__name__}: {str(exc)[:200]}")
    return None, None, None, errors


def slim_rows(ds) -> list[dict]:
    cols = set(ds.column_names)
    rows = []
    for r in ds:
        rows.append(
            {
                "instance_id": r.get("instance_id", ""),
                "repo": r.get("repo", "") or "",
                "version": str(r.get("version", "") or ""),
                "created_at": str(r.get("created_at", "") or "")[:10],
                "n_fail_to_pass": _count_tests(r.get("FAIL_TO_PASS"))
                if "FAIL_TO_PASS" in cols
                else "",
                "n_pass_to_pass": _count_tests(r.get("PASS_TO_PASS"))
                if "PASS_TO_PASS" in cols
                else "",
                **_patch_meta(r.get("patch") if "patch" in cols else None),
            }
        )
    return rows


def _patch_meta(patch: str | None) -> dict:
    """Gold-patch metadata only (files, functions, edit-pattern families); no code is kept."""
    if not patch:
        return {"files": "", "functions": "", "n_added": "", "n_removed": "", "patterns": ""}
    p = parse_patch(patch)
    return {
        "files": ";".join(p.files),
        "functions": ";".join(sorted(p.functions)),
        "n_added": len(p.added),
        "n_removed": len(p.removed),
        "patterns": ";".join(sorted(edit_patterns(p))),
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    summary: dict = {"generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    repos_by: dict[str, set[str]] = {}
    for name in SOURCES:
        ds_id, split, ds, errors = load(name)
        if ds is None:
            summary[name] = {"status": "failed", "errors": errors}
            print(f"[{name}] FAILED: {errors}")
            continue
        rows = slim_rows(ds)
        repos = Counter(r["repo"] for r in rows)
        scopes = Counter(f"{r['repo']}@{r['version']}" for r in rows if r["version"])
        dates = sorted(r["created_at"] for r in rows if r["created_at"])
        repos_by[name] = set(repos)
        summary[name] = {
            "status": "ok",
            "hf_id": ds_id,
            "split": split,
            "fingerprint": getattr(ds, "_fingerprint", ""),
            "n_tasks": len(rows),
            "n_repos": len(repos),
            "tasks_per_repo": dict(repos.most_common()),
            "n_repo_versions": len(scopes),
            "top_repo_versions": dict(scopes.most_common(40)),
            "created_at_range": [dates[0], dates[-1]] if dates else None,
            "load_warnings": errors,
        }
        if name == "swe-smith" and "problem_statement" in getattr(ds, "column_names", []):
            # section 32 (A7): tasks whose issue description is empty, per repository. Column access
            # only; no task text is stored.
            empty: Counter = Counter()
            for repo, ps in zip(ds["repo"], ds["problem_statement"], strict=True):
                empty[repo] += not (ps or "").strip()
            summary[name]["empty_problem_statement_per_repo"] = {
                r: int(empty[r]) for r in summary[name]["tasks_per_repo"]
            }
            summary[name]["n_empty_problem_statement"] = int(sum(empty.values()))
        if name in KEEP_ROWS:
            with (OUT / f"{name}.csv").open("w", newline="", encoding="utf-8") as fh:
                w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
                w.writeheader()
                w.writerows(rows)
        print(f"[{name}] {ds_id}:{split} tasks={len(rows)} repos={len(repos)}")

    names = list(repos_by)
    summary["repo_overlap"] = {
        f"{a}|{b}": sorted(repos_by[a] & repos_by[b])
        for i, a in enumerate(names)
        for b in names[i + 1 :]
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n")
    failed = [n for n in SOURCES if summary.get(n, {}).get("status") != "ok"]
    print("failed:", failed)
    # the core sources must load; optional ones may fail and are reported
    return 1 if {"swe-bench", "swe-bench-verified"} & set(failed) else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        traceback.print_exc()
        sys.exit(1)
