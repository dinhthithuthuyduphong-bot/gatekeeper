# C5 probe (plan_v4.md section 6): which kind of isolation does this machine allow?
# NO model call, 0 USD. Paste this whole file into ONE cell of a notebook created from
# https://www.kaggle.com/benchmarks/tasks/new, run it (under a minute), and send the printed
# JSON (also saved as /kaggle/working/c5_probe.json). It prints no key and no environment value.
import json
import os
import shutil
import subprocess
import tempfile

out = {}


def sh(cmd: str, timeout: int = 120) -> dict:
    try:
        r = subprocess.run(["bash", "-c", cmd], capture_output=True, text=True, timeout=timeout)
        return {"rc": r.returncode, "out": (r.stdout + r.stderr).strip()[-400:]}
    except Exception as e:
        return {"rc": -1, "out": repr(e)[:300]}


d = tempfile.mkdtemp(prefix="c5p_")
open(d + "/canary", "w").write("x")
out["machine"] = {
    "uid": os.getuid(),
    "kernel": os.uname().release,
    "tools": {t: shutil.which(t) for t in ("unshare", "nsenter", "mount", "pivot_root", "chroot")},
    "tools2": {t: shutil.which(t) for t in ("proot", "bwrap", "runc", "setpriv", "su", "curl")},
}
out["caps"] = sh(
    "grep -E 'Cap(Eff|Bnd)' /proc/self/status; cat /proc/sys/kernel/unprivileged_userns_clone 2>&1"
)
out["seccomp"] = sh("grep -E 'Seccomp|NoNewPrivs' /proc/self/status")
# S1: a private mount namespace and a private pid namespace, as root
out["s1_mount_ns"] = sh("unshare --mount true && echo ok")
out["s1_pid_ns"] = sh(
    "unshare --mount --pid --fork --mount-proc sh -c 'ls /proc | grep -c \"^[0-9]\"'"
)
out["s1_tmpfs"] = sh(f"unshare --mount sh -c 'mount -t tmpfs none {d} && ls -a {d} | wc -l'")
out["s1_bind"] = sh(
    f"mkdir -p {d}/a {d}/b && echo 1 > {d}/a/f && "
    f"unshare --mount sh -c 'mount --bind {d}/a {d}/b && cat {d}/b/f'"
)
out["s1_bind_ro"] = sh(
    f"unshare --mount sh -c 'mount --bind {d}/a {d}/b && mount -o remount,ro,bind {d}/b && "
    f"(touch {d}/b/g 2>&1; echo rc=$?)'"
)
out["s1_overlay"] = sh(
    f"mkdir -p {d}/lo {d}/t {d}/mg && echo 1 > {d}/lo/f && unshare --mount sh -c '"
    f"mount -t tmpfs none {d}/t && mkdir {d}/t/up {d}/t/wk && "
    f"mount -t overlay overlay -o lowerdir={d}/lo,upperdir={d}/t/up,workdir={d}/t/wk {d}/mg && "
    f"echo 2 > {d}/mg/f && cat {d}/lo/f {d}/mg/f'"
)
out["s1_pivot"] = sh(
    f"mkdir -p {d}/root && unshare --mount sh -c '"
    f"mount -t tmpfs none {d}/root && mkdir -p {d}/root/usr {d}/root/old {d}/root/proc && "
    f"mount --rbind /usr {d}/root/usr && for x in bin sbin lib lib64 lib32; do "
    f"[ -L /$x ] && cp -a /$x {d}/root/$x; [ -d /$x ] && [ ! -L /$x ] && mkdir {d}/root/$x && "
    f"mount --rbind /$x {d}/root/$x; done; cd {d}/root && pivot_root . old && "
    f'umount -l /old && ls / | tr "\\n" " "\''
)
out["s1_userns_nonroot"] = sh("unshare --user --map-root-user --mount true && echo ok")
# persistent namespace: a holder process, then enter it from outside (what `docker exec` does)
out["s1_nsenter"] = sh(
    "unshare --mount --pid --fork --mount-proc sleep 30 & sleep 1; "
    "p=$(pgrep -n -f 'sleep 30'); "
    "nsenter -t $p -m -p sh -c 'echo entered; ls /proc | grep -c \"^[0-9]\"'; "
    "pkill -f 'unshare --mount --pid --fork --mount-proc sleep 30'; echo done"
)
# S2: ptrace (what proot needs)
out["s2_ptrace"] = sh(
    "cat /proc/sys/kernel/yama/ptrace_scope 2>&1; "
    "(command -v strace && strace -c true 2>&1 | tail -1)"
)
# S3: run as an unprivileged user
out["s3_setpriv"] = sh("setpriv --reuid=65534 --regid=65534 --clear-groups id 2>&1")
out["mounts_head"] = sh(
    "grep -cE ' / |overlay' /proc/mounts; df -T / /tmp /kaggle/working 2>/dev/null | tail -3"
)
shutil.rmtree(d, ignore_errors=True)
os.makedirs("/kaggle/working", exist_ok=True)
json.dump(out, open("/kaggle/working/c5_probe.json", "w"), indent=1)
print(json.dumps(out, indent=1))
