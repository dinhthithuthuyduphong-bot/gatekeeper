"""Section 25 F1 (paid, cap fixed by the registration): no-skill arm of gskill's agent on SWE-smith.

Calls gskill's own SWEHarness.setup_task / run_agent (gepa@8c7b697) with empty skills and a
copy of gskill's mini.yaml in which only cost_limit and model_kwargs are set to the values
registered in docs/preregistration_main.md section 25. Every patch is scored with both
gskill's flow (L, scripts/f0_scorer_check.py::score_lenient) and SWE-smith's grading (S).

Budget: before each run, stop if spent + worst > cap (worst = cost_limit). Spend is summed
from LiteLLM's per-call response_cost (success callback). Prints only operational fields (L28).

  PYTHONPATH=<gepa>/src/gepa/gskill:<repo>/scripts <venv>/bin/python scripts/f1_probe.py \
      --rows data/instances/swesmith_pallets__jinja.jsonl --split test \
      --model vertex_ai/gemini-3.1-flash-lite --seed 41 --cost-limit 0.30 --cap 2.0 \
      --registry tests/fixtures/e1_litellm_registry.json --out results/f1_probe.json
"""

from __future__ import annotations

import argparse
import gzip
import json
import threading
from pathlib import Path

import yaml

# Section 25 step 3 (out of scope: no leaked bug commit). Run in the AGENT container only, after
# gskill's setup_task: one parentless commit with the buggy tree; every other ref, the remote, the
# mirror, reflogs and unreachable objects removed. Scoring containers are fresh and unaffected.
LEAK_FREE_SH = (
    "set -e; cd /testbed; "
    "git checkout -q --orphan gk_clean; git add -A; "
    "git -c user.name=gk -c user.email=gk@local commit -q -m 'Initial commit'; "
    "for r in $(git for-each-ref --format='%(refname)' | grep -v '^refs/heads/gk_clean$'); "
    'do git update-ref -d "$r"; done; '
    "git remote remove origin 2>/dev/null || true; rm -rf /opt/mirror.git; "
    "git reflog expire --expire=now --all; git gc -q --prune=now; "
    "echo commits=$(git rev-list --all | wc -l) refs=$(git for-each-ref | wc -l) "
    "remotes=$(git remote | wc -l) "
    "objects_with_bug_msg=$(git log --all --format=%s | grep -c 'Bug Patch' || true)"
)
LEAK_FREE_OK = "commits=1 refs=1 remotes=0 objects_with_bug_msg=0"

_spent = 0.0
_lock = threading.Lock()


def _track(kwargs, response, start, end):  # LiteLLM success callback signature
    global _spent
    with _lock:
        _spent += float(kwargs.get("response_cost") or 0.0)


def crash_infra_reason(trace: str, steps: int) -> str | None:
    """A crash before the agent's first step is a provider/environment failure (e.g. Vertex 403
    "Spend cap breached"), not an agent outcome: recorded as infrastructure and re-run (A124)."""
    if trace.startswith("Agent crashed") and steps == 0:
        return f"agent crashed before its first step: {trace[15:200]}"
    return None


