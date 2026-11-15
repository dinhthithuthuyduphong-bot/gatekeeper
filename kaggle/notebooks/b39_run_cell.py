# Section 39 B (kaggle/preregistration_s39.md): other vendors' auditors on the sham-audit prompts.
# Paste this whole file into ONE cell of a notebook created from
# https://www.kaggle.com/benchmarks/tasks/new, attach the private dataset holding
# b39_prompts.jsonl.gz, and run it until it prints "all done".
#
# Safety (registered): it stops before the estimated spend of THIS session would pass DAY_CAP_USD,
# and before the estimated spend of all sessions (previous result files attached as a dataset, plus
# this one) would pass ITEM_CAP_USD. The estimate per call is the measured P0 cost per call times
# the prompt's length ratio, times SAFETY. A call that already has a reply is never sent again.
# It prints no key, no account detail and no environment value.
import glob
import gzip
import hashlib
import json
import os
import re
import time
import urllib.request

# ---- filled in from P0 before this file is sent (registered in preregistration_s39.md, 39-P0) ----
NAME = "b39"  # section 39; this is kaggle/notebooks/a38_run_cell.py with its own block
COMMIT = "not-in-repo"  # the data file holds trajectory text: attach it as a private dataset
SHA256 = "de507e4bb30caf587d15b37caaafb436d0331e368d81bfcf33878249e76f48d5"
MODELS = {}  # kaggle model key -> measured USD per call on the P0 prompt (74,305 characters)
P0_CHARS = 74305
SEEDS = (1,)  # section 19 C called each auditor once per prompt, with seed 1
TEMPERATURE = None  # section 19 C set no temperature (configs/models/vertex_gemini.json)
DAY_CAP_USD = 8.0  # 80% of the 10 USD daily quota
ITEM_CAP_USD = 8.0  # approved cap of item B (plan_v2.md)
SAFETY = 1.5  # estimate is multiplied by this (output length varies; P0 measured one reply)
MAX_ERRORS_IN_A_ROW = 3  # then that model is skipped for this session
# --------------------------------------------------------------------------------------------------
WORK, INPUT = "/kaggle/working", "/kaggle/input"
URL = (
    "https://raw.githubusercontent.com/dinhthithuthuyduphong-bot/gatekeeper/"
    f"{COMMIT}/kaggle/data/{NAME}_prompts.jsonl.gz"
)
OUT = WORK + f"/{NAME}_results_" + time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()) + ".jsonl"


def extract_skills(response_text: str) -> str:
    """gskill's LoggingProposer.extract_skills (train_optimize_anything.py at 8c7b697), verbatim."""
    first = re.search(r"```(?:\w*[ \t]*\r?\n)?", response_text)
    if not first:
        return response_text.strip()
    last_pos = response_text.rfind("```")
    if last_pos <= first.end():
        return response_text.strip()
    return response_text[first.end() : last_pos].strip()


def load_prompts() -> list[dict]:
    local = glob.glob(INPUT + f"/**/{NAME}_prompts.jsonl.gz", recursive=True)
    raw = open(local[0], "rb").read() if local else urllib.request.urlopen(URL, timeout=120).read()
    if hashlib.sha256(raw).hexdigest() != SHA256:
        raise SystemExit("data file does not match the registered sha256; stopping")
    return [json.loads(x) for x in gzip.decompress(raw).decode().splitlines()]


def previous() -> list[dict]:
    rows = []
    for f in sorted(set(glob.glob(INPUT + f"/**/{NAME}_results_*.jsonl", recursive=True))) + sorted(
        glob.glob(WORK + f"/{NAME}_results_*.jsonl")
    ):
        for line in open(f):
            if line.strip():
                rows.append(json.loads(line))
    return rows


def plan(prompts: list[dict]) -> tuple[list[tuple[str, str, int]], dict]:
    """Unique prompts x models x seeds, seed-major then a fixed shuffled order of prompts, so a
    session cut short leaves every model and condition with the same seeds done."""
    import random

    uniq = {}
    for p in prompts:
        uniq.setdefault(p["sha256"], p)
    order = sorted(uniq)
    random.Random(38).shuffle(order)
    return [(sha, m, s) for s in SEEDS for sha in order for m in sorted(MODELS)], uniq


def estimate(model: str, chars: int) -> float:
    return MODELS[model] * chars / P0_CHARS * SAFETY


def main() -> None:
    import kaggle_benchmarks as kbench

    if not MODELS or "__" in COMMIT:
        raise SystemExit("MODELS/COMMIT not filled in from P0; do not run this file yet")
    prompts = load_prompts()
    jobs, uniq = plan(prompts)
    old = previous()
    done = {(r["sha256"], r["model"], r["seed"]) for r in old if r.get("ok")}
    spent_before = sum(r.get("est_usd", 0.0) for r in old)
    spent_now, errors, skipped = 0.0, {}, set()
    todo = [j for j in jobs if j not in done]
    print(f"jobs {len(jobs)}, done {len(jobs) - len(todo)}, est. spent so far {spent_before:.2f}")
    with open(OUT, "a") as fh:
        for sha, m, s in todo:
            if m in skipped:
                continue
            est = estimate(m, len(uniq[sha]["prompt"]))
            if spent_now + est > DAY_CAP_USD:
                print("day cap reached; run again tomorrow")
                break
            if spent_before + spent_now + est > ITEM_CAP_USD:
                print("item cap reached; stopping for good")
                break
            t0 = time.time()
            row = {"sha256": sha, "model": m, "seed": s, "temperature": TEMPERATURE}
            try:
                r = kbench.llms[m].prompt(uniq[sha]["prompt"], temperature=TEMPERATURE, seed=s)
                text = str(r)
                row.update(ok=True, response=text, new_skills=extract_skills(text))
                errors[m] = 0
            except Exception as e:
                row.update(ok=False, error=repr(e)[:600])
                errors[m] = errors.get(m, 0) + 1
                if errors[m] >= MAX_ERRORS_IN_A_ROW:
                    skipped.add(m)
            row.update(secs=round(time.time() - t0, 1), est_usd=est, utc=time.time())
            spent_now += est
            fh.write(json.dumps(row) + "\n")
            fh.flush()
            os.fsync(fh.fileno())
    left = [j for j in jobs if j not in done and j[1] not in skipped]
    print(f"est. spent this session {spent_now:.2f}; skipped models {sorted(skipped)}")
    print("all done" if not left else f"saved {OUT}; download it and attach it next time")


if __name__ != "cell_test":
    main()
