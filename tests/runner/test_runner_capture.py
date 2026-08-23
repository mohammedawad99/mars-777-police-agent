"""The four capture routes, over two real agents and the real FastMCP wire.

Every outcome below is decoded from an actual `receive_turn` response: the
commit and acknowledgement go through `PeerRunner`, and the reveal crosses the
same real `PeerTransportPort`, client, server, `InboundPeerOperations` and the
thief's own `TurnProtocolRuntime` before coming back as `TurnOutcomeWire`. No
test constructs a `TurnOutcome`, and the thief's position never travels.
"""

import asyncio
from collections.abc import Iterator

import pytest
import runner_builders as build
import turn_builders
from r16_builders import GROUP_A, GROUP_B
from test_runner_two_sided import CURSOR, sealed, step0_on

from mars777_police.app.capture_values import CaptureAnswer, CaptureClaim
from mars777_police.app.peer_turn_messages import Reveal
from mars777_police.app.sealed_record_values import ActorRole, Intent
from mars777_police.domain.actions import BarrierAction
from mars777_police.domain.board import Board, Position


@pytest.fixture
def pair() -> Iterator[tuple[object, object]]:
    """Side A police, side B thief, each behind its own real inbound server."""
    a = build.side(GROUP_A, ActorRole.POLICE)
    b = build.side(GROUP_B, ActorRole.THIEF)
    with build.server_for(a) as server_a, build.server_for(b) as server_b:
        a.url, b.url = server_a.url, server_b.url
        yield a, b


async def declare(a: object, b: object, reveal_of: object) -> object:
    """Drive one real commit, ack and reveal, returning the peer's outcome."""
    a_to_b = await step0_on(a, b.url)
    b_to_a = await step0_on(b, a.url)
    prepared = await a.runner(a_to_b).open_turn(
        state=sealed(ActorRole.POLICE),
        action=turn_builders.legal_reveal().action,
        intent=Intent.TRUTH,
        hint="closing in",
        cursor=CURSOR,
    )
    await b.runner(b_to_a).acknowledge_peer_turn()
    return await a_to_b.send_reveal(reveal_of(prepared))


def move_claiming(cell: Position) -> object:
    """A police movement reveal that declares *cell* holds the thief."""
    return lambda prepared: Reveal(
        CURSOR,
        prepared.reveal.action,
        prepared.reveal.hint,
        CaptureClaim(cell),
        prepared.reveal.scent_emission,
    )


def barrier_on(cell: Position) -> object:
    """A police barrier reveal whose public target is *cell*."""
    return lambda prepared: Reveal(
        CURSOR, BarrierAction(cell), prepared.reveal.hint, None, prepared.reveal.scent_emission
    )


def test_a_true_same_cell_claim_answers_caught_over_the_real_wire(pair: tuple) -> None:
    a, b = pair
    here = b.turn.truth.own_position
    outcome = asyncio.run(declare(a, b, move_claiming(here)))
    assert outcome.capture is CaptureAnswer.CAUGHT
    assert outcome.accepted is True
    assert b.turn.audit_required is True
    assert b.turn.truth.own_position == here


def test_a_false_claim_answers_not_caught_and_still_requires_the_audit(pair: tuple) -> None:
    a, b = pair
    here = b.turn.truth.own_position
    elsewhere = Position(0, 0) if here != Position(0, 0) else Position(1, 1)
    outcome = asyncio.run(declare(a, b, move_claiming(elsewhere)))
    assert outcome.capture is CaptureAnswer.NOT_CAUGHT
    assert b.turn.audit_required is True
    assert b.turn.truth.own_position == here


def test_a_barrier_on_the_thief_cell_answers_caught_without_a_claim(pair: tuple) -> None:
    a, b = pair
    here = b.turn.truth.own_position
    outcome = asyncio.run(declare(a, b, barrier_on(here)))
    assert outcome.capture is CaptureAnswer.CAUGHT
    assert b.turn.truth.own_position == here
    assert b.turn.audit_required is False


def test_a_barrier_that_closes_the_last_escape_answers_caught(pair: tuple) -> None:
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
    outcome = asyncio.run(declare(a, b, barrier_on(ways_out[-1])))
    assert outcome.capture is CaptureAnswer.CAUGHT
    assert b.turn.truth.board.is_blocked(ways_out[-1])


def test_an_ordinary_turn_over_the_wire_asks_no_capture_question(pair: tuple) -> None:
    a, b = pair
    outcome = asyncio.run(declare(a, b, lambda prepared: prepared.reveal))
    assert outcome.capture is CaptureAnswer.NO_QUESTION
    assert b.turn.audit_required is False
