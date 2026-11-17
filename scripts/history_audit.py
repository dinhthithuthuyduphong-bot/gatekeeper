"""History audit S0 (docs/todo_ease_revision.md section 6; exploratory, 0 USD, no model call).

What the git history of a SWE-smith task contains, and what of it the agent was shown, in three
levels that are never merged:

  level 1  EXISTS     the commits on each task branch of the task repositories (from the
                      repositories themselves, not from the traces): their messages, whether the
                      "Bug Patch" diff equals the benchmark's own bug patch, which files the
                      "Remove F2P Tests" commit deletes and whether they hold the FAIL_TO_PASS
                      tests.
  level 2  SHOWN      per saved trace: which commit message, and which commit content, appeared
                      in an observation returned to the agent.
  level 3  INDICATORS of use, indirect only: the agent's final patch is the exact reversal of the
                      bug patch; the agent ran a command that reads or restores the deleted tests
                      from the history; the patch edits the files the bug patch edited.

  python scripts/history_audit.py --mirrors <dir with <repo>.git mirrors> --rows <dir with rows> \
      --out results/history_audit.json

Detection rules (fixed in this file, applied identically to every arm):
  * HISTORY_CMD: a git command that reads a commit other than the working tree.
  * bug diff shown: an observation holds a diff line "-x" whose content x is a line the bug patch
    REMOVES (same sign). A whole-tree dump of a single commit (`git show HEAD` in the single-commit
    environment) shows every line with "+", and the agent's own `git diff` of a fix shows the
    removed lines with "+", so neither is counted. A bug patch that removes no line (pure
    addition) counts on a "+x" line whose x it adds, and only when the same observation names the
    "Bug Patch" commit. In both cases the observation must come from a HISTORY_CMD or name the
    "Bug Patch" commit: the agent's own `git diff` of a fix that swaps two branches of an `if`
    removes the very lines the bug patch removed (six such runs in the single-commit Bleve
    environment). Lines shorter than MIN_LINE characters after stripping are ignored (brackets,
    "pass", blank lines occur everywhere).
  * deleted tests shown: an observation holds a deletion line "-..." that contains the signature
    of a FAIL_TO_PASS test ("def <name>(" for Python, "func <Name>(" for Go): the content of the
    "Remove F2P Tests" commit, as `git show` prints it.
  * deleted tests restored and run: a RESTORE_CMD (checkout, restore or `git show REF:PATH` from a
    commit) is followed, at the same or a later turn, by the output of a non-git command that
    names a path the "Remove F2P Tests" commit deleted (test runners print the file of every
    test they collect or fail; the path cannot occur in such output while the file is absent).
  * The first rule set (either sign after a history command; signatures on any line) gave false
    positives in single-commit environments, where nothing can be seen; it is kept as
    `*_loose` for comparison.
"""

from __future__ import annotations

import argparse
import gzip
import json
import re
import subprocess
from collections import Counter
from pathlib import Path

R = Path("results")
MIN_LINE = 8
STRUCTURE = ["Initial commit", "Bug Patch", "Remove F2P Tests"]
REPOS = {
    "jinja": ("pallets__jinja.ada0a9a6", ["swesmith_pallets__jinja.jsonl", "extra36.jsonl"]),
    "bleve": ("blevesearch__bleve.f2876b5e", ["swesmith_blevesearch__bleve.jsonl.gz"]),
    "pygments": ("pygments__pygments.27649ebb", ["swesmith_pygments__pygments.jsonl.gz"]),
}
HISTORY_CMD = re.compile(
    r"git\s+(log\b[^\n|;&]*(-p\b|--patch|--stat|--name-|-\d)"
    r"|show\b|reflog\b|blame\b|cat-file\b|format-patch\b|rev-list\b|whatchanged\b"
    r"|(diff|checkout|restore|switch|reset)\b[^\n|;&]*(HEAD~|HEAD\^|@~|\b[0-9a-f]{7,40}\b|--source))"
)
ANY_LOG = re.compile(r"git\s+log\b")
RESTORE_CMD = re.compile(
    r"git\s+(checkout|restore)\b[^\n|;&]*(HEAD~|HEAD\^|@~|\b[0-9a-f]{7,40}\b|--source|-s\s)"
    r"|git\s+show\s+[^\s|;&]*:[^\s|;&]+"
)
CMD_BLOCK = re.compile(r"```(?:bash|mswea_bash_command)?\n(.*?)```", re.S)

