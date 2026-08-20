"""Who we are paired with, what we may answer, and how far we may seal.

The pairing a greeting establishes is the identity every later artifact is bound
to; a claim about a turn we never held is not a question we may answer; and the
signed maximum is a ceiling, not a suggestion.
"""

import asyncio

from fastmcp import Client
from kit_backend_builders import drop
from r16_builders import config
from test_kit_gateway import greeting

from mars777_police.__main__ import ROLE
from mars777_police.app.capture_values import CaptureAnswer, CaptureClaim
from mars777_police.app.commitment_codecs import CommitmentCodec
from mars777_police.app.config_rules import limits_of
from mars777_police.app.kit_friendly import KitFriendlySession
from mars777_police.app.kit_messages import KitRole
from mars777_police.app.kit_payload import PeerPayload
from mars777_police.app.kit_play import KitPlayState
from mars777_police.app.kit_records import KitRecordChain
from mars777_police.app.kit_session import KitSessionContext
from mars777_police.app.run_class import RunClassification
from mars777_police.domain.terminal import Outcome
from mars777_police.protocol.secure_nonce import SecretsNonceSource

OURS = KitRole(ROLE.value)


def test_a_friendly_greeting_records_the_pairing_it_established() -> None:
    from peer_recorder import RecordingOperations
    from test_kit_gateway import TERMS

    from mars777_police.transport.server import build_server
    from mars777_police.transport.transport_profiles import TransportEnvelopeProfile

    friendly = KitFriendlySession(RunClassification.friendly(kit_terms_agreement=True))
    other = KitRole.THIEF if OURS is KitRole.POLICE else KitRole.POLICE
    context = KitSessionContext("MaRs-777", OURS, PeerPayload(TERMS), 1, friendly=friendly)
    server = build_server(
        RecordingOperations(), profile=TransportEnvelopeProfile.KIT_EXTERNAL, context=context
    )

    async def run() -> None:
        async with Client(server) as client:
            body = greeting(role=other.value, sub_game_number=1)
            body.pop("game_uid", None)
            await client.call_tool("negotiate", {"message": body})

    asyncio.run(run())

    assert friendly.greetings == 1
    assert friendly.pairing is not None
    assert friendly.greeted.is_set()


def test_a_claim_we_cannot_answer_is_no_question_at_all() -> None:
    state = KitPlayState.opening(config(), ROLE)
    from mars777_police.app.kit_adjudicate import answer_claim
    from mars777_police.domain.board import Position

    elsewhere = CaptureClaim(
        Position(state.truth.own_position.row, state.truth.own_position.col + 1)
    )

    assert answer_claim(elsewhere, state.truth.own_position) is CaptureAnswer.NOT_CAUGHT


def test_the_ceiling_stops_us_sealing_past_the_signed_maximum() -> None:
    from test_kit_play_loop import maker

    from mars777_police.app.kit_inbox import KitTurnInbox
    from mars777_police.app.kit_sub_game import KitSubGame

    limits = limits_of(config())
    chain = KitRecordChain(CommitmentCodec.KIT_CORE_COMMITMENT_V1, SecretsNonceSource())
    game = KitSubGame(
        maker=maker(chain),
        inbox=KitTurnInbox(),
        send=drop,
        role=OURS,
        limits=limits,
        deadline=0.05,
        state=KitPlayState(
            KitPlayState.opening(config(), ROLE).truth,
            KitPlayState.opening(config(), ROLE).field,
            limits.max_moves,
        ),
    )

    assert asyncio.run(game._own_turn()).outcome in (None, Outcome.SURVIVAL)
    assert chain.records == ()
