"""Unified-diff analysis of benchmark gold patches (TODO.md Phase 4).

* parse_patch: files, functions (from hunk headers), added / removed source lines (tests excluded)
* edit_patterns: coarse, regex-based families of what the patch adds (null guard, type guard,
  exception handling, ...). Families that recur across *training* repositories are candidate
  edit-program skills; their prevalence in the test split says where such a skill could apply.
* composition_candidates: test tasks of one repository whose gold patches touch the same
  function — the raw material for composition pairs (Theorem 7').
"""

from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field

__all__ = ["PATTERNS", "ParsedPatch", "composition_candidates", "edit_patterns", "parse_patch"]

_FILE = re.compile(r"^diff --git a/(\S+) b/(\S+)")
_HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+\d+(?:,\d+)? @@ ?(.*)$")
_DEF = re.compile(r"(?:async\s+)?def\s+(\w+)|class\s+(\w+)")
_TEST_PATH = re.compile(r"(^|/)(tests?|testing)(/|$)|(^|/)test_[^/]*\.py$|_test\.py$|conftest\.py$")

PATTERNS: dict[str, re.Pattern[str]] = {
    "null_guard": re.compile(r"\bis (not )?None\b"),
    "type_guard": re.compile(r"\bisinstance\(|\bhasattr\("),
    "exception_handling": re.compile(r"^\s*(try:|except\b)"),
    "raise_error": re.compile(r"^\s*raise \w+(Error|Exception|Warning)\b"),
    "deprecation_warning": re.compile(r"warnings\.warn\(|DeprecationWarning|FutureWarning"),
    "encoding": re.compile(r"\.(encode|decode)\(|\bbytes\(|\bstr\(\w+, ?['\"]"),
    "defensive_copy": re.compile(r"\.copy\(\)|deepcopy\("),
    "dtype_cast": re.compile(r"\.astype\(|\bdtype\b"),
    "path_handling": re.compile(r"\bos\.path\.|\bPath\(|\bpathlib\b"),
    "regex_change": re.compile(r"\bre\.(compile|match|search|sub|findall|fullmatch)\("),
    "empty_check": re.compile(r"\bif not \w+\s*:|\blen\(\w+\) == 0"),
    "kwarg_default": re.compile(r"^\s*def \w+\(.*=\s*(None|True|False|\d+)"),
}


@dataclass
class ParsedPatch:
    files: list[str] = field(default_factory=list)
    functions: set[str] = field(default_factory=set)  # "path::name"
    added: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)


def parse_patch(patch: str, include_tests: bool = False) -> ParsedPatch:
    out = ParsedPatch()
    current: str | None = None
    skip = False
    for line in (patch or "").splitlines():
        m = _FILE.match(line)
        if m:
            current = m.group(2)
            skip = bool(_TEST_PATH.search(current)) and not include_tests
            if not skip:
                out.files.append(current)
            continue
        if skip or current is None:
            continue
        h = _HUNK.match(line)
        if h:
            d = _DEF.search(h.group(1) or "")
            if d:
                out.functions.add(f"{current}::{d.group(1) or d.group(2)}")
            continue
        if line.startswith("+++") or line.startswith("---"):
            continue
        if line.startswith("+"):
            text = line[1:]
            out.added.append(text)
            d = _DEF.match(text.strip())
            if d:
                out.functions.add(f"{current}::{d.group(1) or d.group(2)}")
        elif line.startswith("-"):
            out.removed.append(line[1:])
    return out


def edit_patterns(p: ParsedPatch) -> set[str]:
    found = set()
    for name, rx in PATTERNS.items():
        if any(rx.search(line) for line in p.added):
            found.add(name)
    return found


def composition_candidates(
    tasks: Iterable[Mapping[str, object]],
) -> list[dict[str, object]]:
    """tasks: dicts with instance_id, repo, functions (iterable of 'path::name').
    Returns pairs of tasks in one repo whose gold patches touch a common function."""
    by_fn: dict[tuple[str, str], list[str]] = defaultdict(list)
    for t in tasks:
        for fn in t["functions"]:  # type: ignore[union-attr]
            by_fn[(str(t["repo"]), fn)].append(str(t["instance_id"]))
    pairs: dict[tuple[str, str], set[str]] = defaultdict(set)
    for (_repo, fn), ids in by_fn.items():
        ids = sorted(set(ids))
        for i, a in enumerate(ids):
            for b in ids[i + 1 :]:
                pairs[(a, b)].add(fn)
    return [
        {"a": a, "b": b, "shared_functions": sorted(fns)} for (a, b), fns in sorted(pairs.items())
    ]


_DIFF_HEAD = re.compile(r"^diff --git a/(\S+) b/(\S+)", re.M)


def touched_files(patch: str) -> set[str]:
    return {m.group(2) for m in _DIFF_HEAD.finditer(patch or "")}


def drop_files(patch: str, files: set[str]) -> str:
    """Remove the per-file sections of a git diff that touch `files` (e.g. the files the
    evaluation's test patch writes: they are overwritten at scoring time anyway, and a model
    patch that already created them makes `git apply` of the test patch fail)."""
    if not patch or not files:
        return patch
    starts = [m.start() for m in _DIFF_HEAD.finditer(patch)]
    if not starts:
        return patch
    keep = [patch[: starts[0]]]
    for a, b in zip(starts, starts[1:] + [len(patch)], strict=True):
        sec = patch[a:b]
        m = _DIFF_HEAD.match(sec)
        if m and (m.group(1) in files or m.group(2) in files):
            continue
        keep.append(sec)
    return "".join(keep)
