# Section 37, diagnosis of K10: does unpacking the image (many small files) restart the Kaggle
# session, and does it matter where the files go? Paste this whole file into ONE cell of a fresh
# notebook (Internet on) and run it. Then, in new cells:
#   start("/tmp/rootfs")                 # unpack with plain tar outside /kaggle/working
#   show()                               # every 30-60 s until "exit 0"
#   start("/kaggle/working/rootfs")      # the same, inside /kaggle/working
#   show()
# If the session restarts, show() prints a smaller uptime and the log is gone (it lives in /tmp
# and /kaggle/working, both reset by a restart).
import json
import os
import subprocess
import urllib.request

IMAGE = "swebench/swesmith.x86_64.pallets_1776_jinja.ada0a9a6"
LOG = "/kaggle/working/diag2.log"
LAYERS = "/tmp/diag2_layers"


def show():
    boot = open("/proc/sys/kernel/random/boot_id").read().strip()
    up = open("/proc/uptime").read().split()[0]
    print(
        "boot id:",
        boot,
        "| uptime s:",
        up,
        "| working:",
        sorted(os.listdir("/kaggle/working")),
    )
    if os.path.exists(LOG):
        print("--- diag2.log (last 12 lines):")
        print("\n".join(open(LOG).read().splitlines()[-12:]))


def _layers():
    tok = json.load(
        urllib.request.urlopen(
            f"https://auth.docker.io/token?service=registry.docker.io&scope=repository:{IMAGE}:pull"
        )
    )["token"]
    h = {
        "Authorization": f"Bearer {tok}",
        "Accept": "application/vnd.docker.distribution.manifest.v2+json",
    }
    base = f"https://registry-1.docker.io/v2/{IMAGE}"
    req = urllib.request.Request(f"{base}/manifests/latest", headers=h)
    m = json.load(urllib.request.urlopen(req))
    return tok, base, [x["digest"] for x in m["layers"]]


def start(dest):
    tok, base, digests = _layers()
    os.makedirs(LAYERS, exist_ok=True)
    lines = [
        f"mkdir -p {dest}",
        f'echo "[$(date +%T)] start: {len(digests)} layers -> {dest}"',
    ]
    for i, d in enumerate(digests):
        f = f"{LAYERS}/{d.split(':')[1]}"
        lines.append(
            f"[ -f {f} ] || curl -sSfL -H 'Authorization: Bearer {tok}' -o {f} {base}/blobs/{d}"
        )
        lines.append(f"tar -xzf {f} -C {dest} --no-same-owner 2>&1 | tail -2")
        lines.append(
            f'echo "[$(date +%T)] layer {i + 1}/{len(digests)} done; '
            f'files $(find {dest} | wc -l); used $(du -sh {dest} | cut -f1)"'
        )
    lines.append('echo "exit $?"')
    subprocess.Popen(
        ["/bin/bash", "-c", "\n".join(lines)],
        stdout=open(LOG, "a"),
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    print(f"started: unpack into {dest}; run show() again in 30-60 s")


print("Đã nạp hai hàm: show() và start(dest). Trạng thái hiện tại:")
show()
print('Bước tiếp: start("/tmp/rootfs") trong một ô mới, rồi show() mỗi 30-60 giây.')
