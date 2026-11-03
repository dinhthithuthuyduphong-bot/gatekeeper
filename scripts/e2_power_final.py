"""Power of the E2 decision rule for the FINAL task set (configs/pools/e2_selected.json; repo
clusters of that set) at n = 105 and 121. Same plasmode as scripts/verify_methods.py (same q,
simulate, decide, R and rng seed); method_check.json's E2 row used block 1 only (n = 119).
Writes results/e2_power_final.json."""

import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, "scripts")
import verify_methods as vm

ids = json.loads(Path("configs/pools/e2_selected.json").read_text())["instances"]
rng = np.random.default_rng(20271103)
q = vm.measured_q()
out = {}
for n in (105, 121):
    t = time.time()
    sizes = vm.clusters_of(ids[:n])
    out[n] = vm.design("E2", rng, q, n, sizes, vm.ALPHA, vm.R_VALID, vm.R_POWER)
    print(
        n,
        round(time.time() - t),
        "s",
        json.dumps(
            {
                "type1": out[n]["type1"],
                "power": {d: v["primary"] for d, v in out[n]["power"].items()},
            }
        ),
        flush=True,
    )

Path("results/e2_power_final.json").write_text(
    json.dumps({str(k): v for k, v in out.items()}, indent=1) + "\n"
)
