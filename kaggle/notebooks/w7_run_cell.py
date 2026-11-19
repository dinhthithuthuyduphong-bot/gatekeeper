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
import threading
import time
import urllib.request
import zipfile

DRY_RUN = True
POOL = None  # "A" (shipped history) or "B" (single-commit history); no default
# ---- registered (section 45) ------------------------------------------------------------------
COMMIT = "0cb4874963fcc3c416271ecfa8539915f3e8a008"  # holds both data files
DATA_SHA256 = {
    "A": "cf5d58aedb36e5aa0ddc9c7eb14035cfc4629f7bec9c844319c20fd3072777ce",
    "B": "01f3475515611ac2238d73d486e0b0b98e18b358c60160ac09efea4bc119be40",
}
XREPOSKILL = "26fd70345698108c0fdce2d8904293a38b9cd42f"  # the commit E2 ran (preregistration_e2)
MODEL = "openai/google/gemini-3.1-pro-preview"  # gskill's reflection model, through Kaggle's proxy
PIN, POUT = 2e-6, 12e-6  # USD/token, LiteLLM 1.106.6 list price; used only for the guard below
MAX_OUT = 24000  # max_tokens of every Stage 1 and 2 call of XRepoSkill (discover, merge, judge)
CHARS_PER_TOKEN = 3.09  # measured on this model's Kaggle replies in section 38 A' (note 38-11)
DAY_CAP_USD = None  # set from the measured cost of the dry run + first chunk (@thuthuy)
ITEM_CAP_USD = None
CHUNK_PAIRS = 3  # pairs per discover call; a session never starts a chunk it cannot pay for
MAX_CHUNKS = None  # chunks this session at most (1 = the measuring chunk); None = no limit
MEASURE_MERGE_JUDGE = False  # True: after MAX_CHUNKS, merge + judge on a copy (note 45-4)
PRECHECK_CALL_USD = 0.0647  # largest call cost of the measuring chunk (note 45-4); a chunk is
# started only when the cap left covers this per analyst and pair. Operational: it avoids
# starting a chunk the guard would cut; the guard itself is what bounds the spend
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


# The guard (A147, note 45-4): every model attempt of XRepoSkill goes through litellm.completion
# (its llm.chat and call_with_retry included); the cell wraps that function, reserves the attempt's
# worst case (worst_call_usd) before it is sent and refuses it when spent + reserved + worst case
# would pass a cap. So the spend never passes a cap, whatever the number of re-prompts, retries
# or merge splits. A unit (a discover chunk, merge, judge) cut by the guard is rolled back to the
# files it found and runs again in a later session.
class BudgetStop(Exception):
    pass


def snapshot(root: str) -> dict[str, int]:
    return {
        os.path.join(d, f): os.path.getsize(os.path.join(d, f))
        for d, _, fs in os.walk(root)
        for f in fs
    }


def rollback(root: str, snap: dict[str, int]) -> int:
    n = 0
    for f in list(snapshot(root)):
        if f not in snap:
            os.remove(f)
            n += 1
        elif os.path.getsize(f) != snap[f]:
            with open(f, "r+b") as h:
                h.truncate(snap[f])
            n += 1
    return n


def call_usd(usage) -> float:
    c = getattr(usage, "cost", None) or {}
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
            int(getattr(usage, "prompt_tokens", 0) or 0) * PIN
            + int(getattr(usage, "completion_tokens", 0) or 0) * POUT
        )
    return usd


