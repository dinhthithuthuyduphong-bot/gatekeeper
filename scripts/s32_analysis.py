"""Section 32 (docs/preregistration_main.md, registered before any computation): tier 0. 0 USD.

  python scripts/s32_analysis.py --xrepo <XRepoSkill clone at 26fd703>

32a  history-access monitor on every saved trace (M1: a history command; M2: "Bug Patch" seen);
32b  eight decision rules on the real paired streams, labels fixed in advance, 10,000 orders;
32c  an e-process for the environment contrast D_i = (Z_ship - Z_single_commit) / 2.
Exploratory: every input was seen before in another form. Writes results/s32_analysis.json.
"""

from __future__ import annotations

import argparse
import gzip
import json
import re
import sys
from pathlib import Path

import numpy as np
from scipy.stats import binom

sys.path.insert(0, str(Path(__file__).parent))
import gates  # noqa: E402
import replicate_attribution as ra  # noqa: E402
import s25_ab as ab  # noqa: E402

from gatekeeper.eprocess import BettingEProcess  # noqa: E402

ALPHA, THETA, C, LOOK = 0.025, 0.0, 0.5, 10  # as registered
ORDERS, SEED_B, SEED_C = 10000, 3211, 3212
R = Path("results")

M1 = re.compile(
    r"git\s+(log|show|reflog|blame)\b"
    r"|git\s+(diff|checkout|restore|cat-file)\b[^\n|;&]*(HEAD~|HEAD\^|\b[0-9a-f]{7,}\b)"
)
M2 = "Bug Patch"

# 32a: arm -> (trace files, result files, environment, description)
ARMS = {
    "jinja/shipped/original skill (34 tasks)": (["s27_trace34", "s27_trace34b"], "shipped"),
    "jinja/shipped/no skill": (["s29_none"], "shipped"),
    "jinja/shipped/placebo": (["s27_placebo"], "shipped"),
    "jinja/shipped/skill without history line": (["s29_ablate"], "shipped"),
    "jinja/shipped/re-learned skill (34 tasks)": (["s30_shipped34"], "shipped"),
    "pygments/shipped/no skill": (["s27pyg_none"], "shipped"),
    "pygments/shipped/jinja skill": (["s27pyg_skill", "s27pyg_skillb", "s27pyg_skillc"], "shipped"),
    "jinja/single commit/no skill": (["s30_none", "s30_none_rest"], "single commit"),
    "jinja/single commit/re-learned skill": (["s30_skill", "s30_skill_rest"], "single commit"),
    "bleve/single commit/no skill": (["s25bleve_leakfree_none"], "single commit"),
    "bleve/single commit/skill": (
        ["s25bleve_leakfree_skill", "s25bleve_leakfree_skillb"],
        "single commit",
    ),
}


def load(name: str) -> dict:
    return json.loads((R / name).read_text())


def flags(messages: list[dict]) -> tuple[bool, bool]:
    cmd = "\n".join(str(m.get("content", "")) for m in messages if m["role"] == "assistant")
    obs = [str(m.get("content", "")) for m in messages if m["role"] == "user"][1:]
    return bool(M1.search(cmd)), any(M2 in o for o in obs)


def monitor() -> dict:
    out = {}
    for arm, (stems, env) in ARMS.items():
        recs, res, dropped = {}, {}, 0
        for s in stems:
            for x in gzip.open(R / f"{s}.traces.jsonl.gz", "rt"):
                r = json.loads(x)
                if r.get("messages"):
                    recs[r["instance_id"]] = r["messages"]  # a later file replaces a crashed run
                else:
                    dropped += 1
            for r in load(f"{s}.json")["runs"]:
                if "infra_error" not in r and not r.get("crashed"):
                    res[r["instance_id"]] = bool(r["S"]["resolved"])
        rows = [(i, *flags(m), res.get(i)) for i, m in recs.items()]
        m2 = [r for r in rows if r[2]]
        no = [r for r in rows if not r[2]]
        out[arm] = {
            "environment": env,
            "runs": len(rows),
            "runs_without_messages_dropped": dropped,
            "M1": sum(r[1] for r in rows),
            "M2": len(m2),
            "resolved_with_M2": sum(bool(r[3]) for r in m2),
            "resolved_without_M2": sum(bool(r[3]) for r in no),
            "runs_without_M2": len(no),
        }
    return out


