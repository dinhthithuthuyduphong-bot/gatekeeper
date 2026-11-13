"""Data for the paper's figures, recomputed from the raw result files (0 USD). The figures are
drawn by pgfplots in paper/main.tex from these files; no number is typed by hand.

  python scripts/make_figures.py --trial <worktree of origin/trial>

Writes
  paper/figures/eprocess.dat  task k and log10 E_k of the registered admission rule (theta = 0,
                              c = 0.5) on five paired streams, in gskill's order;
  paper/figures/nops.dat      resolved tasks out of the 34 Jinja test tasks without a description,
                              environment as shipped, by condition (scorer S).
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

THETA, C, ALPHA = 0.0, 0.5, 0.025  # as registered (section 25)
OUT = Path("paper/figures")


def curve(mod, skill: Path, none: Path) -> list[float]:
    from gatekeeper.eprocess import BettingEProcess

    pairs = mod.paired(json.loads(skill.read_text()), json.loads(none.read_text()))
    ep = BettingEProcess(theta=THETA, alpha=ALPHA, c=C)
    out = []
    for _, a, b in pairs:
        ep.update(float(not mod.passed(a, "S")) - float(not mod.passed(b, "S")))
        out.append(ep.log_e / math.log(10))
    return out


def solved_no_issue(res: Path, ids: set[str]) -> int:
    runs = json.loads(res.read_text())["runs"]
    return sum(bool((r.get("S") or {}).get("resolved")) for r in runs if r["instance_id"] in ids)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--trial", required=True, type=Path)
    ap.add_argument("--rows", required=True, type=Path)
    a = ap.parse_args()
    from make_numbers import s25_module

    mod = s25_module(a.trial)
    t, r = a.trial / "results", Path("results")
    streams = {
        "shipped": (t / "f1_skill_probe.json", t / "f1_probe.json"),
        "single": (t / "s25_leakfree_skill.json", t / "s25_leakfree_none.json"),
        "ablated": (r / "s29_ablate.json", r / "s29_none.json"),
        "relearned": (r / "s30_skill.json", r / "s30_none.json"),
        "pygments": (t / "s27pyg_skill_all.json", t / "s27pyg_none_all.json"),
    }
    cols = {k: curve(mod, *v) for k, v in streams.items()}
    n = min(len(v) for v in cols.values())
    OUT.mkdir(parents=True, exist_ok=True)
    lines = ["k " + " ".join(cols)]
    lines += [f"{i + 1} " + " ".join(f"{cols[k][i]:.4f}" for k in cols) for i in range(n)]
    (OUT / "eprocess.dat").write_text("\n".join(lines) + "\n")

    rows = [
        json.loads(x)
        for x in (a.rows / "swesmith_pallets__jinja.jsonl").read_text().splitlines()
        if x.strip()
    ]
    ids = {
        x["instance_id"]
        for x in rows
        if x["_gskill_split"] == "test" and not (x.get("problem_statement") or "").strip()
    }
    bars = [
        ("No skill", t / "f1_probe.json"),
        ("Learned skill", t / "f1_skill_probe.json"),
        ("Instruction removed", r / "s29_ablate.json"),
        ("Re-learned without leak", r / "s30_shipped34.json"),
    ]
    out = ["label y"] + [f"{{{lab}}} {solved_no_issue(f, ids)}" for lab, f in bars]
    (OUT / "nops.dat").write_text("\n".join(out) + "\n")
    print((OUT / "nops.dat").read_text(), len(ids))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
