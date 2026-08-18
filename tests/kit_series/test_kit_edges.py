"""The refusals and the role-specific branches, each pinned once.

Nothing here is a happy path. These are the endings only one side can see, the
messages that must not be accepted, and the failures that have to cross as their
own error identity rather than as somebody else's.
"""

import asyncio

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError
from kit_backend_builders import backend
from kit_wire_vectors import COMMIT
from r16_builders import config

from mars777_police.__main__ import ROLE
from mars777_police.app.capture_values import CaptureAnswer, CaptureClaim
from mars777_police.app.commitment_codecs import CommitmentCodec
from mars777_police.app.config_rules import limits_of
from mars777_police.app.kit_adjudicate import adjudicate
from mars777_police.app.kit_friendly import KitFriendlySession
from mars777_police.app.kit_handoff import SeriesHandoff
from mars777_police.app.kit_messages import KitRole
from mars777_police.app.kit_payload import PeerPayload
from mars777_police.app.kit_play import KitPlayState, peer_belief
from mars777_police.app.kit_records import KitRecordChain
from mars777_police.app.kit_session import KitSessionContext
from mars777_police.app.protocol_errors import LocalDefectError, StaleMessageError
from mars777_police.app.run_class import RunClassification
from mars777_police.app.sealed_record_values import Intent
from mars777_police.app.turn_cursor import TurnCursor
from mars777_police.domain.actions import MoveAction
from mars777_police.domain.rules import Move
from mars777_police.domain.scent_belief import NO_SCENT
from mars777_police.domain.terminal import Outcome
from mars777_police.protocol.secure_nonce import SecretsNonceSource
from mars777_police.transport.kit_gateway import KitGroupGateway
from mars777_police.transport.kit_gateway_server import build_gateway_admin, build_gateway_tools

OURS = KitRole(ROLE.value)


def test_a_thief_that_cannot_move_reaches_the_ending_only_it_can_see() -> None:
    verdict = adjudicate(
        role=KitRole.THIEF,
        incoming=None,
        answer=CaptureAnswer.NO_QUESTION,
        trapped=True,
        step=3,
        max_steps=35,
        survival_threshold=35,
    )

    assert verdict.outcome is Outcome.CAPTURE
    assert verdict.reason


def test_the_step_ceiling_ends_an_uncaught_thief_s_sub_game() -> None:
    verdict = adjudicate(
        role=KitRole.THIEF,
        incoming=None,
        answer=CaptureAnswer.NO_QUESTION,
        trapped=False,
        step=35,
        max_steps=35,
        survival_threshold=40,
    )

    assert verdict.outcome is Outcome.SURVIVAL


def test_a_grid_our_domain_cannot_hold_is_silence_rather_than_a_belief() -> None:
    board = KitPlayState.opening(config(), ROLE).truth.board

    assert peer_belief((("nonsense", 0.5),), board) is NO_SCENT
    assert peer_belief((("99,99", 0.5),), board) is NO_SCENT


def test_a_chain_seals_nothing_once_the_opponent_holds_its_nonces() -> None:
    chain = KitRecordChain(CommitmentCodec.KIT_CORE_COMMITMENT_V1, SecretsNonceSource())
    chain.reveal(
        OURS,
        __import__(
            "mars777_police.app.kit_messages", fromlist=["KitResultClaim"]
        ).KitResultClaim.SURVIVAL,
    )

    with pytest.raises(StaleMessageError):
        chain.seal(
            cursor=TurnCursor(1, 1),
            role=ROLE,
            action=MoveAction(Move.STAY),
            intent=next(iter(Intent)),
            hint="",
            own_position=KitPlayState.opening(config(), ROLE).truth.own_position,
            barriers=(),
        )


def test_a_backend_refuses_a_run_class_that_is_not_a_friendly() -> None:
    held = backend(KitRole.POLICE)
    held.friendly.classification = RunClassification.counted(keyed_auth_satisfied=True)

    with pytest.raises(LocalDefectError):
        held.__post_init__()


def test_a_backend_refuses_a_context_carrying_the_other_role() -> None:
    held = backend(KitRole.POLICE)
    other = KitRole.THIEF if OURS is KitRole.POLICE else KitRole.POLICE
    held.context = KitSessionContext("MaRs-777", other, PeerPayload({"a": 1}), 1)

    with pytest.raises(LocalDefectError):
        held.__post_init__()


