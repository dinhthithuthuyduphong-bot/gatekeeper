"""Archive the raw evidence of every batch (agent trajectories, patches, the exact prompts given to
the agent, harness test logs) to the git branch `raw-archive` (docs/raw_archive.md, audit A52).

  python scripts/archive_raw.py            # archive every batch not yet archived, then push
  python scripts/archive_raw.py --dry-run  # build and check the archives, push nothing

Per batch <part> (a directory runs/<part>/): one deterministic archive/<stage>/<part>.tar.gz
(same content -> same bytes -> same SHA-256) holding runs/<part>/** and the harness logs of that
batch (logs/run_evaluation/<part>-<arm>[-...]/** and the harness's run-report file
<model>.<part>-<arm>[-...].json). archive/MANIFEST.json records, per batch: SHA-256, size, file
count, number of agent trajectories, and the SHA-256 of the matching results/pilot/<part>.json.

Safety, checked before anything is written (a failure stops the script):
  - no file may contain key material (PEM header with dashes, a service-account "private_key");
  - a batch whose skills include third-party text without a licence (XRepoSkill, E2) is WITHHELD
    from the public branch: only its local SHA-256 is recorded, never its content;
  - every archive must stay below GitHub's 100 MB file limit (95 MB margin).
The branch is written with git plumbing (separate index, no checkout): the working tree used by
running experiments is never touched, and no git hook runs, hence the explicit checks above."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import os
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

BRANCH = "raw-archive"
MAX_BYTES = 95 * 1024 * 1024  # GitHub rejects files > 100 MB
SECRET = ["-" * 5 + "BEGIN " + "PRIVATE KEY" + "-" * 5, '"private' + '_key":']
WITHHELD_SKILLS = {"xreposkill"}  # third-party text without a licence (docs/preregistration_e2.md)
STAGING = Path(os.environ.get("ARCHIVE_STAGING", "/tmp/gatekeeper-raw-archive"))


def git(*args: str, env: dict | None = None, inp: bytes | None = None) -> str:
    return subprocess.run(
        ["git", *args], check=True, capture_output=True, input=inp, env=env
    ).stdout.decode()


def stage_of(part: str) -> str:
    return part.rsplit("-p", 1)[0] if part.rsplit("-p", 1)[-1].isdigit() else part


def batch_files(part: str) -> list[Path]:
    """runs/<part>/** plus this batch's harness logs. Log directories are matched to the LONGEST
    arm name first (arm 'control-none' must not take 'control-none-seed1')."""
    root = Path("runs") / part
    arms = sorted((p.name for p in root.iterdir() if p.is_dir()), key=len, reverse=True)
    files = sorted(p for p in root.rglob("*") if p.is_file())
    logs = Path("logs/run_evaluation")
    taken: set[str] = set()
    for arm in arms:
        prefix = f"{part}-{arm}"
        for d in sorted(logs.glob(f"{prefix}*")) if logs.is_dir() else []:
            if d.name in taken or not (d.name == prefix or d.name.startswith(prefix + "-")):
                continue
            taken.add(d.name)
            files += sorted(p for p in d.rglob("*") if p.is_file())
    for run_id in sorted(taken):  # the harness's run report, written in the repository root
        files += sorted(Path(".").glob(f"*.{run_id}.json"))
    return files


def deterministic_tar(files: list[Path]) -> bytes:
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode="w", format=tarfile.PAX_FORMAT) as tar:
        for f in files:
            info = tarfile.TarInfo(str(f))
            data = f.read_bytes()
            info.size, info.mtime, info.mode = len(data), 0, 0o644
            info.uid = info.gid = 0
            info.uname = info.gname = ""
            tar.addfile(info, io.BytesIO(data))
    out = io.BytesIO()
    with gzip.GzipFile(fileobj=out, mode="wb", mtime=0, compresslevel=9) as gz:
        gz.write(raw.getvalue())
    return out.getvalue()


def check_secrets(files: list[Path]) -> None:
    for f in files:
        data = f.read_bytes()
        for pat in SECRET:
            if pat.encode() in data:
                raise SystemExit(f"key material in {f}: nothing archived")


def skills_of(part: str) -> set[str]:
    res, _ = result_of(part)
    if res is not None:
        return set(json.loads(res.read_text()).get("skills", {}))
    return {p.name for p in (Path("runs") / part).iterdir() if p.is_dir()} - {"none"}


def result_of(part: str) -> tuple[Path | None, str]:
    """The batch's result file and its status: valid (results/pilot/), invalid (kept for the
    record in results/pilot/invalid/, excluded from analyses), or none (stopped before writing)."""
    res = Path("results/pilot") / f"{part}.json"
    if res.exists():
        return res, "valid"
    inv = sorted(Path("results/pilot/invalid").rglob(f"{part}.json"))
    if inv:
        return inv[0], "invalid"
    ab = Path("results/pilot/aborted") / f"{part}.json"  # cut off mid-batch; spend recorded (A53)
    return (ab, "aborted") if ab.exists() else (None, "no result file")


def is_running(part: str) -> bool:
    """A batch is running while a run_pilot.py process carries its name (no age threshold)."""
    out = subprocess.run(["pgrep", "-af", "run_pilot.py"], capture_output=True, text=True).stdout
    return any(f"--name {part} " in line + " " for line in out.splitlines())


def load_manifest() -> dict:
    try:
        git("fetch", "-q", "origin", BRANCH)
        return json.loads(git("show", f"origin/{BRANCH}:archive/MANIFEST.json"))
    except subprocess.CalledProcessError:
        return {"_comment": "see docs/raw_archive.md", "batches": {}}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument(
        "--redacted-ok",
        action="store_true",
        help="third-party text was already replaced by scripts/redact_third_party.py (which "
        "exits 1 on any leak, and the caller then deletes the raw files): archive such batches",
    )
    a = ap.parse_args()
    manifest = load_manifest()
    done = manifest["batches"]
    parts = sorted(p.name for p in Path("runs").iterdir() if p.is_dir())
    new: dict[str, bytes] = {}
    changed = False
    for part in parts:
        res, status = result_of(part)
        if res is None and is_running(part):  # still running: archived once it has finished
            continue
        files = batch_files(part)
        check_secrets(files)
        blob = deterministic_tar(files)
        sha = hashlib.sha256(blob).hexdigest()
        res_sha = hashlib.sha256(res.read_bytes()).hexdigest() if res else None
        if part in done and done[part].get("sha256") == sha:
            if done[part].get("result_sha256") != res_sha:  # result file updated after archiving
                done[part]["result_sha256"] = res_sha
                changed = True
            continue
        n_traj = sum(1 for f in files if f.name.endswith(".traj.json"))
        entry = {
            "sha256": sha,
            "bytes": len(blob),
            "n_files": len(files),
            "n_trajectories": n_traj,
            "result_file": str(res) if res else None,
            "result_status": status,
            "result_sha256": res_sha,
        }
        if skills_of(part) & WITHHELD_SKILLS and a.redacted_ok:
            entry["redacted"] = "XRepoSkill text replaced by <<XREPOSKILL_...>> markers (A55)"
            entry["path"] = f"archive/{stage_of(part)}/{part}.tar.gz"
            new[entry["path"]] = blob
        elif skills_of(part) & WITHHELD_SKILLS:
            entry["withheld"] = (
                "third-party text without a licence: content kept off the public branch"
            )
        elif len(blob) > MAX_BYTES:
            raise SystemExit(f"{part}: archive {len(blob)} bytes > {MAX_BYTES}; split needed")
        else:
            entry["path"] = f"archive/{stage_of(part)}/{part}.tar.gz"
            new[entry["path"]] = blob
        done[part] = entry
        changed = True
    print(f"{len(new)} new or changed archives; {len(done)} batches in the manifest")
    if a.dry_run or not changed:
        return 0
    # write the branch with plumbing: a temporary index and a staging work tree
    env = dict(os.environ)
    with tempfile.TemporaryDirectory() as tmp:
        env["GIT_INDEX_FILE"] = str(Path(tmp) / "index")
        try:
            parent = git("rev-parse", f"origin/{BRANCH}").strip()
            git("read-tree", parent, env=env)
        except subprocess.CalledProcessError:
            parent = None
        for path, blob in sorted(new.items()):
            oid = git("hash-object", "-w", "--stdin", inp=blob).strip()
            git("update-index", "--add", "--cacheinfo", f"100644,{oid},{path}", env=env)
        mf = json.dumps(manifest, indent=1, sort_keys=True).encode() + b"\n"
        oid = git("hash-object", "-w", "--stdin", inp=mf).strip()
        git("update-index", "--add", "--cacheinfo", f"100644,{oid},archive/MANIFEST.json", env=env)
        tree = git("write-tree", env=env).strip()
        msg = (
            f"Raw evidence: {len(new)} new batch archive(s)\n\n"
            "scripts/archive_raw.py; docs/raw_archive.md"
        )
        args = ["commit-tree", tree, "-m", msg] + (["-p", parent] if parent else [])
        commit = git(*args).strip()
    git("push", "-q", "origin", f"{commit}:refs/heads/{BRANCH}")
    print(f"pushed {commit[:7]} to {BRANCH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
