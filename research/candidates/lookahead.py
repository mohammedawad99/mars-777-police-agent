"""P6 - bounded adversarial lookahead over the evader's legal replies.

**Why a different mechanism, not another weighting.** P5 and V3 both spent the
move on containment and both lost, hardest on the families a pursuer should
exploit. That is not a coefficient being wrong; it is evidence that giving up a
step of pursuit costs more than the region it buys. So this candidate keeps
every move as a move and changes only *which* move, by asking what the evader
can do about it.

**The shipped mover is greedy about now.** It closes on the strongest believed
cell, which is right when the evader is cornered and wrong when the evader can
step away from the exact direction we chose. A cell one step nearer that leaves
the evader four escapes can be worth less than a cell equally near that leaves
it one.

**One ply, and the worst case.** For each legal move of ours, the evader is
assumed to reply with whichever legal move maximises its distance from where we
would then stand - the strongest reply available to it, not an average over
replies it might make. We take the move whose worst case is best. That is a
minimax of depth one on each side: enough to see a step-away, cheap enough to
stay far inside the response budget, and bounded by construction rather than by
a cutoff, since both branching factors are at most five.

**Ties break toward pressure, then deterministically.** Equal worst cases are
separated by the distance after our own move, so a move that closes ground is
preferred to one that circles; anything still equal breaks on the move's own
name, so the same state always produces the same action and a replay agrees
with the log.

**Only lawful evidence enters.** The evader's assumed position is the strongest
believed cell and nothing else - no hidden truth, no remembered trajectory, no
opponent identity. With no belief at all there is nothing to search against, so
the shipped policy answers unchanged.

**The barrier gate is untouched, and that is the whole discipline.** A first
version of this candidate returned a move in every state and captured nothing at
all, across every family: the shipped policy captures largely by placing a
barrier under a believed cell (BAR-003), and answering with a move discarded
that mechanism entirely. It measured two changes at once and could not have said
which one mattered. So the shipped policy is asked first; when it wants a
barrier it gets one, and the search decides only what a move would have been.
"""

from dataclasses import dataclass, field
from typing import Final

from mars777_police.app.competitive_strategy import CompetitiveStrategy, believed_cells
from mars777_police.domain.actions import MoveAction, PhysicalAction
from mars777_police.domain.board import Board, Position
from mars777_police.domain.observation import Observation
from mars777_police.domain.rules import Move, destination_of, legal_moves

REVISION: Final[str] = "p6-lookahead-1"


def _distance(one: Position, other: Position) -> int:
    """Manhattan distance - the board's own step metric."""
    return abs(one.row - other.row) + abs(one.col - other.col)


def believed_position(observation: Observation) -> Position | None:
    """The strongest believed cell, or `None` when nothing is believed."""
    believed = believed_cells(observation)
    if not believed:
        return None
    return max(believed, key=lambda pair: (pair[1], -pair[0].row, -pair[0].col))[0]


def evader_best_reply(board: Board, evader: Position, pursuer: Position) -> int:
    """How far the evader can get from *pursuer*, playing its strongest reply.

    Staying is a legal reply and is included: an evader already at its furthest
    has no reason to move, and omitting it would credit us with pressure the
    evader can simply decline.
    """
    options = [evader, *(destination_of(evader, move) for move in legal_moves(board, evader))]
    return max(_distance(pursuer, cell) for cell in options)


@dataclass(frozen=True, slots=True)
class LookaheadStrategy:
    """Take the move whose worst case, after the evader's best reply, is best."""

    fallback: CompetitiveStrategy = field(default_factory=CompetitiveStrategy)

    def choose_action(self, observation: Observation) -> PhysicalAction:
        """Search one ply each side, or defer when there is nothing to search.

        Deferred in two cases, not one: no belief to search against, and a state
        where the shipped policy wants a barrier. The second keeps this candidate
        to a single change.
        """
        shipped = self.fallback.choose_action(observation)
        target = believed_position(observation)
        if target is None or not isinstance(shipped, MoveAction):
            return shipped
        board, here = observation.board, observation.own_position
        moves = [Move.STAY, *legal_moves(board, here)]
        scored = [
            (
                evader_best_reply(board, target, destination_of(here, move)),
                _distance(destination_of(here, move), target),
                move.value,
                move,
            )
            for move in moves
        ]
        return MoveAction(min(scored)[3])
