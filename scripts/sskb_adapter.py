"""SWE-Skills-Bench adapter (docs/plan_replication.md, C0). Runs OUR agent (mini-swe-agent
2.4.6 with the E1 model and agent settings) on SWE-Skills-Bench tasks inside THEIR images, and
scores with THEIR hidden tests and THEIR pytest pass-rate rule
(src/evaluator/unit_test_runner.py, repo 4d3450d).

Differences from SWE-Skills-Bench, by design (to be registered in section 22):
  * agent: mini-swe-agent (not Claude Code / Codex CLI);
  * skill arm: the SKILL.md text is placed before the requirement in the prompt (not a /<skill-id>
    slash command over an installed skill directory);
  * scoring happens in the agent's container right after it submits, as theirs does.

  python scripts/sskb_adapter.py build --sskb <clone> --skill asyncio-patterns
  python scripts/sskb_adapter.py run --sskb <clone> --skill asyncio-patterns --batch 1 \
      --arm skill --seed 41 --model gemini-flash-lite --out runs/sskb-x
The `run` step needs the agent environment (litellm, minisweagent); `build` only needs docker.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from pathlib import Path

import yaml

CA = "/root/.ccr/ca-bundle.crt"
CA_IN = "/etc/ssl/certs/ccr-ca.crt"
PROXY_VARS = ("HTTPS_PROXY", "HTTP_PROXY", "https_proxy", "http_proxy", "NO_PROXY", "no_proxy")
CA_VARS = ("GIT_SSL_CAINFO", "SSL_CERT_FILE", "REQUESTS_CA_BUNDLE", "PIP_CERT", "CURL_CA_BUNDLE")
MSWEA_CFG = "minisweagent/config/benchmarks/swebench.yaml"
MODELS = Path("configs/models/vertex_gemini.json")
REGISTRY = Path("runs/g1-e1-s41-p00/litellm_registry.json")  # the price registry E1 used

# ---------- pure functions (tests/test_sskb_adapter.py) ----------

TEMPLATE_EDITS = [
    (
        "Your task is specifically to make changes to non-test files in the current directory "
        "in order to fix the issue described in the PR description in a way that is general and "
        "consistent with the codebase.",
        "Your task is to implement the requirements in the PR description in the repository in "
        "the current directory, in a way that is general and consistent with the codebase.",
    ),
    (
        "- MODIFY: Regular source code files in /testbed (this is the working directory for all "
        "your subsequent commands)\n- DO NOT MODIFY: Tests, configuration files "
        "(pyproject.toml, setup.cfg, etc.)",
        "- MODIFY: any files the PR description asks you to create or change, in {repo_dir} "
        "(this is the working directory for all your subsequent commands)",
    ),
]
SUBMISSION = (
    "## Submission\n\nWhen you have finished, submit with this EXACT command, on its own:"
    "\n\n```bash\necho COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT\n```\n\n"
    "Your changes are evaluated in place in the "
    "repository. You CANNOT continue working after submitting.\n</instructions>\n"
)


def adapt_template(t: str, repo_dir: str) -> str:
    """E1's instance template with the three registered edits; each edit must apply exactly once."""
    for old, new in TEMPLATE_EDITS:
        if t.count(old) != 1:
            raise ValueError(f"template edit does not apply exactly once: {old[:60]}")
        t = t.replace(old, new.replace("{repo_dir}", repo_dir))
    i, j = t.find("## Submission"), t.find("</instructions>")
    if i < 0 or j < i:
        raise ValueError("submission section not found")
    return t[:i] + SUBMISSION + t[j + len("</instructions>") :].lstrip("\n")


SKILL_DIR_IN = "/home/dev/skills"


def task_text(requirement: str, skill_md: str | None, skill_id: str = "") -> str:
    if skill_md is None:
        return requirement
    return (
        "The following skill document is available for this task. Use it if it helps. Its "
        f"supporting files, if any, are in {SKILL_DIR_IN}/{skill_id}/.\n"
        f"<skill>\n{skill_md}\n</skill>\n\n{requirement}"
    )


def strip_cd(cmd: str) -> str:
    """Their lifecycle.py strips a leading 'cd /workspace/<x> &&' and runs in the real repo dir."""
    return re.sub(r"^\s*cd\s+/workspace/\S+\s*&&\s*", "", cmd)


_ANSI = re.compile(r"\x1b\[[0-9;]*[mGKH]")
_SUMMARY = re.compile(
    r"^=.*\b\d+\s+(?:passed|failed|error|skipped).*\bin\s+[\d.]+s\b.*=*\s*$", re.MULTILINE
)


