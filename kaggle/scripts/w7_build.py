"""Section 45 (W7-b): the saved trajectories in the layout XRepoSkill reads (0 USD).

  python kaggle/scripts/w7_build.py --pool A --out kaggle/data/w7_poolA.tar.gz
  python kaggle/scripts/w7_build.py --pool B --out kaggle/data/w7_poolB.tar.gz

XRepoSkill (commit 26fd703) reads `<trajs>/<submission>/trajs/<iid>/<iid>.traj.json` and
`<evals>/<submission>/per_instance_details.json` (src/xreposkill/ingest.py). Two adaptations, both
of format only (docs/reviewer_fidelity.md):
  1. Instance ids. `repo_from_instance_id` follows the SWE-bench convention `<org>__<name>-<num>`;
     a SWE-smith id has no "-", so every task would become its own repository. Each of the 34
     tasks gets `pallets__jinja-<k>`, k = 1..34 in the order of its SWE-smith id; the map is
     written to the archive.
  2. Actions. XRepoSkill takes a command from an assistant turn's `tool_calls` and an observation
     from a `tool` turn (mini-SWE-agent 2.x). Our harness is the text format: one ```bash block
     per assistant turn, observations as user turns. The command is the single block matched by
     CMD (checked against the harness on every saved turn: a turn with exactly one block is
     followed by an observation, any other turn by the format error); the observation that
     answers it becomes a `tool` turn. Turns, text and order are unchanged.
Resolved = the benchmark's own scorer S, as everywhere in the paper.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import re
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CMD = re.compile(r"```bash\s*\n(.*?)\n```", re.S)
FLASH, LITE = "gemini-3.8-flash", "gemini-3.1-flash-lite"
# (submission, result files, model): the agent runs of each pool, no skill, Jinja test tasks
# without a problem statement (section 45)
POOLS = {
    "A": [
        ("w7a__flash_s41", ["s34_none_pilot", "s34_none_rest"], FLASH),
        ("w7a__lite_s41", ["s29_none"], LITE),
        ("w7a__lite_s51", ["s33_ship_none"], LITE),
    ],
    "B": [
        ("w7b__flash_s41", ["s34_lfnone"], FLASH),
        ("w7b__lite_s41", ["s30_none"], LITE),
        ("w7b__lite_s51", ["s33_lf_none"], LITE),
    ],
}
TASKS_FROM = ["s34_none_pilot", "s34_none_rest"]  # the 34 tasks: the agent's registered pool


def task_ids(results: Path) -> list[str]:
    ids = set()
    for stem in TASKS_FROM:
        ids |= {
            r["instance_id"] for r in json.loads((results / f"{stem}.json").read_text())["runs"]
        }
    return sorted(ids)


def to_tool_format(messages: list[dict]) -> list[dict]:
    """Text-format mini-SWE-agent messages -> tool-call format (see module docstring)."""
    out = []
    pending = False  # the previous assistant turn issued a command
    for k, m in enumerate(messages):
        role, content = m.get("role"), m.get("content")
        content = content if isinstance(content, str) else json.dumps(content)
        if role == "assistant":
            blocks = CMD.findall(content)
            mm = {"role": "assistant", "content": content}
            if len(blocks) == 1:
                mm["tool_calls"] = [
                    {
                        "id": f"call_{k}",
                        "type": "function",
                        "function": {
                            "name": "bash",
                            "arguments": json.dumps({"command": blocks[0]}),
                        },
                    }
                ]
            pending = len(blocks) == 1
            out.append(mm)
        elif role == "user" and pending:
            if content.strip():  # the empty closing message after the last command is dropped
                out.append({"role": "tool", "content": content, "tool_call_id": f"call_{k - 1}"})
            pending = False
        else:
            out.append({"role": role, "content": content})
    return out


def build(pool: str, results: Path) -> tuple[dict[str, bytes], dict]:
    ids = task_ids(results)
    idmap = {iid: f"pallets__jinja-{k}" for k, iid in enumerate(ids, start=1)}
    files: dict[str, bytes] = {}
    summary = {"pool": pool, "tasks": len(ids), "submissions": {}}
    subs = []
    for sub, stems, model in POOLS[pool]:
        runs, traces = {}, {}
        for stem in stems:
            for r in json.loads((results / f"{stem}.json").read_text())["runs"]:
                if r["instance_id"] in idmap and "infra_error" not in r:
                    runs[r["instance_id"]] = r
            for line in gzip.open(results / f"{stem}.traces.jsonl.gz", "rt"):
                t = json.loads(line)
                if t["instance_id"] in idmap:
                    traces[t["instance_id"]] = t
        missing = sorted(set(ids) - (set(runs) & set(traces)))
        if missing:
            raise SystemExit(f"{sub}: {len(missing)} of the 34 tasks have no run or trace")
        details = {}
        for iid in ids:
            new = idmap[iid]
            traj = {
                "instance_id": new,
                "trajectory_format": "mini-swe-agent-1.1",
                "info": {"config": {"model": {"model_name": model}}, "source_instance_id": iid},
                "messages": to_tool_format(traces[iid]["messages"]),
            }
            files[f"trajs/{sub}/trajs/{new}/{new}.traj.json"] = json.dumps(traj).encode()
            details[new] = {"resolved": bool((runs[iid].get("S") or {}).get("resolved"))}
        files[f"evals/{sub}/per_instance_details.json"] = json.dumps(details, indent=1).encode()
        summary["submissions"][sub] = {
            "model": model,
            "sources": stems,
            "resolved": sum(v["resolved"] for v in details.values()),
        }
        subs.append(sub)
    files["submissions.txt"] = ("\n".join(subs) + "\n").encode()
    files["id_map.json"] = json.dumps(idmap, indent=1).encode()
    return files, summary


def write_tar(files: dict[str, bytes], out: Path) -> str:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w", format=tarfile.PAX_FORMAT) as tf:
        for name in sorted(files):  # deterministic: same content -> same bytes
            data = files[name]
            info = tarfile.TarInfo(name)
            info.size, info.mtime, info.mode = len(data), 0, 0o644
            tf.addfile(info, io.BytesIO(data))
    raw = buf.getvalue()
    with open(out, "wb") as f, gzip.GzipFile(filename="", fileobj=f, mode="wb", mtime=0) as fh:
        fh.write(raw)  # no file name in the gzip header: the bytes do not depend on the path
    return hashlib.sha256(out.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pool", required=True, choices=sorted(POOLS))
    ap.add_argument("--results", type=Path, default=ROOT / "results")
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    files, summary = build(a.pool, a.results)
    summary["sha256"] = write_tar(files, a.out)
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