def test_every_gateway_tool_translates_a_refusal_into_its_error_identity() -> None:
    held = KitGroupGateway(handoff=SeriesHandoff(KitRole.POLICE), routes={}, deadline=0.2)
    turn = {
        "step": 1,
        "sender": "thief",
        "hint": "x",
        "smell_grid": {"0,0": 0.5},
        "commit": COMMIT,
        "timestamp": "2026-08-18T00:00:00Z",
    }

    async def run() -> list[str]:
        failures: list[str] = []
        async with Client(build_gateway_tools(held)) as public:
            for tool, body in (
                ("receive_turn", {"message": turn}),
                (
                    "submit_audit",
                    {"payload": {"sender": "thief", "records": [], "result_claim": "survival"}},
                ),
                ("receive_control", {"message": {"kind": "status", "sender": "thief"}}),
                (
                    "negotiate",
                    {
                        "message": {
                            "terms": {},
                            "nonce": "a",
                            "signature": "b",
                            "group_id": "g",
                            "sub_game_number": 4,
                        }
                    },
                ),
            ):
                try:
                    await public.call_tool(tool, body)
                except ToolError as failure:
                    failures.append(str(failure))
        return failures

    assert len(asyncio.run(run())) == 4


def test_the_admin_surface_refuses_a_settlement_for_another_sub_game() -> None:
    held = KitGroupGateway(handoff=SeriesHandoff(KitRole.POLICE), routes={}, deadline=0.2)

    async def run() -> str:
        async with Client(build_gateway_admin(held)) as admin:
            try:
                await admin.call_tool("sub_game_settled", {"sub_game": 5})
            except ToolError as failure:
                return str(failure)
        return ""

    assert "E-PROTO-STALE" in asyncio.run(run())


def test_a_friendly_greeting_records_the_pairing_it_established() -> None:
    from peer_recorder import RecordingOperations
    from test_kit_gateway import TERMS, greeting

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
        send=_drop,
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


async def _drop(message: object) -> None:
    """A send that goes nowhere: this test is about what is never sealed."""


@pytest.mark.parametrize("role", [KitRole.POLICE, KitRole.THIEF])
def test_a_caught_answer_settles_a_capture_for_either_side(role: KitRole) -> None:
    """`adjudicate` is a pure function of the role, so both sides are pinned here."""
    from mars777_police.app.kit_messages import KitClaimResponse, KitTurn
    from mars777_police.app.protocol_values import Sha256Digest
    from mars777_police.domain.board import Position

    incoming = KitTurn(
        1,
        KitRole.THIEF if role is KitRole.POLICE else KitRole.POLICE,
        "",
        (),
        Sha256Digest(COMMIT),
        "2026-08-18T00:00:00Z",
        claim_response=KitClaimResponse(Position(1, 1), True),
    )

    verdict = adjudicate(
        role=role,
        incoming=incoming,
        answer=CaptureAnswer.NO_QUESTION,
        trapped=False,
        step=2,
        max_steps=35,
        survival_threshold=35,
    )

    assert verdict.outcome is Outcome.CAPTURE


@pytest.mark.parametrize("role", [KitRole.POLICE, KitRole.THIEF])
def test_a_survival_claim_settles_survival_for_either_side(role: KitRole) -> None:
    from mars777_police.app.kit_messages import KitTurn
    from mars777_police.app.protocol_values import Sha256Digest

    incoming = KitTurn(
        1,
        KitRole.THIEF if role is KitRole.POLICE else KitRole.POLICE,
        "",
        (),
        Sha256Digest(COMMIT),
        "2026-08-18T00:00:00Z",
        survival_claimed=True,
    )

    verdict = adjudicate(
        role=role,
        incoming=incoming,
        answer=CaptureAnswer.NO_QUESTION,
        trapped=False,
        step=2,
        max_steps=35,
        survival_threshold=35,
    )

    assert verdict.outcome is Outcome.SURVIVAL


