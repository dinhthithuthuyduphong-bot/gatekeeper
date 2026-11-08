"""Section 28m step 2: the exact agent patches to rescore with network (0 USD).

  python scripts/s28_manifest.py --e2-logs <dir> --e2-runs <dir>

Rescore set (registered rule): instances of E1/E2/T4 with a network signature in at least one
original test_output.txt (results/s28_rescore_set.json). For every registered pair of such an
instance, the report that produced each side is found as in harness_audit.py (same seed and arm,
loss equal to the registered loss), and the patch is read from runs/<name>/<arm>/agent/
preds_scored.json of that report's run - the very file the harness scored. A side with no report
(registered loss 2/3: no submission / not applied / timed out) is not rescored. Writes
results/s28_manifest.json.gz: one entry per (experiment, run, arm, instance).
"""

from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness_audit as ha  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--e2-logs", type=Path, required=True)
    ap.add_argument("--e2-runs", type=Path, required=True)
    a = ap.parse_args()
    rescore = json.loads(Path("results/s28_rescore_set.json").read_text())
    reports = ha.load_reports([Path("logs/run_evaluation"), a.e2_logs / "logs/run_evaluation"])
    entries, missing = {}, []
    for exp, files in ha.EXPERIMENTS.items():
        mine = [r for r in reports if r["name"].startswith(ha.PREFIX[exp])]
        idx: dict = {}
        for r in mine:
            idx.setdefault((r["seed"], r["arm"], r["iid"]), []).append(r)
        for f in files:
            run = json.loads(Path(f"results/pilot/{f}.json").read_text())
            seed = int(ha.SEED_RE.search(f + "-").group(1))
            for skill, v in run["skills"].items():
                for p in v["pairs"]:
                    iid = p["instance_id"]
                    if iid not in rescore[exp]:
                        continue
                    for arm, loss in ((skill, p["loss_with"]), ("none", p["loss_without"])):
                        rep = ha.link(loss, idx.get((seed, arm, iid), []))
                        if rep is None:
                            continue  # no report: nothing was scored, nothing to rescore
                        key = f"{exp}|{rep['name']}|{arm}|{iid}"
                        if key in entries:
                            continue
                        root = Path("runs") if exp != "E2" else a.e2_runs
                        pf = root / rep["name"] / arm / "agent" / "preds_scored.json"
                        preds = json.loads(pf.read_text()) if pf.exists() else {}
                        patch = (preds.get(iid) or {}).get("model_patch")
                        if not patch:
                            missing.append(key)
                            continue
                        entries[key] = {
                            "exp": exp,
                            "name": rep["name"],
                            "arm": arm,
                            "seed": seed,
                            "iid": iid,
                            "orig_run": rep["run"],
                            "orig_loss": rep["loss"],
                            "patch": patch,
                        }
    with gzip.open("results/s28_manifest.json.gz", "wt") as fh:
        json.dump({"entries": list(entries.values()), "missing": missing}, fh)
    by = {}
    for e in entries.values():
        by[e["exp"]] = by.get(e["exp"], 0) + 1
    print("entries", by, "missing", len(missing), missing[:5])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
