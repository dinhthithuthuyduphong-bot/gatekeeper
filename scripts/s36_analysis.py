"""Section 36 (registered 13/11/2026 before computing; all exploratory, 0 USD).

36a family-wise reading of every registered e-process decision (K = 12), Bonferroni alpha / K;
36b how the learner found the leak: candidates, validation scores (gskill's scorer L), and the
    saved proposer calls (what the skill-writing model saw and wrote);
36c agent patches against the reversed bug-injecting commit;
36d clean versus original skill: instruction groups and behaviour in the single-commit environment.

  python scripts/s36_analysis.py --trial <worktree of origin/trial> --rows <dir with jinja rows> \
      --archives <s25_learn_run.tar.gz> <s25bleve_learn_run.tar.gz> results/s30_learn_run.tar.gz
Writes results/s36_analysis.json.
"""

from __future__ import annotations

import argparse
import gzip
import json
import re
import sys
import tarfile
from collections import Counter
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_ablation import RULE  # noqa: E402

ALPHA, THETA, C = 0.025, 0.0, 0.5  # as registered (section 25)
R = Path("results")
M1 = re.compile(
    r"git\s+(log|show|reflog|blame)\b"
    r"|git\s+(diff|checkout|restore|cat-file)\b[^\n|;&]*(HEAD~|HEAD\^|\b[0-9a-f]{7,}\b)"
)  # as section 32a
M2 = "Bug Patch"
MENTION = re.compile(r"commit|history|Bug Patch", re.IGNORECASE)
TEST = re.compile(r"\bpytest\b|python[0-9.]*\s+-m\s+(pytest|unittest)\b|\bunittest\b")


def load(p: Path) -> dict:
    return json.loads(p.read_text())


# ---------------------------------------------------------------- 36a
def first_crossing(mod, pairs, alpha: float) -> int | None:
    from gatekeeper.eprocess import BettingEProcess

    ep = BettingEProcess(theta=THETA, alpha=alpha, c=C)
    for k, (_, a, b) in enumerate(pairs, 1):
        ep.update(float(not mod.passed(a, "S")) - float(not mod.passed(b, "S")))
        if ep.crossed:
            return k
    return None


def family(mod, trial: Path) -> dict:
    s31 = load(R / "s31_alpha_family.json")["family"]["streams"]
    adm = {
        "seed51_as_shipped": (R / "s33_ship_skill.json", R / "s33_ship_none.json"),
        "seed51_single_commit": (R / "s33_lf_skill.json", R / "s33_lf_none.json"),
    }
    s33, s35 = load(R / "s33_analysis.json"), load(R / "s35_analysis.json")
    k = len(s31) + len(adm) + 2
    a_k = ALPHA / k
    out: dict = {"K": k, "alpha_bonferroni": a_k, "threshold": round(1 / a_k), "decisions": {}}
    for name, v in s31.items():
        out["decisions"][name] = {
            "registered": v["admit_at_alpha"] is not None,
            "holds": bool(v["admit_at_alpha"] is not None and v["max_e"] >= 1 / a_k),
            "max_e": v["max_e"],
        }
    for name, (s, n) in adm.items():
        pairs = mod.paired(load(s), load(n))
        reg, kept = first_crossing(mod, pairs, ALPHA), first_crossing(mod, pairs, a_k)
        out["decisions"][name] = {
            "registered": reg is not None,
            "holds": kept is not None,
            "first": reg,
            "first_at_bonferroni": kept,
        }
    for name, p in (
        ("P33c_environment_contrast", s33["P33c"]["p_anytime"]),
        ("P35_environment_contrast_unseen", s35["P35"]["p_anytime"]),
    ):
        out["decisions"][name] = {
            "registered": bool(p <= ALPHA),
            "holds": bool(p <= a_k),
            "p_anytime": p,
        }
    reg = [v for v in out["decisions"].values() if v["registered"]]
    out["registered_positive"] = len(reg)
    out["held"] = sum(v["holds"] for v in reg)
    out["not_held"] = sorted(
        n for n, v in out["decisions"].items() if v["registered"] and not v["holds"]
    )
    return out


# ---------------------------------------------------------------- 36b
def split_trace(t: str) -> tuple[str, list[str]]:
    """gskill's printed trace: '[SYSTEM]', '[USER]', '[ASSISTANT]' blocks. Returns the agent's
    commands and the observations (every user block after the first)."""
    parts = re.split(r"^\[(SYSTEM|USER|ASSISTANT)\]\s*$", t, flags=re.M)
    blocks = list(zip(parts[1::2], parts[2::2], strict=True))
    cmd = "\n".join(b for r, b in blocks if r == "ASSISTANT")
    users = [b for r, b in blocks if r == "USER"]
    return cmd, users[1:]


