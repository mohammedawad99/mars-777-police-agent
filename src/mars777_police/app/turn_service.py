"""Local turn service: applies exactly one validated local action.

This is the LOCAL EFFECT step of a turn and nothing more. It validates a single
proposed action through the existing domain rules - it never reimplements
movement or placement - and returns new own truth. It declares no game outcome,
computes no points, exchanges nothing with a peer and performs no I/O.

PRD01-FR-010 gives one action per turn per agent, so the command union makes a
move and a placement structurally exclusive. PRD01-FR-011/FR-012 require
validation strictly before effect and leave state byte-identical on rejection:
every value object is frozen and a new one is built only after the domain
accepts the action. The step ceiling comes from the already-validated
``TurnLimits`` (App F T15 #3, MINIMUM 35, JDEC-015 applied at construction);
exhaustion is a local refusal, never a terminal verdict.
"""

from dataclasses import dataclass

from ..domain.actions import ActionKind as ActionKind
from ..domain.actions import BarrierAction as BarrierAction
from ..domain.actions import MoveAction as MoveAction
from ..domain.actions import PhysicalAction
from ..domain.barriers import BarrierQuota, place_barrier
from ..domain.board import Board, Position
from ..domain.errors import DomainError
from ..domain.rules import apply_move
from ..domain.terminal import TurnLimits
from ..domain.truth import LocalTruth


class ApplicationError(Exception):
    """Base class for local application-layer failures."""


class UnsupportedActionError(ApplicationError):
    """Raised when this role's local API cannot execute the requested action."""


class ActionsExhaustedError(ApplicationError):
    """Raised when the configured local step ceiling is already reached."""


class InvalidActionError(ApplicationError):
    """Raised when the domain rejects the proposed action."""


LocalAction = PhysicalAction
"""The action this service applies - the domain's `PhysicalAction`, not a copy.

Stage 4E-R5 moved `ActionKind`, `MoveAction` and `BarrierAction` down to
`domain.actions`, because the same chosen action must also be reachable by outer
protocol modules that may not import this one. The names stay importable here so
callers keep working, but they are **the same class objects** - there is exactly
one definition of each, and this alias is a second name for the domain's own
union, never a second union.
"""


@dataclass(frozen=True, slots=True)
class LocalActionResult:
    """What the caller needs after one accepted local action."""

    truth: LocalTruth
    kind: ActionKind
    completed_step: int


@dataclass(frozen=True, slots=True)
class LocalTurnService:
    """Applies one local action for this role: a move or a barrier placement."""

    limits: TurnLimits
    quota: BarrierQuota

    def apply(self, truth: LocalTruth, action: LocalAction) -> LocalActionResult:
        """Validate and apply *action*, returning new own truth."""
        if not isinstance(truth, LocalTruth):
            raise ApplicationError(f"truth must be a LocalTruth, got {type(truth).__name__}")
        if truth.completed_steps >= self.limits.max_moves:
            raise ActionsExhaustedError(
                f"local actions exhausted: {truth.completed_steps} of {self.limits.max_moves}",
            )
        if isinstance(action, MoveAction):
            return self._apply_move(truth, action)
        if isinstance(action, BarrierAction):
            return self._apply_barrier(truth, action)
        raise UnsupportedActionError(f"unsupported local action {type(action).__name__}")

    def _apply_move(self, truth: LocalTruth, action: MoveAction) -> LocalActionResult:
        try:
            destination = apply_move(truth.board, truth.own_position, action.move)
        except DomainError as exc:
            raise InvalidActionError(f"rejected move: {exc}") from exc
        return _advanced(truth, destination, truth.board, ActionKind.MOVE)

    def _apply_barrier(self, truth: LocalTruth, action: BarrierAction) -> LocalActionResult:
        try:
            board = place_barrier(truth.board, truth.own_position, action.target, self.quota)
        except DomainError as exc:
            raise InvalidActionError(f"rejected barrier: {exc}") from exc
        return _advanced(truth, truth.own_position, board, ActionKind.BARRIER)


def _advanced(
    truth: LocalTruth,
    position: Position,
    board: Board,
    kind: ActionKind,
) -> LocalActionResult:
    step = truth.completed_steps + 1
    return LocalActionResult(
        truth=LocalTruth(board=board, own_position=position, completed_steps=step),
        kind=kind,
        completed_step=step,
    )
