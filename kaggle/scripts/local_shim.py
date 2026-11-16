"""Plan v3, item C: run SWE-smith's own grading (and gskill's agent) with no container at all.

For a pure-Python repository the task image is: a clone of SWE-smith's mirror at /testbed (every
task is a branch of three commits: "Initial commit", "Bug Patch", "Remove F2P Tests"), and a conda
environment `testbed` with the repository installed in editable mode. This module rebuilds both on
the host and gives SWE-smith's harness (used verbatim) the handful of Docker SDK calls it uses,
executed as plain processes:

  /testbed                       the current container's own copy of the clone, as a real
                                 directory (the copies of other containers are parked aside and
                                 swapped in by rename before each of their commands)
  /opt/miniconda3/bin/activate   a stub: `conda activate testbed` puts the rebuilt environment
                                 (same Python minor version, same package versions as the image)
                                 first on PATH
  /opt/mirror.git                the bare mirror the clone fetches its task branches from

What differs from Docker, by construction (stated in the registration): no isolation from the
host, no memory limit, one container's /testbed at a time (runs are sequential), Python and the
packages are rebuilt from the image's package list instead of copied. Whether grading is the same
is not assumed: gate C1 re-scores patches whose Docker grade is on record and compares.

  import local_shim; local_shim.prepare(...); local_shim.install()
Needs write access to /, /opt and /tmp (root); `probe()` says whether that holds.
"""

from __future__ import annotations

import io
import json
import os
import shlex
import shutil
import signal
import subprocess
import tarfile
import tempfile
import uuid
from pathlib import Path

WORKDIR = Path("/testbed")
MIRROR = Path("/opt/mirror.git")
ACTIVATE = Path("/opt/miniconda3/bin/activate")
STATE = Path(os.environ.get("LOCAL_SHIM_DIR", "/opt/local_shim"))  # base clone, environment
SKIP = {"pip", "jinja2"}  # pip comes with the environment; the repository is installed editable


def probe() -> dict:
    def writable(p: str) -> bool:
        return os.access(p, os.W_OK)

    return {
        "uid": os.getuid(),
        "root_writable": writable("/"),
        "opt_writable": writable("/opt") if Path("/opt").exists() else writable("/"),
        "testbed_exists": WORKDIR.exists() or WORKDIR.is_symlink(),
        "same_filesystem": os.stat("/").st_dev == os.stat("/opt").st_dev
        if Path("/opt").exists()
        else None,
        "git": shutil.which("git"),
        "uv": shutil.which("uv"),
        "patch": shutil.which("patch"),
    }


