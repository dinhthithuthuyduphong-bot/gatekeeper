# Section 45 (W7-b, docs/preregistration_main.md): XRepoSkill's learner on our saved Jinja
# trajectories, with gskill's reflection model. Paste this whole file into ONE cell of a notebook
# created from https://www.kaggle.com/benchmarks/tasks/new (check: `import kaggle_benchmarks`).
#   1. First run: DRY_RUN = True, POOL = "A". No model call (the model call is replaced by a stub
#      that returns no rule), 0 USD of quota. Send w7_<POOL>.json and w7_<POOL>_run.zip.
#   2. Paid runs, only after Claude has read the dry run and @thuthuy has set the caps:
#      DRY_RUN = False. Run once a day until it prints "all stages done"; before each new session,
#      attach the previous session's output (w7_<POOL>_run.zip) as a dataset.
# The model key stays in this process; this cell prints no key and no environment value.
import glob
import gzip
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
import time
import urllib.request
import zipfile

DRY_RUN = True
POOL = None  # "A" (shipped history) or "B" (single-commit history); no default
# ---- registered (section 45) ------------------------------------------------------------------
COMMIT = "__FILL__"  # commit of this repository that holds kaggle/data/w7_pool<POOL>.tar.gz
DATA_SHA256 = {"A": "cf5d58aedb36e5aa0ddc9c7eb14035cfc4629f7bec9c844319c20fd3072777ce", "B": None}
XREPOSKILL = "26fd70345698108c0fdce2d8904293a38b9cd42f"  # the commit E2 ran (preregistration_e2)
MODEL = "openai/google/gemini-3.1-pro-preview"  # gskill's reflection model, through Kaggle's proxy
PIN, POUT = 2e-6, 12e-6  # USD/token, LiteLLM 1.106.6 list price; used only for the guard below
MAX_OUT = 24000  # max_tokens of every Stage 1 and 2 call of XRepoSkill (discover, merge, judge)
CHARS_PER_TOKEN = 3.09  # measured on this model's Kaggle replies in section 38 A' (note 38-11)
DAY_CAP_USD = None  # set from the measured cost of the dry run + first chunk (@thuthuy)
ITEM_CAP_USD = None
CHUNK_PAIRS = 3  # pairs per discover call; a session never starts a chunk it cannot pay for
WORKERS = 3
# ------------------------------------------------------------------------------------------------
WORK, INPUT = "/kaggle/working", "/kaggle/input"
RAW = "https://raw.githubusercontent.com/dinhthithuthuyduphong-bot/gatekeeper/"


def sh(cmd: str) -> tuple[int, str]:
    p = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return p.returncode, (p.stdout + p.stderr)[-3000:]


def fetch(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=120) as r:
        return r.read()


def safe_extract(tar_bytes: bytes, dest: str) -> int:
    """Regular files only, relative paths only (the archive is data, never code)."""
    n = 0
    with tarfile.open(fileobj=io.BytesIO(tar_bytes)) as tf:
        for m in tf.getmembers():
            if not m.isfile() or m.name.startswith("/") or ".." in m.name.split("/"):
                continue
            path = os.path.join(dest, m.name)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "wb") as fh:
                fh.write(tf.extractfile(m).read())
            n += 1
    return n


def worst_call_usd(chars: int) -> float:
    return chars / CHARS_PER_TOKEN * PIN + MAX_OUT * POUT


