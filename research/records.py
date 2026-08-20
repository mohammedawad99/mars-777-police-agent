"""The versioned research result record, and what it deliberately never carries.

**This is research evidence, not a game artifact.** Appendix F Table 20 fixes the
official set at one declaration, six configs, six logs and one result; a
benchmark row is none of those and must never land in that namespace or be
counted toward it.

**Stable by construction.** Fields are ordered, values are plain text or whole
numbers, and serialisation sorts keys - so two runs of the same benchmark
produce byte-identical files and a diff means a real change rather than a
dictionary ordering.
"""

import csv
import json
from dataclasses import asdict, dataclass, fields
from pathlib import Path

SCHEMA_VERSION = "research-1"
"""Raised only when a column changes meaning or disappears, never for a new run."""


@dataclass(frozen=True, slots=True)
class GameRecord:
    """One benchmark game: what was played, by whom, and how it ended."""

    schema: str
    role: str
    commit: str
    strategy: str
    strategy_sha256: str
    opponent_family: str
    seed_set: str
    seed: int
    config: str
    grid: int
    quota: int
    horizon: int
    outcome: str
    captured: int
    steps: int
    barriers_placed: int
    own_score: int
    opponent_score: int

    @property
    def won(self) -> int:
        """Whether this game is a win for the role under test, by the score."""
        return int(self.own_score > self.opponent_score)


def columns() -> tuple[str, ...]:
    """The record's field names, in declaration order. The CSV header."""
    return tuple(one.name for one in fields(GameRecord))


def write_csv(records: tuple[GameRecord, ...], path: Path) -> Path:
    """Write *records* as deterministic CSV, newline-normalised for every platform."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(columns()), lineterminator="\n")
        writer.writeheader()
        for record in records:
            writer.writerow(asdict(record))
    return path


def read_csv(path: Path) -> tuple[GameRecord, ...]:
    """Read records back, refusing a file written by a different schema."""
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return tuple(_record(row, path) for row in rows)


def _record(row: dict[str, str], path: Path) -> GameRecord:
    if row.get("schema") != SCHEMA_VERSION:
        raise ValueError(f"{path} was written by schema {row.get('schema')!r}")
    typed = {one.name: _value(one.type, row[one.name]) for one in fields(GameRecord)}
    return GameRecord(**typed)  # type: ignore[arg-type]


def _value(kind: object, text: str) -> object:
    return int(text) if kind is int or kind == "int" else text


def write_json(document: dict[str, object], path: Path) -> Path:
    """Write one deterministic JSON document: sorted keys, trailing newline."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path
