# Gate C5 + check C6 of section 40 (kaggle/preregistration_s40.md, notes 40-4 and 40-6;
# plan_v4.md section 7). Paste this whole file into ONE cell of a notebook created from
# https://www.kaggle.com/benchmarks/tasks/new.
#   1. First run: leave DRY_RUN = True. No model call, 0 USD of quota (about 20 minutes: it
#      downloads the 1.4 GB task image). Send c6.json and c6_results.zip from the Output panel.
#   2. Second run, only after Claude has read the first: set DRY_RUN = False. Haiku, 6 tasks,
#      single-commit arm, at most 0.50 USD of quota. Send the same two files.
# The model key stays in this notebook's process; the agent's commands see none of the notebook's
# variables. This cell prints no key and no environment value.
import json
import os
import shlex
import shutil
import subprocess
import sys
import time
import urllib.request

DRY_RUN = True  # set to False for the second run only

COMMIT = "063c796d172d784e53a1ca58d023e4acdefd5ecc"  # kaggle/scripts of section 40, note 40-6
TRIAL = "97cd0a5c9d69b45b95a978dc872ad91ac6f90e91"  # branch trial: the paper's agent-run script
GEPA = "8c7b697a71977980afc7537dac0881e784eef99f"  # gskill, as in every run of the paper
RAW = "https://raw.githubusercontent.com/dinhthithuthuyduphong-bot/gatekeeper/"
FILES = {
    "chroot_shim.py": f"{COMMIT}/kaggle/scripts/chroot_shim.py",
    "udocker_shim.py": f"{COMMIT}/kaggle/scripts/udocker_shim.py",
    "c5_gate.py": f"{COMMIT}/kaggle/scripts/c5_gate.py",
    "k0_stage0.py": f"{COMMIT}/kaggle/scripts/k0_stage0.py",
    "c3_agent.py": f"{COMMIT}/kaggle/scripts/c3_agent.py",
    "c4_driver.py": f"{COMMIT}/kaggle/scripts/c4_driver.py",
    "c4_monitor.py": f"{COMMIT}/kaggle/scripts/c4_monitor.py",
    "f1_probe.py": f"{TRIAL}/scripts/f1_probe.py",
    "f0_scorer_check.py": f"{TRIAL}/scripts/f0_scorer_check.py",
    "skill.txt": f"{COMMIT}/docs/skills/gskill/jinja_best_skills.txt",
    "rows.jsonl": "data-snapshots/data/instances/swesmith_pallets__jinja.jsonl",
}
# ---- registered (note 40-6) ----------------------------------------------------------------------
MODEL, PIN, POUT = "anthropic/claude-haiku-5-5", 1e-7, 5e-7  # note 40-1 prices
N_EMPTY, N_DESC = 3, 3  # first tasks of the test split, gskill order, without / with a description
SEED, COST_LIMIT, CAP = 41, 0.30, 0.50  # USD of quota; f1_probe stops before passing CAP
# dry run: the scripted reply repeats every step (it never submits), so each run reaches the step
# limit; it tries the outside paths of note 40-3, and the monitor must see 0 exposure
MOCK = (
    "THOUGHT: dry run.\n\n```bash\nfind / -name compiler.py | head; ls /kaggle /var/lib/cshim\n```"
)
# --------------------------------------------------------------------------------------------------
W, OUTDIR = "/kaggle/working/c6", "/kaggle/working/c6out"
out = {"started": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "dry_run": DRY_RUN}


def sh(cmd: str, timeout: int = 20000) -> tuple[int, str]:
    r = subprocess.run(["bash", "-c", cmd], capture_output=True, text=True, timeout=timeout)
    return r.returncode, (r.stdout + r.stderr)[-2500:]


def save():
    with open("/kaggle/working/c6.json", "w") as fh:
        json.dump(out, fh, indent=1, default=str)