def main() -> dict:
    out = {
        "started": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "dry_run": DRY_RUN,
        "pool": POOL,
        "model": MODEL,
    }
    if POOL not in ("A", "B"):
        raise SystemExit('set POOL = "A" or "B" (section 45)')
    if not DRY_RUN and (DAY_CAP_USD is None or ITEM_CAP_USD is None):
        raise SystemExit("caps not set: paid runs only after @thuthuy sets them")
    if "__" in COMMIT or DATA_SHA256[POOL] is None:
        raise SystemExit("COMMIT or the data hash of this pool is not filled in")
    run = f"{WORK}/w7_{POOL}"
    os.makedirs(run, exist_ok=True)
    # resume: the previous session's run directory, attached as a dataset
    prev = sorted(glob.glob(f"{INPUT}/**/w7_{POOL}_run.zip", recursive=True))
    if prev and not os.path.exists(f"{run}/state.json"):
        with zipfile.ZipFile(prev[-1]) as z:
            for name in z.namelist():
                if name.startswith("/") or ".." in name.split("/"):
                    continue
                z.extract(name, run)
    state_path = f"{run}/state.json"
    state = (
        json.load(open(state_path))
        if os.path.exists(state_path)
        else {"spent_usd": 0.0, "chunks_done": [], "stages_done": []}
    )
    out["spent_before"] = state["spent_usd"]
    if not DRY_RUN:
        import kaggle_benchmarks  # noqa: F401  (Benchmarks notebook check)

        base = os.environ.get("MODEL_PROXY_URL", "").rstrip("/")
        for suffix in ("/openapi", "/genai"):
            base = base.removesuffix(suffix)
        if not base or not os.environ.get("MODEL_PROXY_API_KEY"):
            raise SystemExit("not a Benchmarks notebook: create it from benchmarks/tasks/new")
        os.environ["OPENAI_API_BASE"] = base + "/openapi"
        os.environ["OPENAI_API_KEY"] = os.environ["MODEL_PROXY_API_KEY"]
    # XRepoSkill at its pinned commit; only the dependencies of the stages run here
    src = f"{WORK}/xreposkill_src"
    if not os.path.exists(f"{src}/src/xreposkill"):
        rc, log = sh(
            f"git init -q {src} && cd {src} && git remote add origin "
            f"https://github.com/XREPOSKILL/XRepoSkill && git fetch -q --depth 1 origin "
            f"{XREPOSKILL} && git checkout -q FETCH_HEAD"
        )
        if rc:
            raise SystemExit("could not fetch XRepoSkill: " + log)
    rc, head = sh(f"git -C {src} rev-parse HEAD")
    if head.strip() != XREPOSKILL:
        raise SystemExit(f"XRepoSkill is not at the pinned commit: {head.strip()}")
    sh(f"{sys.executable} -m pip install -q 'pydantic>=2.7' 'litellm>=1.40' 'pyyaml>=6.0'")
    sys.path.insert(0, f"{src}/src")
    from xreposkill import cli, llm  # noqa: E402

    # data: the converted trajectories of this pool (kaggle/scripts/w7_build.py)
    data = f"{WORK}/w7_data_{POOL}"
    if not os.path.exists(f"{data}/submissions.txt"):
        raw = fetch(f"{RAW}{COMMIT}/kaggle/data/w7_pool{POOL}.tar.gz")
        if hashlib.sha256(raw).hexdigest() != DATA_SHA256[POOL]:
            raise SystemExit("data file does not match the registered sha256; nothing sent")
        out["files_extracted"] = safe_extract(gzip.decompress(raw), data)
    cfg = f"{src}/configs/pipeline.yaml"
    empty_ids = f"{WORK}/no_eval_ids.txt"
    open(empty_ids, "w").close()

    # cost: the proxy reports each call's cost; the guard uses list prices and MAX_OUT
    spent = {"session": 0.0, "calls": 0, "tokens_in": 0, "tokens_out": 0}
    if DRY_RUN:

        def stub(*, model, system, user, **kw):  # every Stage 1/2 prompt: "no rule"
            spent["calls"] += 1
            return llm.Reply(text="[]", in_tokens=0, out_tokens=0, cost=0.0, finish_reason="stop")

        llm.chat = stub
    else:
        import litellm

        def track(kwargs, response, start, end):
            u = getattr(response, "usage", None)
            spent["calls"] += 1
            spent["tokens_in"] += int(getattr(u, "prompt_tokens", 0) or 0)
            spent["tokens_out"] += int(getattr(u, "completion_tokens", 0) or 0)
            c = getattr(u, "cost", None) or {}
            usd = (
                (
                    (c.get("input_tokens_cost_nanodollars") or 0)
                    + (c.get("output_tokens_cost_nanodollars") or 0)
                )
                / 1e9
                if isinstance(c, dict)
                else 0.0
            )
            if not usd:  # no reported cost: list price of the tokens (an upper estimate)
                usd = (
                    int(getattr(u, "prompt_tokens", 0) or 0) * PIN
                    + int(getattr(u, "completion_tokens", 0) or 0) * POUT
                )
            spent["session"] += usd

        litellm.success_callback = [track]

    def stage(name: str, *args: str) -> None:
        if name in state["stages_done"]:
            return
        rc = cli.main([name, *args])
        if rc:
            raise SystemExit(f"stage {name} returned {rc}")
        state["stages_done"].append(name)

    def save() -> None:
        state["spent_usd"] = out["spent_before"] + spent["session"]
        json.dump(state, open(state_path, "w"), indent=1)

    pool_dir, pairs = f"{run}/traj_pool", f"{run}/pairs/pairs.jsonl"
    stage(
        "ingest",
        "--submissions",
        f"{data}/submissions.txt",
        "--trajs-root",
        f"{data}/trajs",
        "--evals-root",
        f"{data}/evals",
        "--pool-dir",
        pool_dir,
    )
    stage(
        "pair",
        "--pool-dir",
        pool_dir,
        "--out",
        pairs,
        "--stats-out",
        f"{run}/pairs/stats.json",
        "--K",
        "4",
        "--eval-ids",
        empty_ids,
    )
    stage("fork", "--pairs", pairs, "--pool-dir", pool_dir, "--out", f"{run}/pairs/forks.jsonl")
    out["pair_stats"] = json.load(open(f"{run}/pairs/stats.json"))
    save()

    # Stage 1 in chunks of pairs (each pair is independent; outputs are appended)
    plines = [x for x in open(pairs).read().splitlines() if x.strip()]
    chunks = [plines[i : i + CHUNK_PAIRS] for i in range(0, len(plines), CHUNK_PAIRS)]
    tsize = {}
    for f in glob.glob(f"{data}/trajs/*/trajs/*/*.traj.json"):
        sub = f.split("/trajs/")[1].split("/")[0]
        tsize[f"{sub}::{json.load(open(f))['instance_id']}"] = os.path.getsize(f)
    status = "all stages done"
    for k, ch in enumerate(chunks):
        if k in state["chunks_done"]:
            continue
        worst = sum(
            3
            * worst_call_usd(
                tsize.get(json.loads(p)["fail_traj_id"], 10**6)
                + tsize.get(json.loads(p)["pass_traj_id"], 10**6)
                + 12000
            )
            for p in ch
        )
        if not DRY_RUN and (
            spent["session"] + worst > DAY_CAP_USD
            or out["spent_before"] + spent["session"] + worst > ITEM_CAP_USD
        ):
            status = (
                f"cap reached before chunk {k} (worst case {worst:.2f} USD); run again tomorrow"
            )
            break
        cf = f"{run}/pairs/chunk_{k:03d}.jsonl"
        open(cf, "w").write("\n".join(ch) + "\n")
        rc = cli.main(
            [
                "discover",
                "--pairs",
                cf,
                "--forks",
                f"{run}/pairs/forks.jsonl",
                "--pool-dir",
                pool_dir,
                "--out-dir",
                f"{run}/candidates",
                "--config",
                cfg,
                "--model",
                MODEL,
                "--workers",
                str(WORKERS),
                "--failed",
                f"{run}/candidates/failed.jsonl",
                "--cost-log",
                f"{run}/cost_log.jsonl",
                "--transcripts-dir",
                f"{run}/transcripts",
            ]
        )
        if rc:
            status = f"discover returned {rc} on chunk {k}"
            break
        state["chunks_done"].append(k)
        save()
    else:
        for name, args in (
            (
                "merge",
                [
                    "--candidates-dir",
                    f"{run}/candidates",
                    "--buckets-dir",
                    f"{run}/buckets",
                    "--out-root",
                    f"{run}/rules_merged",
                    "--config",
                    cfg,
                    "--model",
                    MODEL,
                    "--cost-log",
                    f"{run}/cost_log.jsonl",
                ],
            ),
            (
                "judge",
                [
                    "--rules-root",
                    f"{run}/rules_merged",
                    "--out",
                    f"{run}/rules_judged",
                    "--judge-log",
                    f"{run}/judge_log.jsonl",
                    "--config",
                    cfg,
                    "--model",
                    MODEL,
                    "--workers",
                    str(WORKERS),
                    "--cost-log",
                    f"{run}/cost_log.jsonl",
                ],
            ),
            (
                "score",
                [
                    "--rules-root",
                    f"{run}/rules_judged",
                    "--out",
                    f"{run}/rules_scored",
                    "--pool-dir",
                    pool_dir,
                    "--pairs",
                    pairs,
                    "--log",
                    f"{run}/score_log.jsonl",
                ],
            ),
            (
                "audit",
                [
                    "--rules-root",
                    f"{run}/rules_scored",
                    "--pairs",
                    pairs,
                    "--pool-dir",
                    pool_dir,
                    "--out",
                    f"{run}/ngram_audit.jsonl",
                ],
            ),
        ):
            if (
                name in ("merge", "judge")
                and not DRY_RUN
                and (out["spent_before"] + spent["session"] > ITEM_CAP_USD)
            ):
                status = f"cap reached before {name}"
                break
            cdir = f"{run}/candidates"
            has_candidates = os.path.isdir(cdir) and any(
                f.endswith(".jsonl") and f != "failed.jsonl" and os.path.getsize(f"{cdir}/{f}") > 0
                for f in os.listdir(cdir)
            )
            if not has_candidates:  # Stage 1 wrote no rule at all: nothing to merge or score
                if name not in state["stages_done"]:
                    state["stages_done"].append(name)
                continue
            stage(name, *args)
            save()
    save()
    out.update(
        status=status,
        chunks=len(chunks),
        chunks_done=len(state["chunks_done"]),
        spent_session_usd=round(spent["session"], 4),
        spent_total_usd=round(state["spent_usd"], 4),
        calls=spent["calls"],
        tokens_in=spent["tokens_in"],
        tokens_out=spent["tokens_out"],
        finished=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    )
    shutil.make_archive(f"{WORK}/w7_{POOL}_run", "zip", run)
    json.dump(out, open(f"{WORK}/w7_{POOL}.json", "w"), indent=1)
    return out


try:
    print(json.dumps(main(), indent=1)[:6000])
except SystemExit as e:
    print("stopped:", e)
