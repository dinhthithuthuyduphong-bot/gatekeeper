"""Section 24 survey: can an edit-program skill induced from training fixes reach target tasks?

Registered in docs/preregistration_main.md section 24 before any output of this script existed.
Costs nothing: no model call, no agent run.

The original paper defines a skill's procedure as a "parameterised edit program (AST rewrites
plus shell steps) induced from successful trajectories". A parameterised edit program writes a
fixed shape of code with parameters for names and literals. So a single such skill can produce
the gold fix of a target task only if every edited block of that fix has the token shape of an
edit the skill was induced from. This script counts, for SWE-bench-style test tasks, how often
that necessary condition holds when the skills may come from any SWE-Gym training fix
(an upper bound: location and parameters are not checked).

Definitions (section 24):
* change block: maximal run of removed/added lines in a non-test `.py` file (`change_blocks`).
* normalised line: lexed; Python keywords (incl. True/False/None) and operators kept, every other
  name -> ID, number -> NUM, string -> STR, comment dropped; empty result -> line dropped.
* block shape: (normalised removed lines, normalised added lines); blocks with both empty dropped.
* single-skill coverage (primary): the task has >= 1 block, all its blocks share one shape h, and
  h occurs among training blocks of >= k distinct training repositories (k = 1 primary).
* library coverage (secondary): every block shape of the task occurs in training (k = 1).
* cell: (shape h, target repository); pooled cell: shape h over all target repositories.
* n_min(K): fewest consecutive trials with Z = -1 (the skill fixes every task) after which the
  registered e-process (gatekeeper.eprocess, theta, c) reaches E >= K / alpha.

Usage (GitHub Actions, HuggingFace reachable):
  python scripts/survey_edit_shapes.py --alpha 0.025 --theta 0 --c 0.5 \
      --out data/survey/edit_shapes.json
Offline dry run on exported rows:
  ... --train-jsonl a.jsonl --test-jsonl b.jsonl
"""

from __future__ import annotations

import argparse
import hashlib
import json
import keyword
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from gatekeeper.eprocess import BettingEProcess
from gatekeeper.patches import change_blocks

SPLIT = Path("data/splits/split_v0.json")
KS = (1, 2, 3)  # k = 1 primary; 2 and 3 descriptive only (section 24)
TOP = 25

_TOKEN = re.compile(
    r"""(?P<str>[rRbBuUfF]{0,2}(?P<q>\"\"\"|'''|"|')(?:\\.|(?!(?P=q)).)*(?P=q)?)"""
    r"|(?P<num>0[xXoObB][0-9a-fA-F_]+|\d[\d_]*(?:\.\d*)?(?:[eE][+-]?\d+)?[jJ]?|\.\d+(?:[eE][+-]?\d+)?[jJ]?)"
    r"|(?P<name>[A-Za-z_]\w*)"
    r"|(?P<op>\S)"
)
_KEEP = set(keyword.kwlist) | set(getattr(keyword, "softkwlist", []))


def normalise(line: str) -> str:
    toks: list[str] = []
    for m in _TOKEN.finditer(line):
        if m.group("str") is not None:
            toks.append("STR")
        elif m.group("num") is not None:
            toks.append("NUM")
        elif m.group("name") is not None:
            toks.append(m.group("name") if m.group("name") in _KEEP else "ID")
        else:
            op = m.group("op")
            if op == "#":
                break
            toks.append(op)
    return " ".join(toks)


Shape = tuple[tuple[str, ...], tuple[str, ...]]


def block_shapes(patch: str) -> list[Shape]:
    shapes = []
    for _path, rem, add in change_blocks(patch):
        r = tuple(x for x in (normalise(s) for s in rem) if x)
        a = tuple(x for x in (normalise(s) for s in add) if x)
        if r or a:
            shapes.append((r, a))
    return shapes


def shape_id(h: Shape) -> str:
    return hashlib.sha256(json.dumps(h).encode()).hexdigest()[:12]


def n_min(K: int, alpha: float, theta: float, c: float, cap: int) -> int | None:
    """Fewest all-helped trials (Z = -1) for the registered e-process to reach E >= K/alpha."""
    e = BettingEProcess(theta=theta, alpha=alpha / K, c=c)
    for n in range(1, cap + 1):
        e.update(-1.0)
        if e.crossed:
            return n
    return None