def learning(archive: Path) -> dict:
    with tarfile.open(archive) as tf:
        names = tf.getnames()

        def read(suffix: str) -> str:
            m = next(n for n in names if n.endswith(suffix))
            return tf.extractfile(m).read().decode("utf-8")

        cands = [c["skills"] for c in json.loads(read("/candidates.json"))]
        tree = read("/candidate_tree.html")
        runlog = json.loads(read("/run_log.json"))
        calls = sorted(n for n in names if re.search(r"proposer_calls/call_\d+\.json$", n))
        calls = [json.loads(tf.extractfile(n).read().decode("utf-8")) for n in calls]
    scores = [float(s) for s, _ in re.findall(r'"score": ([0-9.]+), "parents": "([^"]*)"', tree)]
    assert len(scores) == len(cands), (archive, len(scores), len(cands))
    made = {it["new_program_idx"]: it for it in runlog if "new_program_idx" in it}
    hist = [bool(RULE.search(s)) for s in cands]
    cand_rows = [
        {
            "idx": i,
            "parent": made[i]["selected_program_candidate"] if i in made else None,
            "iteration": made[i]["i"] if i in made else None,
            "history_line": hist[i],
            "val_L": scores[i],
        }
        for i in range(len(cands))
    ]
    call_rows = []
    for d in calls:
        cur, new = d["current_skills"], d["new_skills"]
        trajs = []
        for e in d["evaluation_data"]:
            cmd, obs = split_trace(e["Generated Outputs"].get("Agent Trace", ""))
            trajs.append(
                {
                    "empty_issue": not (e["Input"].get("Problem") or "").strip(),
                    "M1": bool(M1.search(cmd)),
                    "M2": any(M2 in o for o in obs),
                    "score": e["Scores (Higher is Better)"].get("correctness"),
                }
            )
        call_rows.append(
            {
                "parent_idx": next((i for i, s in enumerate(cands) if s == cur), None),
                "child_idx": next((i for i, s in enumerate(cands) if s == new), None),
                "parent_history": bool(RULE.search(cur)),
                "child_history": bool(RULE.search(new)),
                "response_mentions": bool(MENTION.search(d.get("llm_response") or "")),
                "trajectories": trajs,
            }
        )
    adds = [c for c in call_rows if c["child_history"] and not c["parent_history"]]
    nonseed = [r for r in cand_rows if r["idx"] > 0]
    return {
        "candidates": cand_rows,
        "val_L_mean_with_history": float(
            np.mean([r["val_L"] for r in nonseed if r["history_line"]])
        )
        if any(r["history_line"] for r in nonseed)
        else None,
        "val_L_mean_without_history": float(
            np.mean([r["val_L"] for r in nonseed if not r["history_line"]])
        ),
        "first_history_candidate": next((r["idx"] for r in cand_rows if r["history_line"]), None),
        "best_candidate": int(np.argmax(scores)),
        "best_has_history": hist[int(np.argmax(scores))],
        "proposer_calls_saved": len(calls),
        "calls": call_rows,
        "calls_adding_history": len(adds),
        "calls_adding_history_with_M2_traj": sum(
            any(t["M2"] for t in c["trajectories"]) for c in adds
        ),
        "calls_adding_history_M2_traj_scores": [
            [t["score"] for t in c["trajectories"] if t["M2"]] for c in adds
        ],
        "trajectories_shown": sum(len(c["trajectories"]) for c in call_rows),
        "trajectories_M2": sum(t["M2"] for c in call_rows for t in c["trajectories"]),
    }


# ---------------------------------------------------------------- 36c
def changed(patch: str) -> tuple[Counter, Counter]:
    rem, add, f = Counter(), Counter(), None
    for line in (patch or "").splitlines():
        if line.startswith("+++ "):
            f = line[6:] if line.startswith("+++ b/") else line[4:]
        elif line.startswith("--- "):
            continue
        elif line.startswith("-") and f is not None:
            rem[(f, line[1:].rstrip())] += 1
        elif line.startswith("+") and f is not None:
            add[(f, line[1:].rstrip())] += 1
    return rem, add


def is_revert(agent: str, bug: str) -> bool:
    ar, aa = changed(agent)
    br, ba = changed(bug)
    return bool(br or ba) and ar == ba and aa == br


def rows_of(paths: list[Path]) -> dict[str, dict]:
    out = {}
    for p in paths:
        for x in p.read_text().splitlines():
            if x.strip():
                r = json.loads(x)
                out[r["instance_id"]] = r
    return out


