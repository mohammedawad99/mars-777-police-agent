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
from .seeds import (
    FINAL_HOLDOUT,
    FINAL_HOLDOUT_V2,
    SEALED_NAMESPACE,
    SEALED_NAMESPACE_V2,
    final_holdout_bank,
    final_holdout_v2_bank,
)

SEALED_AT = "stage-9B-0F"
"""The stage that fixed this set. Recorded so "before the candidate" is checkable."""

SEALED_AT_V2 = "stage-E-0"
"""The stage that fixed the **second** set, before any v2 candidate existed."""

RESULTS_PRESENT: Final[bool] = False
"""Whether any final-holdout outcome exists in this repository. It must be false
until a frozen candidate is evaluated exactly once, in a later stage."""

RESULTS_PRESENT_V2: Final[bool] = False

RESULTS_PRESENT_V3: Final[bool] = True
"""False when sealed; true now. The v3 bank was consumed once by the P6
evaluation and can never be blind again - see `results/final_holdout_v3_result`,
which rejected the candidate."""
"""The same claim for the second sealed set, and true of it today.

The v1 flag stayed `False` in the *sealed manifest* even after that set was
consumed, because the manifest records what was true when the set was sealed;
the consumption is recorded by the separate one-shot result file existing at
all. This flag is that same claim, for a set nothing has yet been played on."""


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
    """Enumerate the v1 sealed scenarios for *role*. Plays nothing, scores nothing."""
    return _enumerate(role, final_holdout_bank().seeds)


def sealed_set_v2(role: str) -> SealedSet:
    """Enumerate the **v2** sealed scenarios, minus anything v1 already consumed.

    A new bank is not automatically a blind one. `scenario_id` covers the family,
    the configuration and both opening cells, so a configuration whose legal
    opening space is *finite* produces the same scenarios however the seeds are
    drawn - `appendixF-example` has exactly one opening and collides every time.
    Enumerating v2 from a fresh namespace still reproduced **66** scenarios that
    the spent v1 evaluation already played.

    Sixty-six out of a couple of thousand would have moved no headline, which is
    precisely why it is worth removing rather than mentioning: a holdout is not
    "mostly blind". They are excluded here, before any v2 candidate exists, and
    the count is recorded in the manifest so the exclusion is checkable rather
    than trusted.
    """
    consumed = set(sealed_set(role).scenarios)
    fresh = tuple(
        one
        for one in _enumerate(role, final_holdout_v2_bank().seeds).scenarios
        if one not in consumed
    )
    return SealedSet(role, fresh)


def carried_over(role: str) -> int:
    """How many v2 scenarios were dropped because v1 had already played them."""
    enumerated = len(_enumerate(role, final_holdout_v2_bank().seeds).scenarios)
    return enumerated - len(sealed_set_v2(role).scenarios)


def _enumerate(role: str, seeds: tuple[int, ...]) -> SealedSet:
    """The scenarios *seeds* name, in a fixed order. Nothing is played or scored."""
    found: list[str] = []
    for family in FAMILIES:
        for config in corpus():
            for seed, police, thief in openings(config, seeds):
                found.append(scenario_id(role, family, config, seed, police, thief))
    return SealedSet(role, tuple(found))


def sealed_document_v2(role: str) -> dict[str, object]:
    """The v2 sealed manifest, naming its own namespace, bank and stage."""
    document = dict(sealed_set_v2(role).as_document())
    document.update(
        {
            "sealed_at": SEALED_AT_V2,
            "namespace": SEALED_NAMESPACE_V2,
            "bank": FINAL_HOLDOUT_V2,
            "seed_sha256": final_holdout_v2_bank().digest,
            "results_present": RESULTS_PRESENT_V2,
            "supersedes": FINAL_HOLDOUT,
            "excluded_as_already_played": carried_over(role),
        }
    )
    return document
