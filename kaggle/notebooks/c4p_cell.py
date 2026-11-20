# C4' of section 40 (kaggle/preregistration_s40.md, section 6 with notes 40-5 and 40-6): gskill's
# agent with three models of other vendors, four arms (no skill / learned skill, environment as
# shipped / single commit), each task in its own chroot of the task image (gate C5). Free AI quota
# only. Run it only after the C6 cell has passed.
# Paste this whole file into ONE cell of a notebook created from
# https://www.kaggle.com/benchmarks/tasks/new, set POOL below, then Save Version -> Save & Run All
# (it runs for hours without the tab). Next day: Add Input -> the output of the previous version
# of this notebook, and run it again; finished chunks are never run again. Send c4p.json and
# c4p_results.zip from the Output panel after each session.
#
# The model key stays in this notebook's process; the agent's commands see none of the notebook's
# variables. This cell prints no key and no environment value.
import glob
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request

# ---- set before running (note 40-5) --------------------------------------------------------------
POOL = "B"  # T5, @thuthuy 17/11: "chọn B" (100 test tasks + the 36 tasks of section 35)

COMMIT = "505cab724aff00dc46e7510e654fa1e429c3ee4a"  # notes 40-6, 40-7, 40-13 to 40-15
TRIAL = "97cd0a5c9d69b45b95a978dc872ad91ac6f90e91"  # branch trial: the paper's agent-run script
GEPA = "8c7b697a71977980afc7537dac0881e784eef99f"  # gskill, as in every run of the paper
RAW = "https://raw.githubusercontent.com/dinhthithuthuyduphong-bot/gatekeeper/"
FILES = {
    "chroot_shim.py": f"{COMMIT}/kaggle/scripts/chroot_shim.py",
    "udocker_shim.py": f"{COMMIT}/kaggle/scripts/udocker_shim.py",
    "c5_gate.py": f"{COMMIT}/kaggle/scripts/c5_gate.py",
    "c3_agent.py": f"{COMMIT}/kaggle/scripts/c3_agent.py",
    "c4_driver.py": f"{COMMIT}/kaggle/scripts/c4_driver.py",
    "c4_monitor.py": f"{COMMIT}/kaggle/scripts/c4_monitor.py",
    "k0_stage0.py": f"{COMMIT}/kaggle/scripts/k0_stage0.py",
    "skill.txt": f"{COMMIT}/docs/skills/gskill/jinja_best_skills.txt",
    "f1_probe.py": f"{TRIAL}/scripts/f1_probe.py",
    "f0_scorer_check.py": f"{TRIAL}/scripts/f0_scorer_check.py",
    "rows.jsonl": "data-snapshots/data/instances/swesmith_pallets__jinja.jsonl",
    "rows_extra36.jsonl": "data-snapshots/data/instances/swesmith_pallets__jinja_extra36.jsonl",
}
# ---- registered in preregistration_s40.md section 6 ----------------------------------------------
MODELS = [  # (tag, Kaggle model key, USD per token in, out: note 40-1), run in this order
    ("haiku", "anthropic/claude-haiku-5-5", 1e-7, 5e-7),
    ("nano", "openai/gpt-5.4-nano-2026-03-17", 2e-7, 1.25e-6),
    # gpt-oss restarted under a new tag with its format tags stripped (note 40-15); the files of
    # tag "oss" (one chunk before the fix) are kept aside and not used
    ("ossh", "openai/gpt-oss-120b", 9e-8, 3.6e-7),
]
CHUNK, SEED, COST_LIMIT = 10, 41, 0.30  # seed and per-task limit as in section 25
DAY_CAP = 2.0  # USD of quota per session, all models together (leaves room for section 38)
MODEL_CAP = 12.0  # USD of quota per model, all sessions
SPENT_BEFORE_RESTART = {"ossh": 0.3769}  # tag "oss" before note 40-15 counts toward the cap
HOURS = 8.0  # no new chunk after this many hours of one session
EXPECT_PREVIOUS = True  # K29: from session 2 on, the last output must be attached
DONE_MODELS = ("haiku", "nano")  # finished (notes 40-11, 40-15); checked in the input
# --------------------------------------------------------------------------------------------------
W, OUTDIR = "/kaggle/working/c4p", "/kaggle/working/c4pout"
out = {"started": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "models": {}}
T0 = time.time()


def sh(cmd: str, timeout: int = 40000) -> tuple[int, str]:
    r = subprocess.run(["bash", "-c", cmd], capture_output=True, text=True, timeout=timeout)
    return r.returncode, (r.stdout + r.stderr)[-2500:]


def save():
    with open("/kaggle/working/c4p.json", "w") as fh:
        json.dump(out, fh, indent=1, default=str)


def spent_now() -> float:
    return sum(
        json.load(open(f)).get("endpoint_usd", 0.0) for f in glob.glob(OUTDIR + "/*.cost.json")
    )


