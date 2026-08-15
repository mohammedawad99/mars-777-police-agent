"""Turning one finished lockstep round into the truth the next one starts from.

Three small readings of values other owners already validated. Nothing here
decides a rule: legality was settled by `LocalTurnService` before the action was
sealed, the peer's placement was settled by `capture_rules.adopt_barrier` when
its reveal arrived, and the capture answers were settled by whichever side owned
the cell in question. This only reads them off.

Kept beside the driver rather than inside it because the driver is a sequence
and this is arithmetic - and because a merge that quietly re-validated something
would be much harder to notice buried in a protocol loop.
"""

from ..domain.board import Board, Position
from ..domain.truth import LocalTruth
from .capture_values import CaptureAnswer
from .turn_protocol_runtime import TurnProtocolRuntime


def declared_barriers(truth: LocalTruth) -> tuple[Position, ...]:
    """The public barrier set as a sealed state reports it: ordered, not hashed.

    Sorted explicitly rather than by iterating the set, so the bytes a peer
    recomputes cannot depend on this process's hash seed.
    """
    return tuple(sorted(truth.board.blocked, key=lambda cell: (cell.row, cell.col)))


def merged_truth(pending: LocalTruth, live: LocalTruth) -> LocalTruth:
    """Our own accepted effect and the peer's public one, in one authoritative truth.

    Both boards descend from the same step-start board: *pending* adds only the
    placement our own rules validated, *live* only the one the peer publicly
    declared and `observe_reveal` adopted. Their union is exactly JDEC-016 §4's
    "the step's effects, applied afterwards" - no physics is repeated, nothing is
    re-validated against the other side's change, and neither placement can
    overwrite the other.

    The position and the step count come from *pending* alone: the peer's
    movement is the peer's, and only our own accepted action moves our counter.
    """
    board = Board(
        rows=pending.board.rows,
        cols=pending.board.cols,
        start_index=pending.board.start_index,
        blocked=pending.board.blocked | live.board.blocked,
    )
    return LocalTruth(board, pending.own_position, pending.completed_steps)


def caught_in(turn: TurnProtocolRuntime) -> bool:
    """Whether either direction of this turn answered a capture question yes.

    Both directions, because either can carry the fact: the answer we gave the
    peer's reveal, and the answer the peer gave ours. Neither is computed here -
    each was produced by the side that owns the cell being asked about.
    """
    rows = turn.capture.inbound + turn.capture.outbound
    return any(row.answer is CaptureAnswer.CAUGHT for row in rows)
