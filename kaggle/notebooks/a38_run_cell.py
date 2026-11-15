# Section 38 A (kaggle/preregistration_s38.md): other skill writers on gskill's saved prompts.
# Paste this whole file into ONE cell of a notebook created from
# https://www.kaggle.com/benchmarks/tasks/new and run it once a day until it prints "all done".
#
# Safety (registered): before each call it checks that the spend of THIS session plus the
# estimate of the call stays within DAY_CAP_USD, and that the spend of all sessions (previous
# result files attached as a dataset, plus this one) stays within ITEM_CAP_USD. Spend = the cost
# Kaggle reports on each reply; the estimate (measured P0b cost per call x prompt length ratio x
# SAFETY) is used before a call and when no cost is reported. A call that already has a reply is
# never sent again.
# It prints no key, no account detail and no environment value.
import glob
import gzip
import hashlib
import json
import os
import re
import time
import urllib.request

# ---- filled in from P0 before this file is sent (registered in preregistration_s38.md, 38-P0) ----
NAME = "a38"  # section 38; kaggle/notebooks/b39_run_cell.py is this file with its own block
COMMIT = "__DATA_COMMIT__"
SHA256 = "2e6425aa48553a2fd337e57935ab924f69bb27348441dda4730ec1e57e718b02"
MODELS = {}  # kaggle model key -> measured USD per call on the P0 prompt (74,305 characters)
P0_CHARS = 74305
SEEDS = (1, 2, 3)
TEMPERATURE = None  # gskill sets none (gepa/lm.py at 8c7b697): provider default
DAY_CAP_USD = 8.0  # 80% of the 10 USD daily quota
ITEM_CAP_USD = 40.0  # approved cap of item A (plan_v2.md)
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


def reported(text: str) -> tuple:
    """Tokens and cost that Model Proxy attached to the reply just received (kaggle_benchmarks
    0.6.3: the global chat keeps only the last message, the reply; its .usage holds them)."""
    try:
        from kaggle_benchmarks import chats

        msg = chats.get_current_chat().messages[-1]
        if str(msg.content) != text:
            return None, None, None
        u = msg.usage
        c = u.total_cost_nanodollars
        return u.input_tokens, u.output_tokens, None if c is None else c / 1e9
    except Exception:
        return None, None, None


def main() -> None:
    import kaggle_benchmarks as kbench

    if not MODELS or "__" in COMMIT:
        raise SystemExit("MODELS/COMMIT not filled in from P0; do not run this file yet")
    prompts = load_prompts()
    jobs, uniq = plan(prompts)
    old = previous()
    done = {(r["sha256"], r["model"], r["seed"]) for r in old if r.get("ok")}
    spent_before = sum(r.get("charged_usd", r.get("est_usd", 0.0)) for r in old)
    spent_now, errors, skipped = 0.0, {}, set()
    todo = [j for j in jobs if j not in done]
    print(f"jobs {len(jobs)}, done {len(jobs) - len(todo)}, spent so far {spent_before:.2f}")
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
                row["tokens_in"], row["tokens_out"], row["cost_usd"] = reported(text)
                errors[m] = 0
            except Exception as e:
                row.update(ok=False, error=repr(e)[:600])
                errors[m] = errors.get(m, 0) + 1
                if errors[m] >= MAX_ERRORS_IN_A_ROW:
                    skipped.add(m)
            # charged: the cost Kaggle reported, else the estimate (a failed call counts in full)
            charged = row.get("cost_usd") if row.get("cost_usd") is not None else est
            row.update(secs=round(time.time() - t0, 1), est_usd=est, charged_usd=charged)
            row["utc"] = time.time()
            spent_now += charged
            fh.write(json.dumps(row) + "\n")
            fh.flush()
            os.fsync(fh.fileno())
    left = [j for j in jobs if j not in done and j[1] not in skipped]
    print(f"spent this session {spent_now:.2f} USD of quota; skipped models {sorted(skipped)}")
    print("all done" if not left else f"saved {OUT}; download it and attach it next time")


if __name__ != "cell_test":
    main()
