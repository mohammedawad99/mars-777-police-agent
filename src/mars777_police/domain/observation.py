"""Everything a strategy is allowed to see, and structurally nothing else.

Ch 6 §6.4 states the epistemic premise the whole project rests on: *"the two
sides are entirely symmetric: **neither of them sees the opponent's real
position**"*. A rule that lives only in prose is a rule someone eventually
breaks, so it lives here as a *shape*. This value has three members, and there
is no field an opponent cell, a peer nonce, a reveal or a final-audit trajectory
could arrive in - a strategy that wanted to cheat would have nothing to read.

**Three members, chosen by ownership rather than convenience.** The board
carries the barrier set, which `STATE_OWNERSHIP.md` classifies PUBLIC because
App E #15/#16 make every placement openly declared and truthful. The position is
this agent's own, from `domain.truth`. The quota is locked configuration (App F
T15 #2). Nothing here is a second copy of an authoritative fact: the remaining
barrier budget stays *derived* from the board against the quota, exactly as
`domain.truth` refuses to store it.

**Deliberately absent, and not "yet".** No role - the two repositories are
separated by process, so which side is deciding is a fact about *which binary is
running*, not a value to branch on, and `LocalTurnService` already makes the
same choice by refusing the action its role cannot perform. No step count: the
baseline has no step-dependent behaviour, and a field nothing reads is a field
that invites one. No scent, hint or belief: Ch 10 §10.3.3 puts a **blind**
strategy at this stage, with those arriving one layer later.

The own cell need not be traversable. BAR-004 lets the police place a barrier on
its own cell, after which it legally stands on a blocked one - the same latitude
`domain.truth` already grants.
"""

from dataclasses import dataclass

from .barriers import BarrierQuota
from .board import Board, Position
from .errors import DomainError
from .truth import LocalTruth


class InvalidObservationError(DomainError):
    """Raised when an observation is composed from a malformed value."""


@dataclass(frozen=True, slots=True)
class Observation:
    """The role-legal facts one decision is allowed to be made from."""

    board: Board
    own_position: Position
    quota: BarrierQuota

    def __post_init__(self) -> None:
        if not isinstance(self.board, Board):
            raise InvalidObservationError(
                f"board must be a Board, got {type(self.board).__name__}",
            )
        if not isinstance(self.own_position, Position):
            raise InvalidObservationError(
                f"own_position must be a Position, got {type(self.own_position).__name__}",
            )
        if not isinstance(self.quota, BarrierQuota):
            raise InvalidObservationError(
                f"quota must be a BarrierQuota, got {type(self.quota).__name__}",
            )
        if not self.board.contains(self.own_position):
            raise InvalidObservationError(
                f"own_position {self.own_position} lies outside its own board",
            )


def observation_of(truth: LocalTruth, quota: BarrierQuota) -> Observation:
    """Project own truth and the locked quota into one decidable observation.

    A projection, never a copy with extras: the board and the cell are the very
    objects `domain.truth` holds - both frozen, so sharing them cannot leak a
    write path - and `completed_steps` is deliberately left behind rather than
    carried along for a reader that does not exist.
    """
    return Observation(board=truth.board, own_position=truth.own_position, quota=quota)