# trace stem -> (repository, environment, condition, agent); environment as the run was set up
ARMS: dict[str, tuple[str, str, str, str]] = {
    "s27_trace34": ("jinja", "shipped", "original skill", "study agent, seed 41"),
    "s27_trace34b": ("jinja", "shipped", "original skill", "study agent, seed 41"),
    "s29_none": ("jinja", "shipped", "no skill", "study agent, seed 41"),
    "s27_placebo": ("jinja", "shipped", "placebo", "study agent, seed 41"),
    "s29_ablate": ("jinja", "shipped", "skill without history line", "study agent, seed 41"),
    "s30_shipped34": ("jinja", "shipped", "re-learned skill", "study agent, seed 41"),
    "s30_none": ("jinja", "single commit", "no skill", "study agent, seed 41"),
    "s30_none_rest": ("jinja", "single commit", "no skill", "study agent, seed 41"),
    "s30_skill": ("jinja", "single commit", "re-learned skill", "study agent, seed 41"),
    "s30_skill_rest": ("jinja", "single commit", "re-learned skill", "study agent, seed 41"),
    "s33_ship_none": ("jinja", "shipped", "no skill", "study agent, seed 51"),
    "s33_ship_skill": ("jinja", "shipped", "original skill", "study agent, seed 51"),
    "s33_lf_none": ("jinja", "single commit", "no skill", "study agent, seed 51"),
    "s33_lf_skill": ("jinja", "single commit", "original skill", "study agent, seed 51"),
    "s35_ship_none": ("jinja", "shipped", "no skill", "study agent, seed 51, 36 new tasks"),
    "s35_ship_skill": ("jinja", "shipped", "original skill", "study agent, seed 51, 36 new tasks"),
    "s35_lf_none": ("jinja", "single commit", "no skill", "study agent, seed 51, 36 new tasks"),
    "s35_lf_skill": ("jinja", "single commit", "original skill", "study agent, seed 51, 36 new"),
    "s34_none_pilot": ("jinja", "shipped", "no skill", "second Gemini agent, seed 41"),
    "s34_none_rest": ("jinja", "shipped", "no skill", "second Gemini agent, seed 41"),
    "s34_skill_pilot": ("jinja", "shipped", "original skill", "second Gemini agent, seed 41"),
    "s34_skill_rest": ("jinja", "shipped", "original skill", "second Gemini agent, seed 41"),
    "s27pyg_none": ("pygments", "shipped", "no skill", "study agent, seed 41"),
    "s27pyg_skill": ("pygments", "shipped", "jinja skill", "study agent, seed 41"),
    "s27pyg_skillb": ("pygments", "shipped", "jinja skill", "study agent, seed 41"),
    "s27pyg_skillc": ("pygments", "shipped", "jinja skill", "study agent, seed 41"),
    "s25bleve_leakfree_none": ("bleve", "single commit", "no skill", "study agent, seed 41"),
    "s25bleve_leakfree_skill": ("bleve", "single commit", "skill", "study agent, seed 41"),
    "s25bleve_leakfree_skillb": ("bleve", "single commit", "skill", "study agent, seed 41"),
}


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=True
    ).stdout


def changed(patch: str) -> tuple[Counter, Counter]:
    """(removed, added) lines per file, as in scripts/s36_analysis.py."""
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


def files_of(patch: str) -> set[str]:
    return {m.group(1) for m in re.finditer(r"^\+\+\+ b/(\S+)", patch or "", re.M)}


def load_rows(rows_dir: Path, names: list[str]) -> dict[str, dict]:
    out = {}
    for n in names:
        p = rows_dir / n
        lines = gzip.open(p, "rt") if n.endswith(".gz") else open(p)
        for x in lines:
            if x.strip():
                r = json.loads(x)
                out[r["instance_id"]] = r
    return out