def make_config(gskill_yaml: Path, out: Path, cost_limit: float, model_kwargs: dict) -> Path:
    cfg = yaml.safe_load(gskill_yaml.read_text())
    cfg["agent"]["cost_limit"] = cost_limit
    cfg.setdefault("model", {})["model_kwargs"] = model_kwargs
    out.write_text(yaml.safe_dump(cfg, sort_keys=False))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    for k in ("--rows", "--split", "--model", "--registry", "--out", "--gskill-yaml"):
        ap.add_argument(k, required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--cost-limit", type=float, required=True)
    ap.add_argument("--cap", type=float, required=True)
    ap.add_argument("--mock-response", help="free dry run: LiteLLM mock_response, cost 0 allowed")
    ap.add_argument("--skills-file", help="skills text injected into {{ skills }} (default: none)")
    ap.add_argument(
        "--subset",
        choices=["all", "no-problem-statement"],
        default="all",
        help="task selection only (tasks are never changed): the tasks whose problem statement is "
        "empty (section 27, 2c)",
    )
    ap.add_argument(
        "--skip-done",
        nargs="+",
        help="result file of an earlier, capped run of the same arm: its tasks are not run again "
        "(task selection only; A107)",
    )
    ap.add_argument(
        "--leak-free",
        action="store_true",
        help="remove the bug commit from the agent's git history",
    )
    a = ap.parse_args()
    if a.seed == 0:
        raise SystemExit("seed 0 means 'no seed' on Vertex (A14)")

    import litellm
    from f0_scorer_check import infra_reason, score_lenient, score_strict
    from gskill.swe_harness import SWEHarness

    litellm.register_model(json.loads(Path(a.registry).read_text()))
    litellm.success_callback = [_track]
    kwargs = {"seed": a.seed, "drop_params": True, "parallel_tool_calls": True}
    if a.mock_response:
        kwargs["mock_response"] = a.mock_response
    cfg = make_config(
        Path(a.gskill_yaml), Path(a.out).with_suffix(".mini.yaml"), a.cost_limit, kwargs
    )

    raw = Path(a.rows).read_bytes()
    text = (gzip.decompress(raw) if a.rows.endswith(".gz") else raw).decode("utf-8")
    rows = [json.loads(x) for x in text.splitlines() if x.strip()]
    insts = sorted(
        (r for r in rows if r["_gskill_split"] == a.split), key=lambda r: r["_gskill_order"]
    )
    if a.subset == "no-problem-statement":
        insts = [r for r in insts if not (r.get("problem_statement") or "").strip()]
    if a.skip_done:
        done = {
            r["instance_id"] for f in a.skip_done for r in json.loads(Path(f).read_text())["runs"]
        }
        insts = [r for r in insts if r["instance_id"] not in done]
    skills = Path(a.skills_file).read_text() if a.skills_file else ""
    traces_path = Path(a.out).with_suffix(".traces.jsonl.gz")
    traces_path.unlink(missing_ok=True)  # the result file is rewritten, so are its traces
    out = {
        "model": a.model,
        "seed": a.seed,
        "cost_limit": a.cost_limit,
        "cap": a.cap,
        "skills_chars": len(skills),
        "leak_free": a.leak_free,
        "subset": a.subset,
        "n_tasks": len(insts),
        "runs": [],
    }
    for inst in insts:
        if _spent + a.cost_limit > a.cap:
            out["stopped"] = f"spent {_spent:.4f} + {a.cost_limit} > {a.cap}"
            break
        before = _spent
        rec = {"instance_id": inst["instance_id"], "order": inst["_gskill_order"]}
        h = SWEHarness()
        try:
            h.setup_task(task_instance=inst)
            if a.leak_free:
                r = h.container.exec_run(["bash", "-lc", LEAK_FREE_SH])
                rec["leak_free_check"] = r.output.decode().strip().splitlines()[-1:]
                if r.exit_code != 0 or rec["leak_free_check"] != [LEAK_FREE_OK]:
                    raise RuntimeError(f"leak-free rewrite failed: {r.output.decode()[-300:]}")
            patch, trace, metrics = h.run_agent(
                inst.get("problem_statement", ""), skills, model_name=a.model, config_path=str(cfg)
            )
            # raw evidence (A52, A104): every agent message, gzip JSONL next to the result file
            with gzip.open(traces_path, "at", encoding="utf-8") as tf:
                tf.write(
                    json.dumps(
                        {"instance_id": inst["instance_id"], "messages": metrics.get("messages")},
                        default=str,
                    )
                    + "\n"
                )
            rec["crashed"] = trace.startswith("Agent crashed")
            rec["crash_head"] = trace[:300] if rec["crashed"] else None
            why = crash_infra_reason(trace, metrics.get("steps", 0))
            if why:
                rec["infra_error"] = why
            rec["steps"] = metrics.get("steps", 0)
            rec["patch_chars"] = len(patch)
            rec["L"] = score_lenient(inst, patch)
            rec["S"] = (
                score_strict(inst, patch)
                if patch.strip()
                else {"resolved": False, "status": "no_patch"}
            )
            rec["patch"] = patch
            if patch.strip():
                why = infra_reason(rec["L"], rec["S"])
                if why:
                    rec["infra_error"] = f"scoring: {why}"
        except Exception as e:  # noqa: BLE001 - infrastructure, recorded and counted
            rec["infra_error"] = f"{type(e).__name__}: {str(e)[:300]}"
        finally:
            h.cleanup()
        rec["cost_usd"] = _spent - before
        out["runs"].append(rec)
        if not a.mock_response and rec.get("steps", 0) > 0 and rec["cost_usd"] <= 0.0:
            out["stopped"] = "cost not recorded for a run with steps > 0 (cap would be blind, A84)"
            Path(a.out).write_text(json.dumps(out, indent=1) + "\n")
            return 3
        out["spent_usd"] = _spent
        Path(a.out).write_text(json.dumps(out, indent=1) + "\n")
        print(
            f"[{len(out['runs'])}] {inst['instance_id'][:40]} cost={rec['cost_usd']:.4f}"
            f" spent={_spent:.4f}"
            f" infra={'infra_error' in rec}",
            flush=True,
        )
    out["spent_usd"] = _spent
    Path(a.out).write_text(json.dumps(out, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
