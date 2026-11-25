"""Numbers quoted in the paper text, recomputed from the raw result files (0 USD).

  python scripts/make_numbers.py --trial <worktree of origin/trial> --rows <dir with swesmith rows>

Every number in paper/numbers.tex is computed here from results files, never typed by hand:
- section 25 (gskill on SWE-smith, branch `trial`): the registered decision script
  scripts/s25_ab.py of that branch (exact sign test, task bootstrap, Gatekeeper e-process) is run
  on the raw per-task files; Delta_leak = gain(in scope) - gain(leak-free) with a joint task-level
  bootstrap over the four arms on the same 100 tasks (registered in section 25 step 3);
- F0 (no-op and gold patches under both scorers) summed over the five scored repositories;
- this branch: harness controls (sections 26-28), E2, T4, SSKB transfer, A/A rules (section 19),
  attribution placebo (section 18).
Before writing, every recomputed value is checked against the value already reported in the
preregistration (CHECKS); any mismatch stops the script. Writes paper/numbers.tex.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

REPS, SEED, ALPHA, THETA, C = 10_000, 1, 0.025, 0.0, 0.5  # as registered (section 25)


def load(p: Path) -> dict:
    return json.loads(p.read_text())


def dep_numbers(d: dict) -> dict:
    """R-102: largest false-certification rates of the dependence sensitivity simulation.
    Mild = within-arm rho <= 0.5, shared rho <= 0.8, block outages L <= 20, independent;
    strong = within-arm rho = 0.8 (the end-of-pool test and the registered sign test)."""
    cells = [(k, v) for c in d["results"].values() for k, v in c.items() if k != "pool_mean_EZ"]
    mild = [v["end_of_pool_reject"] for k, v in cells if not k.startswith("a_within_arm_rho0.8")]
    strong = [v for k, v in cells if k.startswith("a_within_arm_rho0.8")]
    assert len(strong) == 2 and len(mild) == len(cells) - 2, (len(strong), len(mild))
    # four decimals: these rates are compared with alpha = 0.025, so two decimals would mislead
    return {
        "depEopMild": f"{max(mild):.4f}",
        "depEopStrong": f"{max(v['end_of_pool_reject'] for v in strong):.4f}",
        "depSignStrong": f"{max(v['sign_test_reject'] for v in strong):.4f}",
        "depSignBlock": f"{max(v['sign_test_reject'] for k, v in cells if k.startswith('c_')):.4f}",
        "depReps": d["inputs"]["reps"],
    }


def s25_module(trial: Path):
    sys.path.insert(0, str(trial / "src"))
    spec = importlib.util.spec_from_file_location("s25_ab", trial / "scripts" / "s25_ab.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def ab(mod, skill: Path, none: Path, rows: Path) -> dict:
    import gzip

    raw = rows.read_bytes()
    text = (gzip.decompress(raw) if rows.name.endswith(".gz") else raw).decode()
    empty = {
        r["instance_id"]: not (r.get("problem_statement") or "").strip()
        for r in (json.loads(x) for x in text.splitlines() if x.strip())
    }
    pairs = mod.paired(load(skill), load(none))
    out = {"all": mod.analyse(pairs, ALPHA, THETA, C, REPS, SEED), "pairs": pairs}
    for name, keep in (("nops", True), ("withps", False)):
        sub = [p for p in pairs if empty[p[0]] == keep]
        out[name] = {**mod.analyse(sub, ALPHA, THETA, C, REPS, SEED)["S"], "n": len(sub)}
    return out


def delta_leak(mod, inscope: dict, leakfree: dict) -> dict:
    a = {i: (s, n) for i, s, n in inscope["pairs"]}
    b = {i: (s, n) for i, s, n in leakfree["pairs"]}
    ids = sorted(set(a) & set(b))
    v = np.array(
        [
            (mod.passed(a[i][0], "S") - mod.passed(a[i][1], "S"))
            - (mod.passed(b[i][0], "S") - mod.passed(b[i][1], "S"))
            for i in ids
        ],
        dtype=float,
    )
    rng = np.random.default_rng(SEED)
    boot = v[rng.integers(0, v.size, size=(REPS, v.size))].mean(1)
    return {
        "n": len(ids),
        "d": float(v.mean()),
        "ci": [float(np.quantile(boot, 0.025)), float(np.quantile(boot, 0.975))],
    }


def f0_totals(trial: Path) -> dict:
    tot = {"L_noop": 0, "S_noop": 0, "n": 0, "S_gold_min": 1.0, "repos": 0}
    for f in sorted((trial / "results").glob("f0_scorer_check*.json")):
        if "pyquery" in f.name:  # reported separately (A93 of `trial`): > 10% infrastructure
            continue
        s = load(f)["summary"]
        tot["L_noop"] += s["noop"]["L_pass"]
        tot["S_noop"] += s["noop"]["S_resolved"]
        tot["n"] += s["n_scored"]
        tot["repos"] += 1
        tot["S_gold_min"] = min(tot["S_gold_min"], s["gold"]["S_rate"])
    return tot


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--trial", type=Path, required=True)
    ap.add_argument("--rows", type=Path, required=True)
    a = ap.parse_args()
    t = a.trial / "results"
    mod = s25_module(a.trial)
    jinja = a.rows / "swesmith_pallets__jinja.jsonl"
    bleve = a.rows / "swesmith_blevesearch__bleve.jsonl.gz"
    j_in = ab(mod, t / "f1_skill_probe.json", t / "f1_probe.json", jinja)
    j_lf = ab(mod, t / "s25_leakfree_skill.json", t / "s25_leakfree_none.json", jinja)
    b_in = ab(mod, t / "s25bleve_skill_probe.json", t / "s25bleve_f1_probe.json", bleve)
    dl = delta_leak(mod, j_in, j_lf)
    f0 = f0_totals(a.trial)
    noop = load(Path("results/harness_noop_gh.json"))
    gold = load(Path("results/harness_gold_gh.json"))
    s28 = load(Path("results/s28_effects.json"))["effects"]
    sskb = load(Path("results/sskb_transfer.json"))
    pl = load(Path("results/placebo_suite.json"))["A"]
    N = {
        # section 25, jinja in scope
        "jinjaNone": j_in["all"]["S"]["none"],
        "jinjaSkill": j_in["all"]["S"]["skill"],
        "jinjaGain": j_in["all"]["S"]["gain"],
        "jinjaGainLo": j_in["all"]["S"]["boot95"][0],
        "jinjaGainHi": j_in["all"]["S"]["boot95"][1],
        "jinjaAdmit": j_in["all"]["gatekeeper_admit_trial"],
        "jinjaLNone": j_in["all"]["L"]["none"],
        "jinjaLSkill": j_in["all"]["L"]["skill"],
        # jinja leak-free
        "jinjaLFNone": j_lf["all"]["S"]["none"],
        "jinjaLFSkill": j_lf["all"]["S"]["skill"],
        "jinjaLFGain": j_lf["all"]["S"]["gain"],
        "jinjaLFGainLo": j_lf["all"]["S"]["boot95"][0],
        "jinjaLFGainHi": j_lf["all"]["S"]["boot95"][1],
        "jinjaLFAdmit": j_lf["all"]["gatekeeper_admit_trial"],
        "jinjaLFp": j_lf["all"]["S"]["p_one_sided"],
        "leak": dl["d"],
        "leakLo": dl["ci"][0],
        "leakHi": dl["ci"][1],
        "leakShare": dl["d"] / j_in["all"]["S"]["gain"],
        "jinjaNoPSn": j_in["nops"]["skill"] + 0,  # skill arm, tasks without a problem statement
        "jinjaNoPSLF": j_lf["nops"]["skill"],
        "jinjaNoPSTasks": j_in["nops"]["n"],
        "jinjaWithPSGain": j_in["withps"]["skill"] - j_in["withps"]["none"],
        "jinjaWithPSLFGain": j_lf["withps"]["skill"] - j_lf["withps"]["none"],
        # bleve in scope
        "bleveNone": b_in["all"]["S"]["none"],
        "bleveSkill": b_in["all"]["S"]["skill"],
        "bleveGain": b_in["all"]["S"]["gain"],
        "bleveGainLo": b_in["all"]["S"]["boot95"][0],
        "bleveGainHi": b_in["all"]["S"]["boot95"][1],
        "bleveAdmit": b_in["all"]["gatekeeper_admit_trial"],
        "bleveLNone": b_in["all"]["L"]["none"],
        "bleveLSkill": b_in["all"]["L"]["skill"],
        "bleveNoPS": b_in["nops"]["skill"],
        "bleveNoPSNone": b_in["nops"]["none"],
        # scorer controls
        "fzeroLNoop": f0["L_noop"],
        "fzeroSNoop": f0["S_noop"],
        "fzeroN": f0["n"],
        "fzeroRepos": f0["repos"],
        "noopOurs": sum(1 for v in noop.values() if v.get("resolved")),
        "noopOursN": len(noop),
        "goldOursOk": sum(1 for v in gold.values() if v.get("label") == "ok"),
        "goldOursN": len(gold),
        # our earlier experiments
        "etwoGain": s28["E2"]["xreposkill"]["new"]["effect"],
        "tfourGain": s28["T4"]["control-oracle-patch"]["new"]["effect"],
        "sskbRho": sskb["point"]["rho"],
        "sskbOpp": sskb["point"]["opposite_sign_big"],
        "pluginOnce": pl["plug_in_once"],
        "pluginMonitored": pl["plug_in_monitored"],
        "gepaNoop": pl["gepa_accept_per_proposal"],
        "gkAdmitAA": pl["gatekeeper_admit"],
    }
    # values already reported in the preregistration (sections 25, 26-28): recomputation must match
    CHECKS = {
        "jinjaNone": 15,
        "jinjaSkill": 53,
        "jinjaAdmit": 29,
        "jinjaLNone": 37,
        "jinjaLSkill": 79,
        "jinjaLFNone": 14,
        "jinjaLFSkill": 35,
        "jinjaLFAdmit": 50,
        "jinjaNoPSn": 15,
        "jinjaNoPSLF": 0,
        "jinjaNoPSTasks": 34,
        "fzeroRepos": 5,
        "bleveNone": 13,
        "bleveSkill": 43,
        "bleveAdmit": 34,
        "bleveLNone": 30,
        "bleveLSkill": 73,
        "bleveNoPS": 11,
        "fzeroLNoop": 206,
        "fzeroSNoop": 0,
        "fzeroN": 216,
        "noopOurs": 0,
        "noopOursN": 40,
        "goldOursOk": 33,
        "goldOursN": 35,
    }
    APPROX = {"jinjaGain": 0.38, "jinjaLFGain": 0.21, "leak": 0.17, "bleveGain": 0.30}
    bad = [k for k, v in CHECKS.items() if N[k] != v]
    bad += [k for k, v in APPROX.items() if abs(N[k] - v) > 0.005]
    if bad:
        for k in bad:
            print("MISMATCH", k, N[k], CHECKS.get(k, APPROX.get(k)))
        return 1
    lines = ["% Generated by scripts/make_numbers.py from results files. Do not edit by hand."]
    ra = load(Path("results/replicate_attribution.json"))["stages"]["e2"]["xreposkill"]
    fa = ra["attribution"]["functional"]
    sa = load(Path("results/section21.json"))["P_A"]["auditors"]
    sa_up = load(Path("results/section21.json"))["P_A"]["upper95_task_cluster"]
    nf = load(Path("results/noise_floor_audit.json"))
    nf_base = nf["base_solve_rate"]
    au = load(Path("results/harness_audit.json"))
    cnt = load(Path("results/s28_effects.json"))["counts"]
    N.update(
        {
            "attrTasks": ra["attribution"]["tasks"],
            "attrSkill": fa["skill_candidates"],
            "attrPlacebo": fa["placebo_candidates"],
            "attrR": fa["R"],
            "attrRLo": fa["R_ci95"][0],
            "attrRHi": fa["R_ci95"][1],
            "shamLite": sa["flash-lite"]["lower_bound_new"],
            "shamFlash": sa["flash"]["lower_bound_new"],
            "shamPro": sa["pro"]["lower_bound_new"],
            "noiseWithin": sum(1 for c in nf["claims"] if not c["beyond_rerun_noise"]),
            "noiseClaims": len(nf["claims"]),
            "noiseTasks": nf["n_tasks_noise_pool"],
            "bxOnce": pl["b_x2_once"],
            "bxMonitored": pl["b_x2_monitored"],
            "libDrift": pl["library_drift"],
            "eSR": pl["e_sr"],
            "gkRetire": pl["gatekeeper_two_stage_retire"],
            "etwoS": au["E2"]["skills"]["xreposkill"]["S"]["effect"],
            "etwoF": au["E2"]["skills"]["xreposkill"]["F"]["effect"],
            "etwoB": au["E2"]["skills"]["xreposkill"]["B"]["effect"],
            "tfourS": au["T4"]["skills"]["control-oracle-patch"]["S"]["effect"],
            "tfourF": au["T4"]["skills"]["control-oracle-patch"]["F"]["effect"],
            "eoneFlips": cnt["E1"].get("flip_up", 0) + cnt["E1"].get("flip_down", 0),
            "eoneSides": cnt["E1"]["rescored"],
            "etwoFlips": cnt["E2"].get("flip_up", 0) + cnt["E2"].get("flip_down", 0),
            "etwoSides": cnt["E2"]["rescored"],
            "rescoredPatches": len(load(Path("results/s28_rescored.json"))),
        }
    )
    for k in ("attrSkill", "attrPlacebo", "noiseWithin", "noiseClaims", "eoneFlips", "etwoFlips"):
        CHECKS.setdefault(
            k,
            {
                "attrSkill": 13,
                "attrPlacebo": 14,
                "noiseWithin": 7,
                "noiseClaims": 13,
                "eoneFlips": 3,
                "etwoFlips": 0,
            }[k],
        )
    bad2 = [k for k, v in CHECKS.items() if N[k] != v]
    if bad2:
        for k in bad2:
            print("MISMATCH", k, N[k], CHECKS[k])
        return 1
    pro = load(Path("results/sskb_s23a-pro.json"))["rows"]
    pb = {}
    for r in pro:
        pb.setdefault((r["skill"], r["batch"]), {})[r["arm"]] = r.get("pass_rate")
    full = [v for v in pb.values() if len(v) == 2]
    N["proPairs"] = len(full)
    N["proSame"] = sum(1 for v in full if v["skill"] == v["none"])
    N["proNoneMedian"] = float(np.median([v["none"] for v in full]))
    N["sskbSame"] = sskb["point"]["same_sign_big"]
    N["sskbSamePct"] = round(100 * N["sskbSame"])
    N["sskbConfigs"] = len(sskb["configs"])
    N["sskbSkills"] = sskb["n_skills"]
    for k, v in {"proPairs": 8, "proSame": 8}.items():
        if N[k] != v:
            print("MISMATCH", k, N[k], v)
            return 1
    mu = load(t / "model_unchanged_check.json")
    N["driftMatch"], N["driftTasks"] = mu["matches_e2"], mu["n_tasks"]
    gn = load(Path("results/harness_gold_net.json"))
    N["blockedGold"] = sum(1 for v in gn.values() if v.get("label") == "broken")
    N["sskbThr"] = int(sskb["thr_pp"])
    # section 27 (branch `trial`): length-matched placebo (27a) and traces (27c)
    import gzip
    import re

    from scipy.stats import binomtest

    con, ln = load(t / "s27a_content.json"), load(t / "s27a_length.json")
    N.update(
        {
            "plcS": con["all"]["S"]["none"],
            "conGain": con["all"]["S"]["gain"],
            "conGainLo": con["all"]["S"]["boot95"][0],
            "conGainHi": con["all"]["S"]["boot95"][1],
            "conP": con["all"]["S"]["p_one_sided"],
            "conAdmit": con["all"]["gatekeeper_admit_trial"],
            "conWithPSSkill": con["with_problem_statement"]["S"]["skill"],
            "conWithPSPlc": con["with_problem_statement"]["S"]["none"],
            "conWithPSp": con["with_problem_statement"]["S"]["p_one_sided"],
            "plcNoPS": con["no_problem_statement"]["S"]["none"],
            "lenGain": ln["all"]["S"]["gain"],
            "lenGainLo": ln["all"]["S"]["boot95"][0],
            "lenGainHi": ln["all"]["S"]["boot95"][1],
            # registered as two-sided: exact binomial on the discordant pairs
            "lenP": binomtest(
                ln["all"]["S"]["b"], ln["all"]["S"]["b"] + ln["all"]["S"]["c"]
            ).pvalue,
        }
    )
    recs = [
        json.loads(x)
        for f in ("s27_trace34.traces.jsonl.gz", "s27_trace34b.traces.jsonl.gz")
        for x in gzip.open(t / f, "rt")
    ]
    g1 = g2 = 0
    for r in recs:
        ms = r["messages"]
        obs = [m for m in ms if m["role"] == "user"][1:]  # the first user message is the task
        cmds = " ".join(str(m.get("content", "")) for m in ms if m["role"] == "assistant")
        g1 += bool(re.search(r"git (log|show)", cmds))
        g2 += any("Bug Patch" in str(m.get("content", "")) for m in obs)
    tr = {
        r["instance_id"]: r
        for f in ("s27_trace34.json", "s27_trace34b.json")
        for r in load(t / f)["runs"]
        if "infra_error" not in r
    }
    old = {r["instance_id"]: r for r in load(t / "f1_skill_probe.json")["runs"]}
    same = sum(
        1 for i, r in tr.items() if bool(r["S"]["resolved"]) == bool(old[i]["S"]["resolved"])
    )
    N.update(
        {
            "trTasks": len(recs),
            "trGitCmd": g1,
            "trBugPatch": g2,
            "trSolved": sum(1 for r in tr.values() if r["S"]["resolved"]),
            "trSame": same,
            "trN": len(tr),
            "jinjaNoPSNoneBase": j_in["nops"]["none"],
        }
    )
    for k, v in {"plcS": 24, "trGitCmd": 34, "trBugPatch": 34, "trTasks": 34, "trSame": 30}.items():
        if N[k] != v:
            print("MISMATCH", k, N[k], v)
            return 1
    # Bleve step 4d (branch `trial`): leak-free environment, and Delta_leak as for jinja
    b_lf = ab(mod, t / "s25bleve_leakfree_skill_all.json", t / "s25bleve_leakfree_none.json", bleve)
    bdl = delta_leak(mod, b_in, b_lf)
    brecs = [
        json.loads(x)
        for f in (
            "s25bleve_leakfree_skill.traces.jsonl.gz",
            "s25bleve_leakfree_skillb.traces.jsonl.gz",
        )
        for x in gzip.open(t / f, "rt")
    ]
    bg1 = bg2 = 0
    for r in brecs:
        ms = r["messages"] or []  # two runs crashed on a rate limit before any step (A114m)
        obs = [m for m in ms if m["role"] == "user"][1:]
        cmds = " ".join(str(m.get("content", "")) for m in ms if m["role"] == "assistant")
        bg1 += bool(re.search(r"git (log|show)", cmds))
        bg2 += any("Bug Patch" in str(m.get("content", "")) for m in obs)
    # exploratory (review Q9): `go` absent from the login PATH, by arm, single-commit Bleve
    gonf = re.compile(r"go: (command )?not found|command not found: go|bash: go:")
    gocmd = re.compile(r"\bgo (test|build|run|vet)\b")

    def go_stats(files):
        recs = {}
        for f in files:
            for x in gzip.open(t / f, "rt"):
                r = json.loads(x)
                if r.get("messages"):
                    recs[r["instance_id"]] = r
        out = {}
        for i, r in recs.items():
            obs = [str(m.get("content", "")) for m in r["messages"] if m["role"] == "user"][1:]
            cmd = " ".join(
                str(m.get("content", "")) for m in r["messages"] if m["role"] == "assistant"
            )
            out[i] = (bool(gocmd.search(cmd)), any(gonf.search(o) for o in obs))
        return out

    gn = go_stats(["s25bleve_leakfree_none.traces.jsonl.gz"])
    gs = go_stats(
        ["s25bleve_leakfree_skill.traces.jsonl.gz", "s25bleve_leakfree_skillb.traces.jsonl.gz"]
    )
    lf_none = {r["instance_id"]: r for r in load(t / "s25bleve_leakfree_none.json")["runs"]}
    lf_skill = {r["instance_id"]: r for r in load(t / "s25bleve_leakfree_skill_all.json")["runs"]}
    hit = [i for i, v in gn.items() if v[1]]
    rest = [i for i in gn if i not in set(hit)]

    def solved(d, ids):
        return sum(bool(d[i]["S"]["resolved"]) for i in ids)

    N.update(
        {
            "goNoneTraced": len(gn),
            "goNoneCmd": sum(v[0] for v in gn.values()),
            "goNoneErr": len(hit),
            "goSkillTraced": len(gs),
            "goSkillCmd": sum(v[0] for v in gs.values()),
            "goSkillErr": sum(v[1] for v in gs.values()),
            "goHitNone": solved(lf_none, hit),
            "goHitSkill": solved(lf_skill, hit),
            "goRestN": len(rest),
            "goRestNone": solved(lf_none, rest),
            "goRestSkill": solved(lf_skill, rest),
        }
    )
    for k, v in {"goNoneErr": 68, "goSkillErr": 3, "goHitSkill": 14, "goRestSkill": 17}.items():
        if N[k] != v:
            print("MISMATCH", k, N[k], v)
            return 1
    # S-infra sensitivity (registered): the two runs that crashed on a rate limit are missing data
    bsk = load(t / "s25bleve_leakfree_skill_all.json")
    crashed = {r["instance_id"] for r in bsk["runs"] if r.get("crashed")}
    keep = [q for q in b_lf["pairs"] if q[0] not in crashed]
    bsi = mod.analyse(keep, ALPHA, THETA, C, REPS, SEED)["S"]
    bsl = delta_leak(mod, b_in, {"pairs": keep})
    N.update(
        {
            "bleveCrash": len(crashed),
            "bleveSiN": len(keep),
            "bleveSiB": bsi["b"],
            "bleveSiC": bsi["c"],
            "bleveSiGain": bsi["gain"],
            "bleveSiLeak": bsl["d"],
        }
    )
    # 27b: the jinja skill reused verbatim on pygments; registered two-sided
    pyg = mod.paired(load(t / "s27pyg_skill_all.json"), load(t / "s27pyg_none_all.json"))
    pa = mod.analyse(pyg, ALPHA, THETA, C, REPS, SEED)
    N.update(
        {
            "bleveLFNone": b_lf["all"]["S"]["none"],
            "bleveLFSkill": b_lf["all"]["S"]["skill"],
            "bleveLFGain": b_lf["all"]["S"]["gain"],
            "bleveLFGainLo": b_lf["all"]["S"]["boot95"][0],
            "bleveLFGainHi": b_lf["all"]["S"]["boot95"][1],
            "bleveLFp": b_lf["all"]["S"]["p_one_sided"],
            "bleveLFAdmit": b_lf["all"]["gatekeeper_admit_trial"],
            "bleveLFLNone": b_lf["all"]["L"]["none"],
            "bleveLFLSkill": b_lf["all"]["L"]["skill"],
            "bleveNoPSLF": b_lf["nops"]["skill"],
            "bleveNoPSN": b_lf["nops"]["n"],
            "bleveLeak": bdl["d"],
            "bleveLeakLo": bdl["ci"][0],
            "bleveLeakHi": bdl["ci"][1],
            "bleveLeakSharePct": round(100 * bdl["d"] / b_in["all"]["S"]["gain"]),
            "bleveTrTasks": len(brecs),
            "bleveTrGitCmd": bg1,
            "bleveTrBugPatch": bg2,
            "pygN": len(pyg),
            "pygSkill": pa["S"]["skill"],
            "pygNone": pa["S"]["none"],
            "pygB": pa["S"]["b"],
            "pygC": pa["S"]["c"],
            "pygGain": pa["S"]["gain"],
            "pygGainLo": pa["S"]["boot95"][0],
            "pygGainHi": pa["S"]["boot95"][1],
            "pygP": binomtest(pa["S"]["b"], pa["S"]["b"] + pa["S"]["c"]).pvalue,
            "pygLSkill": pa["L"]["skill"],
            "pygLNone": pa["L"]["none"],
            "pygLGain": pa["L"]["gain"],
            "pygAdmit": "no" if pa["gatekeeper_admit_trial"] is None else "yes",
            "pygLate": sum(
                len(load(t / f)["runs"]) for f in ("s27pyg_skillb.json", "s27pyg_skillc.json")
            ),
        }
    )
    # registered results of branch `trial` (preregistration_main.md, 27b and step 4d)
    for k, v in {
        "bleveLFSkill": 31,
        "bleveLFNone": 14,
        "bleveLFAdmit": 61,
        "bleveNoPSLF": 0,
        "bleveNoPSN": 42,
        "bleveTrTasks": 100,
        "bleveTrGitCmd": 31,
        "bleveTrBugPatch": 0,
        "pygN": 100,
        "pygSkill": 6,
        "pygNone": 5,
        "pygB": 2,
        "pygC": 1,
        "pygLSkill": 70,
        "pygLNone": 42,
        "pygAdmit": "no",
        "pygLate": 21,
        "bleveCrash": 2,
        "bleveSiB": 19,
        "bleveSiC": 2,
    }.items():
        if N[k] != v:
            print("MISMATCH", k, N[k], v)
            return 1
    for k, v in {"bleveLFGain": 0.17, "bleveLeak": 0.13, "pygP": 1.0}.items():
        if abs(N[k] - v) > 0.005:
            print("MISMATCH", k, N[k], v)
            return 1
    # cost cap and step limit of the SWE-smith runs (docs/reviewer_fidelity.md A2; A121)
    sws = [
        "f1_probe.json",
        "f1_skill_probe.json",
        "s25_leakfree_skill.json",
        "s25_leakfree_none.json",
        "s25bleve_f1_probe.json",
        "s25bleve_skill_probe.json",
        "s25bleve_leakfree_none.json",
        "s25bleve_leakfree_skill_all.json",
        "s27_placebo.json",
        "s27pyg_skill_all.json",
        "s27pyg_none_all.json",
        "s27_trace34.json",
        "s27_trace34b.json",
    ]
    runs = [(f, r, load(t / f)["cost_limit"]) for f in sws for r in load(t / f)["runs"]]
    capped = [(f, r) for f, r, lim in runs if r.get("cost_usd", 0) >= lim]
    pyg_none = {r["instance_id"]: r for r in load(t / "s27pyg_none_all.json")["runs"]}
    # worst case for 27b: every capped skill-arm run would have resolved
    extra = sum(
        1
        for f, r in capped
        if f == "s27pyg_skill_all.json"
        and not r["S"]["resolved"]
        and not pyg_none[r["instance_id"]]["S"]["resolved"]
    )
    steps = {
        f: [r.get("steps", 0) for r in load(t / f)["runs"]]
        for f in ("f1_skill_probe.json", "f1_probe.json")
    }
    ps_src = Path("scripts/placebo_suite.py").read_text()
    n_stream, look = (
        int(x) for x in re.search(r"N_STREAM, LOOK, N_RETIRE = (\d+), (\d+)", ps_src).groups()
    )
    pls = load(Path("results/placebo_suite.json"))
    N.update(
        {
            "swsRuns": len(runs),
            "swsCapLimit": runs[0][2],
            "swsCapped": len(capped),
            "pygWorstSkill": pa["S"]["skill"] + extra,
            "pygWorstB": pa["S"]["b"] + extra,
            "pygWorstP": binomtest(
                pa["S"]["b"] + extra, pa["S"]["b"] + extra + pa["S"]["c"]
            ).pvalue,
            "jinjaStepSkill": sum(s >= 50 for s in steps["f1_skill_probe.json"]),
            "jinjaStepNone": sum(s >= 50 for s in steps["f1_probe.json"]),
            "aaStreams": pls["args"]["reps"],
            "aaTrials": n_stream,
            "aaLook": look,
            "aaTasks": pls["aa_tasks"],
            "shamShareUp": sa_up,
            "noiseBase": nf_base,
            # pairing saving, from the generated table (scripts/make_tables.py)
            "pairSaving": float(
                re.search(
                    r"pairing saving .*? & ([0-9.]+)", Path("paper/tables/sskb.tex").read_text()
                )[1]
            ),
        }
    )
    for k, v in {
        "swsRuns": 1134,
        "swsCapped": 1,
        "pygWorstSkill": 7,
        "aaTrials": 200,
        "aaLook": 10,
        "aaTasks": 221,
        "jinjaStepSkill": 14,
        "jinjaStepNone": 1,
    }.items():
        if N[k] != v:
            print("MISMATCH", k, N[k], v)
            return 1
    # section 29 (registered 08/11): the jinja skill without its history instruction, as shipped
    s29 = load(Path("results/s29_analysis.json"))
    N.update(
        {
            "abSkill": s29["P29"]["skill"],
            "abNone": s29["P29"]["none"],
            "abB": s29["P29"]["b"],
            "abC": s29["P29"]["c"],
            "abP": s29["P29"]["p_one_sided"],
            "abGain": s29["P29"]["gain"],
            "abGainLo": s29["P29"]["boot95"][0],
            "abGainHi": s29["P29"]["boot95"][1],
            "abAdmit": s29["gatekeeper_admit_trial"],
            "abLSkill": s29["L"]["skill"],
            "abLNone": s29["L"]["none"],
            "abNoPS": s29["no_problem_statement"]["skill"],
            "abNoPSNone": s29["no_problem_statement"]["none"],
            "abVsLF": s29["vs_full_single_commit"]["d"],
            "abVsLFLo": s29["vs_full_single_commit"]["ci95"][0],
            "abVsLFHi": s29["vs_full_single_commit"]["ci95"][1],
            "abVsFull": -s29["vs_full_as_shipped"]["d"],
            "abVsFullLo": -s29["vs_full_as_shipped"]["ci95"][1],
            "abVsFullHi": -s29["vs_full_as_shipped"]["ci95"][0],
            "abTrGit": s29["traces"]["git_log_or_show"],
            "abTrBug": s29["traces"]["bug_patch_seen"],
            "abTrRuns": s29["traces"]["runs"],
            "abInfra": s29["checks"]["infra_error"]
            + s29["checks"]["crashed"]
            + s29["checks"]["capped"],
        }
    )
    for k, v in {
        "abSkill": 40,
        "abNone": 17,
        "abB": 25,
        "abC": 2,
        "abAdmit": 24,
        "abNoPS": 2,
        "abTrBug": 6,
        "abInfra": 0,
    }.items():
        if N[k] != v:
            print("MISMATCH", k, N[k], v)
            return 1
    mg = load(Path("results/mg_tool_use.json"))["summary"]
    N["mgUsed"] = mg["v1"]["used"] + mg["v2"]["used"]
    N["mgRuns"] = mg["v1"]["tasks"] + mg["v2"]["tasks"]
    for tag, f in (
        ("Lite", "sham_audit.json"),
        ("Flash", "sham_audit_flash.json"),
        ("Pro", "sham_audit_pro.json"),
    ):
        rows = [r for r in load(Path("results") / f)["rows"] if r["condition"] == "sham"]
        N[f"sham{tag}K"] = sum(1 for r in rows if (r.get("decision") or {}).get("attributed"))
        N[f"sham{tag}N"] = len(rows)
    l1, l2 = load(t / "s25_learn_ledger_h1.json"), load(t / "s25_learn_ledger_h2.json")
    av = l2["argv"]
    N["learnTrain"] = int(av[av.index("--train-size") + 1])
    N["learnVal"] = int(av[av.index("--val-size") + 1])
    N["learnTest"] = int(av[av.index("--test-size") + 1])
    N["learnBudget"] = int(av[av.index("--max-metric-calls") + 1])
    refl = av[av.index("--reflection-model") + 1]
    N["learnReflCalls"] = l1["calls_by_model"][refl] + l2["calls_by_model"][refl]
    ls2 = load(t / "s25_learn_summary_h2.json")["extra_info"]  # GEPA's own summary, learning half 2
    N["learnCalls"] = ls2["total_metric_calls"]
    N["learnCands"] = ls2["num_candidates"]
    N["learnValL"] = ls2["best_score"]  # gskill's validation score, lenient scorer L
    ch = load(Path("results/s25_candidates_history.json"))  # scripts/candidates_history.py
    N["candNonEmpty"] = ch["nonempty"]
    N["candHist"] = ch["with_history_line"]
    N["candFirst"] = ch["first_with_history_line"]
    rs = load(t / "rescore_jinja_summary.json")
    N["rsPatches"] = sum(v["patches"] for v in rs.values())
    N["rsScorings"] = sum(v["repeats_scored"] for v in rs.values())
    N["rsFlips"] = sum(v["tasks_with_any_flip"] for v in rs.values())
    for k, v in {
        "shamLiteK": 25,
        "shamFlashK": 3,
        "shamProK": 5,
        "learnBudget": 600,
        "learnCalls": 606,
        "candNonEmpty": 8,
        "candHist": 5,
        "learnCands": 9,
        "rsScorings": 448,
        "rsFlips": 0,
    }.items():
        if N[k] != v:
            print("MISMATCH", k, N[k], v)
            return 1
    # section 30: skill re-learned with every learning container reduced to one commit
    s30 = load(Path("results/s30_analysis.json"))
    s30l = load(Path("results/s30_learn_summary_h2.json"))["extra_info"]
    sh = s30["as_shipped_no_problem_statement"]
    N.update(
        {
            "cleanSkill": s30["P30"]["skill"],
            "cleanNone": s30["P30"]["none"],
            "cleanB": s30["P30"]["b"],
            "cleanC": s30["P30"]["c"],
            "cleanP": s30["P30"]["p_one_sided"],
            "cleanGain": s30["P30"]["gain"],
            "cleanGainLo": s30["P30"]["boot95"][0],
            "cleanGainHi": s30["P30"]["boot95"][1],
            "cleanAdmit": s30["gatekeeper_admit_trial"],
            "cleanLSkill": s30["L"]["skill"],
            "cleanLNone": s30["L"]["none"],
            "cleanVsOrig": s30["vs_original_skill_single_commit"]["d"],
            "cleanVsOrigLo": s30["vs_original_skill_single_commit"]["ci95"][0],
            "cleanVsOrigHi": s30["vs_original_skill_single_commit"]["ci95"][1],
            "cleanHistLines": s30["skill_text"]["history_lines_in_returned_skill"],
            "cleanCandNonEmpty": s30["skill_text"]["nonempty_candidates"],
            "cleanCandHist": s30["skill_text"]["candidates_with_history_line"],
            "cleanBytes": s30["skill_text"]["bytes"],
            "cleanRewrites": s30["checks"]["learn_rewrites_ok"],
            "cleanCalls": s30l["total_metric_calls"],
            "cleanShipN": sh["n"],
            "cleanShipSolved": sh["resolved"],
            "cleanShipGit": sh["git_log_or_show"],
            "cleanShipBug": sh["bug_patch_seen"],
            "cleanInfra": s30["checks"]["infra_error"]
            + s30["checks"]["crashed"]
            + s30["checks"]["capped"],
        }
    )
    for k, v in {
        "cleanSkill": 33,
        "cleanNone": 16,
        "cleanB": 20,
        "cleanC": 3,
        "cleanAdmit": 65,
        "cleanCandHist": 0,
        "cleanCandNonEmpty": 8,
        "cleanCalls": 609,
        "cleanShipSolved": 1,
        "cleanShipBug": 2,
        "cleanInfra": 0,
    }.items():
        if N[k] != v:
            print("MISMATCH", k, N[k], v)
            return 1
    # section 31 (exploratory, after the data): family-wise reading, without-replacement null
    s31 = load(Path("results/s31_alpha_family.json"))
    fam, wor = s31["family"], s31["wor_null"]
    adm = [v for v in fam["streams"].values() if v["admit_at_alpha"] is not None]
    N.update(
        {
            "famK": fam["K"],
            "famThr": round(fam["K"] / ALPHA),
            "famAdmits": len(adm),
            "famKept": sum(v["admit_at_alpha_over_K"] is not None for v in adm),
            "famUnion": fam["K"] * ALPHA,
            "cleanMaxE": round(fam["streams"]["jinja_relearned_single_commit"]["max_e"]),
            "cleanFamAdmit": "no"
            if fam["streams"]["jinja_relearned_single_commit"]["admit_at_alpha_over_K"] is None
            else "yes",
            "worNulls": len(wor),
            "worReps": next(iter(wor.values()))["reps"],
            "worMaxRate": max(v["rate"] for v in wor.values()),
            "worMaxUpper": max(v["cp95_upper"] for v in wor.values()),
        }
    )
    for name, v in fam["streams"].items():  # registered first crossings must reproduce
        reg = {
            "jinja_as_shipped": N["jinjaAdmit"],
            "jinja_single_commit": N["jinjaLFAdmit"],
            "bleve_as_shipped": N["bleveAdmit"],
            "bleve_single_commit": N["bleveLFAdmit"],
            "jinja_content_vs_placebo": N["conAdmit"],
            "jinja_no_history_instruction": N["abAdmit"],
            "jinja_relearned_single_commit": N["cleanAdmit"],
            "pygments_reuse": None,
        }[name]
        if v["admit_at_alpha"] != reg:
            print("MISMATCH s31", name, v["admit_at_alpha"], reg)
            return 1
    ot, tk = s31["order_theta"], s31["tokens"]
    adm_names = [k for k, v in fam["streams"].items() if v["admit_at_alpha"] is not None]
    firsts = [fam["streams"][k]["admit_at_alpha"] for k in adm_names]
    N.update(
        {
            "permN": next(iter(ot.values()))["perms"],
            "permMinShare": min(ot[k]["share_admitted"] for k in adm_names),
            "permPygShare": ot["pygments_reuse"]["share_admitted"],
            "cleanPermMed": round(ot["jinja_relearned_single_commit"]["first_q25_q50_q75"][1]),
            "cleanPermLo": round(ot["jinja_relearned_single_commit"]["first_q25_q50_q75"][0]),
            "cleanPermHi": round(ot["jinja_relearned_single_commit"]["first_q25_q50_q75"][2]),
            "thetaSmall": 0.02,
            "thetaLarge": 0.05,
            "thetaSmallKept": sum(ot[k]["theta"]["0.02"] is not None for k in adm_names),
            "thetaLargeKept": sum(ot[k]["theta"]["0.05"] is not None for k in adm_names),
            "cleanThetaSmall": ot["jinja_relearned_single_commit"]["theta"]["0.02"],
            "tokTrialIn": round(tk["per_paired_trial_input"] / 1000),
            "tokTrialOut": round(tk["per_paired_trial_output"] / 1000),
            "tokAdmitLo": round(min(firsts) * tk["per_paired_trial_input"] / 1e6, 1),
            "tokAdmitHi": round(max(firsts) * tk["per_paired_trial_input"] / 1e6, 1),
            "admitMinTrials": min(firsts),
            "admitMaxTrials": max(firsts),
            "admitMeanTrials": round(sum(firsts) / len(firsts)),
        }
    )
    for k, v in {"famK": 8, "famAdmits": 7, "famKept": 6, "famThr": 320}.items():
        if N[k] != v:
            print("MISMATCH", k, N[k], v)
            return 1
    # section 32 (exploratory, 0 USD): history monitor, decision rules on real streams, exposure
    s32 = load(Path("results/s32_analysis.json"))
    mon, rl = s32["monitor"], s32["rules"]
    lf_cells = [v for v in mon.values() if v["environment"] == "single commit"]
    pyg = mon["pygments/shipped/jinja skill"]
    jn = mon["jinja/shipped/no skill"]
    orig = mon["jinja/shipped/original skill (34 tasks)"]
    blf = mon["bleve/single commit/skill"]
    streams = rl["streams"]
    aa = [v["share_of_orders_admitted"] for v in streams.values() if v["label"] == "null"]
    pos = [v["share_of_orders_admitted"] for v in streams.values() if v["label"] == "positive"]
    plc = streams["jinja placebo vs none"]["share_of_orders_admitted"]
    ex = load(Path("results/s32d_exposure.json"))

    def frac(x: str) -> tuple[int, int]:
        a_, b_ = x.split("/")
        return int(a_), int(b_)

    def pct(x: float) -> str:  # one decimal, as printed
        return f"{100 * x:.1f}"

    N.update(
        {
            "monExplFlag": orig["M2"],
            "monExplRuns": orig["runs"],
            "monLFFlag": sum(v["M2"] for v in lf_cells),
            "monLFRuns": sum(v["runs"] for v in lf_cells),
            "monNoneFlag": jn["M2"],
            "monNoneRuns": jn["runs"],
            "monNoneSolved": jn["resolved_with_M2"],
            "monPygFlag": pyg["M2"],
            "monPygRuns": pyg["runs"],
            "monPygSolved": pyg["resolved_with_M2"],
            "monPygNoneFlag": mon["pygments/shipped/no skill"]["M2"],
            "monCmdBleve": blf["M1"],
            "monCmdBleveRuns": blf["runs"],
            "rulesStreams": len(streams),
            "rulesPos": frac(rl["summary"]["gatekeeper"]["positive_admitted"])[1],
            "rulesNull": frac(rl["summary"]["gatekeeper"]["null_admitted"])[1],
            "rulesHarm": frac(rl["summary"]["gatekeeper"]["harmful_admitted"])[1],
            "rulesPluginNull": frac(rl["summary"]["plug-in, once"]["null_admitted"])[0],
            "rulesGepaPos": frac(rl["summary"]["gepa, first 3"]["positive_admitted"])[0],
            "rulesGkAAMax": pct(max(x["gatekeeper"] for x in aa)),
            "rulesSignAAMax": pct(max(x["sign test, every 10"] for x in aa)),
            "rulesMHAAMax": pct(max(x["mantel-haenszel, every 10"] for x in aa)),
            "rulesMHAAOver": sum(x["mantel-haenszel, every 10"] > ALPHA for x in aa),
            "rulesGepaAAMin": pct(min(x["gepa, first 3"] for x in aa)),
            "rulesGepaAAMax": pct(max(x["gepa, first 3"] for x in aa)),
            "rulesGepaPosMin": round(100 * min(x["gepa, first 3"] for x in pos)),
            "rulesGepaPosMax": round(100 * max(x["gepa, first 3"] for x in pos)),
            "rulesPlcGk": pct(plc["gatekeeper"]),
            "rulesPlcSign": pct(plc["sign test, every 10"]),
            "rulesPlcMH": pct(plc["mantel-haenszel, every 10"]),
            "expoTasks": f"{ex['n_tasks']:,}".replace(",", "{,}"),
            "expoEmpty": f"{ex['n_empty']:,}".replace(",", "{,}"),
            "expoRepos": ex["n_repos"],
            "expoPct": pct(ex["share_all"]),
            "expoReposHigh": ex["repos_ge_0.30"],
            "expoReposLow": ex["repos_le_0.10"],
        }
    )
    for k, v in {  # values recorded in the preregistration, section 32 results
        "monExplFlag": 34,
        "monExplRuns": 34,
        "monLFFlag": 0,
        "monLFRuns": 398,
        "monNoneFlag": 3,
        "monPygFlag": 9,
        "monPygSolved": 0,
        "monCmdBleve": 31,
        "rulesStreams": 20,
        "rulesPos": 7,
        "rulesNull": 4,
        "rulesHarm": 3,
        "rulesPluginNull": 3,
        "rulesGepaPos": 6,
        "rulesGkAAMax": "0.0",
        "rulesMHAAMax": "7.9",
        "rulesMHAAOver": 3,
        "rulesGepaAAMin": "5.8",
        "rulesGepaAAMax": "20.0",
        "rulesGepaPosMin": 46,
        "rulesGepaPosMax": 75,
        "expoPct": "30.5",
        "expoRepos": 222,
    }.items():
        if N[k] != v:
            print("MISMATCH s32", k, N[k], v)
            return 1
    # section 33 (second seed, confirmatory) and section 35 (36 unused tasks, confirmatory)
    s33 = load(Path("results/s33_analysis.json"))
    s35 = load(Path("results/s35_analysis.json"))
    a33, b33, p35 = s33["P33a"], s33["P33b"], s35["P35"]
    new = s35["resolved_on_new_tasks"]
    nps = s33["no_problem_statement"]
    N.update(
        {
            "sdSkill": a33["skill"],
            "sdNone": a33["none"],
            "sdB": a33["b"],
            "sdC": a33["c"],
            "sdP": a33["p_one_sided"],
            "sdGain": a33["gain"],
            "sdGainLo": a33["boot95"][0],
            "sdGainHi": a33["boot95"][1],
            "sdLFSkill": b33["skill"],
            "sdLFNone": b33["none"],
            "sdLFB": b33["b"],
            "sdLFC": b33["c"],
            "sdLFP": b33["p_one_sided"],
            "sdLFGain": b33["gain"],
            "sdLFGainLo": b33["boot95"][0],
            "sdLFGainHi": b33["boot95"][1],
            "sdAdmit": s33["gatekeeper_admit_trial"]["shipped"],
            "sdLFAdmit": s33["gatekeeper_admit_trial"]["single_commit"],
            "sdLeak": s33["delta_leak_seed51"]["d"],
            "sdLeakLo": s33["delta_leak_seed51"]["ci95"][0],
            "sdLeakHi": s33["delta_leak_seed51"]["ci95"][1],
            "sdPool": f"{s33['delta_leak_pooled']['d']:.3f}",
            "sdPoolLo": f"{s33['delta_leak_pooled']['ci95'][0]:.3f}",
            "sdPoolHi": f"{s33['delta_leak_pooled']['ci95'][1]:.3f}",
            "sdEnvP": s33["P33c"]["p_anytime"],
            "sdEnvPFirst": round(s32["contrast"]["jinja"]["p_anytime"], 3),
            "sdNoPS": nps["ship_skill"],
            "sdNoPSOther": nps["ship_none"] + nps["lf_none"] + nps["lf_skill"],
            "sdInfra": s33["checks"]["infra_error"] + s33["checks"]["crashed"],
            "cfN": p35["n"],
            "cfOld": p35["n_test_seed51"],
            "cfNew": p35["n_new"],
            "cfCross": p35["first_crossing_at_40"],
            "cfP": p35["p_anytime"],
            "cfFor": p35["tasks_with_D_below_0"],
            "cfAgainst": p35["tasks_with_D_above_0"],
            "cfTies": p35["n"] - p35["tasks_with_D_below_0"] - p35["tasks_with_D_above_0"],
            "cfOrders": round(100 * p35["share_of_orders_rejecting"]),
            "cfShipSkill": new["ship_skill"],
            "cfShipNone": new["ship_none"],
            "cfLFSkill": new["lf_skill"],
            "cfLFNone": new["lf_none"],
            "cfMon": int(s35["monitor_M2_as_shipped"]["ship_skill"].split("/")[0]),
            "cfMonNone": int(s35["monitor_M2_as_shipped"]["ship_none"].split("/")[0]),
            "cfSensCross": s35["sensitivity_without_timeout_task"]["first_crossing_at_40"],
        }
    )
    for k, v in {  # values recorded in the preregistration, results of sections 33 and 35
        "sdSkill": 55,
        "sdNone": 21,
        "sdLFSkill": 35,
        "sdLFNone": 17,
        "sdAdmit": 53,
        "sdLFAdmit": 74,
        "sdNoPS": 17,
        "sdNoPSOther": 0,
        "sdInfra": 0,
        "cfN": 70,
        "cfCross": 36,
        "cfFor": 36,
        "cfAgainst": 0,
        "cfTies": 34,
        "cfOrders": 100,
        "cfShipSkill": 20,
        "cfShipNone": 0,
        "cfLFSkill": 1,
        "cfLFNone": 0,
        "cfMon": 36,
        "cfMonNone": 1,
        "cfSensCross": 36,
    }.items():
        if N[k] != v:
            print("MISMATCH s33/s35", k, N[k], v)
            return 1
    if (
        not (s33["holm_reject"]["P33a"] and s33["holm_reject"]["P33b"])
        or s33["holm_reject"]["P33c"]
    ):
        print("MISMATCH s33 holm")
        return 1
    if abs(N["sdLeak"] - 0.16) > 0.005 or not p35["reject"]:
        print("MISMATCH s33 leak / s35 reject")
        return 1
    # section 34 (registered, descriptive): a second Gemini agent on the 34 tasks without a
    # description, environment as shipped; the counts named exploratory were added after the data
    s34 = load(Path("results/s34_analysis.json"))
    fn, fs = s34["none"], s34["skill"]
    N.update(
        {
            "flN": fn["runs"],
            "flNone": fn["resolved"],
            "flSkill": fs["resolved"],
            "flNoneMon": fn["M2"],
            "flSkillMon": fs["M2"],
            "flNoneFirstLog": fn["exploratory_first_command_git_log"],
            "flNoneOpen": fn["exploratory_opened_commit_content"],
            "flNoPatch": fn["runs"] - fn["resolved"],
            "flInfra": fn["infra_error"] + fs["infra_error"] + fn["crashed"] + fs["crashed"],
        }
    )
    for k, v in {
        "flN": 34,
        "flNone": 31,
        "flSkill": 34,
        "flNoneMon": 34,
        "flSkillMon": 34,
        "flNoneFirstLog": 31,
        "flNoneOpen": 33,
        "flNoPatch": 3,
        "flInfra": 0,
    }.items():
        if N[k] != v:
            print("MISMATCH s34", k, N[k], v)
            return 1
    if fs["runs"] != 34:
        print("MISMATCH s34 skill runs")
        return 1
    # section 36 (exploratory, 0 USD): family after sections 33/35, learner provenance, patches
    s36 = load(Path("results/s36_analysis.json"))
    fa, lj, lb, lc = (
        s36["36a"],
        s36["36b"]["jinja_original"],
        s36["36b"]["bleve"],
        s36["36b"]["jinja_clean"],
    )
    add = next(c for c in lj["calls"] if c["child_history"] and not c["parent_history"])
    rv, bh = s36["36c"], s36["36d"]["single_commit"]
    vals = {c["idx"]: c["val_L"] for c in lj["candidates"]}
    N.update(
        {
            "famAllK": fa["K"],
            "famAllThr": fa["threshold"],
            "famAllReg": fa["registered_positive"],
            "famAllHeld": fa["held"],
            "lrnFirst": lj["first_history_candidate"],
            "lrnCands": len(lj["candidates"]) - 1,
            "lrnValHist": lj["val_L_mean_with_history"],
            "lrnValNoHist": lj["val_L_mean_without_history"],
            "lrnBleveValHist": lb["val_L_mean_with_history"],
            "lrnBleveValNoHist": lb["val_L_mean_without_history"],
            "lrnFirstVal": vals[lj["first_history_candidate"]],
            "lrnFirstParentVal": vals[lj["candidates"][lj["first_history_candidate"]]["parent"]],
            "lrnAddParent": add["parent_idx"],
            "lrnAddChild": add["child_idx"],
            "lrnAddParentVal": vals[add["parent_idx"]],
            "lrnAddChildVal": vals[add["child_idx"]],
            "lrnBestVal": max(vals.values()),
            "lrnCallsSaved": lj["proposer_calls_saved"],
            "lrnCallsSavedBleve": lb["proposer_calls_saved"],
            "lrnCallsSavedClean": lc["proposer_calls_saved"],
            "lrnTrajLeak": lj["trajectories_M2"],
            "lrnTrajShown": lj["trajectories_shown"],
            "lrnCleanTrajLeak": lc["trajectories_M2"],
            "lrnCleanTrajShown": lc["trajectories_shown"],
            "rvShipNoIssue": rv["seed41:shipped/skill"]["no_issue"]["exact_revert"],
            "rvShipNoIssueN": rv["seed41:shipped/skill"]["no_issue"]["resolved"],
            "rvShipWith": rv["seed41:shipped/skill"]["with_issue"]["exact_revert"],
            "rvShipWithN": rv["seed41:shipped/skill"]["with_issue"]["resolved"],
            "rvLFWith": rv["seed41:single/skill"]["with_issue"]["exact_revert"],
            "rvLFWithN": rv["seed41:single/skill"]["with_issue"]["resolved"],
            "rvUnseen": rv["unseen36:shipped/skill"]["no_issue"]["exact_revert"],
            "rvUnseenN": rv["unseen36:shipped/skill"]["no_issue"]["resolved"],
            "bhNoneTest": bh["none_seed51"]["ran_tests"],
            "bhOrigTest": bh["original_skill_seed51"]["ran_tests"],
            "bhNoneCleanTest": bh["none_s30"]["ran_tests"],
            "bhCleanTest": bh["clean_skill_s30"]["ran_tests"],
            "bhNoneEmpty": bh["none_seed51"]["empty_patch"],
            "bhOrigEmpty": bh["original_skill_seed51"]["empty_patch"],
            "bhNoneCleanEmpty": bh["none_s30"]["empty_patch"],
            "bhCleanEmpty": bh["clean_skill_s30"]["empty_patch"],
        }
    )
    for k, v in {
        "famAllK": 12,
        "famAllHeld": 7,
        "lrnFirst": 2,
        "lrnAddParent": 4,
        "lrnAddChild": 6,
        "lrnCleanTrajLeak": 0,
        "rvUnseen": 3,
        "bhOrigTest": 85,
        "bhCleanTest": 82,
    }.items():
        if N[k] != v:
            print("MISMATCH", k, N[k], v)
            return 1
    # section 41 (exploratory, 0 USD): the git history of every task, and what the agent was shown
    ha = load(Path("results/history_audit.json"))
    l1 = ha["level1_exists"]
    arm = {
        (r["agent"], r["environment"], r["condition"]): r
        for r in ha["level2_3_by_arm"]
        if r["subset"] == "no description"
    }
    s41 = "study agent, seed 41"
    s51 = "study agent, seed 51"
    s36n = "study agent, seed 51, 36 new tasks"
    fl = "second Gemini agent, seed 41"
    study = [
        arm[(s41, "shipped", "original skill")],
        arm[(s51, "shipped", "original skill")],
        arm[(s36n, "shipped", "original skill")],
    ]
    single = [r for r in ha["level2_3_by_arm"] if r["environment"] == "single commit"]
    single = [r for r in single if r["subset"] == "all"]
    N.update(
        {
            "hiTasks": sum(v["tasks"] for v in l1.values()),
            "hiThree": sum(v["three_commit_structure"] for v in l1.values()),
            "hiBugEq": sum(v["bug_patch_equals_benchmark_patch"] for v in l1.values()),
            "hiOnlyDel": sum(v["f2p_commit_only_deletes_files"] for v in l1.values()),
            "hiStudyDiffA": study[0]["bug_diff_shown"],
            "hiStudyDiffB": study[1]["bug_diff_shown"],
            "hiStudyDiffC": study[2]["bug_diff_shown"],
            "hiStudyNA": study[0]["runs"],
            "hiStudyNC": study[2]["runs"],
            "hiStudyTests": max(
                r["deleted_tests_shown"] + r["tests_restored_and_run"] for r in study
            ),
            "hiStudyResNone": sum(r["resolved_with_neither"] for r in study),
            "hiFlNoneDiff": arm[(fl, "shipped", "no skill")]["bug_diff_shown"],
            "hiFlNoneTests": arm[(fl, "shipped", "no skill")]["deleted_tests_shown"],
            "hiFlNoneRestore": arm[(fl, "shipped", "no skill")]["restore_or_read_old_file_cmd"],
            "hiFlSkillTests": arm[(fl, "shipped", "original skill")]["deleted_tests_shown"],
            "hiSingleRuns": sum(r["runs"] for r in single),
            "hiSingleSeen": sum(
                r["bug_diff_shown"] + r["deleted_tests_shown"] + r["tests_restored_and_run"]
                for r in single
            ),
        }
    )
    conf = {(True, True): 0, (True, False): 0, (False, True): 0, (False, False): 0}
    for stem, runs in ha["runs"].items():  # every saved trace of sections 27-35, one per run
        if stem.startswith("c10"):
            continue  # C10, C10R (sections 43, 44) are reported below; s41 counts predate them
        for r in runs:
            conf[(r["seen_bug_msg"], r["bug_diff_shown"])] += 1
    N.update(
        {
            "monConfTP": conf[(True, True)],
            "monConfFP": conf[(True, False)],
            "monConfFN": conf[(False, True)],
            "monConfTN": conf[(False, False)],
            "monConfN": sum(conf.values()),
            "monConfAgree": conf[(True, True)] + conf[(False, False)],
        }
    )
    for k, v in {
        "hiTasks": 1086,
        "hiThree": 1086,
        "hiBugEq": 1086,
        "hiOnlyDel": 1086,
        "hiStudyDiffA": 29,
        "hiStudyDiffB": 32,
        "hiStudyDiffC": 35,
        "hiStudyTests": 0,
        "hiStudyResNone": 0,
        "hiFlNoneDiff": 33,
        "hiFlNoneTests": 29,
        "hiFlNoneRestore": 32,
        "hiFlSkillTests": 30,
        "hiSingleRuns": 669,
        "hiSingleSeen": 0,
        "monConfTP": 185,
        "monConfFP": 13,
        "monConfFN": 0,
        "monConfN": 1573,
    }.items():
        if N[k] != v:
            print("MISMATCH s41", k, N[k], v)
            return 1
    # section 42 (post hoc, 0 USD): end-of-pool test on the 12 decisions; method check
    e42 = load(Path("results/s42_end_of_pool.json"))["decisions"]
    mc = load(Path("results/method_check.json"))["end_of_pool"]

    def sci(x: float) -> str:
        if x < 1000:
            return f"{x:.0f}" if x >= 10 else f"{x:.1f}"
        m, e = f"{x:.1e}".split("e")
        return rf"\ensuremath{{{m}\times10^{{{int(e)}}}}}"

    keys = {
        "1": "A",
        "2": "B",
        "3": "C",
        "4": "D",
        "5": "E",
        "6": "F",
        "7": "G",
        "8": "H",
        "9": "I",
        "10": "J",
        "11": "K",
        "12": "L",
    }
    for name, d in e42.items():
        num = name.split()[0]
        N["eop" + keys[num]] = sci(d["E"])
        N["eopSame" + keys[num]] = d["run_structure"]["tasks_same_job"]
    regs = [d for n, d in e42.items() if n.split()[0] not in ("8", "11")]
    cov = [v for k, v in mc["type1"].items() if "NOT" not in k]
    sh = [v for k, v in mc["type1"].items() if "NOT" in k][0]
    N.update(
        {
            "eopRegN": len(regs),
            "eopHeldForty": sum(d["reject_at_40"] for d in regs),
            "eopHeldFam": sum(d["reject_at_480"] for d in regs),
            "eopTauMinP": min(
                d["diagnostics"]["kendall_p_two_sided_perm"]
                for d in e42.values()
                if d["diagnostics"]["kendall_tau"] is not None
            ),
            "eopRateCrash": sum(d["diagnostics"]["rate_limit_crashes"] for d in e42.values()),
            "eopTypeMax": max(v["end_of_pool_reject"] for v in cov),
            "eopSignTypeMax": max(v["sign_test_reject"] for v in cov),
            "eopShared": sh["end_of_pool_reject"],
            "eopSignShared": sh["sign_test_reject"],
            "eopPowSmall": mc["power"]["0.109"]["end_of_pool"],
            "eopSignPowSmall": mc["power"]["0.109"]["sign_test"],
            "eopPowMid": mc["power"]["0.2"]["end_of_pool"],
            "eopSignPowMid": mc["power"]["0.2"]["sign_test"],
            "eopValidReps": int(round((1 / mc["type1_mcse"] ** 2) * 0.025 * 0.975)),
            # E-S3 (docs/ease_writing_rules.md): package version of the simulation run
            "simNumpy": load(Path("results/method_check.json"))["environment"]["numpy"],
            # R-102: sensitivity of the end-of-pool test to dependence between tasks
            **dep_numbers(load(Path("results/dependence_sensitivity.json"))),
        }
    )
    for k, v in {
        "eopRegN": 10,
        "eopHeldForty": 10,
        "eopHeldFam": 8,
        "eopRateCrash": 2,
        "eopSameI": 100,
        "eopSameA": 0,
        "eopValidReps": 12000,
    }.items():
        if N[k] != v:
            print("MISMATCH s42", k, N[k], v)
            return 1
    # cohorts of the 70-task test (reviewer P0: 34 known task ids with a new seed + 36 new ids):
    # every D_i is -0.5 or 0 (section 42 values), so each cohort's count follows from its mean
    vals = e42["12 P35_environment_contrast_unseen"]["values"]
    if set(vals) != {"-0.5", "0.0"}:
        print("MISMATCH s42 P35 values", vals)
        return 1
    s35a = load(Path("results/s35_analysis.json"))
    n_new = s35a["P35"]["n_new"]
    new_for = round(-s35a["new_tasks_only"]["mean_D"] * n_new / 0.5)
    N["cfNewFor"] = new_for
    N["cfOldFor"] = vals["-0.5"] - new_for
    N["cfNewSignP"] = 0.5**new_for  # exact one-sided sign test, no discordant pair against
    if (N["cfNewFor"], N["cfOldFor"]) != (19, 17):
        print("MISMATCH cohorts", N["cfNewFor"], N["cfOldFor"])
        return 1
    for k in ("eopTauMinP", "eopSignTypeMax", "eopShared", "eopSignShared"):
        N[k] = f"{N[k]:.3f}"  # three decimals: 0.052 must not print as 0.05
    if (
        e42["8 pygments_reuse"]["reject_at_40"]
        or e42["11 P33c_environment_contrast"]["reject_at_40"]
    ):
        print("MISMATCH s42 non-rejections")
        return 1
    # section 43 (C10, registered before the paid run): message x diff of the git history
    c10 = load(Path("results/c10_analysis.json"))
    cc = c10["contrasts"]
    for name, key in (("main A-C", "AC"), ("A-B", "AB"), ("B-D", "BD"), ("C-D", "CD")):
        N["cten" + key + "N"] = cc[name]["n"]
        N["cten" + key + "Neg"] = cc[name]["n_negative"]
        N["cten" + key + "Pos"] = cc[name]["n_positive"]
        N["cten" + key + "Mean"] = cc[name]["mean_D"]
        N["cten" + key + "Lo"], N["cten" + key + "Hi"] = cc[name]["bootstrap_95"]
        N["cten" + key + "E"] = sci(cc[name]["E"])
    ix = c10["interaction (A-B)-(C-D)"]
    N["ctenIxMean"], (N["ctenIxLo"], N["ctenIxHi"]) = ix["mean"], ix["bootstrap_95"]
    for arm, (k, n) in c10["solved"].items():
        tag = arm.replace("_none", "None").replace("_skill", "Skill")
        N["cten" + tag], N["cten" + tag + "N"] = k, n
    N["ctenTasks"] = c10["task_order_n"]
    c10arm = {
        (r["environment"], r["condition"]): r
        for r in ha["level2_3_by_arm"]
        if r["environment"].startswith("C10")
        and r["subset"] == "all"
        and r["agent"] == "study agent, seed 51"
    }
    N["ctenADiff"] = c10arm[("C10 A: original history", "original skill")]["bug_diff_shown"]
    N["ctenBTests"] = c10arm[("C10 B: neutral message", "original skill")]["tests_restored_and_run"]
    N["ctenCTests"] = c10arm[("C10 C: empty Bug Patch", "original skill")]["tests_restored_and_run"]
    N["ctenDTests"] = c10arm[("C10 D: no bug commit", "original skill")]["tests_restored_and_run"]
    N["ctenNoTzeroDiff"] = sum(
        c10arm[(e, c)]["bug_diff_shown"]
        for e in ("C10 C: empty Bug Patch", "C10 D: no bug commit")
        for c in ("no skill", "original skill")
    )
    N["ctenNoTzeroRuns"] = sum(
        c10arm[(e, c)]["runs"]
        for e in ("C10 C: empty Bug Patch", "C10 D: no bug commit")
        for c in ("no skill", "original skill")
    )
    for k, v in {
        "ctenACN": 45,
        "ctenACNeg": 22,
        "ctenACPos": 2,
        "ctenABN": 51,
        "ctenBDN": 62,
        "ctenCDN": 45,
        "ctenASkill": 35,
        "ctenTasks": 70,
        "ctenADiff": 66,
    }.items():
        if N[k] != v:
            print("MISMATCH s43", k, N[k], v)
            return 1
    sa = load(Path("results/c10_stop_audit.json"))
    sam = sa["contrasts"]["main A-C"]
    N["ctenACEfixed"] = sam["E_on_first_34"]
    N["ctenACFirstK"] = sam["first_k_E_at_threshold"]
    N["ctenACMinAfter"] = sam["min_E_after_first"]
    N["ctenFixedN"] = 34
    if not all(
        a["spend_equals_sum_of_run_costs"]
        and a["runs_started_after_guard"] == 0
        and a["stop_explained_by_guard"]
        and a["prefix_of_task_order"]
        for a in sa["arms"].values()
    ):
        print("MISMATCH s43 stop audit")
        return 1
    if (sam["n"], sam["first_k_E_at_threshold"]) != (45, 36) or sam["E_on_first_34"] >= 40:
        print("MISMATCH s43 stop audit values")
        return 1
    if N["ctenANone"] != max(c10["solved"][v + "_none"][0] for v in "ABCD"):
        print("MISMATCH s43: the text says 'at most ctenANone' without the skill")
        return 1
    if not cc["main A-C"]["reject_at_threshold"] or cc["B-D"]["reject_at_threshold"]:
        print("MISMATCH s43 decisions")
        return 1
    # section 44 (C10R, registered before its run): the fixed 70-task pool, seed 61
    cr = load(Path("results/c10r_analysis.json"))
    for name, key in (("main A-C", "AC"), ("A-B", "AB"), ("B-D", "BD"), ("C-D", "CD")):
        c = cr["contrasts"][name]
        N["ctr" + key + "N"], N["ctr" + key + "Neg"] = c["n"], c["n_negative"]
        N["ctr" + key + "Pos"], N["ctr" + key + "Mean"] = c["n_positive"], c["mean_D"]
        N["ctr" + key + "Lo"], N["ctr" + key + "Hi"] = c["bootstrap_95"]
        N["ctr" + key + "E"] = sci(c["E"])
    ixr = cr["interaction (A-B)-(C-D)"]
    N["ctrIxMean"], (N["ctrIxLo"], N["ctrIxHi"]) = ixr["mean"], ixr["bootstrap_95"]
    for arm, (k, n) in cr["solved"].items():
        tag = arm.replace("_none", "None").replace("_skill", "Skill")
        N["ctr" + tag], N["ctr" + tag + "N"] = k, n
    crarm = {
        (r["environment"], r["condition"]): r
        for r in ha["level2_3_by_arm"]
        if r["environment"].startswith("C10")
        and r["subset"] == "all"
        and r["agent"] == "study agent, seed 61"
    }
    N["ctrADiff"] = crarm[("C10 A: original history", "original skill")]["bug_diff_shown"]
    for v, env in (
        ("B", "C10 B: neutral message"),
        ("C", "C10 C: empty Bug Patch"),
        ("D", "C10 D: no bug commit"),
    ):
        N["ctr" + v + "Tests"] = crarm[(env, "original skill")]["tests_restored_and_run"]
    sar = load(Path("results/c10r_stop_audit.json"))
    if not all(
        a["runs"] == a["n_tasks"] == 70 and a["prefix_of_task_order"] for a in sar["arms"].values()
    ):
        print("MISMATCH s44: an arm of C10R did not run all 70 tasks")
        return 1
    for k, v in {
        "ctrACN": 70,
        "ctrACNeg": 40,
        "ctrACPos": 0,
        "ctrASkill": 41,
        "ctrADiff": 70,
    }.items():
        if N[k] != v:
            print("MISMATCH s44", k, N[k], v)
            return 1
    if not cr["contrasts"]["main A-C"]["reject_at_threshold"]:
        print("MISMATCH s44 decision")
        return 1
    N["ctrNoneMax"] = max(cr["solved"][v + "_none"][0] for v in "ABCD")
    # tasks of A-C with D_i = -1 (the rest of the negative tasks have -1/2): from E, lambda = 0.5
    import math

    c = cr["contrasts"]["main A-C"]
    k_full = round(math.log(c["E"] / 1.25 ** c["n_negative"]) / math.log(1.5 / 1.25))
    if (
        c["n_positive"]
        or abs(1.25 ** (c["n_negative"] - k_full) * 1.5**k_full - c["E"]) > 1e-6 * c["E"]
    ):
        print("MISMATCH s44: E is not 1.25^a 1.5^b over the negative tasks")
        return 1
    N["ctrACFull"] = k_full
    # sections 46-47 (X2', X1', registered 18/11): bridge chroot vs Docker; second learning runs
    from make_ablation import RULE

    x2 = load(Path("results/x2_analysis.json"))
    dock = ("docker41", "docker51", "docker61")
    N["xtN"] = x2["skill"]["n"]
    N["xtChrootSkill"], N["xtChrootNone"] = x2["skill"]["chroot"], x2["none"]["chroot"]
    N["xtDockSkillLo"] = min(x2["skill"][k] for k in dock)
    N["xtDockSkillHi"] = max(x2["skill"][k] for k in dock)
    N["xtDockNoneHi"] = max(x2["none"][k] for k in dock)
    for env, f in (("Ship", "x1eval_ship_ab.json"), ("LF", "x1eval_lf_ab.json")):
        xe = load(Path("results") / f)
        s, nps = xe["all"]["S"], xe["no_problem_statement"]["S"]
        N["xo" + env + "None"], N["xo" + env + "Skill"] = s["none"], s["skill"]
        N["xo" + env + "Gain"], (N["xo" + env + "GainLo"], N["xo" + env + "GainHi"]) = (
            s["gain"],
            s["boot95"],
        )
        N["xo" + env + "Admit"] = xe["all"]["gatekeeper_admit_trial"]
        N["xo" + env + "NoPS"], N["xo" + env + "NoPSNone"] = nps["skill"], nps["none"]
    for env, f in (("Ship", "jinja_x1ship_best_skills.txt"), ("LF", "jinja_x1lf_best_skills.txt")):
        text = Path("docs/skills/gskill", f).read_text()
        N["xo" + env + "HistLines"] = sum(bool(RULE.search(x)) for x in text.splitlines())
    q4 = load(Path("results/x1eval_lfskill_ship34.json"))["runs"]
    N["xoLFOnShip"] = sum(r["S"]["resolved"] for r in q4)
    N["xoLFOnShipN"] = len(q4)
    for k, v in {
        "xoShipSkill": 67,
        "xoShipNone": 13,
        "xoLFSkill": 33,
        "xoLFNone": 8,
        "xoShipNoPS": 22,
        "xoLFNoPS": 0,
        "xoShipHistLines": 3,
        "xoLFHistLines": 0,
        "xoLFOnShip": 0,
        "xoLFOnShipN": 34,
        "xtChrootSkill": 20,
    }.items():
        if N[k] != v:  # the values of notes 47-8 and 47-9
            print("MISMATCH s46-47", k, N[k], v)
            return 1
    # section 40 (C4', kaggle/preregistration_s40.md, note 40-27): other vendors' agents, 70 tasks
    for tag, key in (("ossh", "Oss"), ("nano", "Nano"), ("haiku", "Haiku")):
        m = load(Path(f"results/c4p_{tag}_analysis.json"))["main"]
        N["vend" + key + "N"] = m["n"]
        for arm, a in (
            ("none", "None"),
            ("skill", "Skill"),
            ("lf_none", "LFNone"),
            ("lf_skill", "LFSkill"),
        ):
            N["vend" + key + a] = m["solved"][arm]
        N["vend" + key + "Neg"], N["vend" + key + "Pos"] = m["neg_pos"]
        N["vend" + key + "Mean"] = m["mean_D"]
        N["vend" + key + "Lo"], N["vend" + key + "Hi"] = m["ci95_D"]
        e = m["E"]
        N["vend" + key + "E"] = f"{e:.3f}" if e < 1 else f"{e:.1f}" if e < 1e3 else sci(e)
        N["vend" + key + "Rej"] = "yes" if e >= 120 else "no"  # family threshold 3/alpha
    hs = load(Path("results/c4p_haiku_analysis.json"))
    N["vendHaikuDl"] = len(hs["download_tasks_in_pool"])
    N["vendHaikuDlN"] = hs["sensitivity_without_downloads"]["n"]
    N["vendHaikuDlE"] = f"{hs['sensitivity_without_downloads']['E']:.2f}"
    for k, v in {
        "vendOssSkill": 23,
        "vendNanoSkill": 20,
        "vendHaikuNone": 24,
        "vendHaikuLFSkill": 19,
    }.items():
        if N[k] != v:
            print("MISMATCH s40", k, N[k], v)
            return 1
    if N["vendOssRej"] != "yes" or N["vendNanoRej"] != "no" or N["vendHaikuRej"] != "no":
        print("MISMATCH s40 decisions")
        return 1
    # section 38 and A' (kaggle/preregistration_s38.md, notes 38-6 to 38-11): other skill writers
    a38 = load(Path("results/a38_analysis.json"))
    wr = {
        "Pro": "google/gemini-3.1-pro-preview",
        "Nano": "openai/gpt-5.4-nano-2026-03-17",
        "Oss": "openai/gpt-oss-120b",
        "Grok": "xai/grok-4.6",
        "Haiku": "anthropic/claude-haiku-5-5",
    }
    for key, m in wr.items():
        h = a38["models"][m]["H"]
        N["wr" + key + "Leak"] = h["leak/ablated"]["mean"]
        N["wr" + key + "NoLeak"] = h["noleak_leaky_env/ablated"]["mean"]
        N["wr" + key + "P"] = h["leak/ablated - noleak_leaky_env/ablated"]["p_one_sided"]
    N["wrProClean"] = a38["models"][wr["Pro"]]["G"]["clean/ablated"]["mean"]
    N["wrMinP"] = min(N["wr" + k + "P"] for k in ("Nano", "Oss", "Grok", "Haiku"))
    N["wrHolm"] = f"{0.025 / 4:.5f}"  # Holm's first step over the four other vendors
    if any(a38["holm_primary_H"].values()) or N["wrMinP"] <= 0.025 / 4:
        print("MISMATCH s38: a model of another vendor passes Holm")
        return 1
    ap_ = load(Path("results/a38p_analysis.json"))
    N["wrRenP"] = ap_["H"]["p_one_sided"]
    rows_ap = [
        json.loads(x)
        for x in Path("results/a38p_results_20261117.jsonl").read_text().splitlines()
        if x.strip()
    ]
    N["wrRenN"] = len(rows_ap)
    N["wrRenNamed"] = sum("Merge branch 'stable'" in r.get("new_skills", "") for r in rows_ap)
    if (N["wrRenN"], N["wrRenNamed"]) != (18, 11) or ap_["reject_H"]:
        print("MISMATCH s38 A'")
        return 1
    # bridge K: chroot minus the first Docker run, skill arm (note 47-9)
    N["xtDiff"], (N["xtDiffLo"], N["xtDiffHi"]) = (
        x2["skill"]["chroot-d41"][0],
        x2["skill"]["chroot-d41"][1],
    )
    # C10R arm A with the skill: runs that displayed or restored the deleted tests (history audit)
    arA = crarm[("C10 A: original history", "original skill")]
    N["ctrATests"] = arA["deleted_tests_shown"] + arA["tests_restored_and_run"]
    # section 34 model without a skill in the single-commit environment (W7-b runs, note 45-2)
    flf = [
        r
        for f in ("s34_lfnone.json", "s34_lfnone_rest.json")
        for r in load(Path("results") / f)["runs"]
    ]
    N["flLFNone"] = sum(bool((r.get("S") or {}).get("resolved")) for r in flf)
    N["flLFN"] = len(flf)
    if (N["flLFNone"], N["flLFN"], N["ctrATests"]) != (12, 34, 0):
        print("MISMATCH bridge/C10R/s34 one commit", N["flLFNone"], N["flLFN"], N["ctrATests"])
        return 1
    # section 49 (X3', notes 49-1 to 49-3): blind human labels of the 104-trace stratum
    x3 = load(Path("results/x3_analysis.json"))
    N["xhN"] = x3["n"]
    N["xhAgreeMin"] = min(x3["tables"][q]["agree"] for q in ("q1", "q2", "q3"))
    N["xhDiff"] = (
        x3["tables"]["q2"]["human_yes_detector_yes"] + x3["tables"]["q2"]["human_yes_detector_no"]
    )
    q4 = x3["q4"]
    N["xhUse"] = sum(q4["by_resolved"]["yes"].values())
    N["xhUseRes"] = q4["by_resolved"]["yes"].get("True", 0)
    N["xhUnclear"] = sum(q4["by_resolved"]["unclear"].values())
    N["xhNoUse"] = sum(q4["by_resolved"]["no"].values())
    N["xhUseRevert"] = q4["by_exact_revert"]["yes"].get("True", 0)
    N["xhResWithDiff"] = x3["paper_counts"]["resolved_with_q2"]["human"]
    for k, v in {"xhN": 104, "xhDiff": 96, "xhResWithDiff": 52}.items():
        if N[k] != v:
            print("MISMATCH s49", k, N[k], v)
            return 1
    if N["xhUse"] + N["xhUnclear"] + N["xhNoUse"] != N["xhDiff"]:
        print("MISMATCH s49: Q4 counts do not add up to the traces with Q2")
        return 1
    # section 45 (W7-b, notes 45-9, 45-10): a second learner, XRepoSkill
    w7 = load(Path("results/w7_analysis.json"))
    for p, key in (("A", "A"), ("B", "B")):
        N["wsN" + key], N["wsG" + key] = w7[p]["issues"], w7[p]["issues_G"]
        N["wsPairs" + key], N["wsJudged" + key] = w7[p]["pairs"], w7[p]["judged_rules"]
        N["wsJudgedG" + key] = len(w7[p]["judged_rules_G"])
        N["wsFlag" + key] = sum(r["ngram_flagged"] for r in w7[p]["judged_rules_G"])
    N["wsLiftLoA"] = min(r["gain"] for r in w7["A"]["judged_rules_G"])
    N["wsLiftHiA"] = max(r["gain"] for r in w7["A"]["judged_rules_G"])
    N["wsP"] = w7["p_one_sided_G"]
    wc = load(Path("results/w7_content_posthoc.json"))
    N["wsBugA"] = wc["A"]["issues_with"]["introduced_bug"]
    N["wsBugB"] = wc["B"]["issues_with"]["introduced_bug"]
    N["wsShowA"] = wc["A"]["issues_with"]["git_show"]
    N["wsShowB"] = wc["B"]["issues_with"]["git_show"]
    N["wsStatusA"] = wc["A"]["issues_with"]["git_status"]
    N["wsStatusB"] = wc["B"]["issues_with"]["git_status"]
    N["wsBugP"] = wc["p_one_sided_post_hoc"]["introduced_bug"]
    if w7["reject_G"] or (N["wsGA"], N["wsNA"], N["wsGB"], N["wsNB"]) != (30, 31, 11, 12):
        print("MISMATCH s45")
        return 1
    N["leakSharePct"] = round(100 * N["leakShare"])
    N["fzeroGoldMinPct"] = int(100 * f0["S_gold_min"])  # floor: "at least"
    for k in ("sskbOpp", "sskbRho"):
        N[k + "Pct"] = round(100 * N[k])
    bad = [k for k in N if not k.isascii() or not k.isalpha()]
    if bad:  # a LaTeX macro name may hold letters only (A131)
        print("BAD MACRO NAMES", bad)
        return 1
    for k, v in N.items():
        if isinstance(v, float) and v != 0 and abs(v) < 1e-3:
            m, e = f"{v:.1e}".split("e")
            s = rf"\ensuremath{{{m}\times10^{{{int(e)}}}}}"  # safe in text and in math
        elif isinstance(v, float) and v == 0:
            s = "0"  # an exact zero is printed as 0, not as 0.0000 (reads like a misprint)
        elif isinstance(v, float) and abs(v) < 0.01:
            s = f"{v:.4f}"
        elif isinstance(v, float):
            s = f"{v:.2f}"
        else:
            s = str(v)
        lines.append(rf"\newcommand{{\n{k}}}{{{s}}}")
    Path("paper/numbers.tex").write_text("\n".join(lines) + "\n")
    print(json.dumps(N, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