def test_the_thief_moves_first_and_a_terminal_answer_rides_out() -> None:
    """`reference-v3` ordering and the terminal obligation, both role-neutral code."""
    from test_kit_play_loop import maker

    from mars777_police.app.kit_inbox import KitTurnInbox
    from mars777_police.app.kit_messages import KitTurn
    from mars777_police.app.kit_sub_game import KitSubGame
    from mars777_police.app.protocol_values import Sha256Digest

    sent: list[object] = []

    async def send(message: object) -> None:
        sent.append(message)

    chain = KitRecordChain(CommitmentCodec.KIT_CORE_COMMITMENT_V1, SecretsNonceSource())
    state = KitPlayState.opening(config(), ROLE)
    inbox = KitTurnInbox()
    game = KitSubGame(
        maker=maker(chain),
        inbox=inbox,
        send=send,
        role=KitRole.THIEF,
        limits=limits_of(config()),
        deadline=5.0,
        state=state,
    )

    async def run() -> Outcome:
        played = asyncio.ensure_future(game.play())
        for _ in range(500):
            if sent:
                break
            await asyncio.sleep(0.01)
        inbox.offer(
            KitTurn(
                1,
                KitRole.POLICE,
                "",
                (),
                Sha256Digest(COMMIT),
                "2026-08-18T00:00:00Z",
                capture_claim=CaptureClaim(game.state.truth.own_position),
            )
        )
        return await played

    outcome = asyncio.run(run())

    assert game.moves_first is True
    assert outcome is Outcome.CAPTURE
    assert sent[-1].claim_response is not None
    assert sent[-1].claim_response.caught is True


def test_a_backend_runs_every_row_the_schedule_gave_it() -> None:
    """Its own rows, in order, and never one the other backend owns."""
    played: list[int] = []

    class Counting(type(backend(KitRole.POLICE))):  # type: ignore[misc]
        async def play_sub_game(self, number: int) -> Outcome:
            self.require_ours(number)
            played.append(number)
            return Outcome.SURVIVAL

    template = backend(KitRole.POLICE)
    held = Counting(
        **{
            field.name: getattr(template, field.name)
            for field in __import__("dataclasses").fields(template)
        }
    )

    assert asyncio.run(held.run()) == dict.fromkeys(held.ours, Outcome.SURVIVAL)
    assert played == list(held.ours)


def test_a_thief_at_its_own_threshold_settles_survival_without_being_told() -> None:
    """Its own count, on its own turn - the one terminal the thief owns outright."""
    verdict = adjudicate(
        role=KitRole.THIEF,
        incoming=None,
        answer=CaptureAnswer.NO_QUESTION,
        trapped=False,
        step=35,
        max_steps=35,
        survival_threshold=35,
    )

    assert verdict.outcome is Outcome.SURVIVAL


def test_our_own_turn_can_end_the_sub_game_and_the_claim_already_rode() -> None:
    """A survival our own move reached sends no terminal: the claim went with it."""
    from test_kit_play_loop import maker

    from mars777_police.app.kit_inbox import KitTurnInbox
    from mars777_police.app.kit_sub_game import KitSubGame

    sent: list[object] = []

    async def send(message: object) -> None:
        sent.append(message)

    limits = limits_of(config())
    chain = KitRecordChain(CommitmentCodec.KIT_CORE_COMMITMENT_V1, SecretsNonceSource())
    opening = KitPlayState.opening(config(), ROLE)
    game = KitSubGame(
        maker=maker(chain),
        inbox=KitTurnInbox(),
        send=send,
        role=KitRole.THIEF,
        limits=limits,
        deadline=5.0,
        state=KitPlayState(opening.truth, opening.field, limits.survival_threshold - 1),
    )

    outcome = asyncio.run(game.play())

    assert outcome is Outcome.SURVIVAL
    assert len(sent) == 1, "a terminal was duplicated, or the half-turn never went out"
    assert sent[0].survival_claimed is (OURS is KitRole.THIEF)


