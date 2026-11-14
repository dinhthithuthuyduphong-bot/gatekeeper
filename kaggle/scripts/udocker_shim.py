"""Section 37 (stage 0): run SWE-smith's own grading where no Docker daemon exists (Kaggle).

SWE-smith's harness (swesmith.harness.utils.run_patch_in_container, used verbatim) talks to the
Docker SDK. This module gives it an object with the handful of SDK calls it uses, executed by
udocker (user-space containers, the task image pulled unchanged from Docker Hub). Nothing in
SWE-smith or in the grading is edited: only `docker.from_env` and the image pull are replaced.

What differs from Docker, by construction (stated in the preregistration, section 37):
  * one base container per image is unpacked once; each "container" the harness creates gets its
    own fresh copy of /testbed (bind-mounted), the rest of the file system is shared, so runs are
    sequential (one at a time);
  * no memory limit is enforced (`mem_limit` is ignored);
  * commands run through udocker's default execution mode instead of the Docker runtime.
Whether grading is the same is not assumed: scripts/k0_stage0.py re-scores patches whose Docker
grade is on record and compares.

  import udocker_shim; udocker_shim.install()   # before calling swesmith.harness.eval
"""

from __future__ import annotations

import io
import os
import shlex
import shutil
import signal
import subprocess
import sys
import tarfile
import tempfile
import uuid
from pathlib import Path


def _udocker_cmd() -> list[str]:
    """The udocker command line. UDOCKER_CMD if set; else the `udocker` script on PATH; else the
    udocker package of this very interpreter (on Kaggle the script may not be on the PATH that a
    subprocess sees, while the package is importable)."""
    if os.environ.get("UDOCKER_CMD"):
        return shlex.split(os.environ["UDOCKER_CMD"])
    if shutil.which("udocker"):
        return ["udocker", "--allow-root"]
    entry = (
        "import sys; from udocker.maincmd import main; sys.argv[0] = 'udocker'; sys.exit(main())"
    )
    return [sys.executable, "-c", entry, "--allow-root"]


UDOCKER = _udocker_cmd()
WORKDIR = "/testbed"  # swesmith.constants DOCKER_WORKDIR
_bases: dict[str, str] = {}  # image -> base container name


def _u(*args: str, **kw) -> subprocess.CompletedProcess:
    return subprocess.run([*UDOCKER, *args], capture_output=True, **kw)


def _root(name: str) -> Path:
    r = _u("inspect", "-p", name)
    p = Path(r.stdout.decode().strip().splitlines()[-1])
    if r.returncode != 0 or not p.is_dir():
        raise RuntimeError(f"udocker container {name!r} has no root: {r.stderr.decode()[-300:]}")
    return p


_MEDIA = ", ".join(
    [
        "application/vnd.docker.distribution.manifest.v2+json",
        "application/vnd.oci.image.manifest.v1+json",
        "application/vnd.docker.distribution.manifest.list.v2+json",
        "application/vnd.oci.image.index.v1+json",
    ]
)


