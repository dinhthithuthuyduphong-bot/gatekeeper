"""Risk alerts of sections 46-47 (execution note 47-4). 0 USD; run after every paid stage.

Every alert stops the chain of stages (exit 10) so that @thuthuy is asked before anything else is
spent. No alert changes a registered rule or reading (R5): each one only reports a condition that
the registration already names, with its threshold taken from a registered or derived number.

  A1 infra       a probe run carries `infra_error` (registered norm: 0 infra failures)
  A2 quota       an error or crash text names a quota, rate or billing limit (lesson of A124)
  A3 incomplete  a probe file has fewer runs than the arm's registered n (cap reached or aborted)
  A4 money       spent + expected of the stages still to run before scoring > approved_total -
                 sum of the scoring caps (note 47-3: 35.00 - 10.491 = 24.509), i.e. the cumulative
                 guard is now predicted to block the five scoring arms
  A5 direction   a finished learning run gives the Q1 reading the registration marks as not
                 expected: x1ship best skill without a line matching RULE of section 29, or
                 x1lf best skill with such a line (section 47, "Cách đọc")

An alert that @thuthuy has read and decided to continue past is listed in configs/x1_ack.json
(id plus file or tag, with the date and the quoted decision); listed alerts are reported but no
longer stop the chain.

  python scripts/x1_alerts.py --dir /tmp/prev --dir results --caps configs/x1.json \
      --ack configs/x1_ack.json --stage learnship --out results/x1_alerts_learnship.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_ablation import RULE  # noqa: E402  (section 29's registered rule)

QUOTA = re.compile(r"\b429\b|RESOURCE_EXHAUSTED|quota|rate.?limit|billing", re.IGNORECASE)
# probe file stem (after the prefix) -> arm key in configs/x1.json
PROBES = {
    "x2_none": "x2_none",
    "x2_skill": "x2_skill",
    "x1eval_ship_none": "score_ship_none",
    "x1eval_ship_skill": "score_ship_skill",
    "x1eval_lf_none": "score_lf_none",
    "x1eval_lf_skill": "score_lf_skill",
    "x1eval_lfskill_ship34": "score_lfskill_on_ship34",
}
LEARN = {"x1ship": "learn_ship", "x1lf": "learn_lf"}
PRE_SCORING_PROBES = ("x2_none", "x2_skill")


def _find(dirs: list[Path], name: str) -> Path | None:
    for d in reversed(dirs):  # later directories hold the newer files
        p = d / name
        if p.exists():
            return p
    return None


def alerts(dirs: list[Path], caps: dict, prefix: str) -> list[dict]:
    arms, out = caps["arms"], []
    spent, remaining = 0.0, 0.0
    for stem, key in PROBES.items():
        p = _find(dirs, f"{prefix}{stem}.json")
        if p is None:
            if stem in PRE_SCORING_PROBES:
                remaining += arms[key]["expected"]
            continue
        d = json.loads(p.read_text())
        spent += float(d.get("spent_usd") or 0.0)
        runs = d.get("runs", [])
        bad = [r["instance_id"] for r in runs if "infra_error" in r]
        if bad:
            out.append({"id": "A1", "file": p.name, "tasks": bad})
        texts = [str(r.get("infra_error", "")) + str(r.get("crash_head") or "") for r in runs]
        if any(QUOTA.search(t) for t in texts):
            out.append({"id": "A2", "file": p.name})
        n = arms[key]["n"] if not prefix else d.get("n_tasks", len(runs))
        if len(runs) < n:
            out.append({"id": "A3", "file": p.name, "runs": len(runs), "registered_n": n})
    for tag, key in LEARN.items():
        led = [_find(dirs, f"{prefix}{tag}_learn_ledger_h{h}.json") for h in (1, 2)]
        totals = [float(json.loads(p.read_text())["spent_total"]) for p in led if p]
        got = max(totals) if totals else 0.0
        spent += got
        if led[1] is None:  # learning not finished: what is still expected of it
            remaining += max(arms[key]["expected"] - got, 0.0)
        elif not prefix:  # a dry run's skill comes from a scripted model: A5 is not read there
            sk = _find(dirs, f"{prefix}{tag}_best_skills.txt")
            hits = [ln for ln in sk.read_text().splitlines() if RULE.search(ln)] if sk else None
            if hits is None:
                out.append({"id": "A5", "tag": tag, "why": "best_skills.txt missing"})
            elif (tag == "x1ship") == (not hits):
                out.append({"id": "A5", "tag": tag, "history_lines": len(hits)})
    scoring = sum(v["cap"] for k, v in arms.items() if k.startswith("score_") and v["vertex"])
    limit = round(caps["approved_total"] - scoring, 3)
    scored = any(_find(dirs, f"{prefix}{s}.json") for s in PROBES if s.startswith("x1eval_"))
    if not scored and spent + remaining > limit + 1e-9:
        out.append(
            {
                "id": "A4",
                "spent": round(spent, 3),
                "still_expected": round(remaining, 3),
                "limit_before_scoring": limit,
            }
        )
    return out


def acknowledged(found: list[dict], acks: list[dict]) -> tuple[list[dict], list[dict]]:
    """Split alerts into those @thuthuy acknowledged (same id and same file or tag) and the rest."""

    def key(a: dict) -> tuple:
        return (a["id"], a.get("file") or a.get("tag"))

    keys = {key(a) for a in acks}
    return [a for a in found if key(a) in keys], [a for a in found if key(a) not in keys]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True, type=Path, action="append")
    ap.add_argument("--caps", required=True, type=Path)
    ap.add_argument("--ack", required=True, type=Path)
    ap.add_argument("--stage", required=True)
    ap.add_argument("--prefix", default="", help='"dry" for the files of a free dry run')
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    found = alerts(a.dir, json.loads(a.caps.read_text()), a.prefix)
    acked, stop = acknowledged(found, json.loads(a.ack.read_text())["acknowledged"])
    rec = {"stage": a.stage, "prefix": a.prefix, "alerts": stop, "acknowledged": acked}
    rec["stop"] = bool(stop)
    found = stop
    a.out.write_text(json.dumps(rec, indent=1) + "\n")
    print(json.dumps(rec, indent=1))
    if found:
        print("ALERT: stop the chain of stages and ask @thuthuy before spending more (note 47-4)")
    return 10 if found else 0


if __name__ == "__main__":
    raise SystemExit(main())
