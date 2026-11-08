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
    rs = load(t / "rescore_jinja_summary.json")
    N["rsPatches"] = sum(v["patches"] for v in rs.values())
    N["rsScorings"] = sum(v["repeats_scored"] for v in rs.values())
    N["rsFlips"] = sum(v["tasks_with_any_flip"] for v in rs.values())
    for k, v in {
        "shamLiteK": 25,
        "shamFlashK": 3,
        "shamProK": 5,
        "learnBudget": 600,
        "rsScorings": 448,
        "rsFlips": 0,
    }.items():
        if N[k] != v:
            print("MISMATCH", k, N[k], v)
            return 1
    N["leakSharePct"] = round(100 * N["leakShare"])
    N["fzeroGoldMinPct"] = int(100 * f0["S_gold_min"])  # floor: "at least"
    for k in ("sskbOpp", "sskbRho"):
        N[k + "Pct"] = round(100 * N[k])
    for k, v in N.items():
        if isinstance(v, float) and v != 0 and abs(v) < 1e-3:
            m, e = f"{v:.1e}".split("e")
            s = rf"\ensuremath{{{m}\times10^{{{int(e)}}}}}"  # safe in text and in math
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
