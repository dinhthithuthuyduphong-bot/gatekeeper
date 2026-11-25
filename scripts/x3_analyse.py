#!/usr/bin/env python3
"""Section 49 (X3'): compare the blind human labels with the detector's labels (0 USD).

Registered before any label exists. Inputs: the labels exported from the labelling page (one
record per trace code: q1, q2, q3 in {"yes", "no"}, q4 in {"yes", "no", "unclear", "na"}, note),
the key (results/x3_codes.json) and the detector's per-run fields (results/history_audit.json).

  python scripts/x3_analyse.py --labels results/x3_labels.json --key results/x3_codes.json \
      --audit results/history_audit.json --out results/x3_analysis.json

Reported, all as counts over the whole stratum (no sample, so no interval and no threshold):
  * for Q1, Q2, Q3: the 2 x 2 table (human x detector), agreements, on all traces and on the
    resolved ones;
  * the paper's counts from the human labels: Q2 per cohort, Q3 overall, resolved with Q2;
  * Q4 against exact_revert and against the outcome (descriptive);
  * every trace on which human and detector disagree.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

COHORT = {
    "s27_trace34": "seed 41",
    "s27_trace34b": "seed 41",
    "s33_ship_skill": "seed 51",
    "s35_ship_skill": "new tasks",
}
YES_NO = {"yes", "no"}
Q4_VALUES = {"yes", "no", "unclear", "na"}


def machine(run: dict) -> dict:
    return {
        "q1": run["seen_bug_msg"],
        "q2": run["bug_diff_shown"],
        "q3": run["deleted_tests_shown"] or run["tests_restored_and_run"],
    }


def table(pairs: list[tuple[bool, bool]]) -> dict:
    c = Counter(pairs)
    return {
        "human_yes_detector_yes": c[(True, True)],
        "human_yes_detector_no": c[(True, False)],
        "human_no_detector_yes": c[(False, True)],
        "human_no_detector_no": c[(False, False)],
        "agree": c[(True, True)] + c[(False, False)],
        "n": len(pairs),
    }


def validate(labels: dict[str, dict], codes: dict[str, dict]) -> list[str]:
    errs = []
    missing = sorted(set(codes) - set(labels))
    if missing:
        errs.append(f"missing labels: {missing}")
    for code, lab in labels.items():
        if code not in codes:
            errs.append(f"unknown code {code}")
            continue
        for q in ("q1", "q2", "q3"):
            if lab.get(q) not in YES_NO:
                errs.append(f"{code} {q}={lab.get(q)!r}")
        q4 = lab.get("q4")
        if q4 not in Q4_VALUES:
            errs.append(f"{code} q4={q4!r}")
        elif (lab.get("q2") == "no") != (q4 == "na"):
            errs.append(f"{code}: q4 must be 'na' exactly when q2 is 'no'")
    return errs


def analyse(labels: dict[str, dict], key: dict, audit: dict) -> dict:
    runs = {
        (stem, r["instance_id"]): r
        for stem in COHORT
        for r in (
            audit["runs"][stem]["runs"]
            if isinstance(audit["runs"][stem], dict)
            else audit["runs"][stem]
        )
    }
    rows = []
    for code, k in sorted(key["codes"].items()):
        run = runs[(k["stem"], k["instance_id"])]
        lab = labels[code]
        rows.append(
            {
                "code": code,
                "cohort": COHORT[k["stem"]],
                "resolved": run["resolved_S"],
                "exact_revert": run["exact_revert"],
                "human": {q: lab[q] == "yes" for q in ("q1", "q2", "q3")},
                "q4": lab["q4"],
                "detector": machine(run),
                "note": lab.get("note", ""),
            }
        )
    out: dict = {"n": len(rows), "tables": {}, "tables_resolved": {}}
    for q in ("q1", "q2", "q3"):
        out["tables"][q] = table([(r["human"][q], r["detector"][q]) for r in rows])
        out["tables_resolved"][q] = table(
            [(r["human"][q], r["detector"][q]) for r in rows if r["resolved"]]
        )
    out["paper_counts"] = {
        "q2_by_cohort": {
            c: {
                "human": sum(r["human"]["q2"] for r in rows if r["cohort"] == c),
                "detector": sum(r["detector"]["q2"] for r in rows if r["cohort"] == c),
                "n": sum(r["cohort"] == c for r in rows),
            }
            for c in sorted(set(COHORT.values()))
        },
        "q3_any": {
            "human": sum(r["human"]["q3"] for r in rows),
            "detector": sum(r["detector"]["q3"] for r in rows),
        },
        "resolved_with_q2": {
            "human": sum(r["human"]["q2"] for r in rows if r["resolved"]),
            "detector": sum(r["detector"]["q2"] for r in rows if r["resolved"]),
            "resolved": sum(r["resolved"] for r in rows),
        },
    }
    q4 = [r for r in rows if r["q4"] != "na"]
    out["q4"] = {
        "by_exact_revert": {
            v: dict(Counter(str(r["exact_revert"]) for r in q4 if r["q4"] == v))
            for v in ("yes", "no", "unclear")
        },
        "by_resolved": {
            v: dict(Counter(str(r["resolved"]) for r in q4 if r["q4"] == v))
            for v in ("yes", "no", "unclear")
        },
    }
    out["disagreements"] = [
        {
            "code": r["code"],
            "question": q,
            "human": r["human"][q],
            "detector": r["detector"][q],
            "resolved": r["resolved"],
            "note": r["note"],
        }
        for r in rows
        for q in ("q1", "q2", "q3")
        if r["human"][q] != r["detector"][q]
    ]
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--labels", type=Path, required=True)
    ap.add_argument("--key", type=Path, required=True)
    ap.add_argument("--audit", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    labels = json.loads(a.labels.read_text())
    key = json.loads(a.key.read_text())
    errs = validate(labels, key["codes"])
    if errs:
        print("INVALID LABELS", *errs[:20], sep="\n  ")
        return 1
    out = analyse(labels, key, json.loads(a.audit.read_text()))
    a.out.write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: out[k] for k in ("tables", "paper_counts")}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
