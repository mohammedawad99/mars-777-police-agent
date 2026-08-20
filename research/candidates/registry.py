"""Every candidate this stage evaluated, with a stable identity for each.

A benchmark row that says only "C1" is worthless once C1 has been edited, so a
candidate is identified by name, revision **and** the SHA-256 of the module that
defines it. Two different implementations can never be aggregated under one
label, because their hashes differ and the manifest records the hash.

**Rejected candidates stay in this registry.** A negative result is research
evidence, and deleting it would leave a record that only ever tried things that
worked.
"""

import hashlib
from dataclasses import dataclass
from pathlib import Path

from mars777_police.app.baseline_strategy import BaselineStrategy
from mars777_police.app.competitive_strategy import CompetitiveStrategy

from ..strategy_port import Policy
from . import denial, pursuit

HERE = Path(__file__).resolve().parent


@dataclass(frozen=True, slots=True)
class Candidate:
    """One evaluated revision: what it is called, and exactly what it was."""

    name: str
    revision: str
    module: str
    summary: str

    @property
    def source_sha256(self) -> str:
        """The digest of the module that defines this candidate's behaviour."""
        return hashlib.sha256((HERE / self.module).read_bytes()).hexdigest()

    def as_record(self) -> dict[str, str]:
        """Flat identity for a result row or a manifest."""
        return {
            "candidate": self.name,
            "revision": self.revision,
            "candidate_sha256": self.source_sha256,
            "summary": self.summary,
        }


def c1() -> Policy:
    """Shipped barrier gate, belief-directed mover. One change, not two."""
    return CompetitiveStrategy(baseline=pursuit.PursuitMover())


def c2() -> Policy:
    """C1's mover plus a belief-valued barrier rule at the conservative floor."""
    return denial.DenialStrategy(threshold=denial.CONSERVATIVE)


def c3() -> Policy:
    """The same rule at the aggressive floor, to test the under-use hypothesis."""
    return denial.DenialStrategy(threshold=denial.AGGRESSIVE)


def c4() -> Policy:
    """The ablation: C2's barrier rule behind the **shipped** mover.

    C1 measured the mover alone and collapsed; C2 measured mover and rule
    together. Neither says which half carries the gain, and that is a question
    the first three genuinely cannot answer - which is the only reason a fourth
    candidate exists.
    """
    return denial.DenialStrategy(threshold=denial.CONSERVATIVE, mover=BaselineStrategy())


CANDIDATES: dict[str, Candidate] = {
    "C1": Candidate("C1-pursuit", pursuit.REVISION, "pursuit.py", "belief-directed mover"),
    "C2": Candidate(
        "C2-denial", denial.REVISION, "denial.py", "pursuit mover + belief-valued barriers (0.9)"
    ),
    "C3": Candidate(
        "C3-pressure", denial.REVISION, "denial.py", "pursuit mover + belief-valued barriers (0.3)"
    ),
    "C4": Candidate(
        "C4-ablation",
        denial.REVISION,
        "denial.py",
        "shipped mover + belief-valued barriers (0.9): which half carries C2?",
    ),
}

BUILDERS = {"C1": c1, "C2": c2, "C3": c3, "C4": c4}
"""Frozen before any candidate outcome was known."""
