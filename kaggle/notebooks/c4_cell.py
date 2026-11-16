# C4 of section 40 (kaggle/preregistration_s40.md, section 6): gskill's agent with a model of
# another vendor on the 100 Jinja test tasks, four arms (no skill / learned skill, environment as
# shipped / single commit), no container. Free AI quota only.
# Paste this whole file into ONE cell of a notebook created from
# https://www.kaggle.com/benchmarks/tasks/new, then Save Version -> Save & Run All (it runs for
# hours without the tab). Next day: Add Input -> the output of the previous version of this
# notebook, and run it again; finished chunks are never run again. Send c4.json and
# c4_results.zip from the Output panel after each session.
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

COMMIT = "d37a69dfea7f7e102f33169d78264a8a90de3c5a"  # holds kaggle/scripts of section 40
TRIAL = "97cd0a5c9d69b45b95a978dc872ad91ac6f90e91"  # branch trial: the paper's agent-run script
GEPA = "8c7b697a71977980afc7537dac0881e784eef99f"  # gskill, as in every run of the paper
RAW = "https://raw.githubusercontent.com/dinhthithuthuyduphong-bot/gatekeeper/"
FILES = {
    "local_shim.py": f"{COMMIT}/kaggle/scripts/local_shim.py",
    "fake_docker.py": f"{COMMIT}/kaggle/scripts/fake_docker.py",
    "c3_agent.py": f"{COMMIT}/kaggle/scripts/c3_agent.py",
    "c4_driver.py": f"{COMMIT}/kaggle/scripts/c4_driver.py",
    "k0_stage0.py": f"{COMMIT}/kaggle/scripts/k0_stage0.py",
    "packages.json": f"{COMMIT}/kaggle/data/jinja_image_packages.json",
    "skill.txt": f"{COMMIT}/docs/skills/gskill/jinja_best_skills.txt",
    "f1_probe.py": f"{TRIAL}/scripts/f1_probe.py",
    "f0_scorer_check.py": f"{TRIAL}/scripts/f0_scorer_check.py",
    "rows.jsonl": "data-snapshots/data/instances/swesmith_pallets__jinja.jsonl",
}
# ---- registered in preregistration_s40.md section 6 ----------------------------------------------
MODELS = [  # (tag, Kaggle model key, USD per token in, out: note 40-1), run in this order
    ("haiku", "anthropic/claude-haiku-5-5", 1e-7, 5e-7),
    ("nano", "openai/gpt-5.4-nano-2026-03-17", 2e-7, 1.25e-6),
    ("oss", "openai/gpt-oss-120b", 9e-8, 3.6e-7),
]
CHUNK, SEED, COST_LIMIT = 10, 41, 0.30  # seed and per-task limit as in section 25
DAY_CAP = 2.0  # USD of quota per session, all models together (leaves room for section 38)
MODEL_CAP = 12.0  # USD of quota per model, all sessions
HOURS = 8.0  # no new chunk after this many hours of one session
# --------------------------------------------------------------------------------------------------
W, OUTDIR = "/kaggle/working/c4", "/kaggle/working/c4out"
out = {"started": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "models": {}}
T0 = time.time()


def sh(cmd: str, timeout: int = 40000) -> tuple[int, str]:
    r = subprocess.run(["bash", "-c", cmd], capture_output=True, text=True, timeout=timeout)
    return r.returncode, (r.stdout + r.stderr)[-2500:]


def save():
    with open("/kaggle/working/c4.json", "w") as fh:
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
    os.chmod(f"{W}/code/fake_docker.py", 0o755)
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
    # Gate C2 on THIS machine, before any model call: gold patch 5/5, no patch 0/5.
    with open(W + "/none.json", "w") as fh:
        json.dump({"runs": []}, fh)
    os.makedirs(W + "/ctl", exist_ok=True)
    ctl = W + "/c2_gradings.jsonl"
    if os.path.exists(ctl):
        os.remove(ctl)
    sh(
        f"cd {W}/ctl && PYTHONPATH={W}/code {hv}/bin/python {W}/code/k0_stage0.py "
        f"--rows {W}/code/rows.jsonl --results {W}/none.json --controls 5 --out {ctl} "
        f"--local-packages {W}/code/packages.json > {OUTDIR}/c2_on_this_machine.log 2>&1"
    )
    rows = [json.loads(x) for x in open(ctl) if x.strip()] if os.path.exists(ctl) else []
    gold = [r for r in rows if r["kind"] == "gold" and r["status"] == "completed"]
    noop = [r for r in rows if r["kind"] == "noop" and r["status"] == "completed"]
    out["c2_here"] = {
        "gold": f"{sum(bool(r['resolved']) for r in gold)}/{len(gold)}",
        "noop": f"{sum(bool(r['resolved']) for r in noop)}/{len(noop)}",
    }
    save()
    if out["c2_here"] != {"gold": "5/5", "noop": "0/5"}:
        raise RuntimeError("gate C2 failed on this machine; no agent run started")
    with open(W + "/preflight.py", "w") as fh:
        fh.write(PREFLIGHT)
    yaml = f"{W}/gepa/src/gepa/gskill/gskill/mini_swe_agent_config/mini.yaml"
    start_spent = spent_now()
    for tag, model, pin, pout in MODELS:
        m = out["models"].setdefault(tag, {"model": model})
        left_day = DAY_CAP - (spent_now() - start_spent)
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
        rc, tail = sh(
            f"MSWEA_SILENT_STARTUP=1 MSWEA_CONFIGURED=true "
            f"PYTHONPATH={W}/gepa/src/gepa/gskill:{W}/code {hv}/bin/python {W}/code/c4_driver.py "
            f"--tag {tag} --model openai/{model} --rows {W}/code/rows.jsonl "
            f"--skills-file {W}/code/skill.txt --registry {W}/registry_{tag}.json "
            f"--packages {W}/code/packages.json --gskill-yaml {yaml} --outdir {OUTDIR} "
            f"--prev /kaggle/input --chunk {CHUNK} --seed {SEED} --cost-limit {COST_LIMIT} "
            f"--day-cap {left_day} --total-cap {MODEL_CAP} --hours {left_hours} "
            f"--drop-kwargs {drop} 2>&1 | tail -n 60"
        )
        m["driver_tail"] = tail
        if os.path.exists(f"{OUTDIR}/{tag}_summary.json"):
            m["summary"] = json.load(open(f"{OUTDIR}/{tag}_summary.json"))
        save()
        if (m.get("summary") or {}).get("status") != "all done":
            break  # finish one model before starting the next
except Exception as e:
    out["error"] = repr(e)[:1500]
if os.path.isdir(OUTDIR + "/work"):
    shutil.rmtree(OUTDIR + "/work", ignore_errors=True)
if os.path.isdir(OUTDIR):
    shutil.make_archive("/kaggle/working/c4_results", "zip", OUTDIR)
out["finished"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
save()
print(json.dumps(out, indent=1, default=str)[:8000])
