"""The result owner appears only when the series has one, then both paths see it."""

import asyncio
from collections.abc import Iterator

import composed_builders as build
import pytest
import series_builders
from live_server import LiveServer
from peer_ops import agreement
from r16_builders import GROUP_A, GROUP_B
from test_composed_end_to_end import held_runner

from mars777_police.app.protocol_errors import StaleMessageError
from mars777_police.app.series_audit_gate import SeriesAuditGate
from mars777_police.transport.client import PeerClient
from mars777_police.transport.codec_final import encode_result_agreement
from mars777_police.transport.peer_transport import FastMcpPeerTransport

TIMEOUT = 20.0


@pytest.fixture
def pair() -> Iterator[tuple[object, object]]:
    a, b = build.both("http://127.0.0.1:1/mcp", "http://127.0.0.1:2/mcp")
    with (
        LiveServer(a.inbound_operations, "late-a") as server_a,
        LiveServer(b.inbound_operations, "late-b") as server_b,
    ):
        yield (a, server_a.url), (b, server_b.url)


def verified_gate() -> SeriesAuditGate:
    """Six real completed audits, all verified."""
    gate = SeriesAuditGate()
    for audit in series_builders.series():
        gate.record(audit)
    return gate


def test_an_inbound_result_before_binding_is_a_typed_refusal(pair: tuple) -> None:
    """Not a 500 and not an AttributeError: the existing stale identity."""
    (a, _), (b, url_b) = pair

    async def run() -> None:
        runner, client = await held_runner(a, url_b)
        await runner.send_step0(a.identity.declaration)
        with pytest.raises(StaleMessageError) as raised:
            await client.call(
                "receive_control", "result_agreement", encode_result_agreement(agreement())
            )
        assert raised.value.error_id == "E-PROTO-STALE"

    asyncio.run(run())
    assert b.runtime_context.result is None


def test_the_late_result_becomes_visible_to_both_paths(pair: tuple) -> None:
    (a, _), (_, _) = pair
    build.after_step0(a)
    assert a.runtime_context.result is None
    exchange = a.complete_result(**build.final_result_inputs())
    assert a.peer_runner.results() is exchange
    assert a.inbound_operations.results() is exchange
    assert exchange.transport is a.peer_transport


def test_the_composed_graph_drives_a_real_result_agreement(pair: tuple) -> None:
    """Both sides gated on six real audits, both digests derived by production.

    The Step-0 that authenticates each session is the same one that merges each
    declaration, so the result owners can only be built after it - which is the
    late-binding order this stage exists to make honest.
    """
    (a, url_a), (b, url_b) = pair
    a.peer_runner.series.outcomes.update(verified_gate().outcomes)
    b.peer_runner.series.outcomes.update(verified_gate().outcomes)

    async def run() -> tuple[object, object]:
        import dataclasses

        async with (
            PeerClient(url_b, timeout=TIMEOUT) as a_held,
            PeerClient(url_a, timeout=TIMEOUT) as b_held,
        ):
            a_to_b, b_to_a = FastMcpPeerTransport(a_held), FastMcpPeerTransport(b_held)
            runner_a = dataclasses.replace(a.peer_runner, transport=a_to_b)
            runner_b = dataclasses.replace(b.peer_runner, transport=b_to_a)
            await runner_a.send_step0(a.identity.declaration)
            await runner_b.send_step0(b.identity.declaration)
            exchange_a = a.complete_result(**build.final_result_inputs())
            exchange_b = b.complete_result(**build.final_result_inputs_for(GROUP_B))
            exchange_a.transport, exchange_b.transport = a_to_b, b_to_a
            await runner_b.open_result_agreement()
            await runner_a.respond_to_result(exchange_a.timestamp)
            return exchange_a, exchange_b

    exchange_a, exchange_b = asyncio.run(run())
    assert exchange_a.is_agreed and exchange_b.is_agreed
    assert exchange_a.local_digest == exchange_a.peer_digest
    assert exchange_a.local_digest == exchange_b.local_digest
    assert GROUP_A != GROUP_B
