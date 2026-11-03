"""Pre-execution checks: the machine-checkable part of docs/research_rules.md section 4 (rule R3).

  python scripts/preflight.py            # all checks
  python scripts/preflight.py --ci       # in GitHub Actions (lint and tests run as their own steps)

Checks (each comes from a past error, see docs/lessons_learned.md):
  defaults  no function in src/ or the analysis scripts has a numeric DEFAULT for a scientific
            parameter (alpha, theta, cell_frac, composite_frac, readmit_frac)          (L13, A42)
  sources   every source in configs/sources.json was fetched and contains >= 1 of its keywords;
            the ones that do not are listed as UNVERIFIED (they may not support any conclusion) (R1)
  results   no committed run result has an unexplained endpoint mismatch, and no run result
            carries the removed per-batch admission fields (theta/alpha)                (A29, A42)
  terms     no vague evaluative wording without a number in paper-bound documents      (R6)
  secrets   no tracked or staged file contains a private key                            (security)
  lint/test ruff check, ruff format --check, pytest (skipped with --ci: separate CI steps)
Exit code 1 if any check fails; UNVERIFIED sources are reported, not failures (they are tracked
in docs/research_rules.md section 5)."""

from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
from pathlib import Path

SCIENTIFIC = {"alpha", "theta", "cell_frac", "composite_frac", "readmit_frac", "alpha_cell"}
ANALYSIS = [
    "scripts/analyze_g1_final.py",
    "scripts/rq1_mini.py",
    "scripts/verify_methods.py",
    "scripts/make_e1_extension.py",
    "scripts/make_e2_selection.py",
    "scripts/combine_runs.py",
]


def check_defaults() -> list[str]:
    bad = []
    files = sorted(Path("src/gatekeeper").glob("*.py")) + [Path(f) for f in ANALYSIS]
    for f in files:
        tree = ast.parse(f.read_text())
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            a = node.args
            pos = a.posonlyargs + a.args
            pairs = list(zip(pos[len(pos) - len(a.defaults) :], a.defaults, strict=True))
            pairs += [(k, d) for k, d in zip(a.kwonlyargs, a.kw_defaults, strict=True) if d]
            for arg, d in pairs:
                if (
                    arg.arg in SCIENTIFIC
                    and isinstance(d, ast.Constant)
                    and isinstance(d.value, (int, float))
                    and not isinstance(d.value, bool)
                ):
                    bad.append(f"{f}:{node.lineno} {node.name}({arg.arg}={d.value})")
    return bad


def check_sources() -> tuple[list[str], list[str]]:
    cfg = json.loads(Path("configs/sources.json").read_text())["sources"]
    subprocess.run(["git", "fetch", "-q", "origin", "sources-snapshots"], check=False)
    try:
        names = set(
            subprocess.check_output(
                ["git", "ls-tree", "--name-only", "-r", "origin/sources-snapshots"], text=True
            ).split()
        )
    except subprocess.CalledProcessError:
        return [], ["sources-snapshots branch not available"]
    ok, unverified = [], []
    for s in cfg:
        f = f"data/sources/{s['id']}.json"
        if f not in names:
            unverified.append(f"{s['id']}: not fetched")
            continue
        d = json.loads(subprocess.check_output(["git", "show", f"origin/sources-snapshots:{f}"]))
        hits = [k for k, v in (d.get("excerpts") or {}).items() if v]
        if hits:
            ok.append(s["id"])
            continue
        sys.path.insert(0, str(Path(__file__).parent))
        from fetch_sources import previous_good  # noqa: PLC0415

        prev = previous_good(s["id"])
        unverified.append(
            f"{s['id']}: latest fetch has no keyword; good snapshot in history "
            f"{prev['snapshot_commit'][:7]} ({prev['url']}), restored by the next sources run (A44)"
            if prev
            else f"{s['id']}: never verified"
        )
    return ok, unverified


