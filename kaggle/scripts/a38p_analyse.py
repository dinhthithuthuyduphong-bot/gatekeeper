"""Section 38, note 38-10 (A'): paired analysis, registered before the run (0 USD).

  python kaggle/scripts/a38p_analyse.py --pairs kaggle/data/a38p_prompts.jsonl.gz \
      --original kaggle/results/a38_results_2026111*.jsonl \
      --renamed kaggle/results/a38p_results_*.jsonl --model google/gemini-3.1-pro-preview \
      --alpha 0.025 --out kaggle/results/a38p_analysis.json

Unit: the saved call (pair of prompts). d_j = share of seeds with H on the original prompt (from
section 38) - share on the renamed prompt. One-sided exact sign-flip test over all 2^6 sign
assignments (the d_j are symmetric about 0 under H0: renaming does not change the distribution of
the per-call share). Reject at --alpha. G as secondary (reported, no decision).
"""

from __future__ import annotations

import argparse
import gzip
import itertools
import json
from pathlib import Path

import a38_analyse as an

N_SEEDS = 3  # registered (note 38-10): seeds 1, 2, 3


def signflip_p(d: list[float]) -> float:
    obs = sum(d)
    n = hits = 0
    for signs in itertools.product((1, -1), repeat=len(d)):
        n += 1
        hits += sum(s * x for s, x in zip(signs, d, strict=True)) >= obs - 1e-12
    return hits / n


def seeds_per_prompt(results: list[dict], model: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for r in an.dedupe(results):
        if r["model"] == model and r.get("ok"):
            out[r["sha256"]] = out.get(r["sha256"], 0) + 1
    return out


def shares(results: list[dict], model: str, rule) -> dict[str, float]:
    by: dict[str, list[bool]] = {}
    for r in an.dedupe(results):
        if r["model"] == model and r.get("ok"):
            by.setdefault(r["sha256"], []).append(an.has(rule, r["new_skills"]))
    return {k: sum(v) / len(v) for k, v in by.items()}


def analyse(pairs, original, renamed, model, alpha) -> dict:
    out = {"model": model, "alpha": alpha, "pairs": []}
    for name, rule in (("H", an.RULE), ("G", an.G)):
        so, sr = shares(original, model, rule), shares(renamed, model, rule)
        d = []
        for p in pairs:
            if p["pair_of"] in so and p["sha256"] in sr:
                d.append(so[p["pair_of"]] - sr[p["sha256"]])
                if name == "H":
                    out["pairs"].append(
                        {"pid": p["pid"], "original": so[p["pair_of"]], "renamed": sr[p["sha256"]]}
                    )
        out[name] = {
            "n_pairs": len(d),
            "mean_d": sum(d) / len(d) if d else None,
            "n_positive": sum(x > 0 for x in d),
            "n_negative": sum(x < 0 for x in d),
            "p_one_sided": signflip_p(d) if d else None,
        }
    n_seeds = seeds_per_prompt(renamed, model)
    out["renamed_seeds"] = {p["pid"]: n_seeds.get(p["sha256"], 0) for p in pairs}
    complete = all(v == N_SEEDS for v in out["renamed_seeds"].values())
    out["complete"] = complete  # registered: a missing call means no rejection
    out["reject_H"] = complete and out["H"]["p_one_sided"] <= alpha
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pairs", required=True, type=Path)
    ap.add_argument("--original", required=True, type=Path, nargs="+")
    ap.add_argument("--renamed", required=True, type=Path, nargs="+")
    ap.add_argument("--model", required=True)
    ap.add_argument("--alpha", required=True, type=float)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    read = lambda fs: [json.loads(x) for f in fs for x in f.read_text().splitlines() if x.strip()]  # noqa: E731
    pairs = [json.loads(x) for x in gzip.open(a.pairs, "rt")]
    res = analyse(pairs, read(a.original), read(a.renamed), a.model, a.alpha)
    a.out.write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps(res, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
