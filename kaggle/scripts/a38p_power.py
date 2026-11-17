"""Section 38, note 38-10 (A'): power and size of the registered paired rule (0 USD).

  python kaggle/scripts/a38p_power.py --out kaggle/results/a38p_power.json

Originals: the 3 seeds per call actually observed in section 38 (fixed). Renamed: 3 seeds per call,
each with H with probability q. Rule: one-sided exact sign-flip test, reject at 0.025.
null: each renamed seed has H with the probability equal to that call's observed original share.
"""

from __future__ import annotations

import argparse
import glob
import gzip
import json
import random
from pathlib import Path

import a38_analyse as an
import a38p_analyse as pa

ROOT = Path(__file__).resolve().parents[2]
MODEL, ALPHA, REPS, SEED = "google/gemini-3.1-pro-preview", 0.025, 20000, 4405


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    pairs = [json.loads(x) for x in gzip.open(ROOT / "kaggle/data/a38p_prompts.jsonl.gz", "rt")]
    files = sorted(glob.glob(str(ROOT / "kaggle/results/a38_results_2026111*.jsonl")))
    rows = [json.loads(x) for f in files for x in open(f) if x.strip()]
    so = pa.shares(rows, MODEL, an.RULE)
    orig = [so[p["pair_of"]] for p in pairs]
    rng = random.Random(SEED)

    def rate(qs):
        hits = 0
        for _ in range(REPS):
            d = [
                o - sum(rng.random() < q for _ in range(3)) / 3
                for o, q in zip(orig, qs, strict=True)
            ]
            hits += pa.signflip_p(d) <= ALPHA
        return hits / REPS

    out = {
        "model": MODEL,
        "alpha": ALPHA,
        "reps": REPS,
        "seed": SEED,
        "original_shares": orig,
        "rejection_rate": {},
    }
    for name, q in (
        ("renamed like clean cell (0.05)", 0.05),
        ("like no-leak cell (0.29)", 0.29),
        ("half (0.50)", 0.50),
    ):
        out["rejection_rate"][name] = rate([q] * 6)
    out["rejection_rate"]["null (renamed = original share)"] = rate(orig)
    a.out.write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