def _sh(cmd: str, cwd: Path | None = None, check: bool = True) -> str:
    r = subprocess.run(["bash", "-c", cmd], cwd=cwd, capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError(f"`{cmd[:120]}` failed: {(r.stdout + r.stderr)[-600:]}")
    return r.stdout + r.stderr


def _swap(home: Path) -> None:
    """Make /testbed the directory whose parking place is `home` (a rename each way). A link
    would not do: Python and git resolve it, so an editable install and the agent would see the
    parked path instead of /testbed."""
    mark = STATE / "active"
    cur = Path(mark.read_text()) if mark.exists() else None
    if cur == home:
        return
    if cur is not None and WORKDIR.exists():
        shutil.move(str(WORKDIR), str(cur))
    if WORKDIR.exists() or WORKDIR.is_symlink():
        raise RuntimeError("/testbed exists and was not put there by this module")
    shutil.move(str(home), str(WORKDIR))
    mark.write_text(str(home))


def prepare(
    mirror_url: str, python: str, packages: dict[str, str], install_cmds: list[str]
) -> dict:
    """Build what is missing: the bare mirror, the base clone, the environment, the activate
    stub. `packages` is the image's own list (name -> version); `install_cmds` the profile's.
    Safe to call again after the machine was replaced while STATE survived (or the reverse)."""
    STATE.mkdir(parents=True, exist_ok=True)
    mark = STATE / "active"
    if mark.exists() and not WORKDIR.exists():  # /testbed went away with the old machine
        lost = Path(mark.read_text())
        mark.unlink()
        if lost == STATE / "testbed":
            (STATE / "prepared.json").unlink(missing_ok=True)  # the base clone must be rebuilt
    if (WORKDIR.exists() or WORKDIR.is_symlink()) and not mark.exists():
        raise RuntimeError("/testbed exists and was not put there by this module")
    done = STATE / "prepared.json"
    if done.exists() and ACTIVATE.exists():
        _swap(STATE / "testbed")
        return json.loads(done.read_text())
    MIRROR.parent.mkdir(parents=True, exist_ok=True)
    if not MIRROR.exists():
        _sh(f"git clone -q --mirror {shlex.quote(mirror_url)} {MIRROR}")
    base = STATE / "testbed"
    if not base.exists() and not mark.exists():
        _sh(f"git clone -q -o origin {MIRROR} {base}")
    _swap(base)
    env = STATE / "env"
    if not env.exists():
        _sh(f"uv venv -q --python {python} {env}")
        reqs = STATE / "requirements.txt"
        reqs.write_text(
            "".join(f"{k}=={v}\n" for k, v in sorted(packages.items()) if k not in SKIP)
        )
        _sh(f"uv pip install -q --python {env}/bin/python pip=={packages['pip']} -r {reqs}")
    ACTIVATE.parent.mkdir(parents=True, exist_ok=True)
    ACTIVATE.write_text(
        "# stub written by kaggle/scripts/local_shim.py\n"
        f'conda() {{ if [ "$1" = activate ] && [ "$2" = testbed ]; then '
        f'export VIRTUAL_ENV={env} PATH="{env}/bin:$PATH"; fi; }}\n'
    )
    for cmd in install_cmds:  # the profile's own install commands, in /testbed
        _sh(f"source {ACTIVATE}; conda activate testbed; {cmd}", cwd=WORKDIR)
    info = {
        "python": _sh(f"{env}/bin/python -V").strip(),
        "packages": len(packages),
        "branches": int(_sh(f"git -C {WORKDIR} branch -r | wc -l").strip()),
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
        _swap(STATE / "testbed")  # the base clone is at /testbed; copy it to a parking place
        self.testbed = Path(tempfile.mkdtemp(prefix="testbed_", dir=STATE))
        self.testbed.rmdir()
        shutil.copytree(WORKDIR, self.testbed, symlinks=True)
        Container.by_id[self.id] = self

    def start(self) -> None:
        pass

    def _popen(self, cmd, workdir, environment) -> subprocess.Popen:
        _swap(self.testbed)  # every command of this container sees its own /testbed
        argv = shlex.split(cmd) if isinstance(cmd, str) else list(cmd)
        env = {**os.environ, **(environment or {})}
        for k in ("VIRTUAL_ENV", "PYTHONPATH", "PYTHONHOME"):  # the caller's own environment
            env.pop(k, None)
        return subprocess.Popen(
            argv,
            cwd=workdir or "/",
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )

    def exec_run(self, cmd, workdir=None, user=None, environment=None, detach=False, **_):
        argv = shlex.split(cmd) if isinstance(cmd, str) else list(cmd)
        if argv[:2] == ["kill", "-TERM"]:  # the harness kills a timed-out test run by its pid
            try:
                os.killpg(int(argv[2]), signal.SIGKILL)
            except (ProcessLookupError, ValueError, IndexError):
                pass
            return ExecResult(0, b"")
        try:
            p = self._popen(cmd, workdir, environment)
        except FileNotFoundError as e:
            return ExecResult(127, str(e).encode())
        out, _ = p.communicate()
        return ExecResult(p.returncode, out)

    def put_archive(self, path: str, data: bytes) -> bool:
        _swap(self.testbed)
        Path(path).mkdir(parents=True, exist_ok=True)
        with tarfile.open(fileobj=io.BytesIO(data)) as tar:
            tar.extractall(path, filter="tar")
        return True

    def stop(self, timeout: int = 15) -> None:
        pass

    def remove(self, force: bool = True) -> None:
        _swap(STATE / "testbed")  # parks this container's copy, if it was the active one
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

    def ping(self) -> bool:
        return True


class _DockerModule:
    @staticmethod
    def from_env() -> Client:
        return Client()


def install() -> None:
    """Point SWE-smith's harness at this module. Call once, after prepare()."""
    import swesmith.harness.utils as hu
    import swesmith.profiles.base as pb
    from swesmith.profiles.base import RepoProfile

    hu.docker = _DockerModule()
    pb.docker = _DockerModule()
    RepoProfile.pull_image = lambda self: None