# ---------- 32b ----------


def smith(skill: str, none: str) -> list[tuple[float, int, int]]:
    """(z, resolved with, resolved without) in gskill's order."""
    pairs = ab.paired(load(skill), load(none))
    return [
        (
            float(not ab.passed(a, "S")) - float(not ab.passed(b, "S")),
            int(ab.passed(a, "S")),
            int(ab.passed(b, "S")),
        )
        for _, a, b in pairs
    ]


def stage(name: str, key: str, seed_with: str, seed_without: str, col_with: int) -> list:
    tasks = ra.load(name)[key]
    out = []
    for _i, v in sorted(tasks.items()):
        if seed_with in v and seed_without in v:
            w, n = bool(v[seed_with][col_with]), bool(v[seed_without][1])
            out.append((float(not w) - float(not n), int(w), int(n)))
    return out


def streams() -> dict:
    s = {
        "jinja shipped": ("positive", smith("f1_skill_probe.json", "f1_probe.json")),
        "jinja single commit": (
            "positive",
            smith("s25_leakfree_skill.json", "s25_leakfree_none.json"),
        ),
        "bleve shipped": ("positive", smith("s25bleve_skill_probe.json", "s25bleve_f1_probe.json")),
        "bleve single commit": (
            "positive",
            smith("s25bleve_leakfree_skill_all.json", "s25bleve_leakfree_none.json"),
        ),
        "jinja skill without history line": ("positive", smith("s29_ablate.json", "s29_none.json")),
        "jinja re-learned skill": ("positive", smith("s30_skill.json", "s30_none.json")),
        "jinja skill vs placebo": ("positive", smith("f1_skill_probe.json", "s27_placebo.json")),
        "jinja placebo vs none": ("unlabelled", smith("s27_placebo.json", "f1_probe.json")),
        "pygments reuse": ("unlabelled", smith("s27pyg_skill_all.json", "s27pyg_none_all.json")),
        "A/A jinja shipped": ("null", smith("s29_none.json", "f1_probe.json")),
        "A/A jinja single commit": ("null", smith("s30_none.json", "s25_leakfree_none.json")),
    }
    e1, e2 = ra.load("e1"), ra.load("e2")
    for k in sorted(e1):
        label = "harmful by design" if k.startswith("harm-") else "unlabelled"
        s[f"E1 {k}"] = (label, stage("e1", k, "s41", "s41", 0))
    for k in sorted(e2):
        s[f"E2 {k}"] = ("unlabelled", stage("e2", k, "s41", "s41", 0))
    s["A/A E1"] = ("null", stage("e1", sorted(e1)[0], "s51", "s41", 1))
    s["A/A E2"] = ("null", stage("e2", sorted(e2)[0], "s51", "s41", 1))
    return s


def sign_p(z) -> float:
    b, c = int(sum(x < 0 for x in z)), int(sum(x > 0 for x in z))
    return float(binom.sf(b - 1, b + c, 0.5)) if b + c else 1.0


def rules(score):
    def gk(t):
        ep = BettingEProcess(theta=THETA, alpha=ALPHA, c=C)
        for z, _, _ in t:
            ep.update(z)
            if ep.crossed:
                return True
        return False

    def looks(t):
        return [t[:k] for k in range(LOOK, len(t) + 1, LOOK)] or [t]

    def z(t):
        return [x[0] for x in t]

    def mh(t):
        return gates.b_x2([(w, n, f"t{i}") for i, (_, w, n) in enumerate(t)], score)

    return {
        "gatekeeper": gk,
        "sign test, once": lambda t: sign_p(z(t)) <= ALPHA,
        "sign test, every 10": lambda t: any(sign_p(z(u)) <= ALPHA for u in looks(t)),
        "plug-in, once": lambda t: gates.plug_in(z(t)),
        "plug-in, every 10": lambda t: any(gates.plug_in(z(u)) for u in looks(t)),
        "mantel-haenszel, once": mh,
        "mantel-haenszel, every 10": lambda t: any(mh(u) for u in looks(t)),
        "gepa, first 3": lambda t: gates.b_g(z(t), 3),
    }


