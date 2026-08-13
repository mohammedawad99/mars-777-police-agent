"""Recomputing every capture answer against the cell the thief later disclosed.

The five routes a live turn can take are all here - no question, a true claim, a
false one, a barrier that lands on the thief and a barrier that closes the last
way out - each answered honestly once and dishonestly once.
"""

import pytest
from semantic_builders import NORTH, RULES, THIEF, row

from mars777_police.app.capture_values import CaptureAnswer
from mars777_police.app.sealed_record_values import ActorRole
from mars777_police.app.semantic_capture import AnsweredTurn, expected_answer, review_answer
from mars777_police.app.semantic_values import SemanticVerdict
from mars777_police.domain.actions import BarrierAction
from mars777_police.domain.board import Board, Position

POLICE, THIEF_ROLE = ActorRole.POLICE, ActorRole.THIEF
ELSEWHERE = Position(0, 0)
CAUGHT, NOT_CAUGHT, NO_QUESTION = (
    CaptureAnswer.CAUGHT,
    CaptureAnswer.NOT_CAUGHT,
    CaptureAnswer.NO_QUESTION,
)


def asked(answer: CaptureAnswer, claim: Position | None = None, target: object = None) -> object:
    """One police question of the thief: a claim, a barrier, or neither."""
    action = NORTH if target is None else BarrierAction(target)  # type: ignore[arg-type]
    return AnsweredTurn(row(1, answer, claim), POLICE, THIEF_ROLE, action)


def review(turn: object, board: Board = RULES.board) -> object:
    """Recompute that answer against the thief's disclosed cell."""
    return review_answer(turn, board, THIEF)  # type: ignore[arg-type]


def caged(escape: Position) -> Board:
    """The thief's cell with every way out closed except *escape*."""
    ways = [cell for cell in RULES.board.orthogonal_neighbours(THIEF) if cell != escape]
    return Board(rows=RULES.board.rows, cols=RULES.board.cols, blocked=frozenset(ways))


def test_an_ordinary_turn_asked_nothing_and_said_so() -> None:
    assert review(asked(NO_QUESTION)).consistent


def test_a_true_claim_answered_caught_is_consistent() -> None:
    assert review(asked(CAUGHT, claim=THIEF)).consistent


def test_a_true_claim_answered_not_caught_is_a_dishonest_answer() -> None:
    finding = review(asked(NOT_CAUGHT, claim=THIEF))
    assert finding.verdict is SemanticVerdict.DISHONEST_CAPTURE_ANSWER
    assert (finding.step, finding.at_fault) == (1, THIEF_ROLE)
    assert not finding.honest


def test_a_false_claim_answered_honestly_is_the_claimant_s_own_sanction() -> None:
    finding = review(asked(NOT_CAUGHT, claim=ELSEWHERE))
    assert finding.verdict is SemanticVerdict.FALSE_CAPTURE_CLAIM
    assert (finding.step, finding.at_fault) == (1, POLICE)
    assert finding.honest, "a wrong declaration is a scored end event, not a forgery"


def test_a_false_claim_affirmed_as_caught_names_both_faults() -> None:
    """Neither fault may be dropped: one side declared, the other confirmed."""
    finding = review(asked(CAUGHT, claim=ELSEWHERE))
    assert finding.verdict is SemanticVerdict.FALSE_CLAIM_AFFIRMED
    assert (finding.at_fault, finding.also_at_fault) == (THIEF_ROLE, POLICE)
    assert not finding.honest, "denying reality is CRYPTO-004 disqualifying"


def test_a_barrier_on_the_thief_cell_needed_no_claim_to_ask() -> None:
    assert review(asked(CAUGHT, target=THIEF)).consistent
    assert expected_answer(asked(CAUGHT, target=THIEF), RULES.board, THIEF) is CAUGHT


def test_a_denied_true_claim_is_one_sided_and_stays_one_sided() -> None:
    """The declaration was true, so only the answerer is named."""
    finding = review(asked(NOT_CAUGHT, claim=THIEF))
    assert finding.verdict is SemanticVerdict.DISHONEST_CAPTURE_ANSWER
    assert finding.also_at_fault is None


def test_a_barrier_on_the_thief_cell_answered_no_question_is_dishonest() -> None:
    finding = review(asked(NO_QUESTION, target=THIEF))
    assert finding.verdict is SemanticVerdict.DISHONEST_CAPTURE_ANSWER


def test_the_barrier_that_closes_the_last_way_out_captures() -> None:
    escape = RULES.board.orthogonal_neighbours(THIEF)[0]
    assert review(asked(CAUGHT, target=escape), caged(escape)).consistent


def test_the_same_barrier_answered_no_question_is_dishonest() -> None:
    escape = RULES.board.orthogonal_neighbours(THIEF)[0]
    finding = review(asked(NO_QUESTION, target=escape), caged(escape))
    assert finding.verdict is SemanticVerdict.DISHONEST_CAPTURE_ANSWER


def test_a_barrier_that_misses_asks_nothing_and_cannot_have_caught() -> None:
    assert review(asked(NO_QUESTION, target=ELSEWHERE)).consistent
    finding = review(asked(CAUGHT, target=ELSEWHERE))
    assert finding.verdict is SemanticVerdict.DISHONEST_CAPTURE_ANSWER


def test_an_ordinary_move_that_reported_a_capture_is_dishonest() -> None:
    finding = review(asked(CAUGHT))
    assert finding.verdict is SemanticVerdict.DISHONEST_CAPTURE_ANSWER


def test_a_side_cannot_answer_its_own_question() -> None:
    with pytest.raises(ValueError, match="answered by the other side"):
        AnsweredTurn(row(1, NO_QUESTION), POLICE, POLICE, NORTH)
