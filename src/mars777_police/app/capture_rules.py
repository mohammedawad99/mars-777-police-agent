"""Answering a capture question from our own truth and the public board.

Three routes reach the same answer, and every one of them is computed by the
side that owns the cell in question - never by the side that asks:

* **same cell** (`PRD01-FR-050`): the police declares a cell; we compare it with
  our own position and say yes or no. The claim is the only thing that travels.
* **barrier on our cell** (`BAR-003`): the police's barrier target is already
  public in its reveal, so it needs no claim at all - it *is* the question.
* **trapped** (`GAME-005`): after adopting that public barrier, a thief with no
  traversable neighbour is captured. `domain.terminal.is_trapped` owns that rule,
  including the source's reading that the board edge counts exactly like a
  barrier and that `STAY` is irrelevant - staying still is not an escape.

Nothing here learns or reveals a position. The functions take our own cell and
public facts, and return only a `CaptureAnswer`.
"""

from dataclasses import replace

from ..domain.board import Board, Position
from ..domain.terminal import is_trapped
from .capture_values import CaptureAnswer, CaptureClaim


def adopt_barrier(board: Board, target: Position) -> Board:
    """Return the public board once *target* is impassable for both sides.

    Adoption is deliberately not `place_barrier`: that rule validates the
    *placer's* adjacency against a position we do not know. What a receiver can
    do is record the cell the peer publicly declared blocked.
    """
    if not board.contains(target):
        raise ValueError(f"a public barrier must lie on the board, got {target}")
    return replace(board, blocked=board.blocked | {target})


def answer_for_claim(claim: CaptureClaim, own_position: Position) -> CaptureAnswer:
    """Answer a declared same-cell capture against our own authoritative cell."""
    if claim.cell == own_position:
        return CaptureAnswer.CAUGHT
    return CaptureAnswer.NOT_CAUGHT


def answer_for_barrier(board: Board, target: Position, own_position: Position) -> CaptureAnswer:
    """Answer the question a public barrier asks by existing.

    `NO_QUESTION` rather than `NOT_CAUGHT`: nobody declared a capture, so an
    ordinary barrier that misses is not a false claim and carries no sanction.
    """
    if target == own_position:
        return CaptureAnswer.CAUGHT
    if is_trapped(adopt_barrier(board, target), own_position):
        return CaptureAnswer.CAUGHT
    return CaptureAnswer.NO_QUESTION
