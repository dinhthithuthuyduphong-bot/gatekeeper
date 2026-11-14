# K0c, K0d of section 37 (kaggle/preregistration_s37.md). Paste this whole file into ONE cell of a
# notebook created from https://www.kaggle.com/benchmarks/tasks/new (kaggle_benchmarks is only
# pre-installed there). It calls the default model three times (a few cents of the AI quota),
# prints no key or account detail, and writes /kaggle/working/k0cd.json.
import json
import os
import traceback

out = {"env_names": sorted(k for k in os.environ if k.startswith(("MODEL_PROXY", "LLM")))}
try:
    import kaggle_benchmarks as kbench

    out["version"] = getattr(kbench, "__version__", "?")
    out["api"] = sorted(n for n in dir(kbench) if not n.startswith("_"))
    try:
        llms = kbench.llms
        out["models"] = sorted(llms.keys()) if hasattr(llms, "keys") else str(llms)[:3000]
    except Exception as e:
        out["models_error"] = repr(e)[:300]
    llm = kbench.llm
    out["llm_default"] = str(getattr(llm, "name", llm))[:200]
    out["llm_api"] = sorted(n for n in dir(llm) if not n.startswith("_"))
    # K0d (a): does a second prompt see the first one (multi-turn history)?
    out["reply_1"] = str(llm.prompt("Reply with exactly the word: alpha"))[:200]
    q2 = "Which single word did you reply with in your previous message?"
    out["reply_2"] = str(llm.prompt(q2))[:200]
    # K0d (b): which keyword arguments does prompt() accept (temperature, seed, system prompt)?
    import inspect

    for name in ("prompt", "send", "respond"):
        f = getattr(llm, name, None)
        if f is not None:
            try:
                out[f"signature_{name}"] = str(inspect.signature(f))[:600]
            except (TypeError, ValueError) as e:
                out[f"signature_{name}"] = repr(e)[:200]
    for attr in ("usage", "last_usage", "cost", "last_response", "history", "messages"):
        if hasattr(llm, attr):
            out[attr] = str(getattr(llm, attr))[:800]
except Exception:
    out["error"] = traceback.format_exc()[-1500:]
with open("/kaggle/working/k0cd.json", "w") as fh:
    json.dump(out, fh, indent=1, default=str)
print(json.dumps(out, indent=1, default=str)[:5000])
