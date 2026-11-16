#!/usr/bin/env python3
"""Plan v4, gate C5: SWE-smith's harness and gskill's agent in a chroot of the task image's own
file system, for machines with no Docker daemon and no right to create namespaces (Kaggle
Benchmarks notebooks: CAP_SYS_CHROOT and CAP_MKNOD, no CAP_SYS_ADMIN; kaggle/audit.md K21).

  base     the image's layers, downloaded with curl (sha256 checked) and unpacked with tarfile
           (whiteouts applied), then the two steps of our Dockerfile: the bare mirror at
           /opt/mirror.git and `git fetch` in /testbed. Nothing of the image is rebuilt.
  container  its own directory tree: every file of the base as a hard link (seconds), except the
           directories a task writes to, which are real copies: /testbed, /tmp, /root, /var/tmp,
           /opt/mirror.git, /dev. Commands run after chroot() into that tree, with the image's
           own environment and its own `bash -lc`. A task therefore sees the image's files and
           nothing of the host: no other task, no harness code, no task rows, no notebook.
  cleanup  when a container is removed, every process whose root is its tree is killed, the tree
           is deleted, and the base is checked against a snapshot of (size, mtime) of each file:
           a write through a hard link is detected, the run is failed and the base is rebuilt.

What differs from Docker, by construction (stated in the registration):
  * no /proc and no /sys inside (they cannot be mounted): `ps`, /dev/fd and /dev/stdin do not work;
  * /dev holds only null, zero, full, random, urandom, tty (device nodes made with mknod);
  * no memory limit; processes share the host's process table (they cannot list it);
  * a file of the base written in place (not replaced) would be shared: detected, not prevented;
  * root inside a chroot can leave it deliberately; an agent that only explores cannot see out.
Whether grading and the agent's view are the same is measured by gate C5, not assumed.

  import chroot_shim; chroot_shim.prepare(image, mirror_url); chroot_shim.install()
"""

from __future__ import annotations

import io
import json
import os
import shlex
import shutil
import signal
import stat
import subprocess
import tarfile
import uuid
from pathlib import Path

STATE = Path(os.environ.get("CHROOT_SHIM_DIR", "/var/lib/cshim"))
BASE = STATE / "base"
MUTABLE = ("testbed", "tmp", "root", "var/tmp", "opt/mirror.git", "dev")  # real copies per task
DEVICES = {"null": (1, 3), "zero": (1, 5), "full": (1, 7), "random": (1, 8), "urandom": (1, 9)}
DEVICES["tty"] = (5, 0)
_env: dict[str, str] = {}


def probe() -> dict:
    caps = ""
    for line in Path("/proc/self/status").read_text().splitlines():
        if line.startswith("CapEff"):
            caps = line.split()[1]
    n = int(caps or "0", 16)
    return {
        "uid": os.getuid(),
        "cap_sys_chroot": bool(n >> 18 & 1),
        "cap_mknod": bool(n >> 27 & 1),
        "cap_sys_admin": bool(n >> 21 & 1),
        "state_dir": str(STATE),
        "free_gb": round(shutil.disk_usage(STATE.parent).free / 2**30, 1),
    }


def _unpack(layout: Path, dest: Path) -> dict:
    """Apply the image's layers in order, as a container runtime does (OCI whiteouts)."""
    idx = json.loads((layout / "index.json").read_text())
    blobs = layout / "blobs" / "sha256"
    man = json.loads((blobs / idx["manifests"][0]["digest"].split(":")[1]).read_bytes())
    cfg = json.loads((blobs / man["config"]["digest"].split(":")[1]).read_bytes())
    dest.mkdir(parents=True, exist_ok=True)
    for layer in man["layers"]:
        with tarfile.open(blobs / layer["digest"].split(":")[1]) as tf:
            members = []
            for m in tf:
                name = Path(m.name).name
                parent = dest / Path(m.name).parent
                if name == ".wh..wh..opq":  # everything below this directory is hidden
                    if parent.is_dir():
                        for x in parent.iterdir():
                            shutil.rmtree(x) if x.is_dir() and not x.is_symlink() else x.unlink()
                    continue
                if name.startswith(".wh."):
                    t = parent / name[4:]
                    if t.is_dir() and not t.is_symlink():
                        shutil.rmtree(t)
                    elif t.exists() or t.is_symlink():
                        t.unlink()
                    continue
                t = dest / m.name
                if (t.exists() or t.is_symlink()) and not (m.isdir() and t.is_dir()):
                    shutil.rmtree(t) if t.is_dir() and not t.is_symlink() else t.unlink()
                members.append(m)
            tf.extractall(dest, members=members, filter="fully_trusted")
    return cfg.get("config", {})


