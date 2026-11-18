"""Section 46 (X2'): the paper's agent run through Kaggle's chroot layer instead of Docker, with
the same model on Vertex. 0 lines of the agent or the scorers change.

Runs scripts/f1_probe.py of this repository (the script of every paid agent run on main) unchanged,
after pointing mini-swe-agent's `docker` command (MSWEA_DOCKER_EXECUTABLE) and SWE-smith's and
gskill's Docker SDK at chroot_shim (kaggle/scripts/chroot_shim.py of a pinned commit, copied into
--shim-dir with its dependency udocker_shim.py). Needs root (chroot, mknod).

  sudo -E PYTHONPATH=<gepa>/src/gepa/gskill:<repo>/scripts <venv>/bin/python \
      scripts/x2_chroot_probe.py --shim-dir /tmp/shim -- <arguments of f1_probe.py>
"""

from __future__ import annotations

import argparse
import gzip
import json
import os
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--shim-dir", required=True, type=Path)
    ap.add_argument("rest", nargs=argparse.REMAINDER)
    a = ap.parse_args()
    rest = a.rest[1:] if a.rest[:1] == ["--"] else a.rest
    sys.path.insert(0, str(a.shim_dir))
    os.environ["MSWEA_DOCKER_EXECUTABLE"] = str(
        a.shim_dir / "chroot_shim.py"
    )  # before minisweagent

    from swesmith.profiles import registry

    rows = Path(rest[rest.index("--rows") + 1])
    raw = rows.read_bytes()
    text = (gzip.decompress(raw) if rows.name.endswith(".gz") else raw).decode("utf-8")
    rp = registry.get_from_inst(json.loads(next(x for x in text.splitlines() if x.strip())))
    rp._cache_repo_private = False  # public mirror (f0_scorer_check.assume_public)
    import chroot_shim

    info = chroot_shim.prepare(rp.image_name, f"https://github.com/{rp.mirror_name}")
    print(json.dumps({"chroot_base": {k: v for k, v in info.items() if k != "env"}}), flush=True)
    import gskill.swe_harness  # noqa: F401 - must be imported before install() patches it

    chroot_shim.install()
    import f1_probe

    sys.argv = ["f1_probe.py", *rest]
    return f1_probe.main()


if __name__ == "__main__":
    raise SystemExit(main())
