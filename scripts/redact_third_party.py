"""Replace the XRepoSkill rule text (no LICENSE: not redistributable) in raw E2 files by a marker
that names its SHA-256, so the raw evidence can be published (artifacts, raw-archive) and the
exact text is restored from the pinned commit + recorded rule ids (scripts/build_e2_guidance.py).

  python scripts/redact_third_party.py --guidance guidance_by_instance.json --clone <XRepoSkill> \
      PATH [PATH ...]

Every file under PATH is rewritten in place: each guidance block (as written, and in its JSON
string-escaped form) becomes <<XREPOSKILL_BLOCK sha256=...>>. Afterwards no file may still contain
the opening 60 characters of any of the 36 rule bodies; otherwise the script exits 1 and the caller
must not publish (audit A55)."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from xreposkill_select import pack, parse_strategies  # noqa: E402


def variants(text: str) -> list[str]:
    esc = json.dumps(text)[1:-1]  # as it appears inside a JSON string
    esc2 = json.dumps(esc)[1:-1]  # JSON inside a JSON string (e.g. a jsonl row in a log)
    return sorted(
        {text, text.strip(), esc, json.dumps(text.strip())[1:-1], esc2}, key=len, reverse=True
    )


def load_rules(clone: Path) -> list:
    sys.path.insert(0, str(clone / "src"))
    from xreposkill import retrieval  # noqa: PLC0415

    with tempfile.TemporaryDirectory() as tmp:
        pack(parse_strategies((clone / "data" / "general_strategies_36.md").read_text()), Path(tmp))
        return retrieval.load_rules(Path(tmp))


def rule_replacements(rules: list) -> list[tuple[str, str]]:
    """Single rules too: the agent may quote one in its reasoning. Rendered form, body, title."""
    out = []
    for r in rules:
        mark = f"<<XREPOSKILL_RULE {r.rule_id}>>"
        for text in (f"[{r.rule_id}] {r.title}\n{r.body}", r.body, r.title):
            out += [(v, mark) for v in variants(text)]
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--guidance", required=True, type=Path)
    ap.add_argument("--clone", required=True, type=Path)
    ap.add_argument("paths", nargs="+", type=Path)
    a = ap.parse_args()
    blocks = json.loads(a.guidance.read_text())
    reps = []
    for text in set(blocks.values()):
        mark = f"<<XREPOSKILL_BLOCK sha256={hashlib.sha256(text.encode()).hexdigest()}>>"
        reps += [(v, mark) for v in variants(text)]
    rules = load_rules(a.clone)
    reps += rule_replacements(rules)  # after whole blocks: longest strings are replaced first
    reps.sort(key=lambda x: len(x[0]), reverse=True)
    snippets = [r.body[:60] for r in rules]
    leaks, n_files, n_changed = [], 0, 0
    for root in a.paths:
        for f in sorted(p for p in ([root] if root.is_file() else root.rglob("*")) if p.is_file()):
            n_files += 1
            try:
                s = f.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            new = s
            for old, mark in reps:
                if old and old in new:
                    new = new.replace(old, mark)
            if new != s:
                f.write_text(new, encoding="utf-8")
                n_changed += 1
            for sn in snippets:
                for v in {sn, json.dumps(sn)[1:-1]}:
                    if v in new:
                        leaks.append(f"{f}: '{sn[:30]}...'")
    print(f"{n_files} files, {n_changed} redacted, {len(leaks)} leaks")
    for x in leaks[:20]:
        print("  LEAK", x)
    return 1 if leaks else 0


if __name__ == "__main__":
    raise SystemExit(main())
