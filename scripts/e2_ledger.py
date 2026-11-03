"""Shared budget ledger for jobs that spend money in parallel (E2 on GitHub Actions; audit A60).

Each parallel job (key = "<run id>-k<shard>") keeps ONE file ledger/<key>.json on the branch
`<branch>` with {"spent": USD recorded so far, "reserved": USD held for the call in progress}.
Before a paid call a job RESERVES the call's worst case (arms x tasks x per-run cost limit, the
same bound the batch driver uses); after the call it SETTLES (actual spend, reservation released).
Hence at every moment  sum(spent) + sum(reserved) <= cap,  and since a call can never cost more
than its reservation, total spending can never exceed the cap.

Writes are compare-and-swap: a commit on top of the ledger tip that was read, pushed without
force; git refuses a push whose parent is no longer the tip, and the job re-reads and retries.

  python scripts/e2_ledger.py reserve --branch e2-ledger --key R-k3 --usd 2 --cap 44.5546 \
      --deadline-epoch 1793760000
      exit 0: reserved; exit 3: budget exhausted (spent + usd > cap: stop for good)
      waits (re-reads every --wait-s seconds) while only OTHER jobs' reservations block it
  python scripts/e2_ledger.py settle --branch e2-ledger --key R-k3 --spent 1.234 [--keep-reserved]
  python scripts/e2_ledger.py total --branch e2-ledger
"""

from __future__ import annotations

import argparse
import json
import os
import random
import subprocess
import tempfile
import time
from pathlib import Path

EXHAUSTED = 3


def _git(*args: str, env: dict | None = None, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], capture_output=True, text=True, env=env, check=check)


def read(branch: str, remote: str = "origin") -> tuple[str | None, dict[str, dict]]:
    """(tip commit or None if the branch does not exist yet, {key: entry})."""
    r = _git("fetch", "-q", remote, f"+refs/heads/{branch}:refs/ledger/{branch}", check=False)
    if r.returncode != 0:
        if "couldn't find remote ref" in (r.stderr or "") or "not found" in (r.stderr or ""):
            return None, {}
        raise SystemExit(f"ledger fetch failed: {r.stderr.strip()}")
    tip = _git("rev-parse", f"refs/ledger/{branch}").stdout.strip()
    names = _git("ls-tree", "-r", "--name-only", tip, "ledger/").stdout.split()
    out = {}
    for n in names:
        out[Path(n).stem] = json.loads(_git("show", f"{tip}:{n}").stdout)
    return tip, out


def totals(entries: dict[str, dict], exclude: str | None = None) -> tuple[float, float]:
    spent = sum(float(e.get("spent", 0.0)) for e in entries.values())
    reserved = sum(float(e.get("reserved", 0.0)) for k, e in entries.items() if k != exclude)
    return spent, reserved


def write(
    branch: str, tip: str | None, key: str, entry: dict, msg: str, remote: str = "origin"
) -> bool:
    """One compare-and-swap attempt: True if pushed, False if the tip moved (caller retries)."""
    with tempfile.TemporaryDirectory() as d:
        env = dict(os.environ, GIT_INDEX_FILE=str(Path(d) / "index"))
        if tip:
            _git("read-tree", tip, env=env)
        blob = subprocess.run(
            ["git", "hash-object", "-w", "--stdin"],
            input=json.dumps(entry, sort_keys=True) + "\n",
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        _git("update-index", "--add", "--cacheinfo", f"100644,{blob},ledger/{key}.json", env=env)
        tree = _git("write-tree", env=env).stdout.strip()
    parent = ["-p", tip] if tip else []
    commit = _git(
        "-c",
        "user.name=github-actions[bot]",
        "-c",
        "user.email=41898282+github-actions[bot]@users.noreply.github.com",
        "commit-tree",
        tree,
        *parent,
        "-m",
        msg,
    ).stdout.strip()
    r = _git("push", "-q", remote, f"{commit}:refs/heads/{branch}", check=False)
    return r.returncode == 0


def reserve(branch: str, key: str, usd: float, cap: float, deadline: float, wait_s: float) -> int:
    while True:
        tip, entries = read(branch)
        spent, reserved_others = totals(entries, exclude=key)
        mine = entries.get(key, {"spent": 0.0, "reserved": 0.0})
        if float(mine.get("reserved", 0.0)) > 0:
            raise SystemExit(f"{key} already holds a reservation: settle it first")
        if spent + usd > cap:
            print(f"[ledger] exhausted: spent {spent:.4f} + {usd:.2f} > cap {cap:.4f}", flush=True)
            return EXHAUSTED
        if spent + reserved_others + usd <= cap:
            entry = {"spent": float(mine.get("spent", 0.0)), "reserved": usd}
            if write(branch, tip, key, entry, f"reserve {key} {usd}"):
                print(
                    f"[ledger] reserved {usd:.2f}: spent {spent:.4f}, "
                    f"others hold {reserved_others:.2f}"
                )
                return 0
            time.sleep(random.uniform(1, 5))  # tip moved: re-read
            continue
        if time.time() + wait_s > deadline:
            print("[ledger] no time left to wait for other jobs' reservations", flush=True)
            return EXHAUSTED
        time.sleep(wait_s)  # only other jobs' reservations block: wait for them to settle


def settle(branch: str, key: str, spent: float, keep_reserved: bool) -> None:
    for _ in range(60):
        tip, entries = read(branch)
        mine = entries.get(key, {"spent": 0.0, "reserved": 0.0})
        if spent + 1e-9 < float(mine.get("spent", 0.0)):
            raise SystemExit(f"{key}: recorded spend would decrease ({mine['spent']} -> {spent})")
        entry = {
            "spent": spent,
            "reserved": float(mine.get("reserved", 0.0)) if keep_reserved else 0.0,
        }
        if write(branch, tip, key, entry, f"settle {key} {spent}"):
            print(f"[ledger] settled {key}: spent {spent:.4f}, reserved {entry['reserved']:.2f}")
            return
        time.sleep(random.uniform(1, 5))
    raise SystemExit("ledger: could not settle after 60 attempts")


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("reserve")
    r.add_argument("--branch", required=True)
    r.add_argument("--key", required=True)
    r.add_argument("--usd", required=True, type=float)
    r.add_argument("--cap", required=True, type=float)
    r.add_argument("--deadline-epoch", required=True, type=float)
    r.add_argument("--wait-s", required=True, type=float)
    s = sub.add_parser("settle")
    s.add_argument("--branch", required=True)
    s.add_argument("--key", required=True)
    s.add_argument("--spent", required=True, type=float)
    s.add_argument("--keep-reserved", action="store_true")
    t = sub.add_parser("total")
    t.add_argument("--branch", required=True)
    a = ap.parse_args()
    if a.cmd == "reserve":
        return reserve(a.branch, a.key, a.usd, a.cap, a.deadline_epoch, a.wait_s)
    if a.cmd == "settle":
        settle(a.branch, a.key, a.spent, a.keep_reserved)
        return 0
    _, entries = read(a.branch)
    spent, reserved = totals(entries)
    print(
        json.dumps({"spent": round(spent, 4), "reserved": round(reserved, 4), "jobs": len(entries)})
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
