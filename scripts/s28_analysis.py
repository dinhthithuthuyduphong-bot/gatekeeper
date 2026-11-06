"""Section 28 step 2 analysis: effects (endpoint S) with the network rescoring substituted (0 USD).

  python scripts/s28_analysis.py --e2-logs <dir> --rescored results/s28_rescored.json

For each registered pair (harness_audit.py linking), each side's resolved flag is taken from the
rescored report when the rescore produced one (results/s28_rescored.json, key exp|run|arm|iid);
otherwise the original report is kept (note 28-2) and the case is counted. Sides with no original
report stay unresolved. Effect and task-level bootstrap CI exactly as harness_audit.py. Writes
results/s28_effects.json with old and new numbers side by side.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness_audit as ha  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--e2-logs", type=Path, required=True)
    ap.add_argument("--rescored", type=Path, required=True)
    a = ap.parse_args()
    resc = json.loads(a.rescored.read_text())
    reports = ha.load_reports([Path("logs/run_evaluation"), a.e2_logs / "logs/run_evaluation"])
    rng = np.random.default_rng(ha.SEED)
    out, counts = {}, defaultdict(lambda: defaultdict(int))
    for exp, files in ha.EXPERIMENTS.items():
        mine = [r for r in reports if r["name"].startswith(ha.PREFIX[exp])]
        idx = defaultdict(list)
        for r in mine:
            idx[(r["seed"], r["arm"], r["iid"])].append(r)
        acc = defaultdict(lambda: {"old": defaultdict(list), "new": defaultdict(list)})
        for f in files:
            run = json.loads(Path(f"results/pilot/{f}.json").read_text())
            seed = int(ha.SEED_RE.search(f + "-").group(1))
            for skill, v in run["skills"].items():
                for p in v["pairs"]:
                    iid = p["instance_id"]
                    side = {}
                    for arm, loss in ((skill, p["loss_with"]), ("none", p["loss_without"])):
                        rep = ha.link(loss, idx[(seed, arm, iid)])
                        old = bool(rep and rep["rep"].get("resolved"))
                        new = old
                        if rep is not None:
                            r2 = resc.get(f"{exp}|{rep['name']}|{arm}|{iid}")
                            if r2 is None:
                                counts[exp]["not_in_manifest"] += 1
                            elif r2.get("report"):
                                new = bool(r2.get("resolved"))
                                counts[exp]["rescored"] += 1
                                tag = "same" if new == old else ("flip_up" if new else "flip_down")
                                counts[exp][tag] += 1
                            else:
                                counts[exp]["rescore_no_report_kept_original"] += 1
                        side[arm] = (old, new)
                    o = float(side[skill][0]) - float(side["none"][0])
                    n = float(side[skill][1]) - float(side["none"][1])
                    acc[skill]["old"][iid].append(o)
                    acc[skill]["new"][iid].append(n)
        need = len(files)
        out[exp] = {}
        for skill, d in acc.items():
            out[exp][skill] = {}
            for k in ("old", "new"):
                x = np.array([np.mean(v) for v in d[k].values() if len(v) == need])
                out[exp][skill][k] = {
                    "n_tasks": int(x.size),
                    "effect": float(x.mean()),
                    "ci": ha.boot_ci(x, rng),
                }
    res = {"effects": out, "counts": {e: dict(c) for e, c in counts.items()}}
    Path("results/s28_effects.json").write_text(json.dumps(res, indent=1) + "\n")
    for e, sk in out.items():
        print(e, dict(counts[e]))
        for s, v in sk.items():
            print(
                f"  {s}: old {v['old']['effect']:+.3f} {v['old']['ci']} -> "
                f"new {v['new']['effect']:+.3f} [{v['new']['ci'][0]:+.3f},{v['new']['ci'][1]:+.3f}]"
                f" (n={v['new']['n_tasks']})"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
