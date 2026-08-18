"""What a lawful placement would do to the board, asked before it is made.

Two rules already own everything here and neither is restated: `is_placeable`
and `place_barrier` decide whether a placement is legal and what board it
produces, and `is_trapped` decides whether a cell has any traversable
neighbour left (`GAME-005`, with the board edge counting exactly like a
barrier). This module only puts one question to them - *which cells would this
placement newly corner* - so a policy can weigh an irreversible quota unit
against the answer.

**Newly, and traversable.** A cell that was already cornered before the
placement is not evidence for it; and the target itself is excluded, because
after the placement it is a wall rather than a cornered actor. Both would
otherwise inflate the count a policy is about to spend a barrier on.

**An illegal candidate has no effect to describe.** Rather than raise, it
answers with nothing: the legality authority has already spoken, and a strategy
enumerating candidates should not have to catch an exception to learn that.

The order is `(row, col)`, so two runs and two platforms agree on which cell
comes first.
"""

from .barriers import BarrierQuota, is_placeable, place_barrier
from .board import Board, Position
from .terminal import is_trapped


def newly_trapped(
    board: Board, actor: Position, target: Position, quota: BarrierQuota
) -> tuple[Position, ...]:
    """The traversable cells that *target* would corner and nothing else would."""
    if not is_placeable(board, actor, target, quota):
        return ()
    after = place_barrier(board, actor, target, quota)
    cornered = [
        cell
        for row in range(board.rows)
        for col in range(board.cols)
        if (cell := Position(row + board.start_index, col + board.start_index)) != target
        and after.is_traversable(cell)
        and is_trapped(after, cell)
        and not is_trapped(board, cell)
    ]
    return tuple(sorted(cornered, key=lambda cell: (cell.row, cell.col)))
