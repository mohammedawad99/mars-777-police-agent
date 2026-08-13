"""Recomputing, after the fact, what each capture question should have answered.

During play the answer is unfalsifiable by design: only the thief knows where
the thief is, so `capture_rules` answers from a cell nobody else can see and the
asker must simply take the answer. The retained transcript makes that answer
*checkable later* - once the thief's own log discloses the cell it occupied at
that step, the same three rules can be run again by the side that was told.

The rules themselves are not restated here. `answer_for_claim` and
`answer_for_barrier` are the production ones the live turn used, run a second
time against the disclosed cell, so a live answer and its recomputation cannot
drift into two readings of PRD01-FR-050, BAR-003 or GAME-005.

Three different violations come out of one comparison, and they are not the
same kind of thing:

* the answer contradicts the answerer's own disclosed position - the record is a
  forgery, and `CRYPTO-004` disqualifies it;
* the answer is truthful and says `NOT_CAUGHT` - the *declaration* was false.
  Ch 3 Table 2 and `CRYPTO-005` end that sub-game as a technical loss, 0/0, and
  the claimant carries it;
* the declaration was false **and** the answer confirmed it. That is one event
  with two faults, and it is the one case where dropping the "first" violation
  would lose a real one: the claimant declared a capture that never happened and
  the answerer denied reality to agree with it. It is reported as a single
  bilateral finding naming both sides, and it can never be a capture.
"""

from dataclasses import dataclass

from ..domain.actions import BarrierAction, PhysicalAction
from ..domain.board import Board, Position
from .capture_rules import answer_for_barrier, answer_for_claim
from .capture_transcript import CaptureRecord
from .capture_values import CaptureAnswer
from .sealed_record_values import ActorRole
from .semantic_values import CONSISTENT, SemanticFinding, SemanticVerdict


@dataclass(frozen=True, slots=True)
class AnsweredTurn:
    """One retained capture row, with the two sides the row is about."""

    row: CaptureRecord
    asked_by: ActorRole
    answered_by: ActorRole
    action: PhysicalAction

    def __post_init__(self) -> None:
        if self.asked_by is self.answered_by:
            raise ValueError("a capture question is answered by the other side")


def expected_answer(turn: AnsweredTurn, board: Board, thief_cell: Position) -> CaptureAnswer:
    """What the three capture rules give for this turn, on the disclosed cell."""
    claim = turn.row.claim
    if claim is not None:
        return answer_for_claim(claim, thief_cell)
    action = turn.action
    if isinstance(action, BarrierAction):
        return answer_for_barrier(board, action.target, thief_cell)
    return CaptureAnswer.NO_QUESTION


def review_answer(turn: AnsweredTurn, board: Board, thief_cell: Position) -> SemanticFinding:
    """Compare what was answered live with what the disclosed game required."""
    step, answer = turn.row.cursor.step, turn.row.answer
    expected = expected_answer(turn, board, thief_cell)
    if answer is expected:
        if turn.row.claim is not None and answer is CaptureAnswer.NOT_CAUGHT:
            return SemanticFinding(SemanticVerdict.FALSE_CAPTURE_CLAIM, step, turn.asked_by)
        return CONSISTENT
    if expected is CaptureAnswer.NOT_CAUGHT and answer is CaptureAnswer.CAUGHT:
        return SemanticFinding(
            SemanticVerdict.FALSE_CLAIM_AFFIRMED, step, turn.answered_by, turn.asked_by
        )
    return SemanticFinding(SemanticVerdict.DISHONEST_CAPTURE_ANSWER, step, turn.answered_by)
