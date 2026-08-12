"""The capture question a turn may ask, and the only answers to it.

Stage 5-R8's reconciliation found that the derived `O5` contract had lost a
source-required semantic: `PROTOCOL_TIMELINE` event 8 has the receiving peer
decide "move legality **and capture claim**", while `API_BOUNDARIES` froze the
turn result as a legality-only `bool`. Capture was therefore unreachable -
`GAME-005` (trapped), `BAR-003` (barrier on the thief's cell), `CRYPTO-004` and
`CRYPTO-005` all describe a claim and a truthful answer that had nowhere to live.

**The answer is computed by whoever owns the cell in question.** A claim names a
cell; the receiver compares it with its *own* `LocalTruth` and answers. Nothing
here carries a position back: the thief's cell is never transmitted, so capture
costs the partial-observation model nothing.

**Three answers, because two would hide a sanction.** `NO_QUESTION` and
`NOT_CAUGHT` are deliberately distinct: a claim answered `NOT_CAUGHT` is a
capture the police *declared* and did not have, which `CRYPTO-005` sanctions,
while `NO_QUESTION` is an ordinary turn nobody asked anything about.
"""

from dataclasses import dataclass
from enum import StrEnum

from ..domain.board import Position


class InvalidCaptureError(ValueError):
    """A capture claim or resolution is not one of the frozen shapes."""


@dataclass(frozen=True, slots=True)
class CaptureClaim:
    """The police's declaration that one exact cell holds the thief.

    The cell must be the police's **post-action** position, which the final
    audit recomputes from its disclosed sealed state and revealed action - so a
    claim about any other cell is provable, not merely disputable.
    """

    cell: Position

    def __post_init__(self) -> None:
        if type(self.cell) is not Position:
            raise InvalidCaptureError(
                f"a capture claim needs a Position, got {type(self.cell).__name__}",
            )


class CaptureAnswer(StrEnum):
    """What the receiver of a turn can truthfully say about capture."""

    NO_QUESTION = "NO_QUESTION"
    """Nothing about capture was asked of me by this turn."""

    NOT_CAUGHT = "NOT_CAUGHT"
    """It was asked, and my own authoritative position says no."""

    CAUGHT = "CAUGHT"
    """My own truth says yes: same cell, a barrier on my cell, or trapped."""


@dataclass(frozen=True, slots=True)
class TurnOutcome:
    """What the receiver of a Reveal reports back, and nothing more.

    `accepted` is **not** remote spatial legality: the receiver never learns the
    mover's hidden pre-action cell, so it cannot decide bounds or blockage. It
    reports only what is knowable from public facts at that moment; full
    legality is proved at the final audit from the disclosed sealed record.
    """

    accepted: bool
    capture: CaptureAnswer

    def __post_init__(self) -> None:
        if type(self.accepted) is not bool:
            raise InvalidCaptureError(
                f"accepted must be a bool, got {type(self.accepted).__name__}",
            )
        if not isinstance(self.capture, CaptureAnswer):
            raise InvalidCaptureError(
                f"capture must be a CaptureAnswer, got {type(self.capture).__name__}",
            )

    @property
    def caught(self) -> bool:
        """Whether this turn ended the sub-game by capture, provisionally."""
        return self.capture is CaptureAnswer.CAUGHT
