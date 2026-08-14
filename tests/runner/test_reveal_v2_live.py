"""Two real agents, one real reveal, and the opponent's scent actually arriving.

Nothing is hand-built here: the emission is projected by production from the same
action the turn seals, it crosses the real FastMCP route inside the reveal that
already existed, and the receiver keeps exactly what arrived. The response is the
`TurnOutcome` V1 always answered - scent changes no capture truth.

The profile half of the checkpoint is checked at the seam it belongs to: two
peers that do not both speak `..._SCENT_V2` are refused **before**
`CONFIG_LOCKED`, by the existing gate and the existing error identity.
"""

import asyncio
import dataclasses
from collections.abc import Iterator

import pytest
import runner_builders as build
import turn_builders
from r16_builders import GROUP_A, GROUP_B, PROFILES, config

from mars777_police.app.capture_values import CaptureAnswer
from mars777_police.app.interop_profiles import CompatibilityProfile
from mars777_police.app.protocol_errors import ConfigMismatchError
from mars777_police.app.sealed_record_values import ActorRole, Intent, SealedState
from mars777_police.app.turn_contract_gate import require_counted_turn_contract
from mars777_police.app.turn_cursor import TurnCursor
from mars777_police.domain.rules import Move, apply_move
from mars777_police.domain.scent_model_default import default_scent_model
from mars777_police.domain.scent_observation import emission_of
from mars777_police.transport.client import PeerClient
from mars777_police.transport.peer_transport import FastMcpPeerTransport

TIMEOUT = 20.0
CURSOR = TurnCursor(build.SUB_GAME, 1)
V1 = CompatibilityProfile.STRICT_COUNTED_MATCH_TURN_OUTCOME_V1


@pytest.fixture
def pair() -> Iterator[tuple[object, object]]:
    """Side A and side B, each behind its own real inbound server."""
    a = build.side(GROUP_A, "group_a", ActorRole.POLICE)
    b = build.side(GROUP_B, "group_b", ActorRole.THIEF)
    with build.server_for(a) as server_a, build.server_for(b) as server_b:
        a.url, b.url = server_a.url, server_b.url
        yield a, b


def sealed(role: ActorRole) -> SealedState:
    from evidence_builders import CONFIG, POS

    return SealedState(CONFIG, POS[1], (), 1, role)


async def step0_on(peer: object, url: str) -> FastMcpPeerTransport:
    client = await PeerClient(url, timeout=TIMEOUT).__aenter__()
    transport = FastMcpPeerTransport(client)
    await peer.runner(transport).send_step0(peer.own)
    return transport


async def one_turn(a: object, b: object) -> tuple[object, object]:
    """One whole production turn over two real servers: commit, ack, reveal."""
    a_to_b = await step0_on(a, b.url)
    b_to_a = await step0_on(b, a.url)
    prepared = await a.runner(a_to_b).open_turn(
        state=sealed(ActorRole.POLICE),
        action=turn_builders.legal_reveal().action,
        intent=Intent.TRUTH,
        hint="heading north",
        cursor=CURSOR,
    )
    await b.runner(b_to_a).acknowledge_peer_turn()
    return await a.runner(a_to_b).reveal_turn(prepared), prepared


def test_a_full_v2_turn_delivers_the_opponent_scent_over_the_real_route(
    pair: tuple,
) -> None:
    """Commit, ack, reveal - and the peer's emission is what the receiver keeps."""
    a, b = pair
    outcome, prepared = asyncio.run(one_turn(a, b))
    assert outcome.accepted is True and outcome.capture is CaptureAnswer.NO_QUESTION

    truth = a.turn.truth
    expected = emission_of(
        truth.board,
        default_scent_model().kernel,
        apply_move(truth.board, truth.own_position, Move.N),
        default_scent_model().params,
    )
    assert prepared.reveal.scent_emission == expected, "production projected it"
    (witnessed,) = b.turn.evidence
    assert witnessed.scent == expected, "and the peer kept exactly that"
    assert witnessed.action == prepared.reveal.action, "one action, one emission"


def test_the_sender_truth_is_unchanged_by_sending_the_turn(pair: tuple) -> None:
    """No owner has adopted the turn yet, so nothing may pretend it did."""
    a, b = pair
    before = a.turn.truth
    asyncio.run(one_turn(a, b))
    assert a.turn.truth == before and a.turn.truth.completed_steps == 0


def test_the_receiver_keeps_the_peer_emission_and_none_of_its_own(pair: tuple) -> None:
    a, b = pair
    asyncio.run(one_turn(a, b))
    assert len(b.turn.evidence) == 1, "one opponent emission for this half-turn"
    assert a.turn.evidence == (), "our own reveal leaves no opponent observation"


def test_the_current_counted_gate_requires_v2_before_the_lock() -> None:
    require_counted_turn_contract(PROFILES)
    assert PROFILES.compatibility_profile.value.endswith("SCENT_V2")


@pytest.mark.parametrize(
    "posture",
    [
        V1,
        CompatibilityProfile.STRICT_COUNTED_MATCH,
        CompatibilityProfile.LECTURER_REFERENCE_COMPATIBILITY,
    ],
)
def test_a_peer_that_does_not_speak_v2_is_refused_before_config_locked(
    posture: CompatibilityProfile,
) -> None:
    """Including V1: still parseable, no longer enough for counted play."""
    profiles = dataclasses.replace(PROFILES, compatibility_profile=posture)
    with pytest.raises(ConfigMismatchError, match="counted play needs"):
        require_counted_turn_contract(profiles)
    assert config().agreed_between, "the config itself is untouched by the posture"
