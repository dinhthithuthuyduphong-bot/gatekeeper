"""E2 power with the MEASURED no-skill solve rates of Live (method_check.md: "after the first seed,
re-measure the Live solve rate and recompute the E2 table, without looking at the effect").
q per task = mean over the 3 seeds of 1[resolved] in the NO-SKILL arm only (results/e2); the skill
arm is never read (L28). Same plasmode as scripts/verify_methods.py. Writes
results/e2_power_live_q.json."""

from __future__ import annotations

import glob
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import verify_methods as vm  # noqa: E402


def none_q(files: list[str]) -> dict[str, float]:
    acc: dict[str, dict[str, float]] = defaultdict(dict)
    for f in files:
        d = json.loads(Path(f).read_text())
        seed = re.search(r"-s(\d+)", f).group(1)
        for v in d.get("skills", {}).values():
            for p in v["pairs"]:
                acc[p["instance_id"]][seed] = float(p["loss_without"] == 0.0)
    return {t: float(np.mean(list(v.values()))) for t, v in acc.items() if len(v) == 3}


def main() -> int:
    qd = none_q(sorted(glob.glob("results/e2/g2-e2-s*-k*-p*.json")))
    ids, q = list(qd), np.array(list(qd.values()))
    rng = np.random.default_rng(20271103)
    d = vm.design("E2", rng, q, len(ids), vm.clusters_of(ids), vm.ALPHA, vm.R_VALID, vm.R_POWER)
    out = {
        "q": {
            "n_tasks": len(ids),
            "mean": float(q.mean()),
            "share_q0": float((q == 0).mean()),
            "share_q1": float((q == 1).mean()),
        },
        "type1_primary": d["type1"]["primary"],
        "power": {
            k: {"realised_effect": v["realised_mean_effect"], "primary": v["primary"]}
            for k, v in d["power"].items()
        },
    }
    Path("results/e2_power_live_q.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
