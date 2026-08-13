"""What a semantic review of one finished sub-game can conclude.

The final audit R7 built answers one question - *is the disclosed log the log
that was really committed?* - and it answers it with SHA-256. A peer can pass it
while still having played a game that never happened: a piece that teleports, a
move through a barrier, a capture declared on an empty cell, an answer that
contradicts the position the same peer later discloses. None of that is a hash
failure, because every one of those stories can be sealed honestly.

This is the vocabulary for the second question - *and was that log a legal,
truthful game?* - kept as values so the review itself owns no state and the
finding can be written to disk, recorded in the gate and compared in a test.

**One finding, not a list.** The first violation in step order is the one that
decides the sub-game; nothing after it is trustworthy enough to enumerate.
"""

from dataclasses import dataclass
from enum import StrEnum

from ..domain.barriers import BarrierQuota
from ..domain.board import Board, Position
from .sealed_record_values import ActorRole


class SemanticVerdict(StrEnum):
    """What the replay of a disclosed sub-game found, in one closed vocabulary."""

    CONSISTENT = "CONSISTENT"
    WRONG_START = "WRONG_START"
    BROKEN_TRAJECTORY = "BROKEN_TRAJECTORY"
    ILLEGAL_ACTION = "ILLEGAL_ACTION"
    WRONG_BARRIER_SET = "WRONG_BARRIER_SET"
    FALSE_CAPTURE_CLAIM = "FALSE_CAPTURE_CLAIM"
    DISHONEST_CAPTURE_ANSWER = "DISHONEST_CAPTURE_ANSWER"
    FALSE_CLAIM_AFFIRMED = "FALSE_CLAIM_AFFIRMED"
    """One event, two faults: a declaration that was false **and** an answer
    that confirmed it. Both sides broke a different rule (CRYPTO-005 and
    CRYPTO-004), so neither may be dropped, and the event is not a capture."""


TAMPERING: frozenset[SemanticVerdict] = frozenset(
    {
        SemanticVerdict.WRONG_START,
        SemanticVerdict.BROKEN_TRAJECTORY,
        SemanticVerdict.WRONG_BARRIER_SET,
        SemanticVerdict.DISHONEST_CAPTURE_ANSWER,
        SemanticVerdict.FALSE_CLAIM_AFFIRMED,
    }
)
"""The findings whose disclosed record cannot be believed at all.

Each of these is a *false record*: a sealed state that contradicts the locked
start cells, one that contradicts the mover's own earlier state, a barrier set
that contradicts the placements both sides publicly revealed, or an answer that
contradicts the answerer's own disclosed position. `CRYPTO-004` gives the last
one "immediate DQ for denying reality", and `CRYPTO-003` / `REPLAY-002` give a
disclosure that cannot be reconciled the same treatment.

`ILLEGAL_ACTION` and `FALSE_CAPTURE_CLAIM` are deliberately **absent**, and the
difference is the whole point of splitting the two ideas: both are honest
records of bad play. `GAME-003` sanctions an illegal move as a **technical
loss** and `BAR-004` an illegal placement as an audit loss, while `CRYPTO-005`
sanctions a false declaration as "score 0 + technical loss". None of those says
disqualification, and a record that truthfully says "I played illegally" is not
a forgery."""

SCORED_AS_TECHNICAL_LOSS: frozenset[SemanticVerdict] = frozenset(
    {
        SemanticVerdict.ILLEGAL_ACTION,
        SemanticVerdict.FALSE_CAPTURE_CLAIM,
        SemanticVerdict.FALSE_CLAIM_AFFIRMED,
    }
)
"""The findings that decide the sub-game's end event instead of blocking it.

`FALSE_CLAIM_AFFIRMED` is in **both** sets on purpose: the false declaration is
scored 0/0 (`CRYPTO-005`) and the answer that affirmed it is disqualifying
(`CRYPTO-004`). Neither sanction cancels the other, and the sub-game can never
be recorded as the capture the two of them described."""


@dataclass(frozen=True, slots=True)
class SemanticFinding:
    """The one violation a sub-game's replay found, or that it found none."""

    verdict: SemanticVerdict
    step: int | None = None
    at_fault: ActorRole | None = None
    also_at_fault: ActorRole | None = None
    """The second side, for the one verdict where two sides are each at fault.

    Deliberately a second `ActorRole` rather than a list or a free-text note:
    the game has exactly two sides, so a bilateral event has exactly two named
    faults and nothing here can grow into an unbounded log line."""

    def __post_init__(self) -> None:
        if (self.verdict is SemanticVerdict.CONSISTENT) != (self.step is None):
            raise ValueError("a violation names its step, and a consistent replay names none")
        bilateral = self.verdict is SemanticVerdict.FALSE_CLAIM_AFFIRMED
        if bilateral != (self.also_at_fault is not None):
            raise ValueError("only a bilateral finding names a second side, and it must name one")
        if bilateral and self.at_fault is self.also_at_fault:
            raise ValueError("a bilateral finding names the two different sides")

    @property
    def honest(self) -> bool:
        """Whether the disclosed record may still be trusted as a real game."""
        return self.verdict not in TAMPERING

    @property
    def consistent(self) -> bool:
        """Whether the replay found nothing at all to report."""
        return self.verdict is SemanticVerdict.CONSISTENT


CONSISTENT = SemanticFinding(SemanticVerdict.CONSISTENT)
"""The finding of a sub-game whose replay held together in every respect."""


@dataclass(frozen=True, slots=True)
class SemanticRules:
    """The locked facts a replay needs: geometry, quota and the two start cells."""

    board: Board
    quota: BarrierQuota
    cop_start: Position
    thief_start: Position

    def start_for(self, role: ActorRole) -> Position:
        """The cell the config locked for *role* before any turn was played."""
        return self.cop_start if role is ActorRole.POLICE else self.thief_start