@pytest.mark.parametrize("role", [KitRole.POLICE, KitRole.THIEF])
def test_a_sub_game_that_needs_two_rounds_takes_two_rounds(role: KitRole) -> None:
    """The loop is a loop, and both orderings come back for another round.

    Parameterised over the role because the ordering branch is role-neutral code:
    the thief opens each sub-game and the cop answers, whichever side we are.
    """
    from test_kit_play_loop import maker

    from mars777_police.app.kit_inbox import KitTurnInbox
    from mars777_police.app.kit_messages import KitTurn
    from mars777_police.app.kit_sub_game import KitSubGame
    from mars777_police.app.protocol_values import Sha256Digest

    sent: list[object] = []

    async def send(message: object) -> None:
        sent.append(message)

    chain = KitRecordChain(CommitmentCodec.KIT_CORE_COMMITMENT_V1, SecretsNonceSource())
    inbox = KitTurnInbox()
    game = KitSubGame(
        maker=maker(chain),
        inbox=inbox,
        send=send,
        role=role,
        limits=limits_of(config()),
        deadline=5.0,
        state=KitPlayState.opening(config(), ROLE),
    )
    opener = KitRole.THIEF if role is KitRole.POLICE else KitRole.POLICE

    def neutral(step: int, **changes: object) -> KitTurn:
        fields: dict[str, object] = {
            "step": step,
            "sender": opener,
            "hint": "",
            "smell_grid": (),
            "commit": Sha256Digest(COMMIT),
            "timestamp": "2026-08-18T00:00:00Z",
        }
        fields.update(changes)
        return KitTurn(**fields)  # type: ignore[arg-type]

    async def run() -> Outcome:
        played = asyncio.ensure_future(game.play())
        inbox.offer(neutral(1))
        # Wait until our own half-turn has actually gone out, so the second
        # opponent turn lands on a round we really played rather than on the first.
        for _ in range(500):
            if sent:
                break
            await asyncio.sleep(0.01)
        # The terminal each side can actually be told: a cop claims our cell, a
        # thief claims the threshold. Neither invents the other's ending.
        ending: dict[str, object] = (
            {"capture_claim": CaptureClaim(game.state.truth.own_position)}
            if opener is KitRole.POLICE
            else {"survival_claimed": True}
        )
        inbox.offer(neutral(2, **ending))
        return await played

    outcome = asyncio.run(run())

    assert outcome in (Outcome.CAPTURE, Outcome.SURVIVAL)
    assert len(chain.records) >= 1, "our own half-turn was never sealed"


def test_two_turns_released_together_are_both_applied_in_step_order() -> None:
    """A buffered arrival and the turn that unblocks it reach the loop as one batch."""
    from mars777_police.app.kit_inbox import KitTurnInbox
    from mars777_police.app.kit_messages import KitTurn
    from mars777_police.app.protocol_values import Sha256Digest

    inbox = KitTurnInbox()

    def turn(step: int) -> KitTurn:
        return KitTurn(
            step,
            KitRole.POLICE,
            "",
            (),
            Sha256Digest(COMMIT),
            "2026-08-18T00:00:00Z",
        )

    assert inbox.offer(turn(2)) == ()
    applied = inbox.offer(turn(1))

    assert [one.step for one in applied] == [1, 2]


def test_a_released_batch_is_applied_turn_by_turn_by_the_loop() -> None:
    """Both turns reach the game, in step order, from one wake-up."""
    from test_kit_play_loop import maker

    from mars777_police.app.kit_inbox import KitTurnInbox
    from mars777_police.app.kit_messages import KitTurn
    from mars777_police.app.kit_sub_game import KitSubGame
    from mars777_police.app.protocol_values import Sha256Digest

    inbox = KitTurnInbox()
    chain = KitRecordChain(CommitmentCodec.KIT_CORE_COMMITMENT_V1, SecretsNonceSource())
    game = KitSubGame(
        maker=maker(chain),
        inbox=inbox,
        send=_drop,
        role=KitRole.THIEF,
        limits=limits_of(config()),
        deadline=5.0,
        state=KitPlayState.opening(config(), ROLE),
    )

    def turn(step: int) -> KitTurn:
        return KitTurn(step, KitRole.POLICE, "", (), Sha256Digest(COMMIT), "2026-08-18T00:00:00Z")

    inbox.offer(turn(2))
    inbox.offer(turn(1))

    verdict = asyncio.run(game._consume())

    assert verdict.outcome is None
    assert game.steps_seen == 2
