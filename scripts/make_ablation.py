"""Section 29: the learned jinja skill without its history instruction (0 USD).

  python scripts/make_ablation.py            # writes docs/skills/gskill/jinja_no_history.txt
  python scripts/make_ablation.py --check    # exit 1 if the committed file differs

Rule (registered before any run): drop every line of the skill whose text mentions a commit or the
history, i.e. matches RULE case-insensitively; every other byte is kept. On the learned jinja skill
this drops exactly one line (the "Check Git History" bullet); `git diff` alone is not history.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SRC = Path("docs/skills/gskill/jinja_best_skills.txt")
OUT = Path("docs/skills/gskill/jinja_no_history.txt")
RULE = re.compile(r"commit|history|git log|git show", re.IGNORECASE)


def ablate(text: str) -> tuple[str, list[int]]:
    lines = text.splitlines(keepends=True)
    drop = [i for i, line in enumerate(lines, 1) if RULE.search(line)]
    return "".join(x for i, x in enumerate(lines, 1) if i not in drop), drop


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    new, drop = ablate(SRC.read_text(encoding="utf-8"))
    if drop != [7]:
        raise SystemExit(f"rule dropped lines {drop}, registered: [7]")
    if a.check:
        ok = OUT.exists() and OUT.read_text(encoding="utf-8") == new
        print("ablation file", "matches" if ok else "DIFFERS")
        return 0 if ok else 1
    OUT.write_text(new, encoding="utf-8")
    print(f"dropped line(s) {drop}; {len(new.encode())} bytes -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