def parse_pytest(output: str) -> dict:
    """Same rule as SWE-Skills-Bench _parse_pytest_output: counts from the summary line, total =
    passed + failed + skipped + errors, fallback to PASSED/FAILED lines;
    pass_rate = passed/total."""
    clean = _ANSI.sub("", output)
    r = {"passed": 0, "failed": 0, "skipped": 0, "errors": 0}
    m = _SUMMARY.search(clean)
    if m:
        line = m.group(0)
        for k, pat in (
            ("passed", r"(\d+)\s+passed"),
            ("failed", r"(\d+)\s+failed"),
            ("skipped", r"(\d+)\s+skipped"),
            ("errors", r"(\d+)\s+errors?"),
        ):
            mm = re.search(pat, line)
            if mm:
                r[k] = int(mm.group(1))
    r["total"] = r["passed"] + r["failed"] + r["skipped"] + r["errors"]
    if r["total"] == 0:
        p, f = len(re.findall(r"\bPASSED\b", clean)), len(re.findall(r"\bFAILED\b", clean))
        if p or f:
            r.update(passed=p, failed=f, total=p + f)
    r["pass_rate"] = r["passed"] / r["total"] if r["total"] else None
    return r


# ---------- data ----------


def skill_cfg(sskb: Path, skill: str) -> dict:
    cfg = yaml.safe_load((sskb / "config/benchmark_config.yaml").read_text())["skills"]
    return next(s for s in cfg if s["id"] == skill)


def repo_dir(sc: dict) -> str:
    return "/workspace/" + sc["repo"]["url"].rstrip("/").split("/")[-1]


def image_tag(sc: dict) -> str:
    return f"gk-sskb/{sc['id']}:{sc['repo']['commit'][:12]}"


def net_args() -> list[str]:
    args = ["--network", "host", "-v", f"{CA}:{CA_IN}:ro"]
    return args


def net_env() -> dict[str, str]:
    env = {k: os.environ[k] for k in PROXY_VARS if k in os.environ}
    env.update({k: CA_IN for k in CA_VARS})
    return env


