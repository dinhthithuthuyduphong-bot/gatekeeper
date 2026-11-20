"""Section 40, C4: the four arms of one agent model, in chunks of tasks, resumable.

Arms (each on the same tasks, in gskill's order): none, skill (environment as shipped);
lf_none, lf_skill (single-commit environment: f1_probe.py --leak-free). For chunk 0, 1, ... of
--chunk tasks, the four arms run one after the other, so the runs of a pair are minutes apart
(model drift). Every (arm, chunk) is one unchanged call of c3_agent.py -> f1_probe.py and one
result file; a finished file is never run again; a chunk with an infrastructure error or a
crashed agent is set aside (.bad) and the driver stops (no retry loop on a refused quota).

Spend = the cost the endpoint reports (c3_agent.py's *.cost.json). The driver starts no new
chunk once this session's spend has reached --day-cap or the total (earlier sessions included)
has reached --total-cap, or after --hours of wall clock. A cap can be passed by at most the cost
of one chunk of one arm (each task is itself limited by --cost-limit).

  python c4_driver.py --tag haiku --model openai/anthropic/claude-haiku-5-5 --rows rows.jsonl \
      --skills-file skill.txt --registry registry.json --isolation chroot \
      [--extra-rows rows_extra36.jsonl] [--arms lf_none] \
      --gskill-yaml mini.yaml --outdir out --prev <dirs of earlier sessions> --chunk 10 \
      --seed 41 --cost-limit 0.30 --day-cap 2.0 --total-cap 10.0 --hours 8
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ARMS = {  # arm -> (uses the skill, single-commit environment)
    "none": (False, False),
    "skill": (True, False),
    "lf_none": (False, True),
    "lf_skill": (True, True),
}


def complete(f: Path, n: int) -> bool:
    """A chunk result that counts: all its tasks ran, none crashed or hit the infrastructure."""
    try:
        d = json.loads(f.read_text())
    except (OSError, ValueError):
        return False
    runs = d.get("runs", [])
    # notes 40-13, 40-14: second attempt of a chunk, its crashed or infra runs listed
    kept = set(d.get("accepted_with_crashes") or []) | set(d.get("accepted_with_infra") or [])
    return (
        len(runs) == n
        and not d.get("stopped")
        and not any(
            (r.get("infra_error") or r.get("crashed")) and r["instance_id"] not in kept
            for r in runs
        )
    )


def spent(folder: Path, tag: str) -> float:
    """Spend of one model: its own cost files only (K28), earlier attempts included."""
    return sum(
        json.loads(f.read_text()).get("endpoint_usd", 0.0)
        for f in folder.glob(f"{tag}_*.cost.json")
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    for k in ("--tag", "--model", "--rows", "--skills-file", "--registry"):
        ap.add_argument(k, required=True)
    ap.add_argument("--isolation", required=True, choices=["local", "chroot"])
    ap.add_argument("--packages", help="local isolation only")
    ap.add_argument(
        "--extra-rows",
        help="note 40-5 option B: rows of section 35's 36 tasks (split 'extra'), run after the "
        "test "
        "tasks in their own chunks",
    )
    ap.add_argument("--arms", nargs="+", choices=list(ARMS), default=list(ARMS))
    ap.add_argument(
        "--chunk-cap",
        type=float,
        help="f1_probe.py's own cap for one chunk (it stops before a task when spent + cost_limit "
        "would pass it); default: chunk size x cost_limit + cost_limit",
    )
    ap.add_argument("--gskill-yaml", required=True)
    ap.add_argument("--outdir", required=True, type=Path)
    ap.add_argument("--prev", nargs="*", default=[], type=Path)
    ap.add_argument("--chunk", required=True, type=int)
    ap.add_argument("--seed", required=True, type=int)
    ap.add_argument("--cost-limit", required=True, type=float)
    ap.add_argument("--day-cap", required=True, type=float)
    ap.add_argument("--total-cap", required=True, type=float)
    ap.add_argument("--hours", required=True, type=float)
    ap.add_argument("--drop-kwargs", nargs="*", default=[])
    ap.add_argument("--strip-format-tags", action="store_true")  # note 40-15
    ap.add_argument("--max-failed", type=int, default=3)  # note 40-23: chunks set aside per session
    ap.add_argument("--mock-response")
    a = ap.parse_args()
    t0 = time.time()
    a.outdir.mkdir(parents=True, exist_ok=True)
    work = a.outdir / "work"
    work.mkdir(exist_ok=True)
    for d in a.prev:  # carry earlier sessions into this session's output (kaggle/audit.md K16)
        for f in d.rglob(f"{a.tag}_*"):
            if f.is_file() and not (a.outdir / f.name).exists():
                shutil.copy2(f, a.outdir / f.name)
    before = spent(a.outdir, a.tag)

    def load(path: str, split: str) -> list[dict]:
        rows = [json.loads(x) for x in Path(path).read_text().splitlines() if x.strip()]
        sel = (r for r in rows if r["_gskill_split"] == split)
        return sorted(sel, key=lambda r: r["_gskill_order"])

    chunks = []  # (split, tasks): test tasks first, then the extra tasks, never mixed in a chunk
    for split, path in (("test", a.rows), ("extra", a.extra_rows)):
        if path:
            ts = load(path, split)
            chunks += [(split, ts[i : i + a.chunk]) for i in range(0, len(ts), a.chunk)]
    status = "all done"
    arms = {k: v for k, v in ARMS.items() if k in a.arms}
    stop, failed = False, 0
    for _pass in range(2):  # note 40-23: pass 2 re-runs, once, the chunks set aside in pass 1
        for k, (split, chunk) in enumerate(chunks):
            for arm, (skill, lf) in arms.items():
                out = a.outdir / f"{a.tag}_{arm}_c{k:02d}.json"
                if complete(out, len(chunk)):
                    continue
                total = spent(a.outdir, a.tag)
                worst = a.cost_limit * len(chunk)
                if total - before >= a.day_cap:
                    status = f"day cap: spent today {total - before:.3f}"
                    stop = True
                    break
                if total >= a.total_cap:
                    status = f"total cap: spent {total:.3f}"
                    stop = True
                    break
                if time.time() - t0 > a.hours * 3600:
                    status = "time limit of this session"
                    stop = True
                    break
                # an earlier attempt of this chunk: keep its cost counted under another name (K28)
                cost_file = a.outdir / f"{out.stem}.cost.json"
                if cost_file.exists():
                    m = len(list(a.outdir.glob(f"{out.stem}.try*.cost.json"))) + 1
                    os.replace(cost_file, a.outdir / f"{out.stem}.try{m}.cost.json")
                earlier = sorted(a.outdir.glob(f"{out.name}.bad*"))  # an attempt that crashed
                if len(earlier) >= 2:  # notes 40-13, 40-23: run once, re-run once, no more
                    continue
                sub = work / f"rows_c{k:02d}.jsonl"
                sub.write_text("".join(json.dumps(r) + "\n" for r in chunk))
                cmd = [sys.executable, str(HERE / "c3_agent.py"), "--isolation", a.isolation]
                if a.packages:
                    cmd += ["--packages", a.packages]
                cmd += ["--base-env", "MODEL_PROXY_URL", "--key-env", "MODEL_PROXY_API_KEY"]
                if a.strip_format_tags:
                    cmd += ["--strip-format-tags"]
                cmd += ["--base-suffix", "/openapi", "--drop-kwargs", *a.drop_kwargs, "--"]
                cmd += ["--rows", str(sub), "--split", split, "--model", a.model]
                cmd += ["--seed", str(a.seed), "--cost-limit", str(a.cost_limit)]
                cap = a.chunk_cap if a.chunk_cap is not None else worst + a.cost_limit
                cmd += ["--cap", str(cap), "--registry", a.registry]
                cmd += ["--gskill-yaml", a.gskill_yaml, "--out", str(out)]
                if skill:
                    cmd += ["--skills-file", a.skills_file]
                if lf:
                    cmd += ["--leak-free"]
                if a.mock_response:
                    cmd += ["--mock-response", a.mock_response]
                with (a.outdir / f"{a.tag}.log").open("a") as log:
                    log.write(f"\n=== {arm} chunk {k} {time.strftime('%H:%M:%S')}\n")
                    log.flush()
                    rc = subprocess.run(
                        cmd, cwd=work, stdout=log, stderr=subprocess.STDOUT
                    ).returncode
                out.with_suffix(".mini.yaml").unlink(missing_ok=True)  # holds the endpoint URL
                ok = rc == 0 and complete(out, len(chunk))
                if not ok and rc == 0 and earlier:
                    # notes 40-13, 40-14: the second attempt of a chunk failed again; keep it when
                    # every task ran, with the crashed and infrastructure-error runs listed (the
                    # analysis drops those tasks from every arm of this agent)
                    try:
                        d = json.loads(out.read_text())
                    except (OSError, ValueError):
                        d = {}
                    runs = d.get("runs", [])
                    if len(runs) == len(chunk) and not d.get("stopped"):
                        d["accepted_with_crashes"] = sorted(
                            r["instance_id"] for r in runs if r.get("crashed")
                        )
                        d["accepted_with_infra"] = sorted(  # note 40-14
                            r["instance_id"] for r in runs if r.get("infra_error")
                        )
                        out.write_text(json.dumps(d, indent=1))
                        ok = complete(out, len(chunk))
                print(f"{a.tag} {arm} chunk {k}: {'ok' if ok else 'FAILED'} rc={rc}", flush=True)
                if not ok:
                    n_bad = len(earlier) + 1
                    for f in a.outdir.glob(f"{out.stem}.*"):
                        if f.name.endswith(".cost.json") or ".bad" in f.name:
                            continue  # the money was spent: keep it counted; keep earlier attempts
                        os.replace(f, f.with_name(f"{f.name}.bad{n_bad}"))
                    marker = a.outdir / f"{out.name}.bad{n_bad}"
                    if not marker.exists():  # no result file: still count the attempt
                        marker.write_text(json.dumps({"no_result": True, "rc": rc}) + "\n")
                    # note 40-23: set the chunk aside and go on; the second pass re-runs it once
                    failed += 1
                    status = f"stopped: {arm} chunk {k} did not complete (see {a.tag}.log)"
                    if failed >= a.max_failed:
                        stop = True
                        break
            if stop:
                break
        if stop:
            break
    done = sum(
        complete(a.outdir / f"{a.tag}_{arm}_c{k:02d}.json", len(c))
        for k, (_, c) in enumerate(chunks)
        for arm in arms
    )
    if done == len(chunks) * len(arms):
        status = "all done"
    summary = {
        "tag": a.tag,
        "status": status,
        "chunks_done": done,
        "chunks_total": len(chunks) * len(arms),
        "spent_this_session": round(spent(a.outdir, a.tag) - before, 4),
        "spent_total": round(spent(a.outdir, a.tag), 4),
        "minutes": round((time.time() - t0) / 60, 1),
    }
    (a.outdir / f"{a.tag}_summary.json").write_text(json.dumps(summary, indent=1) + "\n")
    print(json.dumps(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