def guard_completion(sent, left, acct: dict, spent: dict, calls_log: list):
    """Wrap litellm.completion: reserve each attempt's worst case, refuse it past the cap."""
    lock = threading.Lock()
    acct.setdefault("reserved", 0.0)

    def guarded(**kw):
        chars = sum(len(str(m.get("content", ""))) for m in kw.get("messages") or [])
        worst = worst_call_usd(chars)
        with lock:
            if acct["reserved"] + worst > left():
                acct["stopped"] = True
                raise BudgetStop(f"cap: {left():.4f} USD left, worst case {worst:.4f}")
            acct["reserved"] += worst
        try:
            resp = sent(**kw)
        except Exception:
            with lock:  # a failed attempt may still be billed: charge its worst case
                acct["reserved"] -= worst
                spent["session"] += worst
                spent["failed_calls"] += 1
                calls_log.append({"unit": acct.get("unit", ""), "failed": True, "usd": worst})
            raise
        u = getattr(resp, "usage", None)
        usd = call_usd(u)
        tin = int(getattr(u, "prompt_tokens", 0) or 0)
        tout = int(getattr(u, "completion_tokens", 0) or 0)
        with lock:
            acct["reserved"] -= worst
            spent["session"] += usd
            spent["calls"] += 1
            spent["tokens_in"] += tin
            spent["tokens_out"] += tout
            calls_log.append({"unit": acct.get("unit", ""), "in": tin, "out": tout, "usd": usd})
        return resp

    return guarded


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
    # a dry run's state marks every chunk done without any model call: never resume it for real
    if state.get("dry_run", bool(state["chunks_done"]) and not state["spent_usd"]) and not DRY_RUN:
        raise SystemExit(
            f"{run} holds a dry run's state; start from an empty /kaggle/working "
            "and do not attach the dry run's zip"
        )
    state["dry_run"] = DRY_RUN
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
    import yaml

    pcfg = yaml.safe_load(open(cfg))
    guard_attempts = int(pcfg["discover"]["retry_on_guard_reject"]) + 1
    psize = {f: os.path.getsize(f) for f in glob.glob(f"{src}/src/xreposkill/prompts/*.txt")}
    plen = {os.path.basename(f): n for f, n in psize.items()}
    analysts = sum(1 for f in plen if f.startswith("analyst_"))
    empty_ids = f"{WORK}/no_eval_ids.txt"
    open(empty_ids, "w").close()

    # cost: the proxy reports each call's cost; the guard uses list prices and MAX_OUT
    spent = {"session": 0.0, "calls": 0, "tokens_in": 0, "tokens_out": 0, "failed_calls": 0}
    acct = {"reserved": 0.0, "stopped": False, "unit": ""}
    calls_log: list[dict] = []

    def left() -> float:
        return min(
            DAY_CAP_USD - spent["session"], ITEM_CAP_USD - out["spent_before"] - spent["session"]
        )

    if DRY_RUN:

        def stub(*, model, system, user, **kw):  # every Stage 1/2 prompt: "no rule"
            spent["calls"] += 1
            return llm.Reply(text="[]", in_tokens=0, out_tokens=0, cost=0.0, finish_reason="stop")

        llm.chat = stub
    else:
        import litellm

        litellm.completion = guard_completion(litellm.completion, left, acct, spent, calls_log)

    def run_unit(unit: str, argv: list[str]) -> bool:
        """Run one cut-able unit; True when it finished, False when the guard cut it."""
        acct["unit"], acct["stopped"] = unit, False
        snap = snapshot(run)
        try:
            rc = cli.main(argv)
        except BudgetStop:
            rc = None
        if acct["stopped"]:
            out.setdefault("rolled_back", []).append({unit: rollback(run, snap)})
            return False
        if rc:
            raise SystemExit(f"{unit} returned {rc}")
        return True

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

    def later_stages(root: str) -> list[tuple[str, list[str]]]:
        return [
            (
                "merge",
                [
                    "--candidates-dir",
                    f"{root}/candidates",
                    "--buckets-dir",
                    f"{root}/buckets",
                    "--out-root",
                    f"{root}/rules_merged",
                    "--config",
                    cfg,
                    "--model",
                    MODEL,
                    "--cost-log",
                    f"{root}/cost_log.jsonl",
                ],
            ),
            (
                "judge",
                [
                    "--rules-root",
                    f"{root}/rules_merged",
                    "--out",
                    f"{root}/rules_judged",
                    "--judge-log",
                    f"{root}/judge_log.jsonl",
                    "--config",
                    cfg,
                    "--model",
                    MODEL,
                    "--workers",
                    str(WORKERS),
                    "--cost-log",
                    f"{root}/cost_log.jsonl",
                ],
            ),
            (
                "score",
                [
                    "--rules-root",
                    f"{root}/rules_judged",
                    "--out",
                    f"{root}/rules_scored",
                    "--pool-dir",
                    pool_dir,
                    "--pairs",
                    pairs,
                    "--log",
                    f"{root}/score_log.jsonl",
                ],
            ),
            (
                "audit",
                [
                    "--rules-root",
                    f"{root}/rules_scored",
                    "--pairs",
                    pairs,
                    "--pool-dir",
                    pool_dir,
                    "--out",
                    f"{root}/ngram_audit.jsonl",
                ],
            ),
        ]

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
    status = "all stages done"
    session_chunks: list[int] = []
    for k, ch in enumerate(chunks):
        if k in state["chunks_done"]:
            continue
        if MAX_CHUNKS is not None and len(session_chunks) >= MAX_CHUNKS:
            status = f"MAX_CHUNKS = {MAX_CHUNKS} reached; set MAX_CHUNKS = None to continue"
            break
        if not DRY_RUN and left() < len(ch) * analysts * PRECHECK_CALL_USD:
            status = f"cap left {left():.2f} USD before chunk {k}; run again tomorrow"
            break
        cf = f"{run}/pairs/chunk_{k:03d}.jsonl"
        open(cf, "w").write("\n".join(ch) + "\n")
        done = run_unit(
            f"discover chunk {k}",
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
            ],
        )
        if not done:
            status = f"cap reached inside chunk {k}; chunk rolled back, run again tomorrow"
            break
        state["chunks_done"].append(k)
        session_chunks.append(k)
        save()
    else:
        for name, args in later_stages(run):
            cdir = f"{run}/candidates"
            has_candidates = os.path.isdir(cdir) and any(
                f.endswith(".jsonl") and f != "failed.jsonl" and os.path.getsize(f"{cdir}/{f}") > 0
                for f in os.listdir(cdir)
            )
            if not has_candidates:  # Stage 1 wrote no rule at all: nothing to merge or score
                if name not in state["stages_done"]:
                    state["stages_done"].append(name)
                continue
            if name in ("merge", "judge") and not DRY_RUN:
                if name in state["stages_done"]:
                    continue
                if not run_unit(name, [name, *args]):
                    status = f"cap reached inside {name}; {name} rolled back, run again tomorrow"
                    break
                state["stages_done"].append(name)
            else:
                stage(name, *args)
            save()
    if MEASURE_MERGE_JUDGE and not DRY_RUN and status.startswith("MAX_CHUNKS"):
        # measuring only: merge and judge on a copy of the candidates so far; the copy is not
        # part of the run (note 45-4), its spend is
        probe = f"{WORK}/w7_{POOL}_mjprobe"
        shutil.rmtree(probe, ignore_errors=True)
        shutil.copytree(run, probe)
        out["mj_probe"] = {}
        for name, args in later_stages(probe)[:2]:
            n0 = len(calls_log)
            ok = run_unit(f"probe {name}", [name, *args])
            out["mj_probe"][name] = {"finished": ok, "calls": calls_log[n0:]}
            if not ok:
                break
        shutil.make_archive(f"{WORK}/w7_{POOL}_mjprobe", "zip", probe)
    json.dump(calls_log, open(f"{run}/w7_calls_{int(time.time())}.json", "w"), indent=1)
    save()
    out.update(
        status=status,
        chunks=len(chunks),
        chunks_done=len(state["chunks_done"]),
        spent_session_usd=round(spent["session"], 4),
        spent_total_usd=round(state["spent_usd"], 4),
        calls=spent["calls"],
        failed_calls=spent["failed_calls"],
        guard_attempts=guard_attempts,
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
