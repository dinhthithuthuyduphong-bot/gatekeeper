"""Section 40 (C3, C4): gskill's agent on SWE-smith tasks with no container, model through an
OpenAI-compatible endpoint (Kaggle's Model Proxy).

A thin wrapper around scripts/f1_probe.py of branch `trial` (the script of every paid agent run of
the paper), which is executed unchanged. The wrapper only
  * points mini-swe-agent's `docker` command and SWE-smith's and gskill's Docker SDK at one of two
    stand-ins (--isolation): local_shim + fake_docker.py (environment rebuilt from the image's
    package list; gate C1; no isolation, kaggle/audit.md K21), or chroot_shim (a chroot of the
    image's own file system per task; gate C5, note 40-4);
  * gives the model call its endpoint: OPENAI_API_BASE / OPENAI_API_KEY are set in this process
    from the two variables named by --base-env / --key-env (never printed, never written), and the
    base URL is also put into the model kwargs because gskill's run_agent would otherwise send any
    model whose name contains "openai" to api.openai.com;
  * sums the cost the endpoint reports on each reply (usage.cost, nanodollars) next to LiteLLM's
    own figure from --registry, and writes both to <out>.cost.json.

  PYTHONPATH=<gepa>/src/gepa/gskill:<dir with f1_probe.py, f0_scorer_check.py> python c3_agent.py \
      --isolation chroot --base-env MODEL_PROXY_URL \
      --key-env MODEL_PROXY_API_KEY --base-suffix /openapi -- <arguments of f1_probe.py>
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))


FORMAT_TAG = re.compile(r"<\|(?:start|channel|message|end|return|call|constrain)\|>")


def strip_format_tags(messages: list[dict]) -> list[dict]:
    """Copy of the messages with gpt-oss format tags replaced by a space (note 40-15)."""
    out = []
    for m in messages:
        c = m.get("content")
        out.append({**m, "content": FORMAT_TAG.sub(" ", c)} if isinstance(c, str) else m)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--isolation",
        required=True,
        choices=["local", "chroot"],
        help="local: local_shim (no isolation; C3, C4 session 1); chroot: chroot_shim (gate C5)",
    )
    ap.add_argument("--packages", type=Path, help="local isolation only: the image's packages")
    ap.add_argument("--base-env", required=True)
    ap.add_argument("--key-env", required=True)
    ap.add_argument(
        "--base-suffix", required=True, help='appended to the base URL, e.g. "/openapi"'
    )
    ap.add_argument(
        "--drop-kwargs",
        nargs="*",
        default=[],
        help="model kwargs of f1_probe.py that the endpoint rejects (recorded as a deviation)",
    )
    ap.add_argument(
        "--strip-format-tags",
        action="store_true",
        help="remove the model's own format tags from messages sent back (note 40-15)",
    )
    ap.add_argument("rest", nargs=argparse.REMAINDER)
    a = ap.parse_args()
    rest = a.rest[1:] if a.rest[:1] == ["--"] else a.rest
    out = Path(rest[rest.index("--out") + 1])
    rows = Path(rest[rest.index("--rows") + 1])
    mock = "--mock-response" in rest

    if a.isolation == "local" and a.packages is None:
        raise SystemExit("--packages is required with --isolation local")
    docker_cli = "fake_docker.py" if a.isolation == "local" else "chroot_shim.py"
    os.environ["MSWEA_DOCKER_EXECUTABLE"] = str(HERE / docker_cli)  # before minisweagent
    base = os.environ.get(a.base_env, "").rstrip("/")
    for suffix in ("/openapi", "/genai"):
        base = base.removesuffix(suffix)
    base += a.base_suffix
    if not mock:
        if not os.environ.get(a.base_env) or not os.environ.get(a.key_env):
            raise SystemExit(f"{a.base_env} or {a.key_env} is not set")
        os.environ["OPENAI_API_BASE"] = base
        os.environ["OPENAI_API_KEY"] = os.environ[a.key_env]

    import gzip

    from swesmith.profiles import registry

    raw = rows.read_bytes()
    text = (gzip.decompress(raw) if rows.name.endswith(".gz") else raw).decode("utf-8")
    first = json.loads(next(x for x in text.splitlines() if x.strip()))
    rp = registry.get_from_inst(first)
    rp._cache_repo_private = False  # the mirror is public (cloned anonymously); f0: assume_public
    mirror = f"https://github.com/{rp.mirror_name}"
    if a.isolation == "local":
        import local_shim as shim

        spec = json.loads(a.packages.read_text())
        shim.prepare(mirror, spec["python"], spec["packages"], list(rp.install_cmds))
    else:
        import chroot_shim as shim

        shim.prepare(rp.image_name, mirror)
    import gskill.swe_harness  # noqa: F401 - must be imported before install() patches it

    shim.install()

    import f1_probe

    if a.strip_format_tags:
        import litellm

        sent = litellm.completion

        def completion(*args, **kw):  # the stored trajectory keeps the reply as returned
            if kw.get("messages"):
                kw["messages"] = strip_format_tags(kw["messages"])
            return sent(*args, **kw)

        litellm.completion = completion

    reported = {"calls": 0, "endpoint_usd": 0.0, "tokens_in": 0, "tokens_out": 0}
    inner = f1_probe._track  # sums LiteLLM's response_cost into f1_probe._spent (its budget cap)

    def track(kwargs, response, start, end):
        inner(kwargs, response, start, end)
        u = getattr(response, "usage", None)
        reported["calls"] += 1
        reported["tokens_in"] += int(getattr(u, "prompt_tokens", 0) or 0)
        reported["tokens_out"] += int(getattr(u, "completion_tokens", 0) or 0)
        c = getattr(u, "cost", None) or {}
        if isinstance(c, dict):
            n = (c.get("input_tokens_cost_nanodollars") or 0) + (
                c.get("output_tokens_cost_nanodollars") or 0
            )
            reported["endpoint_usd"] += n / 1e9
        out.with_suffix(".cost.json").write_text(
            json.dumps({**reported, "litellm_usd": f1_probe._spent}) + "\n"
        )

    make = f1_probe.make_config

    def make_config(gskill_yaml, cfg_out, cost_limit, model_kwargs):
        model_kwargs = {k: v for k, v in model_kwargs.items() if k not in a.drop_kwargs}
        if not mock:
            model_kwargs = {**model_kwargs, "api_base": base}
        return make(gskill_yaml, cfg_out, cost_limit, model_kwargs)

    f1_probe._track = track  # f1_probe.main registers the module's _track with LiteLLM
    f1_probe.make_config = make_config
    sys.argv = ["f1_probe.py", *rest]
    return f1_probe.main()


if __name__ == "__main__":
    raise SystemExit(main())
