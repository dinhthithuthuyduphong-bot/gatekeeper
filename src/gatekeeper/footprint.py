"""Interaction footprint K and the composition-overlap test (TODO.md Phase 5a/5b).

K = code regions the edit program touches, symbols it reads / writes (static read/write
analysis over the edited Python functions) and behavioural properties named in its
postconditions. Two skills must be screened as a composite when their footprints overlap:
shared region, a write that the other reads or writes, or a shared behavioural property.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from typing import Any

__all__ = ["Footprint", "analyse_source", "overlaps"]


@dataclass(frozen=True)
class Footprint:
    regions: frozenset[str] = field(default_factory=frozenset)
    reads: frozenset[str] = field(default_factory=frozenset)
    writes: frozenset[str] = field(default_factory=frozenset)
    properties: frozenset[str] = field(default_factory=frozenset)

    def union(self, other: Footprint) -> Footprint:
        return Footprint(
            self.regions | other.regions,
            self.reads | other.reads,
            self.writes | other.writes,
            self.properties | other.properties,
        )

    def to_dict(self) -> dict[str, list[str]]:
        return {k: sorted(getattr(self, k)) for k in ("regions", "reads", "writes", "properties")}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Footprint:
        return cls(
            **{k: frozenset(d.get(k, ())) for k in ("regions", "reads", "writes", "properties")}
        )


def _dotted(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _dotted(node.value)
        return f"{base}.{node.attr}" if base else None
    return None


class _RW(ast.NodeVisitor):
    def __init__(self) -> None:
        self.reads: set[str] = set()
        self.writes: set[str] = set()

    def _target(self, t: ast.AST) -> None:
        if isinstance(t, (ast.Tuple, ast.List)):
            for e in t.elts:
                self._target(e)
            return
        if isinstance(t, ast.Subscript):
            name = _dotted(t.value)
            if name:
                self.writes.add(name)
            self.visit(t.slice)
            return
        name = _dotted(t)
        if name:
            self.writes.add(name)
        if isinstance(t, ast.Attribute):
            self.visit(t.value)

    def visit_Assign(self, node: ast.Assign) -> None:
        for t in node.targets:
            self._target(t)
        self.visit(node.value)

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        self._target(node.target)
        name = _dotted(node.target)
        if name:
            self.reads.add(name)
        self.visit(node.value)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        self._target(node.target)
        if node.value:
            self.visit(node.value)

    def visit_Call(self, node: ast.Call) -> None:
        name = _dotted(node.func)
        if name:
            self.reads.add(name)
            # calling a method on an object may mutate it (db.insert, list.append, ...)
            if isinstance(node.func, ast.Attribute):
                owner = _dotted(node.func.value)
                if owner:
                    self.writes.add(owner)
        for a in node.args:
            self.visit(a)
        for k in node.keywords:
            self.visit(k.value)
        if not isinstance(node.func, (ast.Name, ast.Attribute)):
            self.visit(node.func)

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, ast.Load):
            self.reads.add(node.id)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        name = _dotted(node)
        if name and isinstance(node.ctx, ast.Load):
            self.reads.add(name)
        self.visit(node.value)


def analyse_source(source: str, module: str, functions: list[str] | None = None) -> Footprint:
    """Static read/write footprint of `functions` (all top-level defs if None) in `source`."""
    tree = ast.parse(source)
    regions: set[str] = set()
    rw = _RW()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if functions is None or node.name in functions:
                regions.add(f"{module}:{node.name}")
                for stmt in node.body:
                    rw.visit(stmt)
    if functions:
        unknown = set(functions) - {r.split(":", 1)[1] for r in regions}
        if unknown:
            raise ValueError(f"functions not found in {module}: {sorted(unknown)}")
    local_noise = {"self", "cls"}
    return Footprint(
        regions=frozenset(regions),
        reads=frozenset(rw.reads - local_noise),
        writes=frozenset(rw.writes - local_noise),
    )


def overlaps(a: Footprint, b: Footprint) -> bool:
    """True when the pair must be screened as a composite (Algorithm 1, line 2)."""
    if a.regions & b.regions:
        return True
    if a.writes & (b.writes | b.reads) or b.writes & a.reads:
        return True
    return bool(a.properties & b.properties)
