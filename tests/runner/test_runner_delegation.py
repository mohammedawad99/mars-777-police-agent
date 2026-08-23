"""Each outbound operation sends exactly what its owner produced, once."""

import asyncio

import pytest
import runner_builders as build
import turn_builders
from r16_builders import GROUP_A, GROUP_B, config
from spy_transport import SpyTransport

from mars777_police.app.peer_turn_messages import Acknowledgement, Commitment, Reveal
from mars777_police.app.protocol_errors import StaleMessageError
from mars777_police.app.sealed_record_values import ActorRole, Intent
from mars777_police.app.turn_cursor import TurnCursor
from mars777_police.transport.wire_errors import TransportFailureError

CURSOR = TurnCursor(build.SUB_GAME, 1)


def side_and_spy() -> tuple[object, SpyTransport]:
    """One production side wired to a recording transport."""
    peer = build.side(GROUP_A, ActorRole.POLICE)
    return peer, SpyTransport()


def opener_and_spy() -> tuple[object, SpyTransport]:
    """The side the initial-proposer rule actually lets open the exchange."""
    peer = build.side(GROUP_B, ActorRole.THIEF)
    return peer, SpyTransport()


def sealed() -> object:
    from evidence_builders import CONFIG, POS

    from mars777_police.app.sealed_record_values import SealedState

    return SealedState(CONFIG, POS[1], (), 1, ActorRole.POLICE)


def test_step0_sends_the_runtime_built_exchange() -> None:
    peer, spy = side_and_spy()
    asyncio.run(peer.runner(spy).send_step0(peer.own))
    assert spy.names() == ["step0"]
    assert spy.sent[0][1] == peer.pregame.step0.outbound(peer.own)


def test_config_proposal_sends_the_pregame_owners_proposal_and_advances_it() -> None:
    peer, spy = opener_and_spy()
    asyncio.run(peer.runner(spy).send_config_proposal(config()))
    assert spy.names() == ["config_proposal"]
    assert spy.sent[0][1].sub_game == build.SUB_GAME
    assert not peer.pregame.opening and GROUP_B in peer.pregame.seen


def test_config_lock_sends_evidence_over_the_adopted_config() -> None:
    peer, spy = side_and_spy()
    peer.pregame.adopt_config(config())
    asyncio.run(peer.runner(spy).send_config_lock())
    assert spy.names() == ["config_lock"]
    assert spy.sent[0][1].context.sub_game == build.SUB_GAME


def test_opening_a_turn_registers_then_sends_the_same_commitment() -> None:
    peer, spy = side_and_spy()
    prepared = asyncio.run(
        peer.runner(spy).open_turn(
            state=sealed(),
            action=turn_builders.legal_reveal().action,
            intent=Intent.TRUTH,
            hint="north",
            cursor=CURSOR,
        )
    )
    assert spy.names() == ["commitment"]
    assert spy.sent[0][1] is prepared.commitment
    assert type(prepared.commitment) is Commitment
    assert peer.turn.local_commitment is not None
    assert peer.turn.local_commitment.h_commit == prepared.commitment.h_commit


def test_the_prepared_turn_is_returned_not_kept() -> None:
    """The caller holds it between the callback phases; the runner does not."""
    import dataclasses

    peer, spy = side_and_spy()
    runner = peer.runner(spy)
    asyncio.run(
        runner.open_turn(
            state=sealed(),
            action=turn_builders.legal_reveal().action,
            intent=Intent.TRUTH,
            hint="north",
            cursor=CURSOR,
        )
    )
    held = [getattr(runner, f.name) for f in dataclasses.fields(runner)]
    assert all(not isinstance(value, Commitment | Reveal) for value in held)


def test_acknowledging_sends_the_runtime_produced_value() -> None:
    peer, spy = side_and_spy()
    peer.turn.accept_commitment(turn_builders.commitment())
    asyncio.run(peer.runner(spy).acknowledge_peer_turn())
    assert spy.names() == ["acknowledgement"]
    assert type(spy.sent[0][1]) is Acknowledgement
    assert spy.sent[0][1].h_commit == turn_builders.PEER_DIGEST


def test_the_audit_pair_sends_exactly_what_the_evidence_owner_produced() -> None:
    peer, spy = side_and_spy()
    asyncio.run(
        peer.runner(spy).open_turn(
            state=sealed(),
            action=turn_builders.legal_reveal().action,
            intent=Intent.TRUTH,
            hint="north",
            cursor=CURSOR,
        )
    )
    asyncio.run(peer.runner(spy).send_final_nonce_reveal())
    asyncio.run(peer.runner(spy).send_audit_disclosure())
    assert spy.names() == ["commitment", "final_nonce_reveal", "audit_disclosure"]
    assert spy.sent[1][1].entries[0].cursor == CURSOR
    assert spy.sent[2][1]["sub_game"] == build.SUB_GAME


def test_a_transport_failure_propagates_unchanged() -> None:
    """No broad catch, no conversion to `False`."""
    peer, spy = side_and_spy()
    spy.failure = TransportFailureError(TransportFailureError.error_id)
    with pytest.raises(TransportFailureError):
        asyncio.run(peer.runner(spy).send_step0(peer.own))


def test_a_second_local_proposal_in_one_round_is_refused() -> None:
    peer, spy = opener_and_spy()
    asyncio.run(peer.runner(spy).send_config_proposal(config()))
    with pytest.raises(StaleMessageError, match="already proposed"):
        asyncio.run(peer.runner(spy).send_config_proposal(config()))
    assert spy.names() == ["config_proposal"]
