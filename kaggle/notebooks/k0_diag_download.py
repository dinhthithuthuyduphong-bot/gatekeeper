# Section 37, diagnosis of K5-K8: does a plain large download (no udocker) also restart the Kaggle
# session? Paste this whole file into ONE cell of a fresh notebook (Internet on) and run it; then
# run `show()` in another cell, `start(None)`, and `show()` again every 30-60 s.
# If the session restarts (uptime falls, /kaggle/working is empty again), try `start("20M")`.
# Writes everything under /kaggle/working/diag; prints boot id and uptime so a restart is visible.
import json
import os
import subprocess
import urllib.request

W = "/kaggle/working/diag"
os.makedirs(W, exist_ok=True)
IMAGE = "swebench/swesmith.x86_64.pallets_1776_jinja.ada0a9a6"


def show():
    boot = open("/proc/sys/kernel/random/boot_id").read().strip()
    up = open("/proc/uptime").read().split()[0]
    print("boot id:", boot, "| uptime s:", up, "| working:", sorted(os.listdir("/kaggle/working")))
    for f in ("download.log",):
        p = f"{W}/{f}"
        if os.path.exists(p):
            print(f"--- {f} (last 8 lines):")
            print("\n".join(open(p).read().splitlines()[-8:]))


def start(limit):
    tok = json.load(
        urllib.request.urlopen(
            f"https://auth.docker.io/token?service=registry.docker.io&scope=repository:{IMAGE}:pull"
        )
    )["token"]
    h = {
        "Authorization": f"Bearer {tok}",
        "Accept": ", ".join(
            [
                "application/vnd.docker.distribution.manifest.v2+json",
                "application/vnd.oci.image.manifest.v1+json",
                "application/vnd.docker.distribution.manifest.list.v2+json",
                "application/vnd.oci.image.index.v1+json",
            ]
        ),
    }
    base = f"https://registry-1.docker.io/v2/{IMAGE}"
    m = json.load(
        urllib.request.urlopen(urllib.request.Request(f"{base}/manifests/latest", headers=h))
    )
    if "manifests" in m:  # an index: take the amd64 entry
        d = next(x for x in m["manifests"] if x.get("platform", {}).get("architecture") == "amd64")
        m = json.load(
            urllib.request.urlopen(
                urllib.request.Request(f"{base}/manifests/{d['digest']}", headers=h)
            )
        )
    layer = max(m["layers"], key=lambda x: x["size"])
    print(
        "largest layer:",
        layer["digest"][:19],
        round(layer["size"] / 2**20),
        "MB; limit:",
        limit or "none",
    )
    cmd = [
        "curl",
        "-sSL",
        "-H",
        f"Authorization: Bearer {tok}",
        "-o",
        f"{W}/layer.tgz",
        "-w",
        "done: %{size_download} bytes in %{time_total} s\n",
        f"{base}/blobs/{layer['digest']}",
    ]
    if limit:
        cmd[1:1] = ["--limit-rate", limit]
    size = f"$(du -sm {W}/layer.tgz 2>/dev/null | cut -f1)"
    beat = f'while kill -0 $J 2>/dev/null; do echo "[$(date +%T)] {size} MB"; sleep 5; done'
    quoted = " ".join(repr(c) if " " in c else c for c in cmd)
    script = f"({quoted}) & J=$!; {beat} & wait $J; echo exit $?"
    subprocess.Popen(
        ["/bin/bash", "-c", script],
        stdout=open(f"{W}/download.log", "a"),
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    print("download started; run show() again in 30-60 s")


print("Đã nạp hai hàm: show() và start(...). Trạng thái hiện tại:")
show()
print("Bước tiếp: chạy start(None) trong một ô mới, rồi show() mỗi 30-60 giây.")
