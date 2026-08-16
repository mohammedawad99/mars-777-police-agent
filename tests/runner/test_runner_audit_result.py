"""Outbound audit disclosure and the series-gated result, over real transport."""

import asyncio
from collections.abc import Iterator

import pytest
import runner_builders as build
import series_builders
import turn_builders
from r16_builders import GROUP_A, GROUP_B
from test_runner_two_sided import CURSOR, TIMEOUT, sealed, step0_on

from mars777_police.app.peer_supervision import PeerDeadline, TimeoutPolicy
from mars777_police.app.protocol_errors import StaleMessageError
from mars777_police.app.protocol_values import FinalAuditVerdict
from mars777_police.app.sealed_record_values import ActorRole, Intent
from mars777_police.app.series_audit_gate import SeriesAuditGate
from mars777_police.transport.client import PeerClient
from mars777_police.transport.peer_transport import FastMcpPeerTransport


@pytest.fixture
def pair() -> Iterator[tuple[object, object]]:
    a = build.side(GROUP_A, "group_a", ActorRole.POLICE)
    b = build.side(GROUP_B, "group_b", ActorRole.THIEF)
    with build.server_for(a) as server_a, build.server_for(b) as server_b:
        a.url, b.url = server_a.url, server_b.url
        yield a, b


def verified_gate() -> SeriesAuditGate:
    """A real six-sub-game gate, built from six real completed audits."""
    gate = SeriesAuditGate()
    for audit in series_builders.series():
        gate.record(audit)
    return gate


def tampered_gate() -> SeriesAuditGate:
    gate = SeriesAuditGate()
    for audit in series_builders.series(tampered=2):
        gate.record(audit)
    return gate


def test_our_disclosure_reaches_the_peers_real_audit_runtime(pair: tuple) -> None:
    """A seals a turn, B observes it live, then A discloses; B verifies."""
    a, b = pair

    async def run() -> None:
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
        await a.runner(a_to_b).reveal_turn(prepared)
        b.audit = build.audit_over(b.turn, a.group_id, ActorRole.POLICE)
        await a.runner(a_to_b).send_final_nonce_reveal()
        await a.runner(a_to_b).send_audit_disclosure()

    asyncio.run(run())
    assert b.audit.verdict is FinalAuditVerdict.VERIFIED_OK


def test_an_incomplete_series_blocks_the_result_agreement(pair: tuple) -> None:
    a, b = pair

    async def run() -> None:
        a_to_b = await step0_on(a, b.url)
        assert a.gate.verdict is None
        with pytest.raises(StaleMessageError, match="FINAL_AUDIT"):
            await a.runner(a_to_b).open_result_agreement()

    asyncio.run(run())


def test_a_tampered_series_blocks_the_result_agreement(pair: tuple) -> None:
    a, b = pair
    a.gate = tampered_gate()

    async def run() -> None:
        a_to_b = await step0_on(a, b.url)
        assert a.gate.verdict is FinalAuditVerdict.TAMPERED
        with pytest.raises(StaleMessageError, match="FINAL_AUDIT"):
            await a.runner(a_to_b).open_result_agreement()

    asyncio.run(run())


def test_a_verified_series_drives_the_real_result_cadence_to_equal_digests(
    pair: tuple,
) -> None:
    """Both directions, both gated, both digests derived by `ResultExchange`."""
    a, b = pair
    a.gate, b.gate = verified_gate(), verified_gate()

    async def run() -> None:
        async with (
            PeerClient(a.url, PeerDeadline(TimeoutPolicy(TIMEOUT))) as b_held,
            PeerClient(b.url, PeerDeadline(TimeoutPolicy(TIMEOUT))) as a_held,
        ):
            b_to_a, a_to_b = FastMcpPeerTransport(b_held), FastMcpPeerTransport(a_held)
            b.results.transport, a.results.transport = b_to_a, a_to_b
            await b.runner(b_to_a).send_step0(b.own)
            await a.runner(a_to_b).send_step0(a.own)
            await b.runner(b_to_a).open_result_agreement()
            await a.runner(a_to_b).respond_to_result(a.results.timestamp)

    asyncio.run(run())
    assert b.results.is_agreed and a.results.is_agreed
    assert b.results.local_digest == b.results.peer_digest
    assert a.results.local_digest == a.results.peer_digest
    assert a.results.local_digest == b.results.local_digest