def f2p_signatures(f2p: list[str]) -> set[str]:
    sig = set()
    for t in f2p:
        if "::" in t:
            name = t.split("::")[-1].split("[")[0]
            if name:
                sig.add(f"def {name}(")
        else:
            sig.add(f"func {t.split('/')[0]}(")
    return sig


# ---------------------------------------------------------------- level 1
def level1(mirror: Path, rows: dict[str, dict]) -> dict[str, dict]:
    out = {}
    for iid, row in rows.items():
        ref = f"refs/heads/{iid}"
        try:
            log = git(mirror, "log", "--format=%H%x09%s", ref).splitlines()
        except subprocess.CalledProcessError:
            out[iid] = {"branch_found": False}
            continue
        commits = [x.split("\t", 1) for x in reversed(log)]
        msgs = [m for _, m in commits]
        rec: dict = {"branch_found": True, "n_commits": len(commits), "messages": msgs}
        rec["structure_ok"] = msgs == STRUCTURE
        if rec["structure_ok"]:
            (c0, _), (c1, _), (c2, _) = commits
            bug = git(mirror, "diff", c0, c1)
            rec["bug_patch_equals_row"] = changed(bug) == changed(row["patch"])
            st = git(mirror, "diff", "--name-status", c1, c2).split("\n")
            st = [x.split("\t") for x in st if x.strip()]
            rec["f2p_commit_status"] = dict(Counter(s[0] for s in st))
            rec["f2p_deleted_files"] = [s[1] for s in st if s[0] == "D"]
            deleted = git(mirror, "diff", c1, c2)
            f2p = row["FAIL_TO_PASS"]
            f2p = json.loads(f2p) if isinstance(f2p, str) and f2p.startswith("[") else f2p
            if isinstance(f2p, str):
                import ast

                f2p = ast.literal_eval(f2p)
            sigs = f2p_signatures(f2p)
            rec["f2p_tests"] = len(f2p)
            rec["f2p_signatures"] = sorted(sigs)
            rec["f2p_signatures_in_deleted"] = sum(s in deleted for s in sigs)
            rec["deleted_lines"] = sum(
                1 for x in deleted.splitlines() if x.startswith("-") and not x.startswith("---")
            )
        out[iid] = rec
    return out


# ---------------------------------------------------------------- level 2 and 3
def turns(messages: list[dict]) -> list[tuple[str, str]]:
    """(command, observation) pairs in order; the observation is the next user message."""
    out, cmd = [], None
    for m in messages:
        c = m.get("content")
        if isinstance(c, list):
            c = " ".join(x.get("text", "") for x in c if isinstance(x, dict))
        c = str(c or "")
        if m.get("role") == "assistant":
            found = CMD_BLOCK.findall(c)
            cmd = found[-1] if found else ""
        elif m.get("role") == "user" and cmd is not None:
            out.append((cmd, c))
            cmd = None
    return out


def diff_lines(obs: str) -> list[tuple[str, str]]:
    out = []
    for x in obs.splitlines():
        if x.startswith(("+++", "---")) or x[:1] not in ("+", "-"):
            continue
        content = x[1:].strip()
        if len(content) >= MIN_LINE:
            out.append((x[0], content))
    return out


