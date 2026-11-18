"""Section 45 (W7-b): analysis registered before any model call (0 USD).

  python kaggle/scripts/w7_analyse.py --run-a <w7_A dir> --run-b <w7_B dir> --alpha 0.025 \
      --min-issues-b 5 --out kaggle/results/w7_analysis.json

Unit: the issue (task). An issue of a pool counts when XRepoSkill wrote at least one candidate
rule (Stage 1 output, candidates/<analyst>.jsonl, any analyst) for one of its pairs whose text has
a line matching G (`git log` or `git show`, as in section 38) -- the registered primary indicator.
Primary test: one-sided Fisher exact test that the share of such issues is larger in pool A
(shipped history) than in pool B (single-commit history), at --alpha; it is run only when pool B
has at least --min-issues-b issues with a pair (section 45: below that, power < 0.8 even in the
most favourable scenario of the registered table). Otherwise the result is descriptive.
Secondary, reported only: the same with H (RULE of section 29); merged and judged rules
(Stage 2a, 2b) whose title or body has a G line, with their gain and z (Stage 2c) and the n-gram
audit flag (Stage 2d).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from math import comb
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from make_ablation import RULE  # noqa: E402

G = re.compile(r"git log|git show", re.IGNORECASE)


def has(rule: re.Pattern, text: str) -> bool:
    return any(rule.search(line) for line in (text or "").splitlines())


def fisher_greater(a: int, n1: int, b: int, n2: int) -> float:
    """One-sided exact p: P(X >= a) for X hypergeometric with the margins (a + b, n1, n2)."""
    k, n = a + b, n1 + n2
    return sum(comb(n1, x) * comb(n2, k - x) for x in range(a, min(n1, k) + 1)) / comb(n, k)


def jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]


def pool_summary(run: Path) -> dict:
    pairs = jsonl(run / "pairs" / "pairs.jsonl")
    issues = sorted({p["instance_id"] for p in pairs})
    cands = [
        c
        for f in sorted((run / "candidates").glob("*.jsonl"))
        if f.name != "failed.jsonl"
        for c in jsonl(f)
    ]
    by_issue = {i: {"G": False, "H": False, "candidates": 0} for i in issues}
    for c in cands:
        iid = c["pair_id"].split("::", 1)[0]
        if iid not in by_issue:
            continue
        by_issue[iid]["candidates"] += 1
        by_issue[iid]["G"] |= has(G, c.get("rule", ""))
        by_issue[iid]["H"] |= has(RULE, c.get("rule", ""))
    judged = [r for f in sorted((run / "rules_judged").glob("*/rules.jsonl")) for r in jsonl(f)]
    scored = {
        r["rule_id"]: r
        for f in sorted((run / "rules_scored").glob("*/rules.jsonl"))
        for r in jsonl(f)
    }
    flagged = {a.get("rule_id") for a in jsonl(run / "ngram_audit.jsonl") if a.get("flagged")}
    g_rules = []
    for r in judged:
        text = f"{r.get('title', '')}\n{r.get('body', '')}"
        if has(G, text):
            v = (scored.get(r["rule_id"]) or {}).get("validation") or {}
            g_rules.append(
                {
                    "rule_id": r["rule_id"],
                    "title": r.get("title"),
                    "support": r.get("support"),
                    "score_status": v.get("status"),
                    "gain": v.get("lift"),  # score.py: Mantel-Haenszel risk difference "lift"
                    "z": v.get("z"),
                    "ngram_flagged": r["rule_id"] in flagged,
                }
            )
    return {
        "pairs": len(pairs),
        "issues": len(issues),
        "candidates": len(cands),
        "issues_G": sum(v["G"] for v in by_issue.values()),
        "issues_H": sum(v["H"] for v in by_issue.values()),
        "judged_rules": len(judged),
        "judged_rules_G": g_rules,
        "failed_calls": len(jsonl(run / "candidates" / "failed.jsonl")),
    }


def analyse(run_a: Path, run_b: Path, alpha: float, min_issues_b: int) -> dict:
    a, b = pool_summary(run_a), pool_summary(run_b)
    out = {"alpha": alpha, "min_issues_b": min_issues_b, "A": a, "B": b}
    for name in ("G", "H"):
        key = f"issues_{name}"
        if a["issues"] and b["issues"]:
            out[f"p_one_sided_{name}"] = fisher_greater(a[key], a["issues"], b[key], b["issues"])
    out["test_run"] = b["issues"] >= min_issues_b and a["issues"] > 0
    out["reject_G"] = bool(out["test_run"] and out.get("p_one_sided_G", 1.0) <= alpha)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-a", required=True, type=Path)
    ap.add_argument("--run-b", required=True, type=Path)
    ap.add_argument("--alpha", required=True, type=float)
    ap.add_argument("--min-issues-b", required=True, type=int)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    res = analyse(a.run_a, a.run_b, a.alpha, a.min_issues_b)
    a.out.write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps(res, indent=1)[:4000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
