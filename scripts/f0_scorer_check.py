"""Section 25 F0 (0 USD, no model call): does gskill's scorer accept patches that fix nothing?

Run with the environment of gskill at gepa@8c7b697 (swesmith 0.0.9, swebench 4.1.0,
mini-swe-agent 2.2.4) and gskill's package on PYTHONPATH:

  PYTHONPATH=<gepa>/src/gepa/gskill <venv>/bin/python scripts/f0_scorer_check.py \
      --rows data/instances/swesmith_pallets__jinja.jsonl --split test --workers 4 \
      --out results/f0_scorer_check.json

Run from a scratch directory: SWE-smith and gskill write logs under ./logs/run_evaluation.

For every task of the split, two patches are built in the task container at the instance
branch (the state the agent works on):
  (a) no-op: append "# no-op" to the first non-test .py file of the bug patch;
  (b) gold: the bug patch applied in reverse (SWE-smith: "gold patches = bug patches, so fix =
      revert", harness/utils.py::_apply_patch).
Each patch is scored by
  L: gskill's flow of evaluate/mini_swe_agent.py::evaluate_single_task (non-empty patch ->
     verify_with_patch(f2p_only=True) -> verify_with_patch(f2p_only=False)), calling gskill's
     SWEHarness.verify_with_patch unmodified;
  S: SWE-smith's own grading, swesmith.harness.eval.run_evaluation (resolved).
"""

from __future__ import annotations

import argparse
import gzip
import json
import math
import re
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


def wilson(k: int, n: int, z: float) -> list[float]:
    if n == 0:
        return [0.0, 1.0]
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [max(0.0, c - h), min(1.0, c + h)]


_TEST_FILE = re.compile(
    r"(^|/)(tests?|testing)/|(^|/)test_[^/]*\.py$|_test\.(py|go)$|(^|/)conftest\.py$"
)
COMMENT = {".py": "# no-op", ".go": "// no-op"}


def first_source_file(bug_patch: str, test_files: list[str]) -> str:
    """First file of the bug patch that is source code (.py / .go) and not a test file.

    Test files: SWE-smith's own list for the task (F2P and P2P files) plus a path rule
    (test directories, test_*.py, *_test.py, *_test.go, conftest.py). Version 2 (A90): the
    first version rejected every file whose name contained "test" (e.g. src/jinja2/tests.py).
    """
    from unidiff import PatchSet

    for f in PatchSet(bug_patch):
        p = f.path
        if Path(p).suffix in COMMENT and p not in test_files and not _TEST_FILE.search(p):
            return p
    raise ValueError("no non-test source file in bug patch")


def build_patches(inst: dict) -> dict[str, str]:
    """Build the no-op and gold patches inside a fresh task container (instance branch HEAD)."""
    import docker
    from swesmith.profiles import registry

    rp = registry.get_from_inst(inst)
    client = docker.from_env()
    c = client.containers.run(rp.image_name, "tail -f /dev/null", detach=True, remove=True)
    try:

        def sh(cmd: str) -> str:
            r = c.exec_run(["bash", "-lc", cmd], workdir="/testbed")
            if r.exit_code != 0:
                raise RuntimeError(f"{cmd!r} failed: {r.output.decode()[-500:]}")
            return r.output.decode()

        sh(f"git fetch -q && git checkout -q {inst['instance_id']}")
        f2p, p2p = rp.get_test_files(inst)
        src = first_source_file(inst["patch"], list(f2p) + list(p2p))
        sh(f"printf '\\n{COMMENT[Path(src).suffix]}\\n' >> {src}")
        noop = sh("git diff")
        sh("git checkout -q -- .")
        c.put_archive("/tmp", _tar("bug.diff", inst["patch"]))
        sh("git apply --reverse /tmp/bug.diff")
        gold = sh("git diff")
        return {"noop": noop, "gold": gold, "noop_file": src}
    finally:
        c.kill()


def _tar(name: str, text: str) -> bytes:
    import io
    import tarfile

    buf = io.BytesIO()
    data = text.encode()
    with tarfile.open(fileobj=buf, mode="w") as t:
        info = tarfile.TarInfo(name)
        info.size = len(data)
        t.addfile(info, io.BytesIO(data))
    return buf.getvalue()


