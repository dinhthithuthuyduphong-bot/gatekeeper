"""Section 37, K0a: can the task image run here without a Docker daemon, and with which udocker
execution mode? Run as a separate process (a crash cannot take the notebook kernel with it).

Prints every step as it happens, writes /kaggle/working/k0a.json (environment, every attempt)
and /kaggle/working/k0a_mode.txt (the first mode that ran the tests; empty if none).

  python kaggle/scripts/k0a_probe.py --image swebench/swesmith.x86_64.pallets_1776_jinja.ada0a9a6 \
      --out-dir /kaggle/working
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

MODES = ["P1", "P2", "F1", "F2", "R1", "R2"]  # udocker execution modes, default first
INNER = (
    "echo START; git log --oneline | head -2; python --version; "
    "python -m pytest -q tests/test_api.py 2>&1 | tail -2"
)


def sh(cmd: str) -> str:
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return (r.stdout + r.stderr).strip()[-400:]


def log(*a) -> None:
    print(*a, flush=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", required=True)
    ap.add_argument("--out-dir", required=True, type=Path)
    a = ap.parse_args()
    import udocker_shim

    u = udocker_shim.UDOCKER
    env = {
        "UDOCKER_DIR": os.environ.get("UDOCKER_DIR", "(unset: ~/.udocker)"),
        "whoami": sh("whoami"),
        "kernel": sh("uname -r"),
        "cap_eff": sh("grep CapEff /proc/self/status"),
        "userns": sh(
            "cat /proc/sys/kernel/unprivileged_userns_clone 2>&1; "
            "cat /proc/sys/user/max_user_namespaces 2>&1"
        ),
        "ptrace_scope": sh("cat /proc/sys/kernel/yama/ptrace_scope 2>&1"),
        "disk_root_gb": round(shutil.disk_usage("/").free / 2**30, 1),
        "disk_home_gb": round(shutil.disk_usage(os.path.expanduser("~")).free / 2**30, 1),
        "disk_out_gb": round(shutil.disk_usage(a.out_dir).free / 2**30, 1),
        "mem": sh("free -g | sed -n 2p"),
        "udocker_cmd": " ".join(u[:1] + u[-1:]),
        "udocker_version": subprocess.run([*u, "version"], capture_output=True, text=True).stdout[
            -160:
        ],
    }
    log(json.dumps(env, indent=1))
    out = {"env": env, "attempts": [], "chosen": None}

    def save() -> None:
        (a.out_dir / "k0a.json").write_text(json.dumps(out, indent=1))
        (a.out_dir / "k0a_mode.txt").write_text(out["chosen"] or "")

    os.environ.pop("UDOCKER_EXECMODE", None)
    log("step 1/2: pull and unpack the image (a few minutes the first time) ...")
    try:
        name = udocker_shim.base_container(a.image)
    except Exception as e:  # noqa: BLE001 - reported, the probe stops here
        out["error"] = f"{type(e).__name__}: {str(e)[-600:]}"
        log("FAILED:", out["error"])
        save()
        return 1
    out["disk_out_gb_after_unpack"] = round(shutil.disk_usage(a.out_dir).free / 2**30, 1)
    log("unpacked; free disk now", out["disk_out_gb_after_unpack"], "GB")
    log("step 2/2: run the tests of one task, trying each execution mode until one works")
    for mode in MODES:
        s = subprocess.run(
            [*u, "setup", f"--execmode={mode}", name], capture_output=True, text=True
        )
        try:
            r = subprocess.run(
                [*u, "run", "--nobanner", "--workdir=/testbed", name, "/bin/bash", "-lc", INNER],
                capture_output=True,
                text=True,
                timeout=900,
            )
            rc, so, se = r.returncode, r.stdout, r.stderr
        except subprocess.TimeoutExpired:
            rc, so, se = None, "", "timeout after 900 s"
        ok = rc == 0 and "passed" in so
        out["attempts"].append(
            {
                "mode": mode,
                "setup_rc": s.returncode,
                "setup_tail": (s.stdout + s.stderr)[-300:],
                "run_rc": rc,
                "stdout_tail": so[-500:],
                "stderr_tail": se[-800:],
                "ok": ok,
            }
        )
        log(f"--- mode {mode}: setup rc={s.returncode}, run rc={rc}, ok={ok}")
        log(so[-400:].strip())
        if se.strip():
            log("stderr:", se[-600:].strip())
        save()
        if ok:
            out["chosen"] = mode
            break
    save()
    log("==> MODE CHOSEN:", out["chosen"])
    return 0 if out["chosen"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
