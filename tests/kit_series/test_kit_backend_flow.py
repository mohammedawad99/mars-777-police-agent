"""One backend playing one routed sub-game, and the surfaces that carry it.

Everything below the opponent is production: the gateway's two FastMCP
surfaces, the KIT registration, the friendly router branch, the backend, the
record chain and the sub-game loop. What a test supplies is the opponent's half
of the wire and the gateway's forwarding, because those are the two things a
single process cannot honestly be.
"""

import asyncio

from fastmcp import Client
from kit_wire_vectors import COMMIT
from peer_recorder import RecordingOperations
from r16_builders import config

from mars777_police.__main__ import ROLE
from mars777_police.app.capture_values import CaptureClaim
from mars777_police.app.commitment_codecs import CommitmentCodec
from mars777_police.app.kit_friendly import KitFriendlySession
from mars777_police.app.kit_handoff import SeriesHandoff
from mars777_police.app.kit_messages import (
    KitAuditReveal,
    KitRecord,
    KitResultClaim,
    KitRole,
    KitTurn,
)
from mars777_police.app.kit_payload import PeerPayload
from mars777_police.app.kit_peer_audit import peer_chain_verified
from mars777_police.app.kit_session import KitSessionContext
from mars777_police.app.protocol_values import Sha256Digest
from mars777_police.app.run_class import RunClassification
from mars777_police.domain.scent_model_default import default_scent_model
from mars777_police.domain.terminal import Outcome
from mars777_police.infra.clock import SystemClock
from mars777_police.kit_backend import KitRoleBackend
from mars777_police.protocol.kit_commitment import kit_commitment
from mars777_police.protocol.secure_nonce import SecretsNonceSource
from mars777_police.transport.kit_gateway import KitGroupGateway
from mars777_police.transport.kit_gateway_server import (
    ADMIN_TOOLS,
    GATEWAY_TOOLS,
    build_gateway_admin,
    build_gateway_tools,
)

OURS = KitRole(ROLE.value)
THEIRS = KitRole.THIEF if OURS is KitRole.POLICE else KitRole.POLICE
TERMS: dict[str, object] = {"board_size": 7, "max_steps": 35}


def gateway_pair() -> tuple[KitGroupGateway, dict[str, list[str]]]:
    seen: dict[str, list[str]] = {"police": [], "thief": []}

    def route(side: str):
        async def forward(tool: str, arguments: dict[str, object]) -> None:
            seen[side].append(tool)

        return forward

    held = KitGroupGateway(
        handoff=SeriesHandoff(KitRole.POLICE),
        routes={KitRole.POLICE: route("police"), KitRole.THIEF: route("thief")},
        deadline=1.0,
    )
    return held, seen


def test_the_gateway_publishes_the_pinned_surface_and_a_private_one() -> None:
    held, _ = gateway_pair()

    async def run() -> tuple[list[str], list[str]]:
        async with Client(build_gateway_tools(held)) as public:
            names = [tool.name for tool in await public.list_tools()]
        async with Client(build_gateway_admin(held)) as admin:
            private = [tool.name for tool in await admin.list_tools()]
        return names, private

    names, private = asyncio.run(run())

    assert sorted(names) == sorted(GATEWAY_TOOLS)
    assert private == list(ADMIN_TOOLS)


def test_every_gateway_tool_routes_and_acknowledges_over_a_real_client() -> None:
    held, seen = gateway_pair()
    from test_kit_gateway import greeting

    async def run() -> list[object]:
        async with (
            Client(build_gateway_tools(held)) as public,
            Client(build_gateway_admin(held)) as admin,
        ):
            answers = [
                (
                    await public.call_tool(
                        "negotiate", {"message": greeting(role="thief", sub_game_number=1)}
                    )
                ).data,
                (await public.call_tool("receive_turn", {"message": _wire_turn()})).data,
                (
                    await public.call_tool(
                        "receive_control", {"message": {"kind": "status", "sender": "thief"}}
                    )
                ).data,
                (
                    await public.call_tool(
                        "submit_audit",
                        {"payload": {"sender": "thief", "records": [], "result_claim": "survival"}},
                    )
                ).data,
                (await admin.call_tool("sub_game_settled", {"sub_game": 1})).data,
            ]
            return answers

    answers = asyncio.run(run())

    assert answers == [{"ok": True}] * 5
    assert seen["police"] == ["negotiate", "receive_turn", "receive_control", "submit_audit"]


def test_a_refusal_crosses_the_gateway_as_its_own_error_identity() -> None:
    from fastmcp.exceptions import ToolError
    from test_kit_gateway import greeting

    held, _ = gateway_pair()

    async def run() -> None:
        async with Client(build_gateway_tools(held)) as public:
            await public.call_tool(
                "negotiate", {"message": greeting(role="police", sub_game_number=1)}
            )

    try:
        asyncio.run(run())
    except ToolError as failure:
        assert "E-PROTO-STALE" in str(failure)
    else:  # pragma: no cover - the refusal is the point of the test
        raise AssertionError("a role collision was not refused")


def _wire_turn() -> dict[str, object]:
    return {
        "step": 1,
        "sender": THEIRS.value,
        "hint": "over here",
        "smell_grid": {"0,0": 0.5},
        "commit": COMMIT,
        "timestamp": "2026-08-18T00:00:00Z",
    }