def decisions(score, n_orders: int) -> dict:
    rs = rules(score)
    rng = np.random.default_rng(SEED_B)
    out = {}
    for name, (label, t) in streams().items():
        perms = [[t[j] for j in rng.permutation(len(t))] for _ in range(n_orders)]
        out[name] = {
            "label": label,
            "n": len(t),
            "with": sum(x[1] for x in t),
            "without": sum(x[2] for x in t),
            "as_run": {r: bool(f(t)) for r, f in rs.items()},
            "share_of_orders_admitted": {
                r: float(np.mean([f(p) for p in perms])) for r, f in rs.items()
            },
        }
    summary = {}
    for r in rs:
        d = {
            lab: [v["as_run"][r] for v in out.values() if v["label"] == lab]
            for lab in ("positive", "null", "harmful by design")
        }
        summary[r] = {
            "positive_admitted": f"{sum(d['positive'])}/{len(d['positive'])}",
            "null_admitted": f"{sum(d['null'])}/{len(d['null'])}",
            "harmful_admitted": f"{sum(d['harmful by design'])}/{len(d['harmful by design'])}",
        }
    return {"streams": out, "summary": summary}


# ---------- 32c ----------


def contrast(ship: tuple[str, str], lf: tuple[str, str], n_orders: int) -> dict:
    a = {
        i: float(not ab.passed(s, "S")) - float(not ab.passed(n, "S"))
        for i, s, n in ab.paired(load(ship[0]), load(ship[1]))
    }
    order = [i for i, _, _ in ab.paired(load(lf[0]), load(lf[1]))]
    b = {
        i: float(not ab.passed(s, "S")) - float(not ab.passed(n, "S"))
        for i, s, n in ab.paired(load(lf[0]), load(lf[1]))
    }
    d = [(a[i] - b[i]) / 2 for i in order if i in a]

    def run(seq):
        ep = BettingEProcess(theta=THETA, alpha=ALPHA, c=C)
        best, first = 0.0, None
        for k, x in enumerate(seq, 1):
            ep.update(x)
            best = max(best, ep.log_e)
            if first is None and ep.crossed:
                first = k
        return first, best

    first, best = run(d)
    rng = np.random.default_rng(SEED_C)
    share = float(
        np.mean(
            [run([d[j] for j in rng.permutation(len(d))])[0] is not None for _ in range(n_orders)]
        )
    )
    return {
        "n": len(d),
        "mean_D": float(np.mean(d)),
        "share_of_gain_difference": float(-2 * np.mean(d)),
        "rejects_as_run": first is not None,
        "first_crossing": first,
        "p_anytime": float(min(1.0, np.exp(-best))),
        "share_of_orders_rejecting": share,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--xrepo", type=Path, required=True)
    ap.add_argument("--orders", type=int, default=ORDERS)
    a = ap.parse_args()
    score = gates.load_xreposkill_score(a.xrepo)
    out = {
        "monitor": monitor(),
        "rules": decisions(score, a.orders),
        "contrast": {
            "jinja": contrast(
                ("f1_skill_probe.json", "f1_probe.json"),
                ("s25_leakfree_skill.json", "s25_leakfree_none.json"),
                a.orders,
            ),
            "bleve": contrast(
                ("s25bleve_skill_probe.json", "s25bleve_f1_probe.json"),
                ("s25bleve_leakfree_skill_all.json", "s25bleve_leakfree_none.json"),
                a.orders,
            ),
        },
    }
    (R / "s32_analysis.json").write_text(json.dumps(out, indent=1) + "\n")
    print(
        json.dumps(
            {
                "monitor": out["monitor"],
                "summary": out["rules"]["summary"],
                "contrast": out["contrast"],
            },
            indent=1,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
