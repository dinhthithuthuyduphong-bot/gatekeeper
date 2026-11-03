"""RQ1-mini (docs/preregistration_e1.md section 6): decision rules on screening trials, judged
against held-out truth. Usage:
  python scripts/rq1_mini.py --e1 g1-e1-s41 g1-e1-s51 g1-e1-s61 [--g1 g1-c-s11 g1-c-s21 g1-c-s31]
  python scripts/rq1_mini.py --sskb       (external check on SWE-Skills-Bench, exploratory)
Writes results/rq1_mini.json (or results/rq1_mini_sskb.json).
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import analyze_g1_final as gf  # noqa: E402

from gatekeeper.alpha_ledger import AlphaLedger  # noqa: E402
from gatekeeper.eprocess import run_admission  # noqa: E402

ALPHA = 0.05
BUDGET = 40
ORDER_SEED = "2027-order"


def z_by_task(run: dict, skill: str) -> dict[str, float]:
    return gf.z_resolved(run.get("skills", {}).get(skill, {}).get("pairs", []))


def decide(screen: list[float], alpha_cell: float) -> dict[str, bool]:
    """Every rule sees the SAME screening data: the first BUDGET trials."""
    screen = screen[:BUDGET]
    return {
        "Gatekeeper": run_admission(screen, 1e-9, alpha_cell, budget=BUDGET).admitted,
        "Plug-in (mean < 0)": bool(np.mean(screen) < 0) if screen else False,
        "B1 never": False,
        "B2 always": True,
    }


def label(truth: list[float]) -> str:
    m = float(np.mean(truth))
    return "harmful" if m > 0 else ("beneficial" if m < 0 else "neutral")


def label_tested(truth: list[float], alpha_cell: float) -> str:
    """Three classes from exact sign-flip tests on the INDEPENDENT held-out data (advisor_qa 5.2e):
    harm / benefit established if the one-sided test rejects at alpha_cell, else undetermined."""
    if gf.sign_flip_p([-v for v in truth]) <= alpha_cell:
        return "harmful"
    if gf.sign_flip_p(truth) <= alpha_cell:
        return "beneficial"
    return "undetermined"


def summarise_tested(cells: dict[str, dict]) -> dict:
    rules = next(iter(cells.values()))["decisions"].keys()
    out = {}
    for r in rules:
        by = {
            k: [c for c in cells.values() if c["label_tested"] == k]
            for k in ("harmful", "beneficial", "undetermined")
        }
        out[r] = {
            "harmful_established": len(by["harmful"]),
            "harmful_acceptance": (
                sum(c["decisions"][r] for c in by["harmful"]) / len(by["harmful"])
            )
            if by["harmful"]
            else None,
            "beneficial_established": len(by["beneficial"]),
            "clean_reuse_coverage": (
                sum(c["decisions"][r] for c in by["beneficial"]) / len(by["beneficial"])
            )
            if by["beneficial"]
            else None,
            "admitted_undetermined": sum(c["decisions"][r] for c in by["undetermined"]),
        }
    return out


def summarise(cells: dict[str, dict]) -> dict:
    rules = next(iter(cells.values()))["decisions"].keys()
    out = {}
    for r in rules:
        adm = [c for c in cells.values() if c["decisions"][r]]
        harm = [c for c in cells.values() if c["label"] == "harmful"]
        ben = [c for c in cells.values() if c["label"] == "beneficial"]
        out[r] = {
            "admitted": len(adm),
            "harmful_acceptance": (sum(c["decisions"][r] for c in harm) / len(harm))
            if harm
            else None,
            "clean_reuse_coverage": (sum(c["decisions"][r] for c in ben) / len(ben))
            if ben
            else None,
            "mean_true_STR_of_admitted": float(np.mean([c["str_true"] for c in adm]))
            if adm
            else None,
        }
    return out


def cell_from_runs(screen_run: dict, truth_runs: list[dict], skill: str) -> dict:
    s = z_by_task(screen_run, skill)
    tr = [z_by_task(r, skill) for r in truth_runs]
    tasks = sorted(t for t in s if all(t in x for x in tr))
    # preregistration_e1.md section 6: random.Random("2027-order"), a fresh generator per cell
    random.Random(ORDER_SEED).shuffle(tasks)
    screen = [s[t] for t in tasks]
    truth_task = [float(np.mean([x[t] for x in tr])) for t in tasks]
    return {"skill": skill, "n_tasks": len(tasks), "screen": screen, "truth_task": truth_task}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--e1", nargs=3, default=None)
    ap.add_argument("--g1", nargs=3, default=None)
    ap.add_argument("--sskb", action="store_true")
    ap.add_argument(
        "--e2",
        nargs=3,
        default=None,
        help="E2 cell (preregistration_e2.md section 5.5): its own hypothesis at alpha 0.05",
    )
    a = ap.parse_args()
    cells: dict[str, dict] = {}
    if a.sskb:
        raw: dict[tuple[str, str], dict[int, float]] = defaultdict(dict)
        with Path("data/external/swe-skills-bench/ALL_combined_cells.csv").open() as fh:
            for r in csv.DictReader(fh):
                b = int(r["requirement_batch"].replace("batch", ""))
                raw[(r["harness_model"], r["skill"])][b] = (
                    float(r["none_pass_rate"]) - float(r["one_pass_rate"])
                ) / 100.0
        alpha_cell = ALPHA / len(raw)
        for (cfg, sk), zs in raw.items():
            for half, (sa, sb) in {"A": ((1, 5), (6, 10)), "B": ((6, 10), (1, 5))}.items():
                scr = [zs[b] for b in range(sa[0], sa[1] + 1) if b in zs]
                tru = [zs[b] for b in range(sb[0], sb[1] + 1) if b in zs]
                cells[f"{cfg}/{sk}/{half}"] = {
                    "decisions": decide(scr, alpha_cell),
                    "label": label(tru),
                    "str_true": float(np.mean(tru)),
                }
        out = {"alpha_cell": alpha_cell, "n_cells": len(cells), "summary": summarise(cells)}
        Path("results/rq1_mini_sskb.json").write_text(json.dumps(out, indent=1) + "\n")
        print(json.dumps(out, indent=1))
        return 0
    load = lambda n: json.loads(Path(f"results/pilot/{n}.json").read_text())  # noqa: E731
    if a.e2:  # separate from the K = 7 family of E1 (pre-registered as its own hypothesis)
        e2 = [load(n) for n in a.e2]
        sp = cell_from_runs(e2[0], e2[1:], "xreposkill")
        cell = {
            "n_tasks": sp["n_tasks"],
            "decisions": decide(sp["screen"], ALPHA),
            "label_tested": label_tested(sp["truth_task"], ALPHA),
            "label": label(sp["truth_task"]) if sp["truth_task"] else None,
            "str_true": float(np.mean(sp["truth_task"])) if sp["truth_task"] else None,
            "truth_p_benefit": gf.sign_flip_p(sp["truth_task"]),
            "truth_p_harm": gf.sign_flip_p([-v for v in sp["truth_task"]]),
            "screen_mean": float(np.mean(sp["screen"][:BUDGET])) if sp["screen"] else None,
            "screen_trials_used": min(BUDGET, len(sp["screen"])),
        }
        out = {"alpha_cell": ALPHA, "cell": cell, "runs": a.e2}
        Path("results/rq1_e2.json").write_text(json.dumps(out, indent=1) + "\n")
        print(json.dumps(out, indent=1))
        return 0
    specs = []
    if a.e1:
        e1 = [load(n) for n in a.e1]
        for sk in e1[0]["skills"]:
            specs.append(cell_from_runs(e1[0], e1[1:], sk))
    if a.g1:
        g1 = [load(n) for n in a.g1]
        specs.append(cell_from_runs(g1[0], g1[1:], "validation-error"))
    ledger = AlphaLedger.from_plan(ALPHA, [s["skill"] for s in specs])
    for s in specs:
        cells[s["skill"]] = {
            "n_tasks": s["n_tasks"],
            "decisions": decide(s["screen"], ledger.cell(s["skill"])),
            "label": label(s["truth_task"]),
            "str_true": float(np.mean(s["truth_task"])),
            "truth_p_benefit": gf.sign_flip_p(s["truth_task"]),
            "truth_p_harm": gf.sign_flip_p([-v for v in s["truth_task"]]),
            "screen_mean": float(np.mean(s["screen"][:BUDGET])),
            "label_tested": label_tested(s["truth_task"], ledger.cell(s["skill"])),
        }
    out = {
        "alpha_cell": ALPHA / len(specs),
        "cells": cells,
        "summary_tested_labels": summarise_tested(cells),  # primary (advisor_qa 5.2e)
        "summary_point_labels": summarise(cells),  # secondary: sign of the held-out estimate
    }
    Path("results/rq1_mini.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out["summary_tested_labels"], indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