PREFLIGHT = r"""
import json, os, sys, traceback
names = ("MODEL_PROXY_URL", "MODEL_PROXY_API_KEY")
res = {"env_present": {k: bool(os.environ.get(k)) for k in names}}
try:
    import litellm
    base = os.environ["MODEL_PROXY_URL"].rstrip("/")
    for s in ("/openapi", "/genai"):
        base = base.removesuffix(s)
    tries = (("full", {"seed": 41, "parallel_tool_calls": True}), ("no_parallel", {"seed": 41}))
    for name, kw in tries:
        try:
            r = litellm.completion(model="openai/" + sys.argv[1], api_base=base + "/openapi",
                api_key=os.environ["MODEL_PROXY_API_KEY"], drop_params=True,
                messages=[{"role": "user", "content": "Reply with the single word OK."}], **kw)
            u = r.usage
            res[name] = {"ok": True, "reply": r.choices[0].message.content[:40],
                "tokens": [u.prompt_tokens, u.completion_tokens],
                "cost_field": str(getattr(u, "cost", None))[:200]}
            break
        except Exception as e:
            res[name] = {"ok": False, "error": type(e).__name__ + ": " + str(e)[:300]}
except BaseException as e:
    res["setup_error"] = type(e).__name__ + ": " + traceback.format_exc()[-600:]
print("PREFLIGHT " + json.dumps(res))
"""

