"""Anonymized replication package (A4, F2-F4 of docs/todo_ease_revision.md; 0 USD).

  python scripts/build_replication_package.py --trial <worktree of origin/trial> \
      --rows <dir with task rows> --out <empty directory>

A selective export, not the repository with its history: the history and several project files
name the author, the cloud account and the working sessions. The package holds the code, the
registrations (with the commit time of every registration, results/registration_timeline.json),
the results and traces kept on main and on branch `trial`, the paper source, and a README. Text
files are rewritten by the REDACT rules; the export stops if scripts/check_anonymity.py still finds
an identity leak. The task rows are not copied (third-party dataset): the README says how to get
them. Third-party texts without a licence were never committed and are not in the package.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

KEEP = [
    "src",
    "scripts",
    "tests",
    "configs",
    "results",
    "paper",
    "pyproject.toml",
    ".github/workflows",
    "docs/preregistration_main.md",
    "docs/preregistration_e1.md",
    "docs/preregistration_e2.md",
    "docs/preregistration_g1_v2.md",
    "docs/method_end_of_pool.md",
    "docs/method_check.md",
    "docs/research_rules.md",
    "docs/audit_pilot.md",
    "docs/lessons_learned.md",
    "docs/review_log.md",
    "docs/number_provenance.md",
    "docs/glossary.md",
    "docs/skills",
]
TRIAL = ["src", "scripts/s25_ab.py", "results"]
SKIP = re.compile(
    r"(build_replication_package\.py$|__pycache__|\.egg-info|\.pyc$|paper/.*\.(aux|log|out|pdf|bbl|blg|fls)$)"
)
# identity -> neutral text; applied to every text file
REDACT = [
    (re.compile(r"dinhthithuthuyduphong-bot/gatekeeper"), "ANONYMOUS/gatekeeper"),
    (re.compile(r"dinhthithuthuyduphong-bot"), "ANONYMOUS"),
    (re.compile(r"@?[Tt]hu ?[Tt]h[uủ]y"), "the PI"),
    (re.compile(r"Dinh Thi Thu Thuy", re.I), "the PI"),
    (re.compile(r"gatekeeper-research"), "<gcp-project>"),
    (re.compile(r"gatekeeper-pilot(-E2)?@[\w.-]+"), "<service-account>"),
    (re.compile(r"gatekeeper-pilot(-E2)?"), "<service-account>"),
    (re.compile(r"https://claude\.ai/code/session_\w+"), "<session>"),
    (re.compile(r"session_[0-9A-Za-z]{20,}"), "<session>"),
    (re.compile(r"/tmp/claude-0/[^\s'\"]+"), "<scratch>"),
    (re.compile(r"[A-Za-z0-9._%+-]+@gmail\.com"), "<email>"),
]
TEXT = {".py", ".md", ".json", ".jsonl", ".yml", ".yaml", ".toml", ".tex", ".bib", ".txt", ".sh"}


def copy(src: Path, dst: Path) -> int:
    n = 0
    files = [src] if src.is_file() else sorted(p for p in src.rglob("*") if p.is_file())
    for f in files:
        rel = f.relative_to(src.parent if src.is_file() else src)
        if SKIP.search(str(f)):
            continue
        out = dst / rel if src.is_dir() else dst
        out.parent.mkdir(parents=True, exist_ok=True)
        if f.suffix in TEXT:
            t = f.read_text(errors="replace")
            for pat, rep in REDACT:
                t = pat.sub(rep, t)
            out.write_text(t)
        else:
            shutil.copy2(f, out)
        n += 1
    return n


README = """# Replication package (anonymized)

The paper's numbers are generated, never typed: `scripts/make_numbers.py` reads `results/` (runs
kept on the main line of work) and `trial/results/` (runs kept on a second line of work) and writes
`paper/numbers.tex`; it stops on any value that differs from the one registered.

## Rebuild every number of the paper
    python -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]"
    # task rows (SWE-smith, public dataset): scripts/export_swesmith.py,
    # with the arguments of .github/workflows/data.yml
    python scripts/make_numbers.py --trial trial --rows <rows dir>

## Where things are
- `docs/preregistration_main.md`: every registered rule, execution note and deviation, in the
  order written. `results/registration_timeline.json`: the commit time of every registration and
  of the first published result of each section (no result precedes its registration).
- `docs/method_end_of_pool.md`: the end-of-pool test, its proof and its scope.
- `results/*.traces.jsonl.gz`: agent traces; `scripts/history_audit.py`: the trace audit.
- `docs/audit_pilot.md`, `docs/lessons_learned.md`: every error found during the study.
- Documents are written in Vietnamese; code and comments in English.

Third-party texts without a licence (XRepoSkill guidance, MemGovern data) are not included.
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--trial", type=Path, required=True)
    ap.add_argument("--rows", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    if a.out.exists() and any(a.out.iterdir()):
        raise SystemExit("--out must be empty")
    a.out.mkdir(parents=True, exist_ok=True)
    n = 0
    for p in KEEP:
        n += copy(Path(p), a.out / p)
    for p in TRIAL:
        n += copy(a.trial / p, a.out / "trial" / p)
    (a.out / "README.md").write_text(README)
    print(f"{n} files copied")
    r = subprocess.run(
        [
            sys.executable,
            "scripts/check_anonymity.py",
            str(a.out),
            "--names",
            "thuthuy,Thu Thuy,Dinh Thi,dinhthithuthuy,gatekeeper-research",
            "--named-only",
        ],
        capture_output=True,
        text=True,
    )
    print(r.stdout[-3000:])
    if r.returncode != 0:
        raise SystemExit("identity leak found: package not usable")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
