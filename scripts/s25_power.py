"""Section 25 step 2: power of the registered decision rule (exact one-sided sign test on
discordant pairs, Holm over 2 tests at family alpha 0.025 -> first level 0.0125), n = 100,
base rate 0.15 (F1), arms independent (fewer concordant pairs than real pairing: conservative).
Output: results/s25_power.json."""

import json
import random
from math import comb
from pathlib import Path


def pval(b: int, c: int) -> float:
    n = b + c
    return sum(comb(n, k) for k in range(b, n + 1)) / 2**n if n else 1.0


def power(p0: float, delta: float, n: int, level: float, reps: int, seed: int) -> float:
    r = random.Random(seed)
    p1 = min(1.0, p0 + delta)
    hit = 0
    for _ in range(reps):
        b = c = 0
        for _ in range(n):
            a, z = r.random() < p1, r.random() < p0
            b += a and not z
            c += z and not a
        hit += pval(b, c) <= level
    return hit / reps


if __name__ == "__main__":
    res = {str(d): power(0.15, d, 100, 0.0125, 20000, 1) for d in (0.0, 0.05, 0.10, 0.15, 0.27)}
    Path("results/s25_power.json").write_text(json.dumps(res, indent=1) + "\n")
    print(res)