def _fetch_oci(image: str, dest: Path) -> None:
    """Download an image from Docker Hub with curl into an OCI layout at `dest`, checking the
    sha256 of every blob. (On Kaggle, `udocker pull` restarted the whole session; a plain curl
    download of the same layer did not: kaggle/audit.md K8.)"""
    import hashlib
    import json
    import urllib.request

    repo, _, tag = image.partition(":")
    tag = tag or "latest"
    tok = json.load(
        urllib.request.urlopen(
            f"https://auth.docker.io/token?service=registry.docker.io&scope=repository:{repo}:pull"
        )
    )["token"]
    base = f"https://registry-1.docker.io/v2/{repo}"

    def get(url: str, accept: str = _MEDIA) -> bytes:
        """GET with retries on 429 (Docker Hub's rate limit, shared by every user of an IP)."""
        import time
        import urllib.error

        req = urllib.request.Request(
            url, headers={"Authorization": f"Bearer {tok}", "Accept": accept}
        )
        for wait in (0, 30, 60, 120, 240):
            time.sleep(wait)
            try:
                return urllib.request.urlopen(req).read()
            except urllib.error.HTTPError as e:
                if e.code != 429:
                    raise
                print(f"registry rate limit (429); retrying in {wait * 2 or 30} s", flush=True)
        raise RuntimeError("Docker Hub rate limit (429) after 5 attempts")

    raw = get(f"{base}/manifests/{tag}")
    man = json.loads(raw)
    if "manifests" in man:  # an index: take linux/amd64
        d = next(
            x
            for x in man["manifests"]
            if x.get("platform", {}).get("architecture") == "amd64"
            and x.get("platform", {}).get("os", "linux") == "linux"
        )
        raw = get(f"{base}/manifests/{d['digest']}")
        man = json.loads(raw)
    blobs = dest / "blobs" / "sha256"
    blobs.mkdir(parents=True, exist_ok=True)
    seen = set()
    for b in [man["config"], *man["layers"]]:
        if b["digest"] in seen:
            continue
        seen.add(b["digest"])
        hexd = b["digest"].split(":", 1)[1]
        out = blobs / hexd
        r = subprocess.run(
            [
                "curl",
                "-sSfL",
                "-H",
                f"Authorization: Bearer {tok}",
                "-o",
                str(out),
                f"{base}/blobs/{b['digest']}",
            ],
            capture_output=True,
        )
        if r.returncode != 0:
            raise RuntimeError(f"curl {b['digest'][:19]} failed: {r.stderr.decode()[-300:]}")
        h = hashlib.sha256()
        with open(out, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
        if h.hexdigest() != hexd:
            raise RuntimeError(f"sha256 mismatch for {b['digest'][:19]}")
    mdig = hashlib.sha256(raw).hexdigest()
    (blobs / mdig).write_bytes(raw)
    (dest / "oci-layout").write_text(json.dumps({"imageLayoutVersion": "1.0.0"}))
    index = {
        "schemaVersion": 2,
        "manifests": [
            {
                # udocker's OCI loader reads only entries of this media type; the manifest blob
                # itself keeps the registry's own media type and bytes
                "mediaType": "application/vnd.oci.image.manifest.v1+json",
                "digest": f"sha256:{mdig}",
                "size": len(raw),
                "annotations": {"org.opencontainers.image.ref.name": tag},
            }
        ],
    }
    (dest / "index.json").write_text(json.dumps(index))


# `udocker load` moves each layer file into its repository (os.rename). An image whose layer list
# names the same layer twice (the Jinja image does) then fails on the
# second move. This runs udocker's own `load` with one change: a layer already in the repository
# is registered again instead of moved again. The bytes and the order of the layers are unchanged.
_LOAD = """
import os, sys
import udocker.commonlocalfile as c
_orig = c.CommonLocalFileApi._move_layer_to_v1repo
def _move(self, filepath, layer_id, linkname=None):
    if not os.path.exists(filepath) and ':' in layer_id and not filepath.endswith('json'):
        target = self.localrepo.layersdir + '/' + layer_id.split(':', 1)[1] + '.layer'
        if os.path.exists(target):
            self.localrepo.add_image_layer(target, linkname)
            return True
    return _orig(self, filepath, layer_id, linkname)
c.CommonLocalFileApi._move_layer_to_v1repo = _move
from udocker.maincmd import main
sys.argv[0] = 'udocker'
sys.exit(main())
"""


# `udocker create` restarted the Kaggle session (kaggle/audit.md K10, K11), while plain tar
# unpacking of the same layers did not. This runs udocker's own `create` UNCHANGED, but prints every
# command it starts (tar, find, ...) with time and duration, and a heartbeat every 5 s (free RAM,
# number of processes, load), so that the last lines before a restart show where it happened.
_CREATE = """
import os, subprocess, sys, threading, time, types
import udocker.container.structure as st
def beat():
    while True:
        mem = [l for l in open('/proc/meminfo') if l.startswith('MemAvailable')][0].split()[1]
        procs = len([p for p in os.listdir('/proc') if p.isdigit()])
        load = open('/proc/loadavg').read().split()[0]
        print(f'    [beat {time.strftime("%T")}] RAM free {int(mem) // 2**20} GB, '
              f'processes {procs}, load {load}', flush=True)
        time.sleep(5)
threading.Thread(target=beat, daemon=True).start()
_call = subprocess.call
def call(cmd, *a, **k):
    t = time.time()
    print(f'    [{time.strftime("%T")}] start: {" ".join(map(str, cmd))[:160]}', flush=True)
    rc = _call(cmd, *a, **k)
    print(f'    [{time.strftime("%T")}] end (rc {rc}, {time.time() - t:.1f} s)', flush=True)
    return rc
ns = {n: getattr(subprocess, n) for n in dir(subprocess) if not n.startswith('__')}
ns['call'] = call
st.subprocess = types.SimpleNamespace(**ns)
from udocker.maincmd import main
sys.argv[0] = 'udocker'
sys.exit(main())
"""


def pull(image: str) -> None:
    """Make the image available to udocker. Default: curl into an OCI layout, then `udocker load`
    (UDOCKER_PULL=udocker uses `udocker pull` instead)."""
    if _u("inspect", image).returncode == 0:
        return
    if os.environ.get("UDOCKER_PULL") == "udocker":
        r = _u("pull", image)
        if r.returncode != 0:
            raise RuntimeError(f"udocker pull {image} failed: {r.stderr.decode()[-300:]}")
        return
    work = Path(tempfile.mkdtemp(prefix="oci_", dir=os.environ.get("UDOCKER_DIR")))
    try:
        layout = work / "layout"
        _fetch_oci(image, layout)
        tar = work / "image.tar"
        r = subprocess.run(["tar", "-cf", str(tar), "-C", str(layout), "."], capture_output=True)
        if r.returncode != 0:
            raise RuntimeError(f"tar failed: {r.stderr.decode()[-300:]}")
        shutil.rmtree(layout)
        repo = image.partition(":")[0]
        _u("rmi", image)  # a half-loaded image left by an interrupted or failed load
        r = subprocess.run(
            [sys.executable, "-c", _LOAD, "--allow-root", "load", "-i", str(tar), repo],
            capture_output=True,
        )
        if r.returncode != 0 or _u("inspect", image).returncode != 0:
            raise RuntimeError(f"udocker load failed: {(r.stdout + r.stderr).decode()[-400:]}")
    finally:
        shutil.rmtree(work, ignore_errors=True)


def base_container(image: str) -> str:
    """One unpacked container per image, reused (unpacking takes about a minute and 3 GB)."""
    if image not in _bases:
        name = "base_" + "".join(c if c.isalnum() else "_" for c in image)[-60:]
        if _u("inspect", "-p", name).returncode != 0:
            pull(image)
            # output not captured: it goes to the caller's stdout (k0a.log), line by line
            r = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    _CREATE,
                    "--allow-root",
                    "create",
                    f"--name={name}",
                    image,
                ]
            )
            if r.returncode != 0:
                raise RuntimeError(f"udocker create failed (rc {r.returncode}); see the log above")
        mode = os.environ.get("UDOCKER_EXECMODE")  # chosen by the K0a probe of the notebook
        if mode:
            r = _u("setup", f"--execmode={mode}", name)
            if r.returncode != 0:
                raise RuntimeError(f"udocker setup {mode} failed: {r.stderr.decode()[-300:]}")
        _bases[image] = name
    return _bases[image]


