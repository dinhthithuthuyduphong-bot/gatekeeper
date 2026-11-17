# Section 38 A' (kaggle/preregistration_s38.md, note 38-10): reference model, renamed prompts.
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

# ---- note 38-10 (A'): the reference model on the 6 renamed prompts (kaggle/data/a38p_*) --------
NAME = "a38p"  # section 38, note 38-10; this file is a38_run_cell.py with its own block
COMMIT = "__FILL__"
SHA256 = "0f3fe9b4a337fc177f9c2f262b858b7694684d5ead557599bde0c28f824a30b3"
SHA256_JSONL = (
    "51aded479f0cbbe02b6e43412e8e36db46264caacdcdac720abe850e014aa91b"  # the same file unpacked
)
MODELS = {"google/gemini-3.1-pro-preview": 0.08918}  # note 38-3: P0b cost per call
P0_CHARS = 74305
SEEDS = (1, 2, 3)
TEMPERATURE = None  # gskill sets none (gepa/lm.py at 8c7b697): provider default
DAY_CAP_USD = 2.1  # note 38-10: guard simulated on the measured costs of these 6 calls (L66)
ITEM_CAP_USD = 2.1  # note 38-10 (A'), approved by @thuthuy 17/11; expected spend 1.76
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


def load_prompts() -> list[dict] | None:
    """The registered data file: attached as .jsonl.gz, or as .jsonl if Kaggle unpacked it on
    upload (then the sha256 of the unpacked text must match SHA256_JSONL); else from GitHub.
    Returns None (and prints why) instead of raising, so a later cell of a batch run still runs."""
    gz = glob.glob(INPUT + f"/**/{NAME}_prompts.jsonl.gz", recursive=True)
    js = glob.glob(INPUT + f"/**/{NAME}_prompts.jsonl", recursive=True)
    try:
        if gz:
            raw = open(gz[0], "rb").read()
            ok, text = hashlib.sha256(raw).hexdigest() == SHA256, gzip.decompress(raw)
        elif js:
            text = open(js[0], "rb").read()
            ok = hashlib.sha256(text).hexdigest() == SHA256_JSONL
        elif COMMIT != "not-in-repo":
            raw = urllib.request.urlopen(URL, timeout=120).read()
            ok, text = hashlib.sha256(raw).hexdigest() == SHA256, gzip.decompress(raw)
        else:
            seen = sorted(
                os.path.relpath(p, INPUT) for p in glob.glob(INPUT + "/**/*", recursive=True)
            )
            print(f"{NAME}: data file not attached; files under {INPUT}: {seen[:50]}")
            return None
    except Exception as e:
        print(f"{NAME}: could not read the data file: {e!r}"[:500])
        return None
    if not ok:
        print(f"{NAME}: data file does not match the registered sha256; nothing sent")
        return None
    return [json.loads(x) for x in text.decode().splitlines()]


def previous() -> list[dict]:
    """Every earlier result row, from any attached input and this session's folder, each row once
    (the same row can arrive twice, e.g. in a carried file and in its original file)."""
    rows, seen = [], set()
    files = sorted(set(glob.glob(INPUT + f"/**/{NAME}_results_*.jsonl", recursive=True)))
    for f in files + sorted(glob.glob(WORK + f"/{NAME}_results_*.jsonl")):
        for line in open(f):
            if line.strip():
                r = json.loads(line)
                key = (r.get("sha256"), r.get("model"), r.get("seed"), r.get("utc"))
                if key not in seen:
                    seen.add(key)
                    rows.append(r)
    return rows


def carry(rows: list[dict]) -> None:
    """Copy all earlier rows into this session's output, so the next session needs only this
    session's output as input (Kaggle attaches one version of a notebook's output at a time)."""
    if rows:
        with open(WORK + f"/{NAME}_results_carried.jsonl", "w") as fh:
            for r in rows:
                fh.write(json.dumps(r) + "\n")


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
        print(f"{NAME}: MODELS/COMMIT not filled in from P0; nothing sent")
        return
    prompts = load_prompts()
    if prompts is None:
        return
    jobs, uniq = plan(prompts)
    old = previous()
    carry(old)
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
