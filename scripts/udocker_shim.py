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
import tarfile
import tempfile
import uuid
from pathlib import Path

UDOCKER = shlex.split(os.environ.get("UDOCKER_CMD", "udocker --allow-root"))
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


def pull(image: str) -> None:
    if _u("inspect", image).returncode != 0:
        r = _u("pull", image)
        if r.returncode != 0:
            raise RuntimeError(f"udocker pull {image} failed: {r.stderr.decode()[-300:]}")


def base_container(image: str) -> str:
    """One unpacked container per image, reused (unpacking takes about a minute and 3 GB)."""
    if image not in _bases:
        name = "base_" + "".join(c if c.isalnum() else "_" for c in image)[-60:]
        if _u("inspect", "-p", name).returncode != 0:
            pull(image)
            r = _u("create", f"--name={name}", image)
            if r.returncode != 0:
                raise RuntimeError(f"udocker create failed: {r.stderr.decode()[-300:]}")
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
