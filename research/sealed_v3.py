"""The third sealed cycle, kept apart from the two it supersedes.

Its own module rather than three more functions beside the first two: each
sealed cycle is a separate promise made at a separate moment, and a reader
checking whether v3 was honoured should not have to step over v1 and v2 to do
it. The shared machinery - enumeration, the commitment digest, the manifest
shape - is imported rather than repeated.
"""

from typing import Final

from .sealed import SealedSet, _enumerate, sealed_set, sealed_set_v2
from .seeds import FINAL_HOLDOUT_V2, FINAL_HOLDOUT_V3, SEALED_NAMESPACE_V3, final_holdout_v3_bank

SEALED_AT_V3 = "stage-P6-0"
"""Sealed before P6 was evaluated on it, and after P6 itself was frozen."""

RESULTS_PRESENT_V3: Final[bool] = True
"""False when sealed; true now. The v3 bank was consumed once by the P6
evaluation and can never be blind again - see `results/final_holdout_v3_result`,
which rejected the candidate."""


def sealed_set_v3(role: str) -> SealedSet:
    """The **v3** sealed scenarios, minus anything v1 or v2 already played.

    Both earlier banks are spent, so both are excluded rather than only the
    most recent. `scenario_id` covers the family, the configuration and both
    opening cells, so a configuration with a finite opening space reproduces the
    same scenarios however the seeds are drawn - which is exactly how v2
    inherited sixty-six already-played scenarios from v1.

    Excluded before any v3 result exists, and the count recorded in the manifest,
    so the exclusion is checkable rather than trusted.
    """
    spent = set(sealed_set(role).scenarios) | set(sealed_set_v2(role).scenarios)
    fresh = tuple(
        one for one in _enumerate(role, final_holdout_v3_bank().seeds).scenarios if one not in spent
    )
    return SealedSet(role, fresh)


def carried_over_v3(role: str) -> int:
    """How many v3 scenarios were dropped because v1 or v2 had already played them."""
    enumerated = len(_enumerate(role, final_holdout_v3_bank().seeds).scenarios)
    return enumerated - len(sealed_set_v3(role).scenarios)


def sealed_document_v3(role: str) -> dict[str, object]:
    """The v3 sealed manifest, naming its own namespace, bank and stage."""
    document = dict(sealed_set_v3(role).as_document())
    document.update(
        {
            "sealed_at": SEALED_AT_V3,
            "namespace": SEALED_NAMESPACE_V3,
            "bank": FINAL_HOLDOUT_V3,
            "seed_sha256": final_holdout_v3_bank().digest,
            "results_present": RESULTS_PRESENT_V3,
            "supersedes": FINAL_HOLDOUT_V2,
            "excluded_as_already_played": carried_over_v3(role),
        }
    )
    return document
