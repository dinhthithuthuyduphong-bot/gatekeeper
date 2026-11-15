# P0b of sections 38-39 (kaggle/preregistration_s38.md, note 38-2). Paste this whole file into ONE
# cell of a notebook created from https://www.kaggle.com/benchmarks/tasks/new. Write down the AI
# quota used today before and after, as for P0. Cap: about 0.40 USD of the free quota.
#
# It sends the same saved prompt of P0 (clean-c08-ablated, 74,305 characters) once to each model
# of the fixed candidate list below, and records the tokens and cost that Kaggle's Model Proxy
# attaches to the reply (kaggle_benchmarks 0.6.3 keeps them on the reply message: P0 read the
# wrong object). It prints no key, no account detail and no environment value; it writes
# /kaggle/working/p0b.json.
import gzip
import hashlib
import json
import time
import traceback
import urllib.request

COMMIT = "989d6ec31818ece5a2762d9380493a7e92dfbee9"  # holds the data file
SHA256 = "2e6425aa48553a2fd337e57935ab924f69bb27348441dda4730ec1e57e718b02"
URL = (
    "https://raw.githubusercontent.com/dinhthithuthuyduphong-bot/gatekeeper/"
    f"{COMMIT}/kaggle/data/a38_prompts.jsonl.gz"
)
PID = "clean-c08-ablated"
CANDIDATES = [  # note 38-2: small tiers by name, every xAI model, open weights, the reference
    "anthropic/claude-haiku-4-5@20251001",
    "anthropic/claude-haiku-5-5",
    "openai/gpt-5.4-nano-2026-03-17",
    "openai/gpt-5.4-mini-2026-03-17",
    "xai/grok-4.5-0708",
    "xai/grok-4.6",
    "xai/grok-4.7",
    "openai/gpt-oss-120b",
    "google/gemma-4-26b-a4b",
    "google/gemma-4-31b",
    "google/gemini-3.1-pro-preview",
]
OUT = "/kaggle/working/p0b.json"
out = {"started": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "calls": {}}


def save():
    with open(OUT, "w") as fh:
        json.dump(out, fh, indent=1, default=str)


try:
    import kaggle_benchmarks as kbench
    from kaggle_benchmarks import chats

    raw = urllib.request.urlopen(URL, timeout=120).read()
    if hashlib.sha256(raw).hexdigest() != SHA256:
        raise SystemExit("data file does not match the registered sha256")
    rows = {r["pid"]: r for r in map(json.loads, gzip.decompress(raw).decode().splitlines())}
    prompt = rows[PID]["prompt"]
    for m in CANDIDATES:
        rec = {}
        try:
            llm = kbench.llms[m]
            rec["support_temperature"] = getattr(llm, "support_temperature", "?")
            rec["seed_removed"] = bool(getattr(llm, "_should_remove_seed", lambda: "?")())
            t0 = time.time()
            reply = llm.prompt(prompt, seed=1)
            rec["secs"] = round(time.time() - t0, 1)
            msgs = chats.get_current_chat().messages
            u = msgs[-1].usage
            rec.update(
                ok=True,
                reply_chars=len(str(reply)),
                reply_head=str(reply)[:200],
                messages_in_chat_after=len(msgs),
                input_tokens=u.input_tokens,
                output_tokens=u.output_tokens,
                cost_usd=None
                if u.total_cost_nanodollars is None
                else u.total_cost_nanodollars / 1e9,
            )
        except Exception as e:
            rec.update(ok=False, error=repr(e)[:600])
        out["calls"][m] = rec
        save()
        print(m, {k: rec.get(k) for k in ("ok", "input_tokens", "output_tokens", "cost_usd")})
except Exception:
    out["error"] = traceback.format_exc()[-1500:]
out["total_cost_usd"] = sum(c.get("cost_usd") or 0 for c in out["calls"].values())
out["finished"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
save()
print("total cost reported:", out["total_cost_usd"], "- send", OUT, "and the quota before/after")
