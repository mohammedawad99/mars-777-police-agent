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
the first 8 bytes of `SHA-256(namespace + name + "/" + i)` read as a big-endian
unsigned integer. Nothing about the rule depends on the order the sets are built
in, so a later set cannot shift an earlier one.

**One bank was renamed at Stage 9B-0F, and the reason is recorded rather than
tidied away.** Stage 9B-0 ran a bank called `holdout` and then read its results
while ranking candidate hypotheses. A set whose outcomes have been seen is no
longer blind, whatever it is called, so it is now `validation` - what it
actually is. A genuinely sealed `final_holdout` was created afterwards, under
its **own namespace**, and no game has been played on it.
"""

import hashlib
from dataclasses import dataclass
from typing import Final

NAMESPACE: Final[str] = "mars777-research/v1/"
"""Versioned so a future change to the rule cannot silently reuse old numbers."""

SEALED_NAMESPACE: Final[str] = "mars777-research/final-holdout-v1/"
"""A namespace of its own, so the sealed bank cannot collide with a working one."""

SEALED_NAMESPACE_V2: Final[str] = "mars777-research/final-holdout-v2/"

SEALED_NAMESPACE_V3: Final[str] = "mars777-research/final-holdout-v3/"
"""The third sealed namespace. v2 was consumed by the P4 evaluation and can
never be blind again; a new cycle with a genuinely new candidate needs its own."""
"""The second sealed namespace, for the second promotion cycle.

The v1 bank is **spent**: a frozen candidate was evaluated against it exactly
once and the result is committed. A consumed holdout does not become blind again
by being reused, so a new cycle gets a new version rather than a second look at
the old one - which is the rule §9 froze, applied to a cycle that passed rather
than to one that failed."""

DEVELOPMENT: Final[str] = "development"
VALIDATION: Final[str] = "holdout"
"""The bank Stage 9B-0 executed. Its **label** keeps the old name so the
committed result files still load; its **meaning** is validation, because its
outcomes were read before candidate hypotheses were ranked."""

STRESS: Final[str] = "stress"
FINAL_HOLDOUT: Final[str] = "final_holdout"
FINAL_HOLDOUT_V2: Final[str] = "final_holdout_v2"
FINAL_HOLDOUT_V3: Final[str] = "final_holdout_v3"

DEVELOPMENT_SIZE: Final[int] = 64
VALIDATION_SIZE: Final[int] = 64
STRESS_SIZE: Final[int] = 16
FINAL_HOLDOUT_SIZE: Final[int] = 64
FINAL_HOLDOUT_V2_SIZE: Final[int] = 64
FINAL_HOLDOUT_V3_SIZE: Final[int] = 64


def seed_at(name: str, index: int, namespace: str = NAMESPACE) -> int:
    """The seed for *index* of the set called *name*. Pure and reproducible."""
    if index < 0:
        raise ValueError("a seed index is not negative")
    material = f"{namespace}{name}/{index}".encode()
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


def bank(name: str, size: int, namespace: str = NAMESPACE) -> SeedBank:
    """Build the bank called *name* with *size* seeds, deterministically."""
    if size <= 0:
        raise ValueError("a seed bank holds at least one seed")
    return SeedBank(name, tuple(seed_at(name, index, namespace) for index in range(size)))


def development_bank() -> SeedBank:
    """Used while designing a candidate. May be looked at as often as needed."""
    return bank(DEVELOPMENT, DEVELOPMENT_SIZE)


def validation_bank() -> SeedBank:
    """Compared against occasionally, once a coherent candidate revision exists.

    Not a final holdout: Stage 9B-0 already read its baseline outcomes, so it
    can support a comparison but can never again decide a promotion.
    """
    return bank(VALIDATION, VALIDATION_SIZE)


def final_holdout_bank() -> SeedBank:
    """The sealed bank. Exactly one promotion evaluation, after a candidate freezes.

    **No game has been played on it and none may be until Stage 9B-1 finishes a
    candidate.** It has its own namespace so it cannot overlap a working bank,
    and `bench_main` excludes it from every default command.
    """
    return bank(FINAL_HOLDOUT, FINAL_HOLDOUT_SIZE, SEALED_NAMESPACE)


def final_holdout_v2_bank() -> SeedBank:
    """The second sealed bank. Fixed now, while no v2 candidate exists.

    Disjoint from every working bank *and* from the spent v1 bank, by namespace
    and checked by `disjoint`. No game has been played on it.
    """
    return bank(FINAL_HOLDOUT_V2, FINAL_HOLDOUT_V2_SIZE, SEALED_NAMESPACE_V2)


def final_holdout_v3_bank() -> SeedBank:
    """The third sealed bank, fixed before the P6 candidate was evaluated on it.

    v2 is spent: the P4 evaluation consumed it, and a spent holdout does not
    become blind again by being renamed. This bank has its own namespace, is
    checked disjoint from both spent banks and from every working bank, and no
    game has been played on it at the moment it is committed.
    """
    return bank(FINAL_HOLDOUT_V3, FINAL_HOLDOUT_V3_SIZE, SEALED_NAMESPACE_V3)


def stress_bank() -> SeedBank:
    """Rare and adversarial configurations, reported separately."""
    return bank(STRESS, STRESS_SIZE)


def working_banks() -> tuple[SeedBank, ...]:
    """Every bank a research command may execute. The sealed one is not here."""
    return (development_bank(), validation_bank(), stress_bank())


def banks() -> tuple[SeedBank, ...]:
    """Every bank that exists, all three sealed ones included, for the manifest only.

    A sealed bank appears here whether or not it has been consumed. The manifest
    is the record of what was available to a cycle, and a spent bank that
    vanished from it would make an earlier evaluation unauditable.
    """
    return (
        *working_banks(),
        final_holdout_bank(),
        final_holdout_v2_bank(),
        final_holdout_v3_bank(),
    )


def disjoint(first: SeedBank, second: SeedBank) -> bool:
    """Whether two banks share no seed at all - the separation, checked."""
    return not set(first.seeds) & set(second.seeds)
