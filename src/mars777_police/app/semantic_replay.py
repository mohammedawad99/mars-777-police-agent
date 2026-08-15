"""Replaying a finished sub-game from what both sides finally disclosed.

Live play cannot check any of this. A mover's cell is sealed until the final
audit, so `TurnProtocolRuntime.accept_reveal` deliberately reports public facts
only - it cannot know whether the peer's move started where the peer says it
did. Once the nonces and the logs are open, every hidden cell is on the table
and the whole trajectory becomes checkable, with no new message and no new
transmitted field.

**The board is rebuilt, never accepted.** A step's barrier set is derived here
from the placements both sides actually revealed in earlier steps, and each
disclosed `state.barriers` is compared against that canonical set. A peer whose
snapshot carries a barrier nobody placed - or omits one that was - has written
itself a different board to be legal on.

**Within one step, both sides act on the same board.** Commitments for step *k*
are sealed before either reveal, so a barrier placed at step *k* cannot be part
of any step-*k* snapshot; effects are applied only once the step's turns have
all been checked.

Legality itself is not decided here: `domain.rules` and `domain.barriers` own
it, exactly as they do for a local turn.
"""

from dataclasses import dataclass, field

from ..domain.actions import MoveAction, PhysicalAction
from ..domain.barriers import is_placeable, place_barrier
from ..domain.board import Board, Position
from ..domain.rules import destination_of, is_legal_move
from .sealed_record_values import ActorRole
from .semantic_values import CONSISTENT, SemanticFinding, SemanticRules, SemanticVerdict


@dataclass(frozen=True, slots=True)
class PlayedTurn:
    """One side's turn as it was finally disclosed, from either side's records."""

    step: int
    role: ActorRole
    cell: Position
    barriers: tuple[Position, ...]
    action: PhysicalAction


@dataclass(slots=True)
class Replay:
    """The reconstructed sub-game, advanced one whole step at a time."""

    rules: SemanticRules
    board: Board = field(init=False)
    cells: dict[ActorRole, Position] = field(init=False)
    played: set[ActorRole] = field(default_factory=set)

    def __post_init__(self) -> None:
        self.board = self.rules.board
        self.cells = {role: self.rules.start_for(role) for role in ActorRole}

    def cell_of(self, role: ActorRole) -> Position:
        """Where *role* stands before the step now being replayed."""
        return self.cells[role]

    def check(self, turns: tuple[PlayedTurn, ...]) -> SemanticFinding:
        """Whether every turn of one step could have happened as disclosed."""
        for turn in turns:
            finding = self._check(turn)
            if not finding.consistent:
                return finding
        return CONSISTENT

    def apply(self, turns: tuple[PlayedTurn, ...]) -> None:
        """Adopt the whole step at once, after everything about it was checked.

        Separate from `check` because a capture question of the same step is
        answered from the board and the cells *before* the step's effects: the
        barrier that asks the question is the one being placed now.
        """
        for turn in turns:
            self._apply(turn)

    def cell_after(self, turn: PlayedTurn) -> Position:
        """Where *turn* leaves its actor, without adopting the turn.

        The same rule `_apply` uses, asked one turn at a time: a move resolves to
        its destination and a placement leaves the placer exactly where it stood.
        """
        action = turn.action
        if isinstance(action, MoveAction):
            return destination_of(turn.cell, action.move)
        return turn.cell

    def _check(self, turn: PlayedTurn) -> SemanticFinding:
        """Whether this disclosed turn could have happened where it says it did."""
        if turn.cell != self.cells[turn.role]:
            broken = turn.role in self.played
            verdict = SemanticVerdict.BROKEN_TRAJECTORY if broken else SemanticVerdict.WRONG_START
            return SemanticFinding(verdict, turn.step, turn.role)
        if frozenset(turn.barriers) != self.board.blocked:
            return SemanticFinding(SemanticVerdict.WRONG_BARRIER_SET, turn.step, turn.role)
        if not self._legal(turn):
            return SemanticFinding(SemanticVerdict.ILLEGAL_ACTION, turn.step, turn.role)
        return CONSISTENT

    def _legal(self, turn: PlayedTurn) -> bool:
        """Whether the domain accepts this action from this cell on this board.

        BAR-004 gives placement to the police alone. `domain.barriers` cannot
        check that - it is told a cell, not who owns it - but a replay knows
        both config-locked roles, so a thief that disclosed a placement is
        judged here rather than let through.
        """
        action = turn.action
        if isinstance(action, MoveAction):
            return is_legal_move(self.board, turn.cell, action.move)
        if turn.role is not ActorRole.POLICE:
            return False
        return is_placeable(self.board, turn.cell, action.target, self.rules.quota)

    def board_after(self, turn: PlayedTurn) -> Board:
        """The board *turn*'s actor had once its own action landed, and no more.

        Deliberately not `self.board` after `apply`: within one step both sides
        sealed before either revealed, so an emitter could not have seen the
        opponent's step-`k` placement. Judging it against the combined
        end-of-step board would test a world it never had.
        """
        action = turn.action
        if isinstance(action, MoveAction):
            return self.board
        return place_barrier(self.board, turn.cell, action.target, self.rules.quota)

    def _apply(self, turn: PlayedTurn) -> None:
        """Adopt this turn's effect: a piece moves, or a cell becomes impassable."""
        self.played.add(turn.role)
        action = turn.action
        if isinstance(action, MoveAction):
            self.cells[turn.role] = destination_of(turn.cell, action.move)
            return
        self.board = place_barrier(self.board, turn.cell, action.target, self.rules.quota)
