"""The end-of-sub-game peer-visible semantic message families.

The frozen module boundary for finalization, established at Stage 4E-R7 ahead of
the families that will live here, so the next slice adds a family rather than an
architecture. Stage 4E-R6 froze that content as `NonceRevealEntry` and
`FinalNonceReveal` - one batched reveal per peer per sub-game, carrying the
`NonceValue` that `app.protocol_values` will own - and R6-FIX1/FIX2 froze their
exact contracts, and Stage 4E-R8 implements them here.

The batch is **one message per peer per sub-game** covering that side's own
steps (Ch 5 §5.4 p.55; Figure 6 p.52), and association is `TurnCursor` alone -
it already carries ``(sub_game, step)``. No ``role`` travels: a side reveals
only its own nonces and the receiver knows the direction, the Stage 4E-R3
`by_role` result. Nothing already exchanged is repeated either - the digest came
at event 5 and the action and hint at event 7.

Validation is structural. Completeness against the steps actually played,
uniqueness, ordering, same-sub-game agreement, sender, phase, deadlines and any
comparison against outstanding commitments are all **LIVE**: a value that had to
query game state to be constructed would not be a value.
"""

from dataclasses import dataclass

from .protocol_values import NonceValue
from .turn_cursor import TurnCursor


@dataclass(frozen=True, slots=True)
class NonceRevealEntry:
    """One revealed nonce bound to the turn whose commitment it opens.

    Association only. The cursor says *which* sealed turn, the nonce completes
    the material an auditor needs beside what was already revealed - and nothing
    else belongs here, because every other fact is already owned elsewhere.
    """

    cursor: TurnCursor
    nonce: NonceValue

    def __post_init__(self) -> None:
        if type(self.cursor) is not TurnCursor:
            raise ValueError(f"cursor must be a TurnCursor, got {type(self.cursor).__name__}")
        if type(self.nonce) is not NonceValue:
            raise ValueError(f"nonce must be a NonceValue, got {type(self.nonce).__name__}")


@dataclass(frozen=True, slots=True)
class FinalNonceReveal:
    """The peer-visible final reveal: this side's nonces for one sub-game.

    An exact ``tuple`` of entries and nothing more - no ``sub_game`` field, since
    every entry's cursor carries it, and no ``role``. The tuple is taken as given:
    a list, set or generator is refused rather than converted, so the represented
    sequence is never silently reordered or consumed.

    An **empty batch is structurally valid**. Whether it is *complete* depends on
    the steps actually played, which is exactly why that check is LIVE - as are
    duplicate cursors, ordering and mixed sub-games, all accepted here.
    """

    entries: tuple[NonceRevealEntry, ...]

    def __post_init__(self) -> None:
        if type(self.entries) is not tuple:
            raise ValueError(f"entries must be a tuple, got {type(self.entries).__name__}")
        for entry in self.entries:
            if type(entry) is not NonceRevealEntry:
                raise ValueError(
                    f"every entry must be a NonceRevealEntry, got {type(entry).__name__}",
                )