try:
    if POOL not in ("A", "B"):
        raise RuntimeError('set POOL = "A" or POOL = "B" at the top of the cell (note 40-5)')
    out["pool"] = POOL
    # K29: a session without the previous session's output re-runs finished models from
    # scratch. Stop before any model call unless the earlier output is attached exactly once.
    done_before = sorted(glob.glob("/kaggle/input/**/haiku_summary.json", recursive=True))
    out["previous_output"] = done_before
    if EXPECT_PREVIOUS and len(done_before) != 1:
        raise RuntimeError(
            f"expected the previous session's output attached once, found {len(done_before)}: "
            "Add Input -> the output of the LAST version of this notebook, and only that one"
        )
    for tag in DONE_MODELS:  # models already finished must come back finished
        f = glob.glob(f"/kaggle/input/**/{tag}_summary.json", recursive=True)
        st = json.load(open(f[0])).get("status") if len(f) == 1 else None
        if st != "all done":
            raise RuntimeError(
                f"the attached output does not hold the finished {tag} run (status {st!r}): "
                "attach the output of the session that ran after it"
            )
    try:
        import kaggle_benchmarks  # noqa: F401

        out["kaggle_benchmarks"] = "imported"
    except Exception as e:
        out["kaggle_benchmarks"] = repr(e)[:200]
    names = ("MODEL_PROXY_URL", "MODEL_PROXY_API_KEY")
    out["env_present"] = {k: bool(os.environ.get(k)) for k in names}  # presence only, no value
    out["machine"] = {
        "uid": os.getuid(),
        "root_writable": os.access("/", os.W_OK),
        "git": shutil.which("git"),
        "patch": shutil.which("patch"),
        "uv": shutil.which("uv"),
        "python": sys.version.split()[0],
        "cpus": os.cpu_count(),
    }
    save()
    if not all(out["env_present"].values()):
        raise RuntimeError(
            "this is not a Benchmarks notebook (no model endpoint): create the notebook from "
            "https://www.kaggle.com/benchmarks/tasks/new and paste this cell there"
        )
    os.makedirs(W + "/code", exist_ok=True)
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
    # Gate C5 on THIS machine, before any model call (note 40-4): six isolation tests, then
    # gold 5/5 and no patch 0/5 through the chroot.
    os.makedirs(W + "/run", exist_ok=True)
    sh(
        f"cd {W}/run && PYTHONPATH={W}/code {hv}/bin/python {W}/code/c5_gate.py "
        f"--rows {W}/code/rows.jsonl --out {W}/c5_gate.json --extra /kaggle/working "
        f"> {OUTDIR}/c5_on_this_machine.log 2>&1"
    )
    gate = json.load(open(W + "/c5_gate.json")) if os.path.exists(W + "/c5_gate.json") else {}
    out["c5_here"] = {"passed": gate.get("passed")}
    with open(W + "/none.json", "w") as fh:
        json.dump({"runs": []}, fh)
    ctl = W + "/c5_gradings.jsonl"
    if os.path.exists(ctl):
        os.remove(ctl)
    if gate.get("passed"):
        sh(
            f"cd {W}/run && PYTHONPATH={W}/code {hv}/bin/python {W}/code/k0_stage0.py "
            f"--rows {W}/code/rows.jsonl --results {W}/none.json --controls 5 --out {ctl} "
            f"--chroot >> {OUTDIR}/c5_on_this_machine.log 2>&1"
        )
    rows = [json.loads(x) for x in open(ctl) if x.strip()] if os.path.exists(ctl) else []
    gold = [r for r in rows if r["kind"] == "gold" and r["status"] == "completed"]
    noop = [r for r in rows if r["kind"] == "noop" and r["status"] == "completed"]
    out["c5_here"]["gold"] = f"{sum(bool(r['resolved']) for r in gold)}/{len(gold)}"
    out["c5_here"]["noop"] = f"{sum(bool(r['resolved']) for r in noop)}/{len(noop)}"
    save()
    if out["c5_here"] != {"passed": True, "gold": "5/5", "noop": "0/5"}:
        raise RuntimeError("gate C5 failed on this machine; no agent run started")
    with open(W + "/preflight.py", "w") as fh:
        fh.write(PREFLIGHT)
    yaml = f"{W}/gepa/src/gepa/gskill/gskill/mini_swe_agent_config/mini.yaml"
    extra = f"--extra-rows {W}/code/rows_extra36.jsonl" if POOL == "B" else ""
    # spend of THIS session: the sum of each driver's own "spent_this_session". Not
    # spent_now() - spent_now() at start: each driver first copies the earlier sessions' cost
    # files into OUTDIR, which made the second session count the first one's spend (K27)
    session_spent = 0.0
    for tag, model, pin, pout in MODELS:
        m = out["models"].setdefault(tag, {"model": model})
        left_day = DAY_CAP - session_spent
        left_hours = HOURS - (time.time() - T0) / 3600
        if left_day <= 0 or left_hours <= 0:
            m["status"] = "not started: day cap or time limit of this session"
            continue
        rc, tail = sh(f"{hv}/bin/python {W}/preflight.py {model} 2>&1")
        if "PREFLIGHT " in tail:
            pre = json.loads(tail.split("PREFLIGHT ", 1)[1].splitlines()[0])
        else:
            pre = {"no_output": tail[-600:]}
        m["preflight"] = pre
        save()
        if not any(isinstance(v, dict) and v.get("ok") for v in pre.values()):
            m["status"] = "model call failed; skipped"
            continue
        drop = "" if (pre.get("full") or {}).get("ok") else "parallel_tool_calls"
        m["dropped_kwargs"] = drop
        spec = {
            "input_cost_per_token": pin,
            "output_cost_per_token": pout,
            "litellm_provider": "openai",
            "mode": "chat",
        }
        with open(f"{W}/registry_{tag}.json", "w") as fh:
            json.dump({n: spec for n in ("openai/" + model, model, model.split("/", 1)[1])}, fh)
        model_cap = MODEL_CAP - SPENT_BEFORE_RESTART.get(tag, 0.0)
        rc, tail = sh(
            f"MSWEA_SILENT_STARTUP=1 MSWEA_CONFIGURED=true "
            f"PYTHONPATH={W}/gepa/src/gepa/gskill:{W}/code {hv}/bin/python {W}/code/c4_driver.py "
            f"--tag {tag} --model openai/{model} --rows {W}/code/rows.jsonl "
            f"--skills-file {W}/code/skill.txt --registry {W}/registry_{tag}.json "
            f"--isolation chroot {extra} --gskill-yaml {yaml} --outdir {OUTDIR} "
            f"--prev /kaggle/input --chunk {CHUNK} --seed {SEED} --cost-limit {COST_LIMIT} "
            f"--day-cap {left_day} --total-cap {model_cap} --hours {left_hours} "
            f"--drop-kwargs {drop} {'--strip-format-tags' if tag == 'ossh' else ''} "
            f"2>&1 | tail -n 60"
        )
        m["driver_tail"] = tail
        sh(
            f"{hv}/bin/python {W}/code/c4_monitor.py {OUTDIR} --include-bad "
            f"--out {OUTDIR}/monitor.json"
        )
        if os.path.exists(OUTDIR + "/monitor.json"):
            mon = json.load(open(OUTDIR + "/monitor.json"))
            m["monitor_total_all_models"] = mon["total"]
        if os.path.exists(f"{OUTDIR}/{tag}_summary.json"):
            m["summary"] = json.load(open(f"{OUTDIR}/{tag}_summary.json"))
        if "spent_this_session" in (m.get("summary") or {}):
            session_spent += float(m["summary"]["spent_this_session"])
        else:  # no summary: assume the whole day cap was spent (stops this session)
            session_spent = DAY_CAP
        save()
        if (m.get("summary") or {}).get("status") != "all done":
            break  # finish one model before starting the next
except Exception as e:
    out["error"] = repr(e)[:1500]
if os.path.isdir(OUTDIR + "/work"):
    shutil.rmtree(OUTDIR + "/work", ignore_errors=True)
if os.path.isdir(OUTDIR):
    shutil.make_archive("/kaggle/working/c4p_results", "zip", OUTDIR)
out["finished"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
save()
print(json.dumps(out, indent=1, default=str)[:8000])
