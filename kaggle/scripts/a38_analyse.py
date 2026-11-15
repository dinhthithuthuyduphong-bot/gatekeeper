"""Section 38 A: analysis registered in kaggle/preregistration_s38.md (0 USD, after the runs).

  python kaggle/scripts/a38_analyse.py --prompts kaggle/data/a38_prompts.jsonl.gz \
      --results kaggle/results/a38_results_*.jsonl --reference <gemini model key> \
      --out kaggle/results/a38_analysis.json

Endpoints (per returned skill, extracted exactly as gskill does):
  H  the skill has a line matching RULE of section 29 (scripts/make_ablation.py);
  G  the skill has a line matching `git log` or `git show` (the two commands RULE names).
Unit of inference: the saved call (seeds of one call are not independent of each other).
Primary contrast per model: mean over calls of the per-call share of seeds with H, in cell
leak/ablated minus cell noleak_leaky_env/ablated (same two runs, same parent ablation).
One-sided exact permutation p-value over all relabellings of those calls (Hemerik and Goeman
2018); Holm (1979) over the cross-vendor models at family level --alpha (registered: 0.025).
"""

from __future__ import annotations

import argparse
import gzip
import itertools
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from make_ablation import RULE  # noqa: E402

G = re.compile(r"git log|git show", re.IGNORECASE)
PRIMARY = ("leak/ablated", "noleak_leaky_env/ablated")
SECONDARY = (("leak/ablated", "clean/ablated"), ("leak/original", "leak/ablated"))


def has(rule: re.Pattern, skill: str) -> bool:
    return any(rule.search(line) for line in skill.splitlines())


def perm_p(a: list[float], b: list[float]) -> float:
    """Exact one-sided p of mean(a) - mean(b) under all relabellings of the pooled calls."""
    pool, k = a + b, len(a)
    obs = sum(a) / k - sum(b) / len(b)
    tot = sum(pool)
    n = hits = 0
    for idx in itertools.combinations(range(len(pool)), k):
        s = sum(pool[i] for i in idx)
        d = s / k - (tot - s) / len(b)
        n += 1
        hits += d >= obs - 1e-12
    return hits / n


def holm(ps: dict[str, float], alpha: float) -> dict[str, bool]:
    order = sorted(ps, key=ps.get)
    out, stop = {}, False
    for i, m in enumerate(order):
        stop = stop or ps[m] > alpha / (len(order) - i)
        out[m] = not stop
    return out


def per_call(prompts: list[dict], results: list[dict], model: str, rule) -> dict[str, list[float]]:
    by_sha: dict[str, list[bool]] = {}
    for r in results:
        if r["model"] == model and r.get("ok"):
            by_sha.setdefault(r["sha256"], []).append(has(rule, r["new_skills"]))
    cells: dict[str, list[float]] = {}
    for p in prompts:
        v = by_sha.get(p["sha256"])
        if v:
            cells.setdefault(f"{p['condition']}/{p['variant']}", []).append(sum(v) / len(v))
    return cells


def analyse(prompts, results, reference: str, alpha: float) -> dict:
    models = sorted({r["model"] for r in results})
    out = {"alpha": alpha, "reference": reference, "models": {}}
    for m in models:
        row = {"n_ok": sum(1 for r in results if r["model"] == m and r.get("ok"))}
        row["n_failed"] = sum(1 for r in results if r["model"] == m and not r.get("ok"))
        for name, rule in (("H", RULE), ("G", G)):
            cells = per_call(prompts, results, m, rule)
            e = {c: {"calls": len(v), "mean": sum(v) / len(v)} for c, v in cells.items()}
            for a, b in (PRIMARY, *SECONDARY):
                if cells.get(a) and cells.get(b):
                    e[f"{a} - {b}"] = {
                        "diff": e[a]["mean"] - e[b]["mean"],
                        "p_one_sided": perm_p(cells[a], cells[b]),
                    }
            row[name] = e
        out["models"][m] = row
    key = f"{PRIMARY[0]} - {PRIMARY[1]}"
    ps = {
        m: v["H"][key]["p_one_sided"]
        for m, v in out["models"].items()
        if m != reference and key in v["H"]
    }
    out["holm_primary_H"] = holm(ps, alpha) if ps else {}
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompts", required=True, type=Path)
    ap.add_argument("--results", required=True, type=Path, nargs="+")
    ap.add_argument("--reference", required=True)
    ap.add_argument("--alpha", required=True, type=float)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    prompts = [json.loads(x) for x in gzip.open(a.prompts, "rt")]
    results = [json.loads(x) for f in a.results for x in f.read_text().splitlines() if x.strip()]
    res = analyse(prompts, results, a.reference, a.alpha)
    a.out.write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps(res, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
