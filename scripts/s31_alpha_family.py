"""Section 31 (exploratory, after the data): two checks a reviewer asked for, 0 USD.

(a) Family-wise reading of the admissions. Every admission in the paper was registered as its own
    cell at alpha_{S,s} = alpha = 0.025. Read as one family of K claims, Ville plus a union bound
    (the paper's Theorem) holds at level alpha only with alpha_{S,s} = alpha / K (Bonferroni). We
    rerun the registered decision rule (scripts/s25_ab.py of branch `trial`, theta = 0, c = 0.5) on
    the same paired streams with alpha / K and report the first crossing, if any.

(b) Validity of the e-process when the test tasks are run once each, in the order of gskill's
    seeded split (sampling without replacement from a finite pool, not i.i.d.). Monte Carlo of the
    exact rule (BettingEProcess, theta = 0, c = 0.5, alpha = 0.025, N = 100) under nulls whose
    expected pool mean is exactly 0, with per-task outcome probabilities, in a uniformly random
    order. Reports the admission rate with a Clopper-Pearson 95% upper bound.

(c) Order (second review, M1): the registered order is one draw of gskill's seeded shuffle. For
    each stream, the same rule over --perms uniformly random orders of the realised pairs: share of
    orders that admit within the 100 tasks, and the quartiles of the first crossing.
(d) theta (second review, minor 1): first crossing on each stream at theta = 0.02 and 0.05, the
    two margins already used in the paper's design table (scripts/make_tables.py).
(e) Cost of a re-admission (minor 2): tokens per paired trial, counted from the section 30
    evaluation traces (input, cached input, output).

  python scripts/s31_alpha_family.py --trial <worktree of origin/trial> --reps 20000 --seed 1 \
      --out results/s31_alpha_family.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from scipy.stats import beta

ALPHA, THETA, C = 0.025, 0.0, 0.5  # as registered for every admission (section 25)


def streams(trial: Path) -> list[tuple[str, Path, Path]]:
    t, m = trial / "results", Path("results")
    return [
        ("jinja_as_shipped", t / "f1_skill_probe.json", t / "f1_probe.json"),
        ("jinja_single_commit", t / "s25_leakfree_skill.json", t / "s25_leakfree_none.json"),
        ("bleve_as_shipped", t / "s25bleve_skill_probe.json", t / "s25bleve_f1_probe.json"),
        (
            "bleve_single_commit",
            t / "s25bleve_leakfree_skill_all.json",
            t / "s25bleve_leakfree_none.json",
        ),
        ("jinja_content_vs_placebo", t / "f1_skill_probe.json", t / "s27_placebo.json"),
        ("jinja_no_history_instruction", m / "s29_ablate.json", m / "s29_none.json"),
        ("jinja_relearned_single_commit", m / "s30_skill.json", m / "s30_none.json"),
        ("pygments_reuse", t / "s27pyg_skill_all.json", t / "s27pyg_none_all.json"),
    ]


def first_crossing(mod, pairs, alpha: float) -> tuple[int | None, float]:
    from gatekeeper.eprocess import BettingEProcess

    ep = BettingEProcess(theta=THETA, alpha=alpha, c=C)
    first, best = None, 0.0
    for k, (_, a, b) in enumerate(pairs, 1):
        ep.update(float(not mod.passed(a, "S")) - float(not mod.passed(b, "S")))
        best = max(best, ep.log_e)
        if first is None and ep.crossed:
            first = k
    return first, float(np.exp(best))


def family(mod, trial: Path) -> dict:
    ss = streams(trial)
    k = len(ss)
    out = {"K": k, "alpha_per_cell": ALPHA, "alpha_bonferroni": ALPHA / k, "streams": {}}
    for name, s, n in ss:
        pairs = mod.paired(json.loads(s.read_text()), json.loads(n.read_text()))
        a1, emax = first_crossing(mod, pairs, ALPHA)
        ak, _ = first_crossing(mod, pairs, ALPHA / k)
        out["streams"][name] = {
            "n": len(pairs),
            "admit_at_alpha": a1,
            "admit_at_alpha_over_K": ak,
            "max_e": emax,
        }
    return out


NULLS = {
    # (name, per-task (p_skill_resolves, p_none_resolves)); every expected pool mean of Z is 0
    "homogeneous_p0.15": [(0.15, 0.15)] * 100,
    "homogeneous_p0.35": [(0.35, 0.35)] * 100,
    "homogeneous_p0.5": [(0.5, 0.5)] * 100,
    "half_help_half_hurt": [(0.9, 0.1)] * 50 + [(0.1, 0.9)] * 50,
    "help_34_hurt_66": [(0.9, 0.1)] * 33 + [(0.1, 0.5)] * 66 + [(0.5, 0.5)],
    "deterministic_mixed": [(1.0, 0.0)] * 20 + [(0.0, 1.0)] * 20 + [(1.0, 1.0)] * 60,
}


def wor_sim(reps: int, seed: int) -> dict:
    from gatekeeper.eprocess import BettingEProcess

    rng = np.random.default_rng(seed)
    out = {}
    for name, pool in NULLS.items():
        p = np.array(pool)
        ez = float(((1 - p[:, 0]) - (1 - p[:, 1])).mean())
        assert abs(ez) < 1e-9, (name, ez)
        hits = 0
        for _ in range(reps):
            order = rng.permutation(len(p))
            s = rng.random(len(p)) < p[order, 0]
            n = rng.random(len(p)) < p[order, 1]
            ep = BettingEProcess(theta=THETA, alpha=ALPHA, c=C)
            for zs, zn in zip(s, n, strict=True):
                ep.update(float(not zs) - float(not zn))
                if ep.crossed:
                    hits += 1
                    break
        out[name] = {
            "reps": reps,
            "admitted": hits,
            "rate": hits / reps,
            "cp95_upper": float(beta.ppf(0.975, hits + 1, reps - hits)) if hits < reps else 1.0,
        }
    return out


THETAS = (0.02, 0.05)  # the margins of the paper's design table (scripts/make_tables.py)


def run_rule(z: np.ndarray, theta: float, alpha: float) -> int | None:
    from gatekeeper.eprocess import BettingEProcess

    ep = BettingEProcess(theta=theta, alpha=alpha, c=C)
    for k, v in enumerate(z, 1):
        ep.update(float(v))
        if ep.crossed:
            return k
    return None


def order_and_theta(mod, trial: Path, perms: int, seed: int) -> dict:
    rng = np.random.default_rng(seed)
    out = {}
    for name, s, n in streams(trial):
        pairs = mod.paired(json.loads(s.read_text()), json.loads(n.read_text()))
        z = np.array(
            [float(not mod.passed(a, "S")) - float(not mod.passed(b, "S")) for _, a, b in pairs]
        )
        firsts = [run_rule(z[rng.permutation(len(z))], THETA, ALPHA) for _ in range(perms)]
        hit = [f for f in firsts if f is not None]
        out[name] = {
            "perms": perms,
            "share_admitted": len(hit) / perms,
            "first_q25_q50_q75": [float(np.percentile(hit, q)) for q in (25, 50, 75)]
            if hit
            else None,
            "theta": {str(t): run_rule(z, t, ALPHA) for t in THETAS},
        }
    return out


def tokens_per_trial() -> dict:
    import gzip

    def count(files):
        tot = {"input": 0, "cached": 0, "output": 0}
        ids = set()

        def walk(o):
            if isinstance(o, dict):
                u = o.get("usage")
                if isinstance(u, dict) and "prompt_tokens" in u:
                    tot["input"] += u.get("prompt_tokens") or 0
                    tot["output"] += u.get("completion_tokens") or 0
                    d = u.get("prompt_tokens_details") or {}
                    tot["cached"] += d.get("cached_tokens") or 0
                for v in o.values():
                    walk(v)
            elif isinstance(o, list):
                for v in o:
                    walk(v)

        for f in files:
            for line in gzip.open(f, "rt"):
                if line.strip():
                    d = json.loads(line)
                    ids.add(d.get("instance_id"))
                    walk(d)
        return tot, len(ids)

    r = Path("results")
    arms = {
        "none": [r / "s30_none.traces.jsonl.gz", r / "s30_none_rest.traces.jsonl.gz"],
        "skill": [r / "s30_skill.traces.jsonl.gz", r / "s30_skill_rest.traces.jsonl.gz"],
    }
    out = {}
    for arm, files in arms.items():
        tot, n = count(files)
        out[arm] = {**tot, "tasks": n}
    trials = min(out["none"]["tasks"], out["skill"]["tasks"])
    out["per_paired_trial_input"] = (out["none"]["input"] + out["skill"]["input"]) / trials
    out["per_paired_trial_output"] = (out["none"]["output"] + out["skill"]["output"]) / trials
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--trial", required=True, type=Path)
    ap.add_argument("--reps", required=True, type=int)
    ap.add_argument("--seed", required=True, type=int)
    ap.add_argument("--perms", required=True, type=int)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from make_numbers import s25_module

    mod = s25_module(a.trial)
    res = {
        "family": family(mod, a.trial),
        "wor_null": wor_sim(a.reps, a.seed),
        "order_theta": order_and_theta(mod, a.trial, a.perms, a.seed),
        "tokens": tokens_per_trial(),
    }
    a.out.write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps(res, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