def sh(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def build(sskb: Path, skill: str) -> str:
    """Base image + repo at the pinned commit + setup commands -> committed image.
    The proxy settings are passed to `docker exec`, so they are not stored in the image."""
    sc = skill_cfg(sskb, skill)
    tag = image_tag(sc)
    if sh(["docker", "image", "inspect", tag]).returncode == 0:
        return tag
    base, rd = sc["environment"]["base_image"], repo_dir(sc)
    cid = sh(
        ["docker", "run", "-d", "-u", "root", *net_args(), base, "sleep", "infinity"]
    ).stdout.strip()
    if not cid:
        raise SystemExit(f"cannot start {base}")
    envflags = [x for k, v in net_env().items() for x in ("-e", f"{k}={v}")]
    steps = [
        f"mkdir -p {rd} && cd {rd} && git init -q && git remote add origin {sc['repo']['url']}",
        f"cd {rd} && git fetch -q --depth 1 origin {sc['repo']['commit']}",
        f"cd {rd} && git checkout -q FETCH_HEAD",
        *[f"cd {rd} && {strip_cd(c)}" for c in sc["environment"].get("setup_commands") or []],
        "chown -R dev:dev /workspace || true",
    ]
    try:
        for s in steps:
            r = sh(["docker", "exec", "-u", "root", *envflags, cid, "bash", "-lc", s], timeout=3600)
            if r.returncode:
                raise SystemExit(f"build step failed: {s}\n{r.stdout[-2000:]}\n{r.stderr[-2000:]}")
        cfg = sh(["docker", "image", "inspect", base, "--format", "{{json .Config}}"]).stdout
        user = json.loads(cfg or "{}").get("User") or "root"
        # keep the base image's user: the build container ran as root to clone and install
        r = sh(["docker", "commit", "--change", f"USER {user}", cid, tag])
        if r.returncode:
            raise SystemExit(r.stderr)
    finally:
        sh(["docker", "rm", "-f", cid])
    return tag


def score(env, sskb: Path, sc: dict, batch: int) -> dict:
    """Copy the hidden test into the agent's container and run their test_command."""
    test = sskb / f"tests/batch{batch}/test_{sc['id'].replace('-', '_')}.py"
    params = next(
        e["params"] for e in sc["environment"]["evaluation"] if e.get("method") == "unit_test"
    )
    sh(["docker", "exec", "-u", "root", env.container_id, "mkdir", "-p", "/workspace/tests"])
    for helper in sorted((sskb / f"tests/batch{batch}").glob("_*.py")):
        sh(["docker", "cp", str(helper), f"{env.container_id}:/workspace/tests/{helper.name}"])
    r = sh(["docker", "cp", str(test), f"{env.container_id}:/workspace/tests/{test.name}"])
    if r.returncode:
        return {"error": f"cannot copy test: {r.stderr}"}
    sh(
        [
            "docker",
            "exec",
            "-u",
            "root",
            env.container_id,
            "chown",
            "-R",
            "dev:dev",
            "/workspace/tests",
        ]
    )
    out = env.execute({"command": params["test_command"]}, timeout=int(params.get("timeout", 600)))
    res = parse_pytest(out.get("output", ""))
    res["returncode"] = out.get("returncode")
    return res


def run(a) -> dict:
    import importlib.resources as ir

    from minisweagent.agents import get_agent
    from minisweagent.environments import get_environment
    from minisweagent.models import get_model

    sc = skill_cfg(a.sskb, a.skill)
    rd = repo_dir(sc)
    base_cfg = yaml.safe_load((ir.files("minisweagent") / MSWEA_CFG.split("/", 1)[1]).read_text())
    agent_cfg = dict(base_cfg["agent"])
    agent_cfg["instance_template"] = adapt_template(agent_cfg["instance_template"], rd)
    agent_cfg.update(step_limit=250, cost_limit=1.0)  # E1 settings
    env_cfg = dict(base_cfg["environment"])
    env_cfg.update(image=build(a.sskb, a.skill), cwd=rd, run_args=["--rm", *net_args()])
    env_cfg["env"] = {k: v for k, v in env_cfg["env"].items() if k != "BASH_ENV"} | net_env()
    if a.model == "deterministic":
        mcfg = {
            "model_class": "deterministic",
            "model_name": "deterministic",
            "outputs": [
                {
                    "role": "assistant",
                    "content": "THOUGHT: submit.",
                    "extra": {
                        "actions": [{"command": "echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT"}],
                        "cost": 0.0,
                    },
                }
            ],
        }
    else:
        spec = json.loads(MODELS.read_text())["models"][a.model]
        mcfg = dict(base_cfg["model"]) | {
            "model_name": spec["litellm_name"],
            "model_kwargs": {"drop_params": True, "parallel_tool_calls": True, "seed": a.seed},
            "litellm_model_registry": str(REGISTRY.resolve()),
            "cost_tracking": "default",
        }
    model = get_model(config=mcfg)
    env = get_environment(env_cfg, default_type="docker")
    agent = get_agent(model, env, agent_cfg, default_type="default")
    req = (a.sskb / f"tasks/batch{a.batch}/{a.skill}.md").read_text()
    skill_md, skill_files = None, 0
    if a.arm == "skill":  # as their skill_mode "one": the whole skill directory is installed
        skill_md = (a.sskb / f"skills/{a.skill}/SKILL.md").read_text()
        cid = env.container_id
        sh(["docker", "exec", "-u", "root", cid, "mkdir", "-p", SKILL_DIR_IN])
        sh(["docker", "cp", str(a.sskb / f"skills/{a.skill}"), f"{cid}:{SKILL_DIR_IN}/{a.skill}"])
        sh(["docker", "exec", "-u", "root", cid, "chown", "-R", "dev:dev", SKILL_DIR_IN])
        n = sh(
            ["docker", "exec", cid, "bash", "-c", f"find {SKILL_DIR_IN}/{a.skill} -type f | wc -l"]
        )
        skill_files = int(n.stdout.strip() or 0)
    out_dir = Path(a.out) / f"{a.skill}-b{a.batch}-s{a.seed}-{a.arm}"
    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        info = agent.run(task_text(req, skill_md, a.skill))
        exit_status = info.get("exit_status")
    except Exception as e:  # limits or errors end the run; it is still scored as-is
        exit_status = type(e).__name__
    res = score(env, a.sskb, sc, a.batch)
    data = agent.save(out_dir / "traj.json")
    env.cleanup()
    stats = (data.get("info") or {}).get("model_stats") or {}
    result = {
        "skill": a.skill,
        "batch": a.batch,
        "arm": a.arm,
        "seed": a.seed,
        "model": a.model,
        "exit_status": exit_status,
        "cost_usd": stats.get("instance_cost"),
        "n_calls": stats.get("api_calls"),
        "skill_files": skill_files,
        **res,
    }
    (out_dir / "result.json").write_text(json.dumps(result, indent=1) + "\n")
    print(json.dumps(result))
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["build", "run"])
    ap.add_argument("--sskb", type=Path, required=True)
    ap.add_argument("--skill", required=True)
    ap.add_argument("--batch", type=int)
    ap.add_argument("--arm", choices=["none", "skill"])
    ap.add_argument("--seed", type=int)
    ap.add_argument("--model")
    ap.add_argument("--out")
    a = ap.parse_args()
    if a.step == "build":
        print(build(a.sskb, a.skill))
    else:
        if None in (a.batch, a.arm, a.seed, a.model, a.out):
            ap.error("run needs --batch --arm --seed --model --out")
        run(a)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
