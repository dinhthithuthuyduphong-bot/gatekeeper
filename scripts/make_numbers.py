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
