"""The sealed final holdout: fixed before a candidate existed, and unopened.

A holdout only means anything if nobody has looked. Stage 9B-0 ran a bank called
`holdout` and then read its results while ranking candidate ideas, so that bank
is now called what it is - validation. This module builds the replacement and,
more importantly, makes it **provable** that it was fixed first: the scenarios it
names are enumerated now, hashed now, and committed now, while no candidate
exists and no game has been played on them.

**Provenance, not secrecy.** The commitment is a plain SHA-256 over the
canonical scenario list, recorded beside the stage that produced it. Anyone may
recompute it; what nobody can do afterwards is quietly change which scenarios
the promotion was going to be judged on.

**No outcome is computed here.** This module enumerates conditions. It never
constructs a strategy, never plays a game and never records a result.
"""

import hashlib
from dataclasses import dataclass
from typing import Final

from .configs import corpus
from .opponents import FAMILIES
from .scenario import SCENARIO_VERSION, openings, scenario_id
from .seeds import FINAL_HOLDOUT, SEALED_NAMESPACE, final_holdout_bank

SEALED_AT = "stage-9B-0F"
"""The stage that fixed this set. Recorded so "before the candidate" is checkable."""

RESULTS_PRESENT: Final[bool] = False
"""Whether any final-holdout outcome exists in this repository. It must be false
until a frozen candidate is evaluated exactly once, in a later stage."""


@dataclass(frozen=True, slots=True)
class SealedSet:
    """The scenarios a future promotion will be judged on, and their commitment."""

    role: str
    scenarios: tuple[str, ...]

    @property
    def commitment(self) -> str:
        """SHA-256 over the canonical scenario list, in the order enumerated."""
        return hashlib.sha256("|".join(self.scenarios).encode()).hexdigest()

    def as_document(self) -> dict[str, object]:
        """The sealed manifest: enough to prove which scenarios were chosen."""
        return {
            "sealed_at": SEALED_AT,
            "namespace": SEALED_NAMESPACE,
            "bank": FINAL_HOLDOUT,
            "scenario_version": SCENARIO_VERSION,
            "count": len(self.scenarios),
            "seed_sha256": final_holdout_bank().digest,
            "commitment_sha256": self.commitment,
            "results_present": RESULTS_PRESENT,
        }


def sealed_set(role: str) -> SealedSet:
    """Enumerate the sealed scenarios for *role*. Plays nothing, scores nothing."""
    seeds = final_holdout_bank().seeds
    found: list[str] = []
    for family in FAMILIES:
        for config in corpus():
            for seed, police, thief in openings(config, seeds):
                found.append(scenario_id(role, family, config, seed, police, thief))
    return SealedSet(role, tuple(found))
