"""Rerun noise floor F(n) and audit of published gains (docs/preregistration_main.md section 12).

Uses the registered endpoint (resolved <=> loss == 0, analyze_g1_final.resolved) via
plasmode_real.no_skill_runs. Writes results/noise_floor_audit.json. 0 USD.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import plasmode_real as pr  # noqa: E402

SEED = 20271105
REPS = 20000  # section 12
# (system, setting, n tasks, with, without): XRepoSkill Table 1 (snapshot `xreposkill`),
# MemGovern README table (snapshot `memgovern_repo`)
CLAIMS = [
    ("XRepoSkill", "Pro/DeepSeek", 200, 55.5, 51.5),
    ("XRepoSkill", "Pro/GPT", 200, 56.0, 50.5),
    ("XRepoSkill", "Pro/MiMo", 200, 50.0, 41.5),
    ("XRepoSkill", "DeepSWE/DeepSeek", 113, 58.4, 46.0),
    ("XRepoSkill", "DeepSWE/GPT", 113, 56.6, 44.2),
    ("XRepoSkill", "DeepSWE/MiMo", 113, 17.7, 11.5),
    ("MemGovern", "Claude-4-Sonnet", 500, 69.8, 66.6),
    ("MemGovern", "GPT5-Medium", 500, 67.4, 65.0),
    ("MemGovern", "DeepSeek-V3.1T", 500, 65.8, 62.8),
    ("MemGovern", "Qwen3-235B", 500, 55.4, 47.2),
    ("MemGovern", "Kimi-K2-Instruct", 500, 51.8, 43.8),
    ("MemGovern", "GPT-4o", 500, 32.6, 23.2),
    ("MemGovern", "GPT-4o-Mini", 500, 17.2, 14.0),
]


def floor(tasks, n: int, rng) -> float:
    d = np.empty(REPS)
    for k in range(REPS):
        a = b = 0
        for i in rng.integers(0, len(tasks), n):
            t = tasks[i]
            x, y = rng.choice(len(t), 2, replace=False)
            a += t[x]
            b += t[y]
        d[k] = abs(a - b) / n
    return float(np.quantile(d, 0.975))


def main() -> int:
    tasks = pr.no_skill_runs()
    rng = np.random.default_rng(SEED)
    fs = {n: floor(tasks, n, rng) for n in sorted({c[2] for c in CLAIMS})}
    out = {
        "n_tasks_noise_pool": len(tasks),
        "base_solve_rate": float(np.mean([np.mean(t) for t in tasks])),
        "F_pp": {str(n): round(v * 100, 3) for n, v in fs.items()},
        "claims": [],
    }
    for sysn, setting, n, w, b in CLAIMS:
        g = w - b
        out["claims"].append(
            {
                "system": sysn,
                "setting": setting,
                "n": n,
                "gain_pp": round(g, 1),
                "F_pp": round(fs[n] * 100, 2),
                "beyond_rerun_noise": bool(g > fs[n] * 100),
            }
        )
    out["beyond"] = sum(c["beyond_rerun_noise"] for c in out["claims"])
    Path("results/noise_floor_audit.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "claims"}))
    for c in out["claims"]:
        print(c)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
