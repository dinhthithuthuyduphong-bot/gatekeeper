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
from typing import Any

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


def _norm(text: str) -> str:
    return " ".join(text.split())


def _carries(text: str, wins: list[str]) -> bool:
    """A string carries MemGovern text: a search-result line, a printed card, or a window of a
    referenced card or of the instructions (after whitespace normalisation, so a re-indented copy
    in a prompt template is found too)."""
    if "] ID: " in text or ("Content:" in text and "Repo:" in text):
        return True
    flat = _norm(text)
    return any(w in flat for w in wins)


def scrub(obj: Any, wins: list[str], found: list[str], path: str = "$") -> Any:
    """Replace, anywhere in a JSON value, every string that carries MemGovern text by a marker.
    The originals go to `found` (to remove the same text from other files, e.g. the log)."""
    if isinstance(obj, str):
        if _carries(obj, wins):
            found.append(obj)
            return marker(obj)
        return obj
    if isinstance(obj, list):
        return [scrub(v, wins, found, f"{path}[{i}]") for i, v in enumerate(obj)]
    if isinstance(obj, dict):
        return {k: scrub(v, wins, found, f"{path}.{k}") for k, v in obj.items()}
    return obj


def leak_paths(obj: Any, wins: list[str], path: str = "$") -> list[str]:
    """JSON paths of strings that still carry MemGovern text (for the report; no text printed)."""
    if isinstance(obj, str):
        return [path] if _carries(obj, wins) else []
    if isinstance(obj, list):
        return [p for i, v in enumerate(obj) for p in leak_paths(v, wins, f"{path}[{i}]")]
    if isinstance(obj, dict):
        return [p for k, v in obj.items() for p in leak_paths(v, wins, f"{path}.{k}")]
    return []


def referenced_ids(files: list[Path]) -> set[str]:
    ids: set[str] = set()
    for f in files:
        text = f.read_text(errors="replace")
        for r in ID_RES:
            ids |= set(r.findall(text))
    return ids


def _file_leaks(f: Path, probes: set[str]) -> bool:
    raw = f.read_text(errors="replace")
    hay = (raw, _norm(raw), _norm(raw.replace("\\n", " ").replace("\\t", " ")))
    return any(p in h for p in probes for h in hay)


def redact(paths: list[Path], guidance: dict[str, str], cards: dict) -> tuple[int, list[str]]:
    """Returns (files changed or removed, files that still carry MemGovern text).

    Trajectories (*.traj.json) are scrubbed structurally. Every other text file gets the scrubbed
    strings replaced; a non-trajectory file that still carries MemGovern text afterwards (a log
    that formats the same messages differently) is REMOVED and listed in REDACTION.json next to
    it: the trajectory holds the same messages. A trajectory that still carries text fails."""
    files = [
        f for p in paths for f in ([p] if p.is_file() else sorted(p.rglob("*"))) if f.is_file()
    ]
    ids = referenced_ids(files)
    wins = card_windows(cards, ids) + [w for g in guidance.values() for w in windows(g)]
    found: list[str] = [g for g in guidance.values() if g]
    changed = 0
    for f in files:
        if not f.name.endswith(".traj.json"):
            continue
        try:
            d = json.loads(f.read_text())
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        new = scrub(d, wins, found)
        if new != d:
            f.write_text(json.dumps(new, indent=2) + "\n")
            changed += 1
    reps = sorted(
        {(v, marker(t)) for t in found if t.strip() for v in variants(t) if len(v) >= 20},
        key=lambda r: len(r[0]),
        reverse=True,
    )
    probes = {w for w in wins} | {json.dumps(w)[1:-1] for w in wins}
    bad, removed = [], []
    for f in files:
        if f.name.endswith(".traj.json"):
            try:
                left = leak_paths(json.loads(f.read_text()), wins)
            except (json.JSONDecodeError, UnicodeDecodeError):
                left = ["$ (unreadable)"] if _file_leaks(f, probes) else []
            if left:
                bad.append(f"{f} at {', '.join(left[:5])}")
            continue
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
        if _file_leaks(f, probes):
            f.unlink()
            removed.append(f)
            changed += 1
    for f in removed:
        rec = f.parent / "REDACTION.json"
        d = json.loads(rec.read_text()) if rec.exists() else {"removed": []}
        d["removed"].append(f.name)
        d["why"] = "still held MemGovern text after redaction; the trajectory holds the messages"
        rec.write_text(json.dumps(d, indent=1) + "\n")
    return changed, bad


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
    print(f"[redact_memgovern] files changed {changed}, still holding MemGovern text {len(bad)}")
    for b in bad[:20]:
        print("  LEAK:", b)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
