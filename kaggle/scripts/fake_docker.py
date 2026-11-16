#!/usr/bin/env python3
"""Stands in for the `docker` command line that mini-swe-agent's DockerEnvironment calls
(MSWEA_DOCKER_EXECUTABLE points here), so gskill's agent runs unchanged with no container.

Only the one form the agent uses is accepted:
    docker exec -w <cwd> [-e K=V ...] <container id> bash -lc <command>
The command runs as a plain process: /testbed is this container's own copy (local_shim), the
environment is exactly local_shim.SHELL_ENV plus the -e pairs (nothing of the caller's, so no API
key is visible to the agent), and `bash -c` replaces `bash -lc` (the image's login files only
activate the environment, which SHELL_ENV already describes).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import local_shim  # noqa: E402


def main(argv: list[str]) -> int:
    if not argv or argv[0] != "exec":
        print(f"fake_docker: unsupported command {argv[:1]}", file=sys.stderr)
        return 125
    cwd, env, i = "/", dict(local_shim.SHELL_ENV), 1
    while i < len(argv) and argv[i].startswith("-"):
        if argv[i] == "-w":
            cwd = argv[i + 1]
        elif argv[i] == "-e":
            k, _, v = argv[i + 1].partition("=")
            env[k] = v
        else:
            print(f"fake_docker: unsupported option {argv[i]}", file=sys.stderr)
            return 125
        i += 2
    cid, rest = argv[i], argv[i + 1 :]
    home = local_shim.STATE / "containers" / cid
    if not home.exists():
        print(f"Error response from daemon: No such container: {cid}", file=sys.stderr)
        return 1
    if rest[:2] != ["bash", "-lc"] or len(rest) != 3:
        print(f"fake_docker: unsupported exec form {rest[:2]}", file=sys.stderr)
        return 125
    local_shim._swap(Path(home.read_text()))
    os.chdir(cwd)
    os.execve("/bin/bash", ["bash", "-c", rest[2]], env)
    return 126  # not reached


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
