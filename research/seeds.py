"""Deterministic seed banks, fixed before any candidate exists.

Three properties matter, and each is a defence against a way research lies to
itself. **Determinism**: the same bank on any machine, in any process, in any
Python build - so `hash()` is unusable here, and SHA-256 is used instead.
**Candidate independence**: seeds are derived from a set name and an index, never
from anything about the strategy being measured, so nobody can shop for seeds
that flatter a candidate. **Separation**: the promotion set and the holdout set
are disjoint by construction, so a number that decides promotion is not one that
was looked at while tuning.

**Generation rule, stated exactly.** For set *name* and index *i*, the seed is
the first 8 bytes of `SHA-256("mars777-research/v1/" + name + "/" + i)` read as
a big-endian unsigned integer. Nothing about the rule depends on the order the
sets are built in, so a later set cannot shift an earlier one.
"""

import hashlib
from dataclasses import dataclass
from typing import Final

NAMESPACE: Final[str] = "mars777-research/v1/"
"""Versioned so a future change to the rule cannot silently reuse old numbers."""

DEVELOPMENT: Final[str] = "development"
HOLDOUT: Final[str] = "holdout"
STRESS: Final[str] = "stress"

DEVELOPMENT_SIZE: Final[int] = 64
HOLDOUT_SIZE: Final[int] = 64
STRESS_SIZE: Final[int] = 16


def seed_at(name: str, index: int) -> int:
    """The seed for *index* of the set called *name*. Pure and reproducible."""
    if index < 0:
        raise ValueError("a seed index is not negative")
    material = f"{NAMESPACE}{name}/{index}".encode()
    return int.from_bytes(hashlib.sha256(material).digest()[:8], "big")


@dataclass(frozen=True, slots=True)
class SeedBank:
    """One named, ordered, reproducible set of seeds."""

    name: str
    seeds: tuple[int, ...]

    @property
    def digest(self) -> str:
        """A stable identity for this exact bank, for the research manifest."""
        material = ",".join(str(one) for one in self.seeds).encode()
        return hashlib.sha256(material).hexdigest()


def bank(name: str, size: int) -> SeedBank:
    """Build the bank called *name* with *size* seeds, deterministically."""
    if size <= 0:
        raise ValueError("a seed bank holds at least one seed")
    return SeedBank(name, tuple(seed_at(name, index) for index in range(size)))


def development_bank() -> SeedBank:
    """Used while designing a candidate. May be looked at as often as needed."""
    return bank(DEVELOPMENT, DEVELOPMENT_SIZE)


def holdout_bank() -> SeedBank:
    """Used only to confirm a promotion. Never used to tune a candidate."""
    return bank(HOLDOUT, HOLDOUT_SIZE)


def stress_bank() -> SeedBank:
    """Rare and adversarial configurations, reported separately."""
    return bank(STRESS, STRESS_SIZE)


def banks() -> tuple[SeedBank, ...]:
    """Every bank, in the order the manifest records them."""
    return (development_bank(), holdout_bank(), stress_bank())


def disjoint(first: SeedBank, second: SeedBank) -> bool:
    """Whether two banks share no seed at all - the separation, checked."""
    return not set(first.seeds) & set(second.seeds)