try:
    names = ("MODEL_PROXY_URL", "MODEL_PROXY_API_KEY")
    out["env_present"] = {k: bool(os.environ.get(k)) for k in names}  # presence only, no value
    out["machine"] = {"uid": os.getuid(), "python": sys.version.split()[0], "cpus": os.cpu_count()}
    save()
    if not DRY_RUN and not all(out["env_present"].values()):
        raise RuntimeError("not a Benchmarks notebook: create it from benchmarks/tasks/new")
    os.makedirs(W + "/code", exist_ok=True)
    os.makedirs(W + "/run", exist_ok=True)
    os.makedirs(OUTDIR, exist_ok=True)
    for name, path in FILES.items():
        data = urllib.request.urlopen(RAW + path, timeout=120).read()
        with open(f"{W}/code/{name}", "wb") as fh:
            fh.write(data)
    os.chmod(f"{W}/code/chroot_shim.py", 0o755)  # mini-swe-agent's `docker` command
    if not shutil.which("uv"):
        sh(f"{sys.executable} -m pip install -q uv")
    uv = shutil.which("uv") or f"{sys.executable} -m uv"
    hv = W + "/agent_env"
    if not os.path.exists(hv + "/bin/python"):
        out["agent_env"] = sh(
            f"{uv} venv -q --python 3.12 {hv} && {uv} pip install -q --python {hv}/bin/python "
            "swesmith==0.0.9 swebench==4.1.0 mini-swe-agent==1.17.5 litellm==1.108.2 "
            "docker pyyaml unidiff python-dotenv datasets"
        )
    if not os.path.exists(W + "/gepa/.git"):
        out["gepa"] = sh(
            f"git clone -q https://github.com/gepa-ai/gepa {W}/gepa && "
            f"git -C {W}/gepa checkout -q {GEPA} && "
            f"{uv} pip install -q --python {hv}/bin/python -e {W}/gepa"
        )
    save()
    # Gate C5 on THIS machine (note 40-4): six isolation tests, then gold 5/5 and no patch 0/5.
    rc, tail = sh(
        f"cd {W}/run && PYTHONPATH={W}/code {hv}/bin/python {W}/code/c5_gate.py "
        f"--rows {W}/code/rows.jsonl --out {W}/c5_gate.json --extra /kaggle/working "
        f"> {OUTDIR}/c5.log 2>&1; echo rc=$?"
    )
    out["c5_gate"] = (
        json.load(open(W + "/c5_gate.json")) if os.path.exists(W + "/c5_gate.json") else tail
    )
    save()
    if not (isinstance(out["c5_gate"], dict) and out["c5_gate"].get("passed")):
        raise RuntimeError("gate C5 (isolation) failed on this machine; no agent run")
    with open(W + "/none.json", "w") as fh:
        json.dump({"runs": []}, fh)
    ctl = W + "/c5_gradings.jsonl"
    if os.path.exists(ctl):
        os.remove(ctl)
    sh(
        f"cd {W}/run && PYTHONPATH={W}/code {hv}/bin/python {W}/code/k0_stage0.py "
        f"--rows {W}/code/rows.jsonl --results {W}/none.json --controls 5 --out {ctl} "
        f"--chroot >> {OUTDIR}/c5.log 2>&1"
    )
    rows = [json.loads(x) for x in open(ctl) if x.strip()] if os.path.exists(ctl) else []
    gold = [r for r in rows if r["kind"] == "gold" and r["status"] == "completed"]
    noop = [r for r in rows if r["kind"] == "noop" and r["status"] == "completed"]
    out["controls"] = {
        "gold": f"{sum(bool(r['resolved']) for r in gold)}/{len(gold)}",
        "noop": f"{sum(bool(r['resolved']) for r in noop)}/{len(noop)}",
    }
    save()
    if out["controls"] != {"gold": "5/5", "noop": "0/5"}:
        raise RuntimeError("controls failed on this machine; no agent run")
    # C6 tasks: the registered rule (note 40-6)
    allr = [json.loads(x) for x in open(f"{W}/code/rows.jsonl") if x.strip()]
    test = sorted(
        (r for r in allr if r["_gskill_split"] == "test"), key=lambda r: r["_gskill_order"]
    )
    empty = [r for r in test if not (r.get("problem_statement") or "").strip()][:N_EMPTY]
    desc = [r for r in test if (r.get("problem_statement") or "").strip()][:N_DESC]
    pick = sorted(empty + desc, key=lambda r: r["_gskill_order"])
    with open(W + "/rows_c6.jsonl", "w") as fh:
        fh.write("".join(json.dumps(r) + "\n" for r in pick))
    out["tasks"] = [
        [r["instance_id"], bool((r.get("problem_statement") or "").strip())] for r in pick
    ]
    spec = {
        "input_cost_per_token": PIN,
        "output_cost_per_token": POUT,
        "litellm_provider": "openai",
        "mode": "chat",
    }
    with open(W + "/registry.json", "w") as fh:
        json.dump({n: spec for n in ("openai/" + MODEL, MODEL, MODEL.split("/", 1)[1])}, fh)
    yaml = f"{W}/gepa/src/gepa/gskill/gskill/mini_swe_agent_config/mini.yaml"
    mock = f"--mock-response {shlex.quote(MOCK)}" if DRY_RUN else ""  # single-quoted for bash
    rc, tail = sh(
        f"MSWEA_SILENT_STARTUP=1 MSWEA_CONFIGURED=true "
        f"PYTHONPATH={W}/gepa/src/gepa/gskill:{W}/code {hv}/bin/python {W}/code/c4_driver.py "
        f"--tag haiku --model openai/{MODEL} --rows {W}/rows_c6.jsonl --isolation chroot "
        f"--arms lf_none --chunk {len(pick)} --chunk-cap {CAP} "
        f"--skills-file {W}/code/skill.txt --registry {W}/registry.json --gskill-yaml {yaml} "
        f"--outdir {OUTDIR} --seed {SEED} --cost-limit {COST_LIMIT} --day-cap {CAP} "
        f"--total-cap {CAP} --hours 3 {mock} 2>&1 | tail -n 40"
    )
    out["driver_tail"] = tail
    if os.path.exists(OUTDIR + "/haiku_summary.json"):
        out["summary"] = json.load(open(OUTDIR + "/haiku_summary.json"))
    sh(f"{hv}/bin/python {W}/code/c4_monitor.py {OUTDIR} --include-bad --out {OUTDIR}/monitor.json")
    if os.path.exists(OUTDIR + "/monitor.json"):
        mon = json.load(open(OUTDIR + "/monitor.json"))
        out["monitor"] = {"total": mon["total"], "per_arm": mon["per_arm"]}
    res = OUTDIR + "/haiku_lf_none_c00.json"
    runs = json.load(open(res))["runs"] if os.path.exists(res) else []
    out["runs"] = [
        {k: r.get(k) for k in ("instance_id", "crashed", "infra_error", "steps", "leak_free_check")}
        for r in runs
    ]
    # pass rule of C6 (plan_v4.md section 7, note 40-6)
    out["c6_passed"] = (
        len(runs) == len(pick)
        and not any(r.get("infra_error") or r.get("crashed") for r in runs)
        and (out.get("monitor") or {}).get("total", {}).get("exposure") == 0
    )
except Exception as e:
    out["error"] = repr(e)[:1500]
if os.path.isdir(OUTDIR + "/work"):
    shutil.rmtree(OUTDIR + "/work", ignore_errors=True)
if os.path.isdir(OUTDIR):
    for f in os.listdir(OUTDIR):
        if f.endswith(".mini.yaml"):  # holds the endpoint URL
            os.remove(os.path.join(OUTDIR, f))
    shutil.make_archive("/kaggle/working/c6_results", "zip", OUTDIR)
out["finished"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
save()
print(json.dumps(out, indent=1, default=str)[:9000])
