"""Helpers around the official SWE-bench harness (swebench>=5): no-op patch, report lookup,
report -> normalised loss. Shared by scripts/harness_smoke.py and scripts/run_pilot.py."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from gatekeeper.loss import functional_loss

__all__ = [
    "APPLY_PATCH_FAIL",
    "TEST_TIMEOUT",
    "DATASET",
    "NOOP_PATCH",
    "loss_of",
    "eval_timed_out",
    "patch_apply_failed",
    "read_report",
    "run_harness",
]

# swebench>=5 needs the SWE-bench org copy (it carries image, eval_script, log_parser)
DATASET = "SWE-bench/SWE-bench_Verified"

# Adds one unrelated new file: a valid diff on every repository, so the tests really run
# (the harness skips an empty patch).
NOOP_PATCH = (
    "diff --git a/.gatekeeper_noop b/.gatekeeper_noop\n"
    "new file mode 100644\n"
    "index 0000000..ba0e162\n"
    "--- /dev/null\n"
    "+++ b/.gatekeeper_noop\n"
    "@@ -0,0 +1 @@\n"
    "+noop\n"
)


def run_harness(
    preds: str,
    ids: list[str],
    run_id: str,
    workers: int,
    dataset: str = DATASET,
    split: str = "test",
    namespace: str | None = None,
    python: str | None = None,
) -> None:
    """`python`: interpreter whose `swebench` package scores the run (default: this one).
    SWE-bench-Live must be scored with its own harness fork and its prebuilt images
    (`--namespace starryzhang`, README of the python-only branch), installed in a separate
    environment because the fork is also named `swebench`."""
    cmd = [
        python or sys.executable,
        "-m",
        "swebench.harness.run_evaluation",
        "--dataset_name",
        dataset,
        "--split",
        split,
        "--predictions_path",
        preds,
        "--instance_ids",
        *ids,
        "--max_workers",
        str(workers),
        "--run_id",
        run_id,
        "--timeout",
        "1800",
    ]
    if namespace:
        cmd += ["--namespace", namespace]
    print("+", " ".join(cmd), flush=True)
    rc = subprocess.run(cmd, check=False).returncode
    if rc != 0:
        raise SystemExit(f"swebench harness exited with code {rc} for run {run_id}")


def read_report(run_id: str, model: str, iid: str, root: str | Path = "logs/run_evaluation"):
    p = Path(root) / run_id / model / iid / "report.json"
    if not p.exists():  # layout differs across harness versions: search the run directory
        hits = sorted((Path(root) / run_id).glob(f"**/{iid}/report.json"))
        if not hits:
            return None
        p = hits[0]
    return json.loads(p.read_text())[iid]


APPLY_PATCH_FAIL = ">>>>> Patch Apply Failed"  # swebench.harness.constants (5.0.2 and Live fork)


def patch_apply_failed(run_id: str, iid: str, root: str | Path = "logs/run_evaluation") -> bool:
    """True if the harness could not apply the submitted patch (its run_instance.log says so).
    That is the AGENT's output, scored "not resolved" as in SWE-bench (Jimenez et al. 2024,
    Table 5 reports % Resolved over all instances next to % Apply; the harness puts these
    instances in error_ids, never in resolved_ids) - not an infrastructure failure (audit A37)."""
    for log in sorted((Path(root) / run_id).glob(f"*/{iid}/run_instance.log")):
        if APPLY_PATCH_FAIL in log.read_text(errors="replace"):
            return True
    return False


TEST_TIMEOUT = "Test timed out after"  # swebench run_instance: EvaluationError on its --timeout


def eval_timed_out(run_id: str, iid: str, root: str | Path = "logs/run_evaluation") -> bool:
    """True if the harness stopped the tests at its time limit. SWE-bench counts such instances as
    errors, i.e. not resolved (reporting.make_run_report: error_ids, never resolved_ids), the same
    as a patch that does not apply (audit A56). Scoring is serialised across arms
    (run_pilot --score-parallel 1) so CPU contention does not push slow suites over the limit."""
    for log in sorted((Path(root) / run_id).glob(f"*/{iid}/run_instance.log")):
        if TEST_TIMEOUT in log.read_text(errors="replace"):
            return True
    return False


def loss_of(rep: dict | None, w: float = 0.5) -> tuple[float, dict]:
    """No report (patch skipped or not applied) = nothing fixed, nothing broken (assumed)."""
    if rep is None:
        return functional_loss(1.0, 0.0, w), {"resolved": False, "note": "no report"}
    ts = rep.get("tests_status", {})
    f2p, p2p = ts.get("FAIL_TO_PASS", {}), ts.get("PASS_TO_PASS", {})
    n_f = len(f2p.get("success", [])) + len(f2p.get("failure", []))
    n_p = len(p2p.get("success", [])) + len(p2p.get("failure", []))
    # no FAIL_TO_PASS result: if the tests ran (tests_status present) the harness counts the
    # target as met (compute_fail_to_pass returns 1 for an empty list), so F = 0 keeps loss 0 <=>
    # "resolved"; if they did not run (no tests_status: patch not applied) nothing was fixed
    F = len(f2p.get("failure", [])) / n_f if n_f else (0.0 if "tests_status" in rep else 1.0)
    R = len(p2p.get("failure", [])) / n_p if n_p else 0.0
    return functional_loss(F, R, w), {
        "resolved": bool(rep.get("resolved")),
        "F": F,
        "R": R,
        "n_fail_to_pass": n_f,
        "n_pass_to_pass": n_p,
    }