def _in(root: Path, cmd: str, workdir: str = "/") -> str:
    r = _popen(root, ["bash", "-lc", cmd], workdir, None)
    out, _ = r.communicate()
    if r.returncode != 0:
        raise RuntimeError(f"`{cmd[:100]}` failed in the image: {out.decode()[-500:]}")
    return out.decode()


def _popen(root: Path, argv: list[str], workdir: str | None, environment: dict | None):
    def enter():
        os.chroot(root)
        os.chdir(workdir or "/")

    return subprocess.Popen(
        argv,
        env={**_env, **(environment or {})},
        preexec_fn=enter,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )


def _snapshot(root: Path) -> dict[str, tuple[int, int]]:
    snap = {}
    skip = tuple(str(root / m) for m in MUTABLE)
    for d, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if not str(Path(d) / x).startswith(skip)]
        for f in files:
            p = os.path.join(d, f)
            st = os.lstat(p)
            if stat.S_ISREG(st.st_mode):
                snap[p] = (st.st_size, st.st_mtime_ns)
    return snap


def base_intact() -> list[str]:
    """Files of the base whose size or modification time differs from the snapshot."""
    want = {k: tuple(v) for k, v in json.loads((STATE / "snapshot.json").read_text()).items()}
    have = _snapshot(BASE)
    return sorted(k for k in want.keys() | have.keys() if want.get(k) != have.get(k))[:20]


def prepare(image: str, mirror_url: str) -> dict:
    """Build the base once (idempotent). Returns what was built."""
    global _env
    done = STATE / "prepared.json"
    (STATE / "CONTAMINATED").unlink(missing_ok=True)
    if done.exists():
        info = json.loads(done.read_text())
        _env = info["env"]
        return info
    import udocker_shim  # the curl download of the layers, sha256 checked (stage 0)

    STATE.mkdir(parents=True, exist_ok=True)
    layout = STATE / "layout"
    if not (layout / "index.json").exists():
        udocker_shim._fetch_oci(image, layout)
    if BASE.exists():
        shutil.rmtree(BASE)
    cfg = _unpack(layout, BASE)
    shutil.rmtree(layout, ignore_errors=True)
    _env = dict(e.split("=", 1) for e in cfg.get("Env", []))
    _env.setdefault("HOME", "/root")
    dev = BASE / "dev"
    if dev.exists():
        shutil.rmtree(dev)
    dev.mkdir()
    for name, (major, minor) in DEVICES.items():
        os.mknod(dev / name, 0o666 | stat.S_IFCHR, os.makedev(major, minor))
        os.chmod(dev / name, 0o666)
    for d in ("tmp", "var/tmp"):
        (BASE / d).mkdir(parents=True, exist_ok=True)
        os.chmod(BASE / d, 0o1777)
    for f in ("resolv.conf", "hosts"):  # name resolution of this machine (docker does the same)
        if Path("/etc", f).exists():
            shutil.copyfile(Path("/etc", f), BASE / "etc" / f)
    subprocess.run(
        ["git", "clone", "-q", "--mirror", mirror_url, str(BASE / "opt" / "mirror.git")], check=True
    )
    _in(  # our Dockerfile's RUN line (scratchpad ext/img/Dockerfile of section 25)
        BASE,
        "chmod -R a+rX /opt/mirror.git && cd /testbed && git remote set-url origin "
        "/opt/mirror.git && git fetch -q origin && "
        "git config --global --add safe.directory /opt/mirror.git",
    )
    (STATE / "snapshot.json").write_text(json.dumps(_snapshot(BASE)))
    info = {
        "image": image,
        "env": _env,
        "workdir": cfg.get("WorkingDir"),
        "files_in_snapshot": len(json.loads((STATE / "snapshot.json").read_text())),
        "python": _in(BASE, "python -V; which python").split(),
        "branches": int(_in(BASE, "git branch -r | wc -l", "/testbed").strip()),
    }
    done.write_text(json.dumps(info))
    return info


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
        p = _popen(c.root, shlex.split(cmd), None, None)
        self._procs[exec_id] = p
        yield from iter(lambda: p.stdout.read(65536), b"")
        p.wait()

    def exec_inspect(self, exec_id: str) -> dict:
        return {"Pid": self._procs[exec_id].pid}

    def inspect_container(self, container_id: str) -> dict:
        return {"State": {"Pid": 0}}


def kill_inside(root: Path) -> int:
    """Kill every process whose root directory is `root` (what removing a container does)."""
    n = 0
    for p in Path("/proc").iterdir():
        if p.name.isdigit():
            try:
                if os.readlink(p / "root") == str(root):
                    os.kill(int(p.name), signal.SIGKILL)
                    n += 1
            except OSError:
                pass
    return n