def check_results() -> list[str]:
    bad = []
    for f in sorted(Path("results/pilot").glob("*.json")):
        d = json.loads(f.read_text())
        if "instances" not in d or d.get("merged_from"):
            continue
        # every agent run of an arm is either scored or listed as an infrastructure failure: a run
        # that is neither was lost silently (e.g. a harness crash after scoring, audit A51)
        for arm, u in (d.get("usage") or {}).items():
            if u.get("scored") is None:  # files older than the "scored" field (audit A16)
                continue
            n_infra = len((d.get("infra_failures") or {}).get(arm, {}))
            if (u.get("runs") or 0) != (u.get("scored") or 0) + n_infra:
                bad.append(
                    f"{f.name}: arm {arm} runs {u.get('runs')} != scored {u.get('scored')}"
                    f" + infra {n_infra}"
                )
        if d.get("endpoint_mismatch"):
            bad.append(f"{f.name}: endpoint mismatch {d['endpoint_mismatch']}")
        # files written before A42 keep their (unused) fields: raw results are never rewritten
        if d.get("format_version", 1) >= 2 and any(
            "eprocess" in v for v in d.get("skills", {}).values()
        ):
            bad.append(f"{f.name}: per-batch admission decision present (removed, A42)")
    return bad


# Real key material only (audit A47): the PEM header WITH its dashes, and the JSON field of a
# Google service-account key file. Prose that merely names the check does not match.
SECRET_PATTERNS = ["-" * 5 + "BEGIN " + "PRIVATE KEY" + "-" * 5, '"private' + '_key":']


# Rule R6 (docs/research_rules.md): no vague evaluative wording in documents that go into the
# paper or the report. A sentence with one of these words must carry a number; comparisons
# ("nho hon", "lon nhat", "it nhat") and verbatim quotes ("...") are exempt.
VAGUE_TERMS = ["gần như", "rất", "khá", "hơi", "đáng kể", "mạnh", "yếu", "quy mô nhỏ", "quy mô lớn"]
COMPARATIVE = re.compile(r"(nhỏ|lớn|cao|thấp|nhiều|ít|mạnh|yếu)\s+(hơn|nhất)|ít nhất|nhiều nhất")
PAPER_DOCS = [
    "docs/method_check.md",
    "docs/preregistration_e1.md",
    "docs/preregistration_e2.md",
    "docs/glossary.md",
]


def check_terms(files: list[str] = PAPER_DOCS) -> list[str]:
    bad = []
    for f in files:
        for i, line in enumerate(Path(f).read_text(encoding="utf-8").splitlines(), 1):
            text = re.sub(r"\"[^\"]*\"|“[^”]*”", "", line)  # verbatim quotes are exempt
            for sent in re.split(r"(?<=[.;])\s", text):
                low = COMPARATIVE.sub("", sent.lower())
                hits = [w for w in VAGUE_TERMS if re.search(rf"(?<!\w){re.escape(w)}(?!\w)", low)]
                if hits and not re.search(r"\d", sent):
                    bad.append(f"{f}:{i} vague {hits}: {sent.strip()[:100]}")
    return bad


def check_secrets() -> list[str]:
    bad = []
    staged = subprocess.run(["git", "diff", "--cached"], capture_output=True, text=True).stdout
    for pat in SECRET_PATTERNS:
        out = subprocess.run(
            ["git", "grep", "-l", "-F", "--", pat], capture_output=True, text=True
        ).stdout
        bad += [f"tracked file contains key material ({pat!r}): {x}" for x in out.split()]
        if pat in staged:
            bad.append(f"staged changes contain key material ({pat!r})")
    return bad


def run(cmd: list[str]) -> bool:
    return subprocess.run(cmd, check=False).returncode == 0


def main() -> int:
    ci = "--ci" in sys.argv
    failures: list[str] = []
    d = check_defaults()
    print(f"[defaults] {'ok' if not d else 'FAIL'}")
    failures += d
    r = check_results()
    print(f"[results] {'ok' if not r else 'FAIL'}")
    failures += r
    t = check_terms()
    print(f"[terms] {'ok' if not t else 'FAIL'}")
    failures += t
    s = check_secrets()
    print(f"[secrets] {'ok' if not s else 'FAIL'}")
    failures += s
    ok, unverified = check_sources()
    print(
        f"[sources] {len(ok)} verified; {len(unverified)} UNVERIFIED (may support no conclusion):"
    )
    for u in unverified:
        print(f"    - {u}")
    if not ci:
        for name, cmd in [
            ("ruff", ["ruff", "check", "."]),
            ("format", ["ruff", "format", "--check", "."]),
            ("pytest", [sys.executable, "-m", "pytest", "-q"]),
        ]:
            good = run(cmd)
            print(f"[{name}] {'ok' if good else 'FAIL'}")
            if not good:
                failures.append(name)
    for f in failures:
        print("FAIL:", f)
    print("preflight:", "PASS" if not failures else "FAIL")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
