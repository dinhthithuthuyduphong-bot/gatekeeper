"""Power of the primary endpoint for the draft's projected numbers (TODO.md R14).

Writes results/endpoint_power.json.
"""

from __future__ import annotations

import json
from pathlib import Path

from gatekeeper.analysis import endpoint_power

P_BASE, P_GK = 0.115, 0.051  # the draft's projection: B6 11.5% -> Gatekeeper 5.1%
NS = [63, 200, 500, 1000, 2000]


def main() -> None:
    rows = []
    for n in NS:
        row = {"n_harmful": n}
        for label, margin in (("margin5", 0.05), ("superiority", 0.0)):
            for coupling in ("independent", "nested"):
                row[f"{label}_{coupling}"] = endpoint_power(
                    n, P_BASE, P_GK, margin=margin, coupling=coupling, reps=800, n_boot=300, seed=n
                )
        rows.append(row)
        print(row)
    Path("results").mkdir(exist_ok=True)
    Path("results/endpoint_power.json").write_text(
        json.dumps({"p_baseline": P_BASE, "p_gatekeeper": P_GK, "rows": rows}, indent=2) + "\n"
    )


if __name__ == "__main__":
    main()
