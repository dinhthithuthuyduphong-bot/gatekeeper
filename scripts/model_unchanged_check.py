"""Main experiment section 5 / draft section 10: is the model still the one that produced E2?

Before the memgovern cell is paired with E2's `none` arm (seed 41), resend the FIRST agent call
of every E2 task, exactly as E2 made it (mini-swe-agent 2.4.6 LitellmModel with the model name and
model_kwargs recorded in the trajectory, tools=[BASH_TOOL]), TWICE, and compare:
  step 1 (determinism): the two new answers are identical;
  step 2 (unchanged):   they equal the first assistant message of the E2 trajectory, and the
                        response `model` field equals E2's.
Rule (registered): pair only if both steps hold on EVERY task; otherwise run both arms anew.
Compared fields: tool-call function names and arguments, and message content.

  python scripts/model_unchanged_check.py --runs-dir <extracted raw-archive runs> \
      --registry <litellm registry> --out results/model_unchanged_check.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


def e2_tasks() -> list[str]:
    """The 109 E2 tasks: present in all three seeds (per_task_mean rule), in seed-41 order."""
    from analyze_g1_final import per_task_mean

    runs = [json.loads((ROOT / f"results/pilot/g2-e2-s{s}.json").read_text()) for s in (41, 51, 61)]
    keep = per_task_mean(runs, "xreposkill")
    order = runs[0]["instances"]
    return [t for t in order if t in keep]


def signature(msg: dict) -> dict:
    calls = msg.get("tool_calls") or []
    return {
        "content": (msg.get("content") or "").strip(),
        "calls": [
            [c.get("function", {}).get("name"), c.get("function", {}).get("arguments")]
            for c in calls
        ],
    }


def _part_no(traj: Path) -> int:
    """Part number NN of the run dir g2-e2-s41-kK-pNN that holds this trajectory."""
    run_dir = traj.parents[3].name
    head, sep, nn = run_dir.rpartition("-p")
    if not sep or not nn.isdigit() or not head.startswith("g2-e2-s41-k"):
        raise ValueError(f"unexpected run dir {run_dir}")
    return int(nn)


def find_traj(runs_dir: Path, task: str) -> Path:
    """The seed-41 none trajectory that E2 counted.

    A task re-run in a later part of the same batch replaces the older data
    (run_batched_pilot.merge, A98), so the counted run is the one in the highest part.
    """
    hits = sorted(runs_dir.glob(f"g2-e2-s41-*/none/agent/{task}/{task}.traj.json"))
    if not hits:
        raise FileNotFoundError(f"{task}: no seed-41 none trajectory")
    batches = {h.parents[3].name.rpartition("-p")[0] for h in hits}
    if len(batches) != 1:
        raise FileNotFoundError(f"{task}: trajectories in several batches {sorted(batches)}")
    best = max(hits, key=_part_no)
    if sum(_part_no(h) == _part_no(best) for h in hits) != 1:
        raise FileNotFoundError(f"{task}: two trajectories in the same part")
    return best


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs-dir", required=True)
    ap.add_argument("--registry", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, help="first N tasks only (dry run)")
    a = ap.parse_args()

    from minisweagent.models.litellm_model import LitellmModel

    tasks = e2_tasks()
    if a.limit:
        tasks = tasks[: a.limit]
    rows, spent = [], 0.0
    for t in tasks:
        traj = json.loads(find_traj(Path(a.runs_dir), t).read_text())
        cfg = traj["info"]["config"]["model"]
        msgs = traj["messages"]
        first = next(i for i, m in enumerate(msgs) if m.get("role") == "assistant")
        prompt = [{"role": m["role"], "content": m["content"]} for m in msgs[:first]]
        old = msgs[first]
        old_model = (old.get("extra", {}).get("response") or {}).get("model")
        model = LitellmModel(
            model_name=cfg["model_name"],
            model_kwargs=cfg["model_kwargs"],
            litellm_model_registry=a.registry,
        )
        new = [model.query(prompt) for _ in range(2)]
        spent += sum(float(n.get("extra", {}).get("cost") or 0.0) for n in new)
        sigs = [signature(n) for n in new]
        new_models = [(n.get("extra", {}).get("response") or {}).get("model") for n in new]
        rows.append(
            {
                "task": t,
                "deterministic": sigs[0] == sigs[1],
                "matches_e2": sigs[0] == signature(old),
                "model_e2": old_model,
                "model_new": new_models,
                "model_same": all(m == old_model for m in new_models),
                # the compared outputs themselves (tool calls and content only), so that a
                # mismatch can be read rather than inferred (R-51)
                "sig_e2": signature(old),
                "sig_new": sigs,
            }
        )
        print(f"{len(rows)}/{len(tasks)} spent {spent:.4f}", flush=True)
    ok = all(r["deterministic"] and r["matches_e2"] and r["model_same"] for r in rows)
    out = {
        "n_tasks": len(rows),
        "deterministic": sum(r["deterministic"] for r in rows),
        "matches_e2": sum(r["matches_e2"] for r in rows),
        "model_same": sum(r["model_same"] for r in rows),
        "pair_with_e2": ok,
        "spent_usd": spent,
        "rows": rows,
    }
    Path(a.out).write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: out[k] for k in out if k != "rows"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