def score_lenient(inst: dict, patch: str) -> dict:
    """gskill's evaluate_single_task control flow, with its own verify_with_patch."""
    from gskill.swe_harness import SWEHarness

    h = SWEHarness()
    h.current_task = inst  # what setup_task() sets; no agent container is needed for scoring
    if len(patch.strip()) == 0:
        return {"passed": False, "status": "no_patch"}
    f2p_ok, f2p_out = h.verify_with_patch(patch, f2p_only=True)
    if not f2p_ok:
        return {"passed": False, "status": "f2p_failed", "f2p_tail": f2p_out[-300:]}
    full_ok, _ = h.verify_with_patch(patch, f2p_only=False)
    return {"passed": bool(full_ok), "status": "all_passed" if full_ok else "p2p_failed"}


def score_strict(inst: dict, patch: str) -> dict:
    from swesmith.harness.eval import run_evaluation

    pred = {"instance_id": inst["instance_id"], "model_patch": patch, "model_name_or_path": "f0"}
    r = run_evaluation(pred, dict(inst), run_id=f"f0_{uuid.uuid4().hex[:8]}", f2p_only=False)
    return {"resolved": bool(r["resolved"]), "status": r["status"]}


# Messages of gskill's verify_with_patch that mean the tests never ran (tool failure, not a score)
L_INFRA = ("Test output file not found", "Verification error", "returned None", "No task set up")


def infra_reason(lenient: dict, strict: dict) -> str | None:
    """A score is only a score if the tests ran (L1): classify tool failures before counting."""
    if strict.get("status") != "completed":
        return f"strict status {strict.get('status')!r}"
    tail = lenient.get("f2p_tail", "")
    if lenient.get("status") == "f2p_failed" and any(m in tail for m in L_INFRA):
        return f"lenient: {tail[:120]!r}"
    return None


def assume_public(inst: dict) -> None:
    """SWE-smith asks api.github.com whether the mirror repo is private (profiles/base.py
    _is_repo_private). This machine's proxy blocks that host; the mirror is public (cloned
    anonymously here), so the cached answer is set to False before scoring."""
    from swesmith.profiles import registry

    registry.get_from_inst(inst)._cache_repo_private = False


def one(inst: dict) -> dict:
    out = {"instance_id": inst["instance_id"], "order": inst["_gskill_order"]}
    assume_public(inst)
    try:
        p = build_patches(inst)
    except Exception as e:  # noqa: BLE001 - recorded as an infrastructure failure, not a score
        out["infra_error"] = f"build: {type(e).__name__}: {str(e)[:300]}"
        return out
    out["noop_file"] = p["noop_file"]
    for kind in ("noop", "gold"):
        try:
            out[f"L_{kind}"] = score_lenient(inst, p[kind])
            out[f"S_{kind}"] = score_strict(inst, p[kind])
            why = infra_reason(out[f"L_{kind}"], out[f"S_{kind}"])
            if why:
                out["infra_error"] = f"{kind}: {why}"
                return out
        except Exception as e:  # noqa: BLE001
            out["infra_error"] = f"{kind}: {type(e).__name__}: {str(e)[:300]}"
            return out
    return out


def summarise(rows: list[dict]) -> dict:
    ok = [r for r in rows if "infra_error" not in r]
    res = {"n_tasks": len(rows), "n_scored": len(ok), "infra_errors": len(rows) - len(ok)}
    for kind in ("noop", "gold"):
        kL = sum(r[f"L_{kind}"]["passed"] for r in ok)
        kS = sum(r[f"S_{kind}"]["resolved"] for r in ok)
        n = len(ok)
        res[kind] = {
            "L_pass": kL,
            "L_rate": kL / n if n else None,
            "L_wilson95": wilson(kL, n, 1.959963984540054),
            "S_resolved": kS,
            "S_rate": kS / n if n else None,
            "S_wilson95": wilson(kS, n, 1.959963984540054),
        }
    return res


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", required=True)
    ap.add_argument("--split", required=True)
    ap.add_argument("--workers", type=int, required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, help="first N tasks of the split by _gskill_order")
    a = ap.parse_args()
    raw = Path(a.rows).read_bytes()
    text = (gzip.decompress(raw) if a.rows.endswith(".gz") else raw).decode("utf-8")
    rows = [json.loads(x) for x in text.splitlines() if x.strip()]
    insts = sorted(
        (r for r in rows if r["_gskill_split"] == a.split), key=lambda r: r["_gskill_order"]
    )
    if a.limit:
        insts = insts[: a.limit]
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        per = list(ex.map(one, insts))
    out = {"summary": summarise(per), "per_task": per, "split": a.split, "rows": a.rows}
    Path(a.out).write_text(json.dumps(out, indent=1) + "\n")
    s = out["summary"]
    print(json.dumps({"n_scored": s["n_scored"], "infra_errors": s["infra_errors"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
