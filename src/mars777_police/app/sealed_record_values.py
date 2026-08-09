"""The semantic values a sealed commitment record is composed from.

Three of the eight sealed members had no exact representation until Stage
4E-R9-R1 froze them: `role`, `intent` and `state`. This module implements those
three and nothing else - it never serializes, canonicalizes or hashes, and it
does not know what a commitment is. `protocol.canonical` and
`protocol.commitment` own that work and consume these values.

`Intent`'s vocabulary is **source law**: Ch 5 §5.3.1 (p.51) defines the flag as
saying whether the accompanying hint is true *(truth)* or misleading *(lie)*,
printing both English words. `ActorRole`'s is **PROJECT-CONTRACT**: the book
labels the sides only as *Cop* / *Thief* in Figure 6, which is explanatory
terminology and never a byte string. Both are closed vocabularies, so they are
`StrEnum`s rather than validated strings, and mapping the repository's runtime
`ROLE` constant onto `ActorRole` stays a producer duty, deliberately not here.

`SealedState` is the own-known snapshot of JDEC-012 / NDEC-002 / PRD06-FR-068.
It validates composition only: exact component types, a positive `step`, and
barriers that are *already* ordered and unique. Board legality, quotas and the
builder's `state.step == cursor.step` / `state.role == role` checks all live
with owners that can see the game; a value that reached for them would stop
being a value. No opponent truth is representable.
"""

from dataclasses import dataclass
from enum import StrEnum
from itertools import pairwise

from ..domain.board import Position
from .protocol_values import Sha256Digest


class ActorRole(StrEnum):
    """The acting side of a turn, in the canonical sealed spelling.

    Exactly two members and no rescue hook: an unrecognised spelling raises
    rather than resolving, because `Cop` (the book's display word), `POLICE`
    (our runtime constant) and `cop` (a PRD-01 score key) all denote this side
    in some other contract, and silently accepting any of them would let two
    peers seal different bytes for the same turn.
    """

    POLICE = "police"
    THIEF = "thief"


class Intent(StrEnum):
    """Whether the hint sealed alongside it is truthful or deliberately misleading.

    The classification itself must be honest even when the hint is a bluff
    (PRD04-FR-016), but that is a producer obligation: this value only fixes the
    two words the source supplies.
    """

    TRUTH = "truth"
    LIE = "lie"


def _require_barriers(barriers: tuple[Position, ...]) -> None:
    """Refuse anything the canonical mapper would otherwise have to repair."""
    if type(barriers) is not tuple:
        raise ValueError(f"barriers must be a tuple, got {type(barriers).__name__}")
    for barrier in barriers:
        if type(barrier) is not Position:
            raise ValueError(f"every barrier must be a Position, got {type(barrier).__name__}")
    keys = [(barrier.row, barrier.col) for barrier in barriers]
    if any(later <= earlier for earlier, later in pairwise(keys)):
        raise ValueError(
            "barriers must already be sorted by (row, col) and duplicate-free;"
            " they are never sorted, deduplicated or coerced here"
        )


@dataclass(frozen=True, slots=True)
class SealedState:
    """The own-known situation a commitment is bound to.

    Own position, declared barriers, step, role and the config identity - and
    nothing the agent could not legitimately know. The opponent's true position
    is unknown under partial observation, so there is no field for it.
    """

    config_sha256: Sha256Digest
    self_pos: Position
    barriers: tuple[Position, ...]
    step: int
    role: ActorRole

    def __post_init__(self) -> None:
        if type(self.config_sha256) is not Sha256Digest:
            raise ValueError(
                f"config_sha256 must be a Sha256Digest, got {type(self.config_sha256).__name__}"
            )
        if type(self.self_pos) is not Position:
            raise ValueError(f"self_pos must be a Position, got {type(self.self_pos).__name__}")
        _require_barriers(self.barriers)
        if type(self.step) is not int:
            raise ValueError(f"step must be an int, got {type(self.step).__name__}")
        if self.step < 1:
            raise ValueError(f"step must be at least 1, got {self.step}")
        if type(self.role) is not ActorRole:
            raise ValueError(f"role must be an ActorRole, got {type(self.role).__name__}")
