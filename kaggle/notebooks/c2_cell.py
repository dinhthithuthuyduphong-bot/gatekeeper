# Gate C2 of plan v3 (kaggle/preregistration_s40.md): does SWE-smith's grading run on Kaggle with
# no container, and does it grade a known answer correctly? NO model call, 0 USD of quota.
# Paste this whole file into ONE cell of a notebook created from
# https://www.kaggle.com/benchmarks/tasks/new and run it (a few minutes). Then send
# /kaggle/working/c2.json and /kaggle/working/c2.log (Output panel).
#
# It builds, on the notebook machine: /opt/mirror.git and /testbed (SWE-smith's public mirror of
# Jinja), a Python 3.10 environment with the task image's package versions, and a separate
# environment for SWE-smith's harness. It grades the gold patch (must resolve) and no patch
# (must not resolve) of the first 5 test tasks. It prints no key and no environment value.
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request

COMMIT = "6265c2561ef52a7d518ec0a181ecf924f939544a"  # holds the files below
RAW = "https://raw.githubusercontent.com/dinhthithuthuyduphong-bot/gatekeeper/"
FILES = {
    "local_shim.py": f"{COMMIT}/kaggle/scripts/local_shim.py",
    "k0_stage0.py": f"{COMMIT}/kaggle/scripts/k0_stage0.py",
    "udocker_shim.py": f"{COMMIT}/kaggle/scripts/udocker_shim.py",
    "f0_scorer_check.py": f"{COMMIT}/scripts/f0_scorer_check.py",
    "packages.json": f"{COMMIT}/kaggle/data/jinja_image_packages.json",
    "rows.jsonl": "data-snapshots/data/instances/swesmith_pallets__jinja.jsonl",
}
W = "/kaggle/working/c2"
out = {"started": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}


def sh(cmd: str, timeout: int = 1800) -> tuple[int, str]:
    r = subprocess.run(["bash", "-c", cmd], capture_output=True, text=True, timeout=timeout)
    return r.returncode, (r.stdout + r.stderr)[-3000:]


def save():
    with open("/kaggle/working/c2.json", "w") as fh:
        json.dump(out, fh, indent=1, default=str)


try:
    os.makedirs(W + "/code", exist_ok=True)
    out["machine"] = {
        "uid": os.getuid(),
        "root_writable": os.access("/", os.W_OK),
        "opt_writable": os.access("/opt", os.W_OK),
        "testbed_exists": os.path.exists("/testbed"),
        "git": shutil.which("git"),
        "patch": shutil.which("patch"),
        "uv": shutil.which("uv"),
        "python": sys.version.split()[0],
        "cpus": os.cpu_count(),
        "disk_free_gb": round(shutil.disk_usage("/kaggle/working").free / 2**30, 1),
    }
    save()
    for name, path in FILES.items():
        data = urllib.request.urlopen(RAW + path, timeout=120).read()
        with open(f"{W}/code/{name}", "wb") as fh:
            fh.write(data)
    if not shutil.which("uv"):
        out["pip_uv"] = sh(f"{sys.executable} -m pip install -q uv")
    uv = shutil.which("uv") or f"{sys.executable} -m uv"
    hv = W + "/harness_env"
    if not os.path.exists(hv + "/bin/python"):
        out["harness_env"] = sh(
            f"{uv} venv -q --python 3.12 {hv} && "
            f"{uv} pip install -q --python {hv}/bin/python swesmith==0.0.9 swebench==4.1.0"
        )
    save()
    with open(W + "/none.json", "w") as fh:
        json.dump({"runs": []}, fh)
    os.makedirs(W + "/run", exist_ok=True)
    t0 = time.time()
    rc, tail = sh(
        f"cd {W}/run && PYTHONPATH={W}/code {hv}/bin/python {W}/code/k0_stage0.py "
        f"--rows {W}/code/rows.jsonl --results {W}/none.json --controls 5 "
        f"--out {W}/c2_gradings.jsonl --local-packages {W}/code/packages.json "
        "> /kaggle/working/c2.log 2>&1; echo rc=$?; tail -c 2500 /kaggle/working/c2.log",
        timeout=3000,
    )
    out["grading_seconds"] = round(time.time() - t0, 1)
    out["grading_tail"] = tail
    if os.path.exists(W + "/c2_gradings.jsonl"):
        rows = [json.loads(x) for x in open(W + "/c2_gradings.jsonl") if x.strip()]
        out["gradings"] = rows
        gold = [r for r in rows if r["kind"] == "gold" and r["status"] == "completed"]
        noop = [r for r in rows if r["kind"] == "noop" and r["status"] == "completed"]
        out["gold_resolved"] = f"{sum(bool(r['resolved']) for r in gold)}/{len(gold)}"
        out["noop_resolved"] = f"{sum(bool(r['resolved']) for r in noop)}/{len(noop)}"
        out["passed"] = (
            len(gold) == 5
            and len(noop) == 5
            and all(r["resolved"] for r in gold)
            and not any(r["resolved"] for r in noop)
        )
except Exception as e:
    out["error"] = repr(e)[:1500]
out["finished"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
save()
print(json.dumps({k: v for k, v in out.items() if k != "gradings"}, indent=1, default=str)[:6000])
