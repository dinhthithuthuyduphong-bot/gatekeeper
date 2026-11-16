# Gate C3 of section 40 (kaggle/preregistration_s40.md): gskill's agent on 3 Jinja test tasks,
# no skill, no container, a model of another vendor. Cap: 1.00 USD of the free quota.
# Paste this whole file into ONE cell of a notebook created from
# https://www.kaggle.com/benchmarks/tasks/new. Write down "Daily AI Models" before and after.
# Then send /kaggle/working/c3.json, c3.log and the folder /kaggle/working/c3out (Output panel).
#
# The model key stays in this notebook: it is handed to the agent's model client inside the
# process and is never printed or written; the commands the agent runs see none of the notebook's
# variables. This cell prints no key and no environment value.
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request

COMMIT = "c0b2e64ff6835a52ca794b03a5c74dd31791a56f"  # holds kaggle/scripts of section 40
TRIAL = "97cd0a5c9d69b45b95a978dc872ad91ac6f90e91"  # branch trial: the paper's agent-run script
GEPA = "8c7b697a71977980afc7537dac0881e784eef99f"  # gskill, as in every run of the paper
RAW = "https://raw.githubusercontent.com/dinhthithuthuyduphong-bot/gatekeeper/"
FILES = {
    "local_shim.py": f"{COMMIT}/kaggle/scripts/local_shim.py",
    "fake_docker.py": f"{COMMIT}/kaggle/scripts/fake_docker.py",
    "c3_agent.py": f"{COMMIT}/kaggle/scripts/c3_agent.py",
    "packages.json": f"{COMMIT}/kaggle/data/jinja_image_packages.json",
    "f1_probe.py": f"{TRIAL}/scripts/f1_probe.py",
    "f0_scorer_check.py": f"{TRIAL}/scripts/f0_scorer_check.py",
    "rows.jsonl": "data-snapshots/data/instances/swesmith_pallets__jinja.jsonl",
}
MODEL = "anthropic/claude-haiku-5-5"  # Kaggle's key; registered choice of C3
PRICE = {"input_cost_per_token": 1e-7, "output_cost_per_token": 5e-7}  # note 40-1 (measured)
TASKS, SEED, COST_LIMIT, CAP = 3, 41, 0.30, 1.00  # seed and per-task limit as in section 25
W, OUTDIR = "/kaggle/working/c3", "/kaggle/working/c3out"
out = {"started": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "model": MODEL}


def sh(cmd: str, timeout: int = 3000) -> tuple[int, str]:
    r = subprocess.run(["bash", "-c", cmd], capture_output=True, text=True, timeout=timeout)
    return r.returncode, (r.stdout + r.stderr)[-2500:]


def save():
    with open("/kaggle/working/c3.json", "w") as fh:
        json.dump(out, fh, indent=1, default=str)


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
    try:  # the library puts the endpoint and the key into this process's environment
        import kaggle_benchmarks  # noqa: F401

        out["kaggle_benchmarks"] = "imported"
    except Exception as e:
        out["kaggle_benchmarks"] = repr(e)[:200]
    names = ("MODEL_PROXY_URL", "MODEL_PROXY_API_KEY")
    out["env_present"] = {k: bool(os.environ.get(k)) for k in names}  # presence only, no value
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
    rows = [json.loads(x) for x in open(f"{W}/code/rows.jsonl") if x.strip()]
    test = sorted(
        (r for r in rows if r["_gskill_split"] == "test"), key=lambda r: r["_gskill_order"]
    )[:TASKS]
    with open(W + "/rows_c3.jsonl", "w") as fh:
        fh.writelines(json.dumps(r) + "\n" for r in test)
    out["tasks"] = [r["instance_id"] for r in test]
    with open(W + "/registry.json", "w") as fh:
        spec = {**PRICE, "litellm_provider": "openai", "mode": "chat"}
        names = ("openai/" + MODEL, MODEL, MODEL.split("/", 1)[1])  # as LiteLLM may look it up
        json.dump({n: spec for n in names}, fh)
    with open(W + "/preflight.py", "w") as fh:
        fh.write(PREFLIGHT)
    rc, tail = sh(f"{hv}/bin/python {W}/preflight.py {MODEL} 2>&1")
    if "PREFLIGHT " in tail:
        pre = json.loads(tail.split("PREFLIGHT ", 1)[1].splitlines()[0])
    else:
        pre = {"no_output": tail[-600:]}
    out["preflight"] = pre
    save()
    if not any(isinstance(v, dict) and v.get("ok") for v in pre.values()):
        raise RuntimeError("the model call does not work through LiteLLM; agent not started")
    drop = "" if (pre.get("full") or {}).get("ok") else "--drop-kwargs parallel_tool_calls"
    out["dropped_kwargs"] = drop
    os.makedirs(W + "/run", exist_ok=True)
    t0 = time.time()
    yaml = f"{W}/gepa/src/gepa/gskill/gskill/mini_swe_agent_config/mini.yaml"
    rc, tail = sh(
        f"cd {W}/run && MSWEA_SILENT_STARTUP=1 MSWEA_CONFIGURED=true "
        f"PYTHONPATH={W}/gepa/src/gepa/gskill:{W}/code {hv}/bin/python {W}/code/c3_agent.py "
        f"--packages {W}/code/packages.json --base-env MODEL_PROXY_URL "
        f"--key-env MODEL_PROXY_API_KEY --base-suffix /openapi {drop} -- "
        f"--rows {W}/rows_c3.jsonl --split test --model openai/{MODEL} --seed {SEED} "
        f"--cost-limit {COST_LIMIT} --cap {CAP} --registry {W}/registry.json "
        f"--gskill-yaml {yaml} --out {OUTDIR}/c3_none.json "
        "> /kaggle/working/c3.log 2>&1; echo rc=$?; grep -E '^\\[[0-9]+\\]' /kaggle/working/c3.log"
    )
    out["agent_seconds"] = round(time.time() - t0, 1)
    out["agent_tail"] = tail
    if os.path.exists(f"{OUTDIR}/c3_none.mini.yaml"):
        os.remove(f"{OUTDIR}/c3_none.mini.yaml")  # holds the endpoint URL; not a result
    if os.path.exists(f"{OUTDIR}/c3_none.json"):
        res = json.load(open(f"{OUTDIR}/c3_none.json"))
        keep = ("instance_id", "steps", "crashed", "patch_chars", "L", "S", "cost_usd")
        out["runs"] = [{k: r.get(k) for k in (*keep, "infra_error")} for r in res["runs"]]
        out["stopped"] = res.get("stopped")
    if os.path.exists(f"{OUTDIR}/c3_none.cost.json"):
        out["cost"] = json.load(open(f"{OUTDIR}/c3_none.cost.json"))
except Exception as e:
    out["error"] = repr(e)[:1500]
out["finished"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
save()
print(json.dumps(out, indent=1, default=str)[:6000])