def backend_pair() -> tuple[KitRoleBackend, list[object], KitFriendlySession]:
    friendly = KitFriendlySession(RunClassification.friendly(kit_terms_agreement=True))
    context = KitSessionContext("MaRs-777", OURS, PeerPayload(TERMS), 1, friendly=friendly)
    context.peer_group = "sparring-local"
    sent: list[object] = []

    class Transport:
        async def send_kit(self, message: object) -> None:
            sent.append(message)

    async def settled(number: int) -> None:
        sent.append(("settled", number))

    first = KitRole.POLICE if OURS is KitRole.POLICE else KitRole.THIEF
    backend = KitRoleBackend(
        context=context,
        friendly=friendly,
        transport=Transport(),  # type: ignore[arg-type]
        settled=settled,
        config=config(),
        role=ROLE,
        strategy=_First(),
        model=default_scent_model(),
        nonces=SecretsNonceSource(),
        clock=SystemClock(),
        codec=CommitmentCodec.KIT_CORE_COMMITMENT_V1,
        deadline=5.0,
        first_role=first,
    )
    return backend, sent, friendly


class _First:
    def choose_action(self, observation: object) -> object:
        from mars777_police.domain.actions import MoveAction
        from mars777_police.domain.rules import Move

        return MoveAction(Move.STAY)


async def _settle(condition, timeout: float = 5.0) -> None:
    """Wait for the backend to reach the point the opponent is answering."""
    for _ in range(int(timeout / 0.01)):
        if condition():
            return
        await asyncio.sleep(0.01)
    raise AssertionError("the backend never reached the awaited point")


def test_a_backend_plays_the_sub_game_it_is_handed_and_reports_it_settled() -> None:
    backend, sent, friendly = backend_pair()
    pairing = _pairing()
    opening = friendly.inbox

    async def opponent() -> None:
        await _settle(lambda: friendly.inbox is not opening)
        friendly.record_pairing(pairing)
        await _settle(lambda: bool(sent))
        claim = CaptureClaim(backend.config.board_and_agents.thief_start)
        friendly.deliver_turn(
            KitTurn(
                1,
                THEIRS,
                "over here",
                (("0,0", 0.5),),
                Sha256Digest(COMMIT),
                "2026-08-18T00:00:00Z",
                capture_claim=claim if OURS is KitRole.THIEF else None,
                survival_claimed=OURS is KitRole.POLICE,
            )
        )
        await _settle(lambda: any(isinstance(one, KitAuditReveal) for one in sent))
        friendly.deliver_audit(_peer_reveal())

    async def run() -> Outcome:
        played = asyncio.ensure_future(backend.play_sub_game(1))
        await opponent()
        return await played

    outcome = asyncio.run(run())

    assert outcome in (Outcome.CAPTURE, Outcome.SURVIVAL)
    assert ("settled", 1) in sent
    assert backend.verified[1] is True
    assert backend.chains[1].disclosed is True
    assert any(isinstance(one, KitAuditReveal) for one in sent)


def _pairing():
    from mars777_police.app.kit_greeting import KitPairing

    return KitPairing(
        "MaRs-777-vs-sparring-local",
        "1e73c318-5b29-4a7b-1c60-ecb8286265f0",
        "MaRs-777",
        "sparring-local",
        OURS,
        THEIRS,
        1,
        terms_agreed=True,
    )


def _peer_reveal() -> KitAuditReveal:
    payload = {"step": 1, "move": "MOVE:N"}
    nonce = "0" * 32
    return KitAuditReveal(
        THEIRS,
        (KitRecord(PeerPayload(payload), nonce, Sha256Digest(kit_commitment(payload, nonce))),),
        KitResultClaim.SURVIVAL,
    )


def test_our_crypto_gate_refuses_a_chain_whose_bytes_do_not_reproduce() -> None:
    tampered = KitAuditReveal(
        THEIRS,
        (KitRecord(PeerPayload({"step": 1}), "0" * 32, Sha256Digest(COMMIT)),),
        KitResultClaim.SURVIVAL,
    )

    assert peer_chain_verified(_peer_reveal(), 1, CommitmentCodec.KIT_CORE_COMMITMENT_V1) is True
    assert peer_chain_verified(tampered, 1, CommitmentCodec.KIT_CORE_COMMITMENT_V1) is False


def test_the_friendly_router_branch_never_reaches_the_counted_runtime() -> None:
    """A friendly does not merely fail the counted gate - it never reaches it."""
    from mars777_police.transport.server import build_server
    from mars777_police.transport.transport_profiles import TransportEnvelopeProfile

    friendly = KitFriendlySession(RunClassification.friendly(kit_terms_agreement=True))
    context = KitSessionContext("MaRs-777", OURS, PeerPayload(TERMS), 1, friendly=friendly)
    operations = RecordingOperations()
    server = build_server(
        operations, profile=TransportEnvelopeProfile.KIT_EXTERNAL, context=context
    )

    async def run() -> None:
        async with Client(server) as client:
            await client.call_tool("receive_turn", {"message": _wire_turn()})
            await client.call_tool(
                "submit_audit",
                {"payload": {"sender": THEIRS.value, "records": [], "result_claim": "survival"}},
            )

    asyncio.run(run())

    assert operations.seen == []
    assert friendly.audit is not None
    assert friendly.inbox.played == {1: COMMIT}