def survey(train: list[dict], test: list[dict], alpha: float, theta: float, c: float) -> dict:
    repos_of: dict[Shape, set[str]] = defaultdict(set)
    n_train_blocks = 0
    for r in train:
        for h in block_shapes(r["patch"]):
            repos_of[h].add(r["repo"])
            n_train_blocks += 1

    n_test = len(test)
    no_blocks = 0
    single = {k: [] for k in KS}  # (instance_id, repo, shape)
    library = 0
    for r in test:
        hs = block_shapes(r["patch"])
        if not hs:
            no_blocks += 1
            continue
        if all(len(repos_of.get(h, ())) >= 1 for h in hs):
            library += 1
        if len(set(hs)) == 1:
            h = hs[0]
            for k in KS:
                if len(repos_of.get(h, ())) >= k:
                    single[k].append((r["instance_id"], r["repo"], h))

    def cells(rows: list[tuple[str, str, Shape]], pooled: bool) -> dict:
        cnt: Counter = Counter()
        for _iid, repo, h in rows:
            cnt[(h, None if pooled else repo)] += 1
        K = len(cnt)
        nm = n_min(K, alpha, theta, c, cap=10_000) if K else None
        top = cnt.most_common(TOP)
        return {
            "K": K,
            "n_min": nm,
            "max_count": top[0][1] if top else 0,
            "cells_reaching_n_min": sum(1 for v in cnt.values() if nm is not None and v >= nm),
            "passes": bool(nm is not None and top and top[0][1] >= nm),
            "top": [
                {
                    "shape_id": shape_id(h),
                    "repo": repo,
                    "count": v,
                    "train_repos": len(repos_of[h]),
                    "removed": list(h[0]),
                    "added": list(h[1]),
                }
                for (h, repo), v in top
            ],
        }

    def frac(x: int) -> float:
        return x / n_test if n_test else 0.0

    out = {
        "params": {"alpha": alpha, "theta": theta, "c": c, "k_values": list(KS)},
        "n_train_tasks": len(train),
        "n_train_repos": len({r["repo"] for r in train}),
        "n_train_blocks": n_train_blocks,
        "n_train_shapes": len(repos_of),
        "n_test_tasks": n_test,
        "n_test_repos": len({r["repo"] for r in test}),
        "test_tasks_without_py_blocks": no_blocks,
        "library_coverage": {"count": library, "share": frac(library)},
        "single_skill_coverage": {
            str(k): {"count": len(single[k]), "share": frac(len(single[k]))} for k in KS
        },
        "per_repo_cells_k1": cells(single[1], pooled=False),
        "pooled_cells_k1": cells(single[1], pooled=True),
    }
    out["decision"] = {
        "per_repo": "pass" if out["per_repo_cells_k1"]["passes"] else "fail",
        "pooled": "pass" if out["pooled_cells_k1"]["passes"] else "fail",
        "proceed_to_step_2": out["per_repo_cells_k1"]["passes"] or out["pooled_cells_k1"]["passes"],
    }
    return out


def _rows_from_hf(name: str, ids: set[str] | None, repos: set[str]) -> tuple[list[dict], dict]:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from fetch_benchmarks import load  # noqa: PLC0415 - only needed with HuggingFace access

    ds_id, split, ds, errors = load(name)
    if ds is None:
        raise SystemExit(f"cannot load {name}: {errors}")
    rows = []
    for r in ds:
        if ids is not None and r["instance_id"] not in ids:
            continue
        if repos and r["repo"] not in repos:
            continue
        rows.append({"instance_id": r["instance_id"], "repo": r["repo"], "patch": r["patch"]})
    rev = getattr(ds, "_fingerprint", None)
    return rows, {"hf_id": ds_id, "split": split, "fingerprint": rev, "n": len(rows)}


def _jsonl(p: str) -> list[dict]:
    return [json.loads(x) for x in Path(p).read_text(encoding="utf-8").splitlines() if x.strip()]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--alpha", type=float, required=True)
    ap.add_argument("--theta", type=float, required=True)
    ap.add_argument("--c", type=float, required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--train-jsonl")
    ap.add_argument("--test-jsonl")
    a = ap.parse_args()

    split = json.loads(SPLIT.read_text())
    sources: dict = {"split_sha256_16": split["sha256_16"]}
    if a.train_jsonl and a.test_jsonl:
        train, test = _jsonl(a.train_jsonl), _jsonl(a.test_jsonl)
        sources["mode"] = "offline"
    else:
        train_repos = set(split["train_repos"])
        train, sources["swe-gym"] = _rows_from_hf("swe-gym", None, train_repos)
        test_ids = set(split["test_instance_ids"])
        test, seen = [], set()
        for name in ("swe-bench", "swe-bench-verified", "swe-bench-live"):
            rows, sources[name] = _rows_from_hf(name, test_ids, set())
            for r in rows:
                if r["instance_id"] not in seen:
                    seen.add(r["instance_id"])
                    test.append(r)
        missing = test_ids - seen
        sources["test_ids_missing"] = len(missing)
        if missing:
            raise SystemExit(f"{len(missing)} test instance ids of split_v0 not found")
        sources["mode"] = "huggingface"

    res = survey(train, test, alpha=a.alpha, theta=a.theta, c=a.c)
    res["sources"] = sources
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps({k: res[k] for k in ("n_test_tasks", "single_skill_coverage", "decision")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
