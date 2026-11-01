"""Skill package S = <pi, D, I, P, K> and its JSON schema (TODO.md Phase 5a).

The procedure pi is kept opaque here (an edit-program spec consumed by the trial runner);
Gatekeeper only needs D (fingerprints), I (executable input predicates), P (observed
postconditions with contexts), K (interaction footprint) and the separate capability verdict.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from gatekeeper.footprint import Footprint

__all__ = ["CAPABILITY_VERDICTS", "PREDICATE_KINDS", "Postcondition", "Skill", "SCHEMA_VERSION"]

SCHEMA_VERSION = 1
CAPABILITY_VERDICTS = ("approved", "rejected", "unknown")
PREDICATE_KINDS = ("file_exists", "symbol_present", "dependency", "declared_class", "python")


@dataclass(frozen=True)
class Postcondition:
    property: str
    observed_in: tuple[str, ...] = ()


@dataclass(frozen=True)
class Skill:
    id: str
    procedure: dict[str, Any]
    fingerprints: dict[str, str]
    input_predicates: tuple[dict[str, Any], ...] = ()
    postconditions: tuple[Postcondition, ...] = ()
    footprint: Footprint = field(default_factory=Footprint)
    capability_verdict: str = "unknown"
    source: str = ""

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("skill id must be non-empty")
        if self.capability_verdict not in CAPABILITY_VERDICTS:
            raise ValueError(f"capability_verdict must be one of {CAPABILITY_VERDICTS}")
        for p in self.input_predicates:
            if p.get("kind") not in PREDICATE_KINDS:
                raise ValueError(f"unknown predicate kind {p.get('kind')!r} in skill {self.id}")

    # ---- (de)serialisation -------------------------------------------------------------
    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["schema_version"] = SCHEMA_VERSION
        d["input_predicates"] = list(self.input_predicates)
        d["postconditions"] = [
            {"property": p.property, "observed_in": list(p.observed_in)}
            for p in self.postconditions
        ]
        d["footprint"] = self.footprint.to_dict()
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Skill:
        version = d.get("schema_version", SCHEMA_VERSION)
        if version != SCHEMA_VERSION:
            raise ValueError(f"unsupported skill schema_version {version}")
        missing = {"id", "procedure", "fingerprints"} - d.keys()
        if missing:
            raise ValueError(f"skill is missing fields: {sorted(missing)}")
        return cls(
            id=d["id"],
            procedure=dict(d["procedure"]),
            fingerprints={str(k): str(v) for k, v in d["fingerprints"].items()},
            input_predicates=tuple(d.get("input_predicates", ())),
            postconditions=tuple(
                Postcondition(p["property"], tuple(p.get("observed_in", ())))
                for p in d.get("postconditions", ())
            ),
            footprint=Footprint.from_dict(d.get("footprint", {})),
            capability_verdict=d.get("capability_verdict", "unknown"),
            source=d.get("source", ""),
        )

    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n")

    @classmethod
    def load(cls, path: str | Path) -> Skill:
        return cls.from_dict(json.loads(Path(path).read_text()))
