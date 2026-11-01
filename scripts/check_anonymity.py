"""Scan an artifact directory for identity leaks before double-blind submission (Phase 8).

Flags e-mail addresses, GitHub/claude.ai URLs that reveal an account, names listed in
--names, and PDF metadata (Author/Creator). Exit code 1 if anything is found.

Usage: python scripts/check_anonymity.py <dir> [--names "Name One,handle2"] [--json out.json]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
ACCOUNT_URL = re.compile(r"(github\.com/[A-Za-z0-9-]+|claude\.ai/code/session_[A-Za-z0-9]+)")
ALLOWED_EMAILS = {"noreply@anthropic.com", "41898282+github-actions[bot]@users.noreply.github.com"}
SKIP_DIRS = {".git", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache", "node_modules"}
TEXT_EXT = {
    ".py",
    ".md",
    ".txt",
    ".json",
    ".yml",
    ".yaml",
    ".toml",
    ".cfg",
    ".html",
    ".csv",
    ".tex",
    ".bib",
}
PDF_META = re.compile(rb"/(Author|Creator|Producer)\s*\(([^)]*)\)")


def _pdf_string(raw: bytes) -> str:
    """Decode a PDF literal string: octal escapes, optional UTF-16BE BOM."""
    b = re.sub(rb"\\([0-7]{1,3})", lambda m: bytes([int(m.group(1), 8) & 0xFF]), raw)
    if b.startswith(b"\xfe\xff"):
        return b[2:].decode("utf-16-be", "replace").strip()
    return b.decode("latin-1", "replace").strip()


def scan(root: Path, names: list[str], allowed_urls: set[str] = frozenset()) -> list[dict]:
    findings = []
    name_res = [re.compile(re.escape(n), re.IGNORECASE) for n in names if n]
    for p in sorted(root.rglob("*")):
        if not p.is_file() or SKIP_DIRS & set(p.relative_to(root).parts):
            continue
        rel = str(p.relative_to(root))
        if p.suffix.lower() == ".pdf":
            for m in PDF_META.finditer(p.read_bytes()):
                val = _pdf_string(m.group(2))
                if val and m.group(1) == b"Author" and "anonymous" not in val.lower():
                    findings.append({"file": rel, "line": 0, "kind": "pdf-author", "match": val})
            continue
        if p.suffix.lower() not in TEXT_EXT:
            continue
        for i, line in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            for m in EMAIL.finditer(line):
                if m.group(0) not in ALLOWED_EMAILS:
                    findings.append({"file": rel, "line": i, "kind": "email", "match": m.group(0)})
            for m in ACCOUNT_URL.finditer(line):
                if m.group(0) not in allowed_urls:
                    findings.append(
                        {"file": rel, "line": i, "kind": "account-url", "match": m.group(0)}
                    )
            for r in name_res:
                for m in r.finditer(line):
                    findings.append({"file": rel, "line": i, "kind": "name", "match": m.group(0)})
    return findings


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--names", default="")
    ap.add_argument("--allow-url", action="append", default=[])
    ap.add_argument("--json")
    a = ap.parse_args()
    f = scan(Path(a.root), [n.strip() for n in a.names.split(",")], set(a.allow_url))
    for x in f:
        print(f"{x['file']}:{x['line']}: {x['kind']}: {x['match']}")
    if a.json:
        Path(a.json).write_text(json.dumps(f, indent=2, ensure_ascii=False) + "\n")
    print(f"{len(f)} potential identity leaks")
    return 1 if f else 0


if __name__ == "__main__":
    sys.exit(main())
