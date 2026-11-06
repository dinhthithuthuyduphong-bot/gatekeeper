"""Remove MemGovern text (no LICENSE: not redistributable) from raw files of the MemGovern cell, so
the raw evidence can be uploaded and archived (CLAUDE.md "Never": no redistribution; A52 raw
archive). Same pattern as scripts/redact_third_party.py (XRepoSkill, A55).

What is MemGovern text in a run of the memgovern arm:
  (1) the appended instructions (its retrieval step and tool docstrings, orig_guidance.json);
  (2) every observation the agent received that carries card text: any non-assistant message after
      the first assistant message that contains a search-result line ("] ID: "), a printed card
      ("Content:" and "Repo:"), or a 60-character window of a card referenced in the run.
Each such text is replaced, in every file under PATH (also in its JSON-escaped forms), by
<<MEMGOVERN_TEXT sha256=...>>. Afterwards no file may still contain any 60-character window of
any referenced card (bug_description, fix_experience, content_preview) or of the instructions;
otherwise exit 1 and the caller must not publish.

  python scripts/redact_memgovern.py --guidance orig_guidance.json --cards experience_data.json \
      PATH [PATH ...]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

WINDOW = 60  # same window as redact_third_party.py's leak check (A55)
# card ids ("owner/repo<issue id>") as exp_search and exp_read print them, and as the agent passes
# them to exp_read
ID_RES = (
    re.compile(r"ID:\s+([A-Za-z0-9_./-]+)"),
    re.compile(r"exp_read\s+[\\\"']*([A-Za-z0-9_./-]+)"),
)
CARD_FIELDS = ("bug_description", "fix_experience", "content_preview")


def variants(text: str) -> list[str]:
    esc = json.dumps(text)[1:-1]
    esc2 = json.dumps(esc)[1:-1]
    return sorted(
        {text, text.strip(), esc, json.dumps(text.strip())[1:-1], esc2}, key=len, reverse=True
    )


def marker(text: str) -> str:
    return f"<<MEMGOVERN_TEXT sha256={hashlib.sha256(text.encode()).hexdigest()}>>"


def windows(text: str) -> list[str]:
    """Non-overlapping 60-char windows (plus the tail) of a text; empty if shorter than WINDOW."""
    t = " ".join(text.split())
    if len(t) < WINDOW:
        return []
    out = [t[i : i + WINDOW] for i in range(0, len(t) - WINDOW + 1, WINDOW)]
    out.append(t[-WINDOW:])
    return out


def card_windows(cards: dict, ids: set[str]) -> list[str]:
    out: list[str] = []
    for i in sorted(ids):
        c = cards.get(i)
        if c is None:
            continue
        for f in CARD_FIELDS:
            out += windows(str(c.get(f) or ""))
    return out


def _content(m: dict) -> str:
    c = m.get("content")
    if isinstance(c, list):  # content blocks
        return "\n".join(str(b.get("text", "")) if isinstance(b, dict) else str(b) for b in c)
    return "" if c is None else str(c)


def observations_to_redact(traj: dict, card_wins: list[str]) -> list[str]:
    msgs = traj.get("messages") or []
    first = next((i for i, m in enumerate(msgs) if m.get("role") == "assistant"), len(msgs))
    out = []
    for m in msgs[first + 1 :]:
        if m.get("role") == "assistant":
            continue
        text = _content(m)
        flat = " ".join(text.split())
        if (
            "] ID: " in text
            or ("Content:" in text and "Repo:" in text)
            or any(w in flat for w in card_wins)
        ):
            out.append(text)
    return out


def referenced_ids(files: list[Path]) -> set[str]:
    ids: set[str] = set()
    for f in files:
        text = f.read_text(errors="replace")
        for r in ID_RES:
            ids |= set(r.findall(text))
    return ids


def leaks(files: list[Path], wins: list[str]) -> list[str]:
    """Files that still hold a window (as written, whitespace-normalised, or JSON-escaped)."""
    probes = set()
    for w in wins:
        probes.add(w)
        probes.add(json.dumps(w)[1:-1])
    bad = []
    for f in files:
        raw = f.read_text(errors="replace")
        flat = " ".join(raw.split())
        hay = (raw, flat, " ".join(raw.replace("\\n", " ").replace("\\t", " ").split()))
        if any(p in h for p in probes for h in hay):
            bad.append(str(f))
    return bad


def redact(paths: list[Path], guidance: dict[str, str], cards: dict) -> tuple[int, list[str]]:
    files = [
        f for p in paths for f in ([p] if p.is_file() else sorted(p.rglob("*"))) if f.is_file()
    ]
    ids = referenced_ids(files)
    card_wins = card_windows(cards, ids)
    texts = {g for g in guidance.values() if g}
    for f in files:
        if f.name.endswith(".traj.json"):
            try:
                texts.update(observations_to_redact(json.loads(f.read_text()), card_wins))
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass
    reps = sorted(
        {(v, marker(t)) for t in texts if t.strip() for v in variants(t) if len(v) >= 20},
        key=lambda r: len(r[0]),
        reverse=True,
    )
    changed = 0
    for f in files:
        try:
            s = f.read_text()
        except UnicodeDecodeError:
            continue
        new = s
        for old, mk in reps:
            if old in new:
                new = new.replace(old, mk)
        if new != s:
            f.write_text(new)
            changed += 1
    check = card_wins + [w for g in guidance.values() for w in windows(g)]
    return changed, leaks(files, check)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--guidance", required=True, type=Path)
    ap.add_argument("--cards", required=True, type=Path, help="MemGovern experience_data.json")
    ap.add_argument("paths", nargs="+", type=Path)
    a = ap.parse_args()
    guidance = json.loads(a.guidance.read_text())
    cards = json.loads(a.cards.read_text())
    if isinstance(cards, list):
        cards = {str(c.get("id")): c for c in cards}
    changed, bad = redact(a.paths, guidance, cards)
    print(
        f"[redact_memgovern] files changed {changed}, still holding MemGovern text {len(bad)}"
    )
    for b in bad[:20]:
        print("  LEAK:", b)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
