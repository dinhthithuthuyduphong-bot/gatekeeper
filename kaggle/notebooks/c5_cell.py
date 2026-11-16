# Gate C5 of section 40 (kaggle/preregistration_s40.md, note 40-4): is a task isolated when it
# runs in a chroot of the task image's own file system? NO model call, 0 USD of quota.
# Paste this whole file into ONE cell of a notebook created from
# https://www.kaggle.com/benchmarks/tasks/new and run it (about 10 minutes; it downloads the
# 1.4 GB task image). Then send /kaggle/working/c5.json and c5.log (Output panel).
# It prints no key and no environment value.
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request

COMMIT = "__CODE_COMMIT__"  # holds kaggle/scripts of section 40
TRIAL = "97cd0a5c9d69b45b95a978dc872ad91ac6f90e91"
RAW = "https://raw.githubusercontent.com/dinhthithuthuyduphong-bot/gatekeeper/"
FILES = {
    "chroot_shim.py": f"{COMMIT}/kaggle/scripts/chroot_shim.py",
    "udocker_shim.py": f"{COMMIT}/kaggle/scripts/udocker_shim.py",
    "c5_gate.py": f"{COMMIT}/kaggle/scripts/c5_gate.py",
    "k0_stage0.py": f"{COMMIT}/kaggle/scripts/k0_stage0.py",
    "f0_scorer_check.py": f"{TRIAL}/scripts/f0_scorer_check.py",
    "rows.jsonl": "data-snapshots/data/instances/swesmith_pallets__jinja.jsonl",
}
W = "/kaggle/working/c5"
out = {"started": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}


def sh(cmd: str, timeout: int = 5400) -> tuple[int, str]:
    r = subprocess.run(["bash", "-c", cmd], capture_output=True, text=True, timeout=timeout)
    return r.returncode, (r.stdout + r.stderr)[-2500:]


def save():
    with open("/kaggle/working/c5.json", "w") as fh:
        json.dump(out, fh, indent=1, default=str)


try:
    os.makedirs(W + "/code", exist_ok=True)
    os.makedirs(W + "/run", exist_ok=True)
    out["machine"] = {
        "uid": os.getuid(),
        "python": sys.version.split()[0],
        "kaggle_benchmarks": bool(os.path.isdir("/benchmarks")),
        "free_gb_root": round(shutil.disk_usage("/var").free / 2**30, 1),
    }
    save()
    for name, path in FILES.items():
        data = urllib.request.urlopen(RAW + path, timeout=120).read()
        with open(f"{W}/code/{name}", "wb") as fh:
            fh.write(data)
    if not shutil.which("uv"):
        sh(f"{sys.executable} -m pip install -q uv")
    uv = shutil.which("uv") or f"{sys.executable} -m uv"
    hv = W + "/harness_env"
    if not os.path.exists(hv + "/bin/python"):
        out["harness_env"] = sh(
            f"{uv} venv -q --python 3.12 {hv} && "
            f"{uv} pip install -q --python {hv}/bin/python swesmith==0.0.9 swebench==4.1.0"
        )
    save()
    t0 = time.time()
    rc, tail = sh(
        f"cd {W}/run && PYTHONPATH={W}/code {hv}/bin/python {W}/code/c5_gate.py "
        f"--rows {W}/code/rows.jsonl --out {W}/c5_gate.json --extra /kaggle/working "
        "> /kaggle/working/c5.log 2>&1; echo rc=$?"
    )
    out["gate_seconds"] = round(time.time() - t0, 1)
    out["gate_rc"] = tail.strip()[-10:]
    if os.path.exists(W + "/c5_gate.json"):
        out["gate"] = json.load(open(W + "/c5_gate.json"))
    else:
        out["gate_log_tail"] = sh("tail -c 1500 /kaggle/working/c5.log")[1]
    save()
    if (out.get("gate") or {}).get("passed"):
        with open(W + "/none.json", "w") as fh:
            json.dump({"runs": []}, fh)
        ctl = W + "/c5_gradings.jsonl"
        if os.path.exists(ctl):
            os.remove(ctl)
        t0 = time.time()
        sh(
            f"cd {W}/run && PYTHONPATH={W}/code {hv}/bin/python {W}/code/k0_stage0.py "
            f"--rows {W}/code/rows.jsonl --results {W}/none.json --controls 5 --out {ctl} "
            "--chroot >> /kaggle/working/c5.log 2>&1"
        )
        rows = [json.loads(x) for x in open(ctl) if x.strip()] if os.path.exists(ctl) else []
        gold = [r for r in rows if r["kind"] == "gold" and r["status"] == "completed"]
        noop = [r for r in rows if r["kind"] == "noop" and r["status"] == "completed"]
        out["controls"] = {
            "gold": f"{sum(bool(r['resolved']) for r in gold)}/{len(gold)}",
            "noop": f"{sum(bool(r['resolved']) for r in noop)}/{len(noop)}",
            "seconds_each": [r["seconds"] for r in rows],
            "seconds_total": round(time.time() - t0, 1),
        }
        out["passed"] = out["controls"]["gold"] == "5/5" and out["controls"]["noop"] == "0/5"
    else:
        out["passed"] = False
except Exception as e:
    out["error"] = repr(e)[:1500]
out["finished"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
save()
print(json.dumps(out, indent=1, default=str)[:9000])
