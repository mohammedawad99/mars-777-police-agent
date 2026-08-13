"""The five capture routes over the real wire, retained by both sides.

Every row below is produced by production code on both ends: the police declares
through `PeerRunner.open_turn`, the reveal crosses the real FastMCP transport,
the thief's own turn runtime answers from its own truth, and each side keeps the
row it really saw. No test writes a `CaptureRecord`, and the thief's position
never travels.
"""

import asyncio
from collections.abc import Iterator

import pytest
import runner_builders as build
import turn_builders
from r16_builders import GROUP_A, GROUP_B
from test_runner_two_sided import CURSOR, sealed, step0_on

from mars777_police.app.capture_transcript import CaptureRecord
from mars777_police.app.capture_values import CaptureAnswer, CaptureClaim
from mars777_police.app.protocol_errors import LocalDefectError
from mars777_police.app.sealed_record_values import ActorRole, Intent
from mars777_police.domain.actions import BarrierAction, PhysicalAction
from mars777_police.domain.board import Board, Position


@pytest.fixture
def pair() -> Iterator[tuple[object, object]]:
    """Side A police, side B thief, each behind its own real inbound server."""
    a = build.side(GROUP_A, "group_a", ActorRole.POLICE)
    b = build.side(GROUP_B, "group_b", ActorRole.THIEF)
    with build.server_for(a) as server_a, build.server_for(b) as server_b:
        a.url, b.url = server_a.url, server_b.url
        yield a, b


async def play(
    a: object, b: object, action: PhysicalAction, claim: Position | None = None
) -> object:
    """One whole production turn: commit, acknowledge, reveal, answer."""
    a_to_b = await step0_on(a, b.url)
    b_to_a = await step0_on(b, a.url)
    runner = a.runner(a_to_b)
    prepared = await runner.open_turn(
        state=sealed(ActorRole.POLICE),
        action=action,
        intent=Intent.TRUTH,
        hint="closing in",
        cursor=CURSOR,
        claim=None if claim is None else CaptureClaim(claim),
    )
    await b.runner(b_to_a).acknowledge_peer_turn()
    assert a.turn.capture.outbound == (), "nothing may be recorded before the answer arrives"
    return await runner.reveal_turn(prepared)


def turn(a: object, b: object, action: PhysicalAction, claim: Position | None = None) -> object:
    """Run one turn and return the outcome the peer really answered."""
    return asyncio.run(play(a, b, action, claim))


def expect(a: object, b: object, answer: CaptureAnswer, claim: Position | None = None) -> None:
    """Both sides kept the same single row, and it is the one that happened."""
    row = CaptureRecord(CURSOR, None if claim is None else CaptureClaim(claim), answer)
    assert a.turn.capture.outbound == (row,)
    assert b.turn.capture.inbound == (row,)
    assert a.producer.capture == (row,), "our disclosure carries what we were told"


def test_an_ordinary_turn_is_retained_as_a_question_nobody_asked(pair: tuple) -> None:
    a, b = pair
    outcome = turn(a, b, turn_builders.legal_reveal().action)
    assert outcome.capture is CaptureAnswer.NO_QUESTION
    expect(a, b, CaptureAnswer.NO_QUESTION)


def test_a_true_declaration_is_retained_as_caught_on_both_sides(pair: tuple) -> None:
    a, b = pair
    here = b.turn.truth.own_position
    outcome = turn(a, b, turn_builders.legal_reveal().action, here)
    assert outcome.capture is CaptureAnswer.CAUGHT
    expect(a, b, CaptureAnswer.CAUGHT, here)


def test_a_false_declaration_is_retained_with_the_cell_that_was_declared(pair: tuple) -> None:
    a, b = pair
    elsewhere = Position(0, 0)
    assert b.turn.truth.own_position != elsewhere
    outcome = turn(a, b, turn_builders.legal_reveal().action, elsewhere)
    assert outcome.capture is CaptureAnswer.NOT_CAUGHT
    expect(a, b, CaptureAnswer.NOT_CAUGHT, elsewhere)


def test_a_barrier_on_the_thief_cell_is_retained_without_any_claim(pair: tuple) -> None:
    a, b = pair
    here = b.turn.truth.own_position
    outcome = turn(a, b, BarrierAction(here))
    assert outcome.capture is CaptureAnswer.CAUGHT
    expect(a, b, CaptureAnswer.CAUGHT)


def test_the_barrier_that_closes_the_last_escape_is_retained_as_caught(pair: tuple) -> None:
    a, b = pair
    truth = b.turn.truth
    here = truth.own_position
    ways_out = [
        cell for cell in truth.board.orthogonal_neighbours(here) if truth.board.contains(cell)
    ]
    b.turn.truth = type(truth)(
        board=Board(rows=truth.board.rows, cols=truth.board.cols, blocked=frozenset(ways_out[:-1])),
        own_position=here,
        completed_steps=0,
    )
    outcome = turn(a, b, BarrierAction(ways_out[-1]))
    assert outcome.capture is CaptureAnswer.CAUGHT
    expect(a, b, CaptureAnswer.CAUGHT)


def test_our_own_producer_refuses_a_declaration_this_side_may_not_make() -> None:
    """A thief that declared would be refused by the peer; it never sends one."""
    thief = build.side(GROUP_B, "group_b", ActorRole.THIEF)
    with pytest.raises(LocalDefectError, match="only the police"):
        thief.producer.prepare_turn(
            state=sealed(ActorRole.THIEF),
            action=turn_builders.legal_reveal().action,
            intent=Intent.TRUTH,
            hint="running",
            cursor=CURSOR,
            claim=CaptureClaim(Position(1, 1)),
        )
    assert thief.producer.records == ()


def test_a_barrier_carries_no_declaration_because_it_is_one() -> None:
    police = build.side(GROUP_A, "group_a", ActorRole.POLICE)
    with pytest.raises(LocalDefectError, match="declares its own target"):
        police.producer.prepare_turn(
            state=sealed(ActorRole.POLICE),
            action=BarrierAction(Position(1, 1)),
            intent=Intent.TRUTH,
            hint="walling in",
            cursor=CURSOR,
            claim=CaptureClaim(Position(1, 1)),
        )
    assert police.producer.records == ()