def audit_run(msgs: list[dict], row: dict, l1: dict) -> dict:
    rem, add = changed(row["patch"])
    bug_plus = {c.strip() for (_, c) in add if len(c.strip()) >= MIN_LINE}
    bug_minus = {c.strip() for (_, c) in rem if len(c.strip()) >= MIN_LINE}
    sigs = set(l1.get("f2p_signatures") or [])
    deleted = set(l1.get("f2p_deleted_files") or [])
    t = turns(msgs)
    rec = {
        "turns": len(t),
        "history_cmd": False,
        "any_git_log": False,
        "seen_bug_msg": False,
        "seen_f2p_msg": False,
        "bug_diff_shown": False,
        "deleted_tests_shown": False,
        "restore_or_read_old_file_cmd": False,
        "tests_restored_and_run": False,
        "bug_diff_shown_loose": False,
        "deleted_tests_shown_loose": False,
        "first_bug_diff_turn": None,
        "first_tests_turn": None,
    }
    restore_at = None
    for k, (cmd, obs) in enumerate(t):
        hist = bool(HISTORY_CMD.search(cmd))
        rec["history_cmd"] |= hist
        rec["any_git_log"] |= bool(ANY_LOG.search(cmd))
        rec["seen_bug_msg"] |= "Bug Patch" in obs
        rec["seen_f2p_msg"] |= "Remove F2P Tests" in obs
        if RESTORE_CMD.search(cmd):
            rec["restore_or_read_old_file_cmd"] = True
            restore_at = k if restore_at is None else restore_at
        if (
            restore_at is not None
            and not re.match(r"\s*git\b", cmd)
            and any(p in obs for p in deleted)
        ):
            rec["tests_restored_and_run"] = True
        dl = diff_lines(obs)
        if bug_minus:
            shown = (hist or "Bug Patch" in obs) and any(
                sign == "-" and c in bug_minus for sign, c in dl
            )
        else:
            shown = "Bug Patch" in obs and any(sign == "+" and c in bug_plus for sign, c in dl)
        loose = any(
            (sign == "+" and c in bug_plus)
            or (sign == "-" and c in bug_minus)
            or (hist and (c in bug_plus or c in bug_minus))
            for sign, c in dl
        )
        rec["bug_diff_shown_loose"] |= loose
        if shown and not rec["bug_diff_shown"]:
            rec["bug_diff_shown"], rec["first_bug_diff_turn"] = True, k
        minus = [x for x in obs.splitlines() if x.startswith("-") and not x.startswith("---")]
        tests = any(s in x for x in minus for s in sigs)
        rec["deleted_tests_shown_loose"] |= hist and (
            any(s in obs for s in sigs)
            or ("deleted file mode" in obs and any(d in obs for d in deleted))
        )
        if tests and not rec["deleted_tests_shown"]:
            rec["deleted_tests_shown"], rec["first_tests_turn"] = True, k
    return rec


def audit_arms(rows_all: dict[str, dict], l1_all: dict[str, dict]) -> dict:
    out = {}
    for stem, (repo, env, cond, agent) in ARMS.items():
        tf, rf = R / f"{stem}.traces.jsonl.gz", R / f"{stem}.json"
        if not tf.exists() or not rf.exists():
            out[stem] = {"missing": True}
            continue
        res = {r["instance_id"]: r for r in json.loads(rf.read_text())["runs"]}
        runs = []
        for line in gzip.open(tf, "rt"):
            tr = json.loads(line)
            iid, msgs = tr["instance_id"], tr.get("messages")
            r = res.get(iid)
            row = rows_all.get(iid)
            if not msgs or r is None or row is None or "infra_error" in r or r.get("crashed"):
                continue
            a = audit_run(msgs, row, l1_all.get(iid, {}))
            patch = r.get("patch") or ""
            a.update(
                {
                    "instance_id": iid,
                    "no_description": not (row.get("problem_statement") or "").strip(),
                    "resolved_S": bool((r.get("S") or {}).get("resolved")),
                    "exact_revert": is_revert(patch, row["patch"]),
                    "patch_edits_bug_files": bool(files_of(patch) & files_of(row["patch"])),
                }
            )
            runs.append(a)
        out[stem] = {
            "repository": repo,
            "environment": env,
            "condition": cond,
            "agent": agent,
            "runs": runs,
        }
    return out