class ExecResult:
    def __init__(self, exit_code: int, output: bytes):
        self.exit_code, self.output = exit_code, output

    def __iter__(self):  # docker's ExecResult is a named tuple (exit_code, output)
        return iter((self.exit_code, self.output))


class _Api:
    def __init__(self):
        self._execs: dict[str, tuple[Container, str]] = {}
        self._procs: dict[str, subprocess.Popen] = {}

    def exec_create(self, container_id: str, cmd: str) -> dict:
        i = uuid.uuid4().hex
        self._execs[i] = (Container.by_id[container_id], cmd)
        return {"Id": i}

    def exec_start(self, exec_id: str, stream: bool = True):
        c, cmd = self._execs[exec_id]
        p = c._popen(cmd, None, None)
        self._procs[exec_id] = p
        yield from iter(lambda: p.stdout.read(65536), b"")
        p.wait()

    def exec_inspect(self, exec_id: str) -> dict:
        return {"Pid": self._procs[exec_id].pid}

    def inspect_container(self, container_id: str) -> dict:
        return {"State": {"Pid": 0}}


class Container:
    by_id: dict[str, Container] = {}

    def __init__(self, client: Client, image: str, name: str):
        self.client, self.image, self.name = client, image, name
        self.id = uuid.uuid4().hex
        self.base = base_container(image)
        self.root = _root(self.base)
        self.testbed = Path(tempfile.mkdtemp(prefix="testbed_"))
        shutil.copytree(
            self.root / WORKDIR.lstrip("/"), self.testbed, symlinks=True, dirs_exist_ok=True
        )
        Container.by_id[self.id] = self

    def start(self) -> None:
        pass

    def _popen(self, cmd, workdir, environment) -> subprocess.Popen:
        argv = shlex.split(cmd) if isinstance(cmd, str) else list(cmd)
        env = [f"--env={k}={v}" for k, v in (environment or {}).items()]
        full = [
            *UDOCKER,
            "--quiet",
            "run",
            "--nobanner",
            f"--volume={self.testbed}:{WORKDIR}",
            f"--workdir={workdir or '/'}",
            *env,
            self.base,
            *argv,
        ]
        return subprocess.Popen(
            full, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, start_new_session=True
        )

    def exec_run(self, cmd, workdir=None, user=None, environment=None, detach=False, **_):
        argv = shlex.split(cmd) if isinstance(cmd, str) else list(cmd)
        if argv[:2] == ["kill", "-TERM"]:  # the harness kills a timed-out test run by its pid
            try:
                os.killpg(int(argv[2]), signal.SIGKILL)
            except (ProcessLookupError, ValueError, IndexError):
                pass
            return ExecResult(0, b"")
        p = self._popen(cmd, workdir, environment)
        out, _ = p.communicate()
        return ExecResult(p.returncode, out)

    def put_archive(self, path: str, data: bytes) -> bool:
        dest = Path(path)
        if str(dest).startswith(WORKDIR):
            host = self.testbed / str(dest)[len(WORKDIR) :].lstrip("/")
        else:
            host = self.root / str(dest).lstrip("/")
        host.mkdir(parents=True, exist_ok=True)
        with tarfile.open(fileobj=io.BytesIO(data)) as tar:
            tar.extractall(host, filter="tar")
        return True

    def stop(self, timeout: int = 15) -> None:
        pass

    def remove(self, force: bool = True) -> None:
        shutil.rmtree(self.testbed, ignore_errors=True)
        Container.by_id.pop(self.id, None)


class _Containers:
    def __init__(self, client: Client):
        self.client = client

    def create(self, image: str, name: str = "", **_) -> Container:
        return Container(self.client, image, name)


class Client:
    def __init__(self):
        self.api = _Api()
        self.containers = _Containers(self)


class _DockerModule:
    @staticmethod
    def from_env() -> Client:
        return Client()


def install() -> None:
    """Point SWE-smith's harness at udocker. Call once, before any grading."""
    import swesmith.harness.utils as hu
    from swesmith.profiles.base import RepoProfile

    hu.docker = _DockerModule()
    RepoProfile.pull_image = lambda self: pull(self.image_name)
