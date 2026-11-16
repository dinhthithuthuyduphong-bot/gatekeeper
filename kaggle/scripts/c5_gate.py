"""Plan v4, gate C5: does a task run in chroot_shim see only its own image? (0 USD, no model.)

Measured, each with a fixed expected value:
  1 canaries     marker files planted on the host (shim state, base, host /tmp, working directory,
                 --extra dirs) and in another container's /testbed, /tmp, /root: found from inside
                 a container by `find /`: 0.
  2 processes    a background process started in a container: alive after its command returns
                 (as in Docker), dead after the container is removed.
  3 cross-write  files written by container A in /testbed, /tmp, /root, /opt/mirror.git: seen by
                 container B: 0; the base clone's files changed: 0.
  4 shell        python path and version, `pwd -P`, the three commit subjects, HOME, and no host
                 variable in `env` (a marker variable set in this process must not appear).
  5 host         /proc, /kaggle, the harness code and the rows file do not exist inside.
  6 detection    an in-place write to a file of the shared base through a hard link is detected
                 when the container is removed (run last: the base is then rebuilt).

  python kaggle/scripts/c5_gate.py --rows rows.jsonl --out c5_gate.json [--extra /kaggle/working]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
MARK = "gk_canary_7f3a"


def sh(c, cmd: str, workdir: str = "/testbed") -> str:
    return c.exec_run(["bash", "-lc", cmd], workdir=workdir).output.decode()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--extra", nargs="*", default=[], type=Path)
    a = ap.parse_args()
    import chroot_shim as cs
    from swesmith.profiles import registry

    first = json.loads(next(x for x in a.rows.read_text().splitlines() if x.strip()))
    rp = registry.get_from_inst(first)
    os.environ["GK_HOST_MARKER"] = MARK
    res: dict = {"probe": cs.probe()}
    t0 = time.time()
    info = cs.prepare(rp.image_name, f"https://github.com/{rp.mirror_name}")
    res["prepare_seconds"] = round(time.time() - t0, 1)
    res["prepared"] = {k: v for k, v in info.items() if k != "env"}
    client = cs.Client()

    host = [
        cs.STATE / f"{MARK}_state",
        Path("/tmp") / f"{MARK}_hosttmp",
        Path.cwd() / f"{MARK}_cwd",
    ]
    host += [d / f"{MARK}_extra" for d in a.extra if d.is_dir()]
    for p in host:
        p.write_text(MARK)
    t0 = time.time()
    ca = client.containers.create(image=rp.image_name, name="a")
    res["create_seconds"] = round(time.time() - t0, 1)
    cb = client.containers.create(image=rp.image_name, name="b")
    sh(ca, f"git checkout -q {first['instance_id']}")
    sh(cb, f"git checkout -q {first['instance_id']}")
    sh(
        ca,
        f"echo {MARK} > /testbed/{MARK}_a_testbed; echo {MARK} > /tmp/{MARK}_a_tmp; "
        f"echo {MARK} > /root/{MARK}_a_root; echo {MARK} > /opt/mirror.git/{MARK}_a_mirror; "
        "nohup sleep 987654 >/dev/null 2>&1 &",
    )
    found = sh(cb, f"find / -name '*{MARK}*' 2>/dev/null")
    res["1_canaries"] = {
        "planted": len(host) + 4,
        "found_from_inside": [x for x in found.splitlines() if x.strip()],
    }
    alive = lambda: sum(  # noqa: E731
        1
        for p in Path("/proc").iterdir()
        if p.name.isdigit()
        and (p / "cmdline").exists()
        and b"987654" in (p / "cmdline").read_bytes()
    )
    res["2_processes"] = {"alive_after_command": alive()}
    res["3_cross_write"] = {
        "seen_by_b": [
            x
            for x in sh(cb, f"ls /testbed /tmp /root /opt/mirror.git | grep {MARK}").splitlines()
            if x.strip()
        ],
        "base_changed": [str(p) for p in cs.BASE.rglob(f"*{MARK}*")],
    }
    res["4_shell"] = {
        "python": sh(ca, "which python; python -V").split("\n")[:2],
        "pwd": sh(ca, "pwd -P").strip(),
        "commits": sh(ca, "git log --format=%s | head -5").strip().splitlines(),
        "home": sh(ca, "echo $HOME").strip(),
        "host_marker_in_env": MARK in sh(ca, "env"),
        "env_names": sorted(x.split("=")[0] for x in sh(ca, "env").splitlines() if "=" in x),
    }
    res["5_host"] = {
        "exists_inside": [
            p
            for p in ("/proc/1", "/kaggle", "/benchmarks", str(cs.STATE), str(HERE), str(a.rows))
            if sh(ca, f"test -e {p} && echo yes").strip() == "yes"
        ],
        "top_level": sh(ca, "ls /").split(),
    }
    ca.remove()
    res["2_processes"]["alive_after_remove"] = alive()
    cb.remove()
    for p in host:
        p.unlink(missing_ok=True)
    res["base_intact_before_test_6"] = cs.base_intact() == []
    cc = client.containers.create(image=rp.image_name, name="c")
    sh(cc, "echo '# in-place write' >> /etc/os-release")
    try:
        cc.remove()
        res["6_detection"] = {"detected": False}
    except RuntimeError as e:
        res["6_detection"] = {"detected": True, "message": str(e)[:200]}
    try:
        client.containers.create(image=rp.image_name, name="d")
        res["6_detection"]["later_container_refused"] = False
    except RuntimeError:
        res["6_detection"]["later_container_refused"] = True
    t0 = time.time()
    cs.prepare(rp.image_name, f"https://github.com/{rp.mirror_name}")  # rebuilds the base
    res["rebuild_seconds"] = round(time.time() - t0, 1)
    res["base_intact_after_rebuild"] = cs.base_intact() == []
    s4 = res["4_shell"]
    res["passed"] = bool(
        not res["1_canaries"]["found_from_inside"]
        and res["2_processes"] == {"alive_after_command": 1, "alive_after_remove": 0}
        and not res["3_cross_write"]["seen_by_b"]
        and not res["3_cross_write"]["base_changed"]
        and s4["python"][0] == "/opt/miniconda3/envs/testbed/bin/python"
        and s4["pwd"] == "/testbed"
        and s4["commits"] == ["Remove F2P Tests", "Bug Patch", "Initial commit"]
        and s4["home"] == "/root"
        and not s4["host_marker_in_env"]
        and not res["5_host"]["exists_inside"]
        and res["base_intact_before_test_6"]
        and res["6_detection"]
        == {
            "detected": True,
            "message": res["6_detection"].get("message"),
            "later_container_refused": True,
        }
        and res["base_intact_after_rebuild"]
    )
    a.out.write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps(res, indent=1))
    return 0 if res["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
