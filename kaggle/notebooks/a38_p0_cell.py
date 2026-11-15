# P0 of sections 38-39 (kaggle/preregistration_s38.md). Paste this whole file into ONE cell of a
# notebook created from https://www.kaggle.com/benchmarks/tasks/new. Before running it, write down
# the AI quota used today (Settings > Quotas); after it, write it down again and send both numbers.
#
# What it does (cap: about 0.30 USD of the free quota):
#   1. lists every model the library offers;
#   2. sends a 5-word prompt once to each model that matches a name rule below (other models,
#      e.g. large reasoning models, are not called), with temperature=None (gskill sets no
#      temperature, so the provider default is the faithful setting), and records whether that is
#      accepted and what usage or cost information the library returns;
#   3. sends ONE real saved prompt of section 38 (about 19 thousand tokens) to one model per vendor
#      family, chosen by the name rule below, to measure tokens and cost per call.
# It prints no key, no account detail and no environment value; it writes /kaggle/working/p0.json.
import gzip
import hashlib
import inspect
import json
import re
import time
import traceback
import urllib.request

COMMIT = "989d6ec31818ece5a2762d9380493a7e92dfbee9"  # holds the data file
SHA256 = "2e6425aa48553a2fd337e57935ab924f69bb27348441dda4730ec1e57e718b02"  # sha256 of that file
URL = (
    "https://raw.githubusercontent.com/dinhthithuthuyduphong-bot/gatekeeper/"
    f"{COMMIT}/kaggle/data/a38_prompts.jsonl.gz"
)
REAL_PID = "clean-c08-ablated"  # the clean-run prompt whose length is the median (74,305 chars)
OUT = "/kaggle/working/p0.json"
out = {"started": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "tiny": {}, "real": {}}


def save():
    with open(OUT, "w") as fh:
        json.dump(out, fh, indent=1, default=str)


def load_prompts():
    import glob

    local = glob.glob("/kaggle/input/**/a38_prompts.jsonl.gz", recursive=True)
    if local:
        raw, out["data_from"] = open(local[0], "rb").read(), "dataset"
    else:
        raw, out["data_from"] = urllib.request.urlopen(URL, timeout=120).read(), "github"
    got = hashlib.sha256(raw).hexdigest()
    if got != SHA256:
        raise SystemExit(f"data file sha256 {got} != registered {SHA256}")
    return {r["pid"]: r for r in map(json.loads, gzip.decompress(raw).decode().splitlines())}


def describe(obj):
    """Type and public attributes of a returned object, values cut to 300 characters."""
    d = {"type": type(obj).__name__, "text": str(obj)[:300]}
    for n in dir(obj):
        if n.startswith("_") or n in ("text",):
            continue
        try:
            v = getattr(obj, n)
        except Exception:
            continue
        if not callable(v):
            d[n] = str(v)[:300]
    return d


def usage_probe(kbench, llm):
    """Whatever usage or cost the library exposes after a call (names are not documented)."""
    found = {}
    for owner, name in ((llm, "llm"), (kbench, "kbench")):
        for attr in dir(owner):
            if re.search(r"usage|cost|token|spend|budget", attr, re.I):
                try:
                    v = getattr(owner, attr)
                    found[f"{name}.{attr}"] = str(v() if callable(v) else v)[:500]
                except Exception as e:
                    found[f"{name}.{attr}"] = f"error: {e!r}"[:200]
    return found


def call(llm, text, **kw):
    t0 = time.time()
    try:
        r = llm.prompt(text, **kw)
        return {
            "ok": True,
            "secs": round(time.time() - t0, 1),
            "reply_chars": len(str(r)),
            "reply": describe(r),
        }
    except Exception as e:
        return {"ok": False, "secs": round(time.time() - t0, 1), "error": repr(e)[:600]}


# Name rule for step 3 (one model per family; the latest version by name among matching keys).
FAMILIES = {
    "anthropic_small": r"haiku",
    "openai_small": r"gpt-[0-9.]+-(nano|mini)",
    "xai_fast": r"grok.*fast",
    "open_weights_openai": r"gpt-oss",
    "open_weights_google": r"gemma",
    "gemini_pro_reference": r"gemini.*pro",
}

try:
    import kaggle_benchmarks as kbench

    out["version"] = getattr(kbench, "__version__", "?")
    models = sorted(kbench.llms.keys())
    out["models"] = models
    out["signature_prompt"] = str(inspect.signature(kbench.llm.prompt))[:600]
    save()
    cand = [m for m in models if any(re.search(p, m, re.I) for p in FAMILIES.values())]
    out["candidates"] = cand
    for m in cand:
        llm = kbench.llms[m]
        a = call(llm, "Reply with the single word OK.", temperature=None, seed=1)
        if not a["ok"]:
            a["fallback_no_temperature_arg"] = call(llm, "Reply with the single word OK.", seed=1)
        a["usage"] = usage_probe(kbench, llm)
        out["tiny"][m] = a
        save()
    prompts = load_prompts()
    real = prompts[REAL_PID]["prompt"]
    out["real_prompt_chars"] = len(real)
    for fam, pat in FAMILIES.items():
        keys = [m for m in cand if re.search(pat, m, re.I) and out["tiny"][m]["ok"]]
        if not keys:
            out["real"][fam] = {"ok": False, "error": "no model matches the name rule"}
            continue
        m = sorted(keys)[-1]
        r = call(kbench.llms[m], real, temperature=None, seed=1)
        r["model"], r["usage"] = m, usage_probe(kbench, kbench.llms[m])
        out["real"][fam] = r
        save()
except Exception:
    out["error"] = traceback.format_exc()[-1500:]
out["finished"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
save()
print(json.dumps({k: v for k, v in out.items() if k != "tiny"}, indent=1, default=str)[:6000])
print("tiny-prompt results:", {m: v["ok"] for m, v in out["tiny"].items()})
print("Saved", OUT, "- download it (Output panel) and send it, with the quota before and after.")
