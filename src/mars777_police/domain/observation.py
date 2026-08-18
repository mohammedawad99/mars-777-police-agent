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

**A fourth member, and why it is not a fourth truth.** `scent` is what the
opponent's own disclosed emissions imply about the environment - legal partial
evidence, folded by the locked model - and `ScentBelief` has no member an
opponent position could live in. So the rule above is unchanged: there is still
no field an opponent cell, a peer nonce, a reveal or a final-audit trajectory
could arrive in. It defaults to the neutral belief, which answers zero
everywhere, so a sub-game that has heard nothing decides exactly as it did
before scent existed.

**Deliberately absent, and not "yet".** No role - the two repositories are
separated by process, so which side is deciding is a fact about *which binary is
running*, not a value to branch on, and `LocalTurnService` already makes the
same choice by refusing the action its role cannot perform. No step count: the
baseline has no step-dependent behaviour, and a field nothing reads is a field
that invites one. No hint: peer text is untrusted data with no decision role
yet.

The own cell need not be traversable. BAR-004 lets the police place a barrier on
its own cell, after which it legally stands on a blocked one - the same latitude
`domain.truth` already grants.
"""

from dataclasses import dataclass
from typing import Protocol

from .barriers import BarrierQuota
from .board import Board, Position
from .errors import DomainError
from .scent_belief import NO_SCENT, ScentBelief
from .truth import LocalTruth


class InvalidObservationError(DomainError):
    """Raised when an observation is composed from a malformed value."""


@dataclass(frozen=True, slots=True)
class Observation:
    """The role-legal facts one decision is allowed to be made from."""

    board: Board
    own_position: Position
    quota: BarrierQuota
    scent: ScentBelief = NO_SCENT

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
        if not isinstance(self.scent, ScentBelief):
            raise InvalidObservationError(
                f"scent must be a ScentBelief, got {type(self.scent).__name__}",
            )
        if not self.board.contains(self.own_position):
            raise InvalidObservationError(
                f"own_position {self.own_position} lies outside its own board",
            )


class ScentBeliefSource(Protocol):
    """Where the scent member of an observation comes from.

    Named here because this module owns what a decision may see: the runtime
    that folds the peer's emissions is an application concern, but *that an
    observation's belief is obtained rather than assumed* is part of this
    contract. Asked per decision, so the answer is never a stale opening view.
    """

    def for_board(self, board: Board) -> ScentBelief:
        """The belief this side holds about *board* right now."""
        ...


def observation_of(
    truth: LocalTruth, quota: BarrierQuota, scent: "ScentBeliefSource | None" = None
) -> Observation:
    """Project own truth and the locked quota into one decidable observation.

    A projection, never a copy with extras: the board and the cell are the very
    objects `domain.truth` holds - both frozen, so sharing them cannot leak a
    write path - and `completed_steps` is deliberately left behind rather than
    carried along for a reader that does not exist.

    The belief is *asked for* here rather than passed in already folded: the
    board a decision is about is this truth's board, so a caller cannot hand in
    a belief about a different one. Absent a source the observation carries the
    neutral belief, which is what a side that has heard nothing actually holds.
    """
    return Observation(
        board=truth.board,
        own_position=truth.own_position,
        quota=quota,
        scent=NO_SCENT if scent is None else scent.for_board(truth.board),
    )
