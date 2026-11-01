"""Fingerprints D, input predicates I and the scope screen (Algorithm 1, line 1).

A screen failure means OutOfScope (the skill is not run). A screen pass is only the
precondition for quarantine: Figure 1's harmful skill passes it.
"""

from __future__ import annotations

import hashlib
import json
import platform
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from gatekeeper.skill import Skill

__all__ = [
    "LOCKFILES",
    "ScreenResult",
    "TargetContext",
    "compare_fingerprints",
    "fingerprint_repo",
    "screen",
]

LOCKFILES = (
    "requirements.txt",
    "requirements-dev.txt",
    "poetry.lock",
    "uv.lock",
    "Pipfile.lock",
    "pdm.lock",
    "pyproject.toml",
    "setup.cfg",
)
_PIN = re.compile(r"^\s*([A-Za-z0-9_.\-]+)\s*==\s*([A-Za-z0-9_.\-+]+)")


@dataclass(frozen=True)
class TargetContext:
    """What Gatekeeper may inspect about a target repository (no trial needed)."""

    name: str
    fingerprints: Mapping[str, str]
    files: frozenset[str] = frozenset()
    symbols: frozenset[str] = frozenset()
    dependencies: Mapping[str, str] = field(default_factory=dict)
    declared_classes: Mapping[str, str] = field(default_factory=dict)
    issue_text: str = ""  # the task's issue / problem statement (activation predicates I(x))


@dataclass(frozen=True)
class ScreenResult:
    in_scope: bool
    reasons: tuple[str, ...] = ()


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def fingerprint_repo(root: str | Path, interpreter: str | None = None) -> dict[str, str]:
    """D for a checked-out Python repository: lockfile hashes, interpreter, pinned versions,
    and behavioural classes declared in `.gatekeeper/behaviour.json` (if the repo has one)."""
    root = Path(root)
    d: dict[str, str] = {"python": interpreter or platform.python_version().rsplit(".", 1)[0]}
    for name in LOCKFILES:
        p = root / name
        if p.is_file():
            d[f"lock:{name}"] = _sha(p)
    req = root / "requirements.txt"
    if req.is_file():
        for line in req.read_text(encoding="utf-8", errors="replace").splitlines():
            m = _PIN.match(line)
            if m:
                d[f"dep:{m.group(1).lower()}"] = m.group(2)
    beh = root / ".gatekeeper" / "behaviour.json"
    if beh.is_file():
        for k, v in json.loads(beh.read_text()).items():
            d[f"class:{k}"] = str(v)
    return d


def _major(v: str) -> str:
    return v.split(".", 1)[0]


def compare_fingerprints(
    skill_d: Mapping[str, str],
    target_d: Mapping[str, str],
    exact_prefixes: Iterable[str] = ("python", "class:"),
    major_prefixes: Iterable[str] = ("dep:",),
) -> list[str]:
    """Return incompatibilities. Keys absent on the target are incompatible; lockfile hashes
    are informational (a different lockfile alone is not disqualifying)."""
    problems: list[str] = []
    exact_prefixes = tuple(exact_prefixes)
    major_prefixes = tuple(major_prefixes)
    for k, v in skill_d.items():
        if k.startswith("lock:"):
            continue
        if k not in target_d:
            problems.append(f"{k}: missing on target")
        elif k.startswith(exact_prefixes) and target_d[k] != v:
            problems.append(f"{k}: {v} != {target_d[k]}")
        elif k.startswith(major_prefixes) and _major(target_d[k]) != _major(v):
            problems.append(f"{k}: major {_major(v)} != {_major(target_d[k])}")
    return problems


def _version_tuple(v: str) -> tuple[int, ...]:
    return tuple(int(x) for x in re.findall(r"\d+", v)[:3])


def _satisfies(version: str, spec: str) -> bool:
    """Minimal specifier check: comma-separated clauses with >=, <=, >, <, ==, !=."""
    v = _version_tuple(version)
    for clause in filter(None, (c.strip() for c in spec.split(","))):
        m = re.match(r"(>=|<=|==|!=|>|<)\s*(.+)", clause)
        if not m:
            raise ValueError(f"bad version clause {clause!r}")
        op, ref = m.group(1), _version_tuple(m.group(2))
        ok = {
            ">=": v >= ref,
            "<=": v <= ref,
            ">": v > ref,
            "<": v < ref,
            "==": v[: len(ref)] == ref,
            "!=": v[: len(ref)] != ref,
        }[op]
        if not ok:
            return False
    return True


def evaluate_predicate(pred: Mapping[str, Any], target: TargetContext) -> bool:
    kind = pred["kind"]
    if kind == "file_exists":
        return pred["path"] in target.files
    if kind == "symbol_present":
        return pred["name"] in target.symbols
    if kind == "dependency":
        ver = target.dependencies.get(pred["name"].lower())
        return ver is not None and _satisfies(ver, pred.get("spec", ""))
    if kind == "declared_class":
        return target.declared_classes.get(pred["key"]) == pred["value"]
    if kind == "python":
        return _satisfies(target.fingerprints.get("python", "0"), pred["spec"])
    if kind == "issue_regex":
        flags = re.IGNORECASE if pred.get("ignore_case", True) else 0
        return re.search(pred["pattern"], target.issue_text, flags) is not None
    raise ValueError(f"unknown predicate kind {kind!r}")


def screen(skill: Skill, target: TargetContext) -> ScreenResult:
    reasons = [f"D {p}" for p in compare_fingerprints(skill.fingerprints, target.fingerprints)]
    for pred in skill.input_predicates:
        if not evaluate_predicate(pred, target):
            reasons.append(f"I failed: {json.dumps(dict(pred), sort_keys=True)}")
    return ScreenResult(in_scope=not reasons, reasons=tuple(reasons))