def summarise(arms: dict) -> list[dict]:
    keys = [
        "history_cmd",
        "seen_bug_msg",
        "seen_f2p_msg",
        "bug_diff_shown",
        "deleted_tests_shown",
        "restore_or_read_old_file_cmd",
        "tests_restored_and_run",
        "bug_diff_shown_loose",
        "deleted_tests_shown_loose",
        "resolved_S",
        "exact_revert",
    ]
    groups: dict[tuple, list] = {}
    for a in arms.values():
        if a.get("missing"):
            continue
        g = (a["repository"], a["environment"], a["condition"], a["agent"])
        latest = {r["instance_id"]: r for r in a["runs"]}  # a later file replaces a re-run task
        groups.setdefault(g, {}).update(latest)
    out = []
    for (repo, env, cond, agent), runs in groups.items():
        for subset, keep in (("all", None), ("no description", True), ("with description", False)):
            sel = [r for r in runs.values() if keep is None or r["no_description"] == keep]
            if not sel:
                continue
            row = {
                "repository": repo,
                "environment": env,
                "condition": cond,
                "agent": agent,
                "subset": subset,
                "runs": len(sel),
            }
            row.update({k: sum(bool(r[k]) for r in sel) for k in keys})
            row["resolved_with_bug_diff"] = sum(
                r["resolved_S"] and r["bug_diff_shown"] for r in sel
            )
            row["resolved_with_tests"] = sum(
                r["resolved_S"] and (r["deleted_tests_shown"] or r["tests_restored_and_run"])
                for r in sel
            )
            row["resolved_with_neither"] = sum(
                r["resolved_S"]
                and not r["bug_diff_shown"]
                and not r["deleted_tests_shown"]
                and not r["tests_restored_and_run"]
                for r in sel
            )
            out.append(row)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mirrors", type=Path, required=True)
    ap.add_argument("--rows", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    rows_all, l1_all, l1_summary = {}, {}, {}
    for name, (key, files) in REPOS.items():
        rows = load_rows(a.rows, files)
        l1 = level1(a.mirrors / f"{key}.git", rows)
        rows_all.update(rows)
        l1_all.update(l1)
        found = [v for v in l1.values() if v["branch_found"]]
        ok = [v for v in found if v["structure_ok"]]
        l1_summary[name] = {
            "tasks": len(rows),
            "branches_found": len(found),
            "three_commit_structure": len(ok),
            "commit_counts": dict(Counter(v["n_commits"] for v in found)),
            "other_structures": dict(
                Counter(" | ".join(v["messages"]) for v in found if not v["structure_ok"])
            ),
            "bug_patch_equals_benchmark_patch": sum(
                bool(v.get("bug_patch_equals_row")) for v in ok
            ),
            "f2p_commit_only_deletes_files": sum(set(v["f2p_commit_status"]) == {"D"} for v in ok),
            "f2p_commit_status_counts": dict(
                sum((Counter(v["f2p_commit_status"]) for v in ok), Counter())
            ),
            "every_f2p_signature_in_deleted_content": sum(
                v["f2p_signatures_in_deleted"] == len(v["f2p_signatures"]) for v in ok
            ),
            "tasks_with_f2p_signatures": sum(bool(v["f2p_signatures"]) for v in ok),
        }
    arms = audit_arms(rows_all, l1_all)
    out = {
        "level1_exists": l1_summary,
        "level2_3_by_arm": summarise(arms),
        "rules": {
            "MIN_LINE": MIN_LINE,
            "HISTORY_CMD": HISTORY_CMD.pattern,
            "RESTORE_CMD": RESTORE_CMD.pattern,
        },
        "runs": {
            stem: [
                {
                    k: r[k]
                    for k in (
                        "instance_id",
                        "no_description",
                        "resolved_S",
                        "history_cmd",
                        "seen_bug_msg",
                        "seen_f2p_msg",
                        "bug_diff_shown",
                        "deleted_tests_shown",
                        "restore_or_read_old_file_cmd",
                        "tests_restored_and_run",
                        "bug_diff_shown_loose",
                        "deleted_tests_shown_loose",
                        "exact_revert",
                        "patch_edits_bug_files",
                        "first_bug_diff_turn",
                        "first_tests_turn",
                        "turns",
                    )
                }
                for r in a["runs"]
            ]
            for stem, a in arms.items()
            if not a.get("missing")
        },
    }
    a.out.write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out["level1_exists"], indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