def reverts(trial: Path, rows: dict[str, dict]) -> dict:
    t = trial / "results"
    arms = {
        "seed41": {
            "shipped/skill": t / "f1_skill_probe.json",
            "shipped/none": t / "f1_probe.json",
            "single/skill": t / "s25_leakfree_skill.json",
            "single/none": t / "s25_leakfree_none.json",
        },
        "seed51": {
            f"{e}/{a}": R / f"s33_{x}_{a}.json"
            for e, x in (("shipped", "ship"), ("single", "lf"))
            for a in ("skill", "none")
        },
        "unseen36": {
            f"{e}/{a}": R / f"s35_{x}_{a}.json"
            for e, x in (("shipped", "ship"), ("single", "lf"))
            for a in ("skill", "none")
        },
    }
    out: dict = {}
    for grp, files in arms.items():
        for arm, f in files.items():
            runs = load(f)["runs"]
            cell = {}
            for sub, keep in (("all", None), ("no_issue", True), ("with_issue", False)):
                sel = [
                    r
                    for r in runs
                    if (r.get("S") or {}).get("resolved")
                    and (
                        keep is None
                        or keep
                        == (not (rows[r["instance_id"]].get("problem_statement") or "").strip())
                    )
                ]
                k = sum(
                    is_revert(r.get("patch") or "", rows[r["instance_id"]]["patch"]) for r in sel
                )
                cell[sub] = {"resolved": len(sel), "exact_revert": k}
            out[f"{grp}:{arm}"] = cell
    return out


# ---------------------------------------------------------------- 36d
def groups(text: str) -> list[str]:
    """Top-level instruction groups: markdown headings ('# ...') when the skill has them (the clean
    skill), otherwise first-level numbered items without indentation (the original skill)."""
    heads = [m.group(1) for m in re.finditer(r"^#+\s+(.*)$", text, re.M)]
    if not heads:
        heads = [m.group(1) for m in re.finditer(r"^\d+\.\s+(.*)$", text, re.M)]
    return [re.sub(r"[^\w\s:&/()-]", "", h).strip() for h in heads]


def behaviour(results: list[str], traces: list[str]) -> dict:
    runs = {}
    for f in results:
        for r in load(R / f"{f}.json")["runs"]:
            if "infra_error" not in r:
                runs[r["instance_id"]] = r
    msgs = {}
    for f in traces:
        for line in gzip.open(R / f"{f}.traces.jsonl.gz", "rt"):
            if line.strip():
                d = json.loads(line)
                if d.get("messages"):
                    msgs[d["instance_id"]] = d["messages"]
    ids = [i for i in runs if i in msgs]
    tested = [
        bool(
            TEST.search(
                "\n".join(str(m.get("content", "")) for m in msgs[i] if m["role"] == "assistant")
            )
        )
        for i in ids
    ]
    return {
        "runs": len(ids),
        "ran_tests": int(sum(tested)),
        "median_steps": float(np.median([runs[i].get("steps", 0) for i in ids])),
        "empty_patch": int(sum(not (runs[i].get("patch") or "").strip() for i in ids)),
        "resolved": int(sum(bool((runs[i].get("S") or {}).get("resolved")) for i in ids)),
    }


def skills_compare() -> dict:
    orig = Path("docs/skills/gskill/jinja_best_skills.txt").read_text(encoding="utf-8")
    clean = Path("docs/skills/gskill/jinja_clean_best_skills.txt").read_text(encoding="utf-8")
    return {
        "original_groups": groups(orig),
        "clean_groups": groups(clean),
        "single_commit": {
            "none_seed51": behaviour(["s33_lf_none"], ["s33_lf_none"]),
            "original_skill_seed51": behaviour(["s33_lf_skill"], ["s33_lf_skill"]),
            "none_s30": behaviour(["s30_none"], ["s30_none", "s30_none_rest"]),
            "clean_skill_s30": behaviour(["s30_skill"], ["s30_skill", "s30_skill_rest"]),
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--trial", required=True, type=Path)
    ap.add_argument("--rows", required=True, type=Path)
    ap.add_argument("--archives", required=True, nargs=3, type=Path)
    a = ap.parse_args()
    from make_numbers import s25_module

    mod = s25_module(a.trial)
    rows = rows_of(
        [a.rows / "swesmith_pallets__jinja.jsonl", a.rows / "swesmith_pallets__jinja_extra36.jsonl"]
    )
    res = {
        "36a": family(mod, a.trial),
        "36b": {
            n: learning(p)
            for n, p in zip(("jinja_original", "bleve", "jinja_clean"), a.archives, strict=True)
        },
        "36c": reverts(a.trial, rows),
        "36d": skills_compare(),
    }
    (R / "s36_analysis.json").write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps(res, indent=1)[:200])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