class Container:
    by_id: dict[str, Container] = {}

    def __init__(self, client: Client, image: str, name: str):
        self.client, self.image, self.name = client, image, name
        if (STATE / "CONTAMINATED").exists():
            raise RuntimeError("the shared base was written to; rebuild it before any run")
        self.id = uuid.uuid4().hex
        self.root = STATE / f"c_{self.id[:12]}"
        subprocess.run(["cp", "-al", str(BASE), str(self.root)], check=True)
        for m in MUTABLE:
            shutil.rmtree(self.root / m)
            subprocess.run(["cp", "-a", str(BASE / m), str(self.root / m)], check=True)
        (STATE / "containers").mkdir(exist_ok=True)  # read by fake_docker.py (another process)
        (STATE / "containers" / self.id).write_text(str(self.root))
        Container.by_id[self.id] = self

    def start(self) -> None:
        pass

    def exec_run(self, cmd, workdir=None, user=None, environment=None, detach=False, **_):
        argv = shlex.split(cmd) if isinstance(cmd, str) else list(cmd)
        if argv[:2] == ["kill", "-TERM"]:  # the harness kills a timed-out test run by its pid
            try:
                os.killpg(int(argv[2]), signal.SIGKILL)
            except (ProcessLookupError, ValueError, IndexError):
                pass
            return ExecResult(0, b"")
        try:
            p = _popen(self.root, argv, workdir, environment)
        except (FileNotFoundError, subprocess.SubprocessError) as e:
            return ExecResult(127, str(e).encode())
        out, _ = p.communicate()
        return ExecResult(p.returncode, out)

    def put_archive(self, path: str, data: bytes) -> bool:
        dest = self.root / path.lstrip("/")
        dest.mkdir(parents=True, exist_ok=True)
        with tarfile.open(fileobj=io.BytesIO(data)) as tar:
            tar.extractall(dest, filter="tar")
        return True

    def stop(self, timeout: int = 15) -> None:
        kill_inside(self.root)

    def remove(self, force: bool = True) -> None:
        kill_inside(self.root)
        shutil.rmtree(self.root, ignore_errors=True)
        (STATE / "containers" / self.id).unlink(missing_ok=True)
        Container.by_id.pop(self.id, None)
        changed = base_intact()
        if changed:
            (STATE / "CONTAMINATED").write_text("\n".join(changed))  # no further container
            (STATE / "prepared.json").unlink(missing_ok=True)  # the next prepare() rebuilds it
            raise RuntimeError(f"the shared base was written to through a hard link: {changed[:5]}")


class _Containers:
    def __init__(self, client: Client):
        self.client = client

    def create(self, image: str, name: str = "", **_) -> Container:
        return Container(self.client, image, name)


class Client:
    def __init__(self):
        self.api = _Api()
        self.containers = _Containers(self)

    def ping(self) -> bool:
        return True


class _DockerModule:
    @staticmethod
    def from_env() -> Client:
        return Client()


def install() -> None:
    """Point SWE-smith's harness (and gskill's, if importable) at this module."""
    import swesmith.harness.utils as hu
    import swesmith.profiles.base as pb
    from swesmith.profiles.base import RepoProfile

    hu.docker = _DockerModule()
    pb.docker = _DockerModule()
    RepoProfile.pull_image = lambda self: None
    try:
        import gskill.swe_harness as gh

        gh.docker = _DockerModule()
    except ImportError:
        pass


def exec_cli(argv: list[str]) -> int:
    """`docker exec -w <cwd> [-e K=V ...] <id> bash -lc <command>` for mini-swe-agent."""
    import sys

    if not argv or argv[0] != "exec":
        print(f"chroot_shim: unsupported command {argv[:1]}", file=sys.stderr)
        return 125
    cwd, extra, i = "/", {}, 1
    while i < len(argv) and argv[i].startswith("-"):
        if argv[i] == "-w":
            cwd = argv[i + 1]
        elif argv[i] == "-e":
            k, _, v = argv[i + 1].partition("=")
            extra[k] = v
        else:
            print(f"chroot_shim: unsupported option {argv[i]}", file=sys.stderr)
            return 125
        i += 2
    cid, rest = argv[i], argv[i + 1 :]
    home = STATE / "containers" / cid
    if not home.exists():
        print(f"Error response from daemon: No such container: {cid}", file=sys.stderr)
        return 1
    env = {**json.loads((STATE / "prepared.json").read_text())["env"], **extra}
    os.chroot(home.read_text())
    os.chdir(cwd)
    os.execve("/bin/bash", rest, env)  # the image's own bash, with the image's login files
    return 126  # not reached


if __name__ == "__main__":
    import sys

    raise SystemExit(exec_cli(sys.argv[1:]))
