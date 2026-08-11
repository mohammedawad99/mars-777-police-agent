"""The production result workflow, driven against a fake `PeerTransportPort`.

No FastMCP here at all - which is the point of the port. The workflow is proved
in isolation: the proposer sends and retains, the non-proposer receives and
compares, and a mismatch raises from production rather than from the test.
"""

import asyncio

import pytest
from cadence_ops import contribution_for, exchange_for
from r16_builders import GROUP_A, GROUP_B, STAMP

from mars777_police.app.peer_final_messages import ResultAgreement
from mars777_police.app.protocol_errors import ReportDisagreeError
from mars777_police.app.protocol_values import Sha256Digest


class FakeTransport:
    """A `PeerTransportPort` that answers with whatever digest we choose."""

    def __init__(self, answer: Sha256Digest | None = None) -> None:
        self.answer = answer
        self.sent: list[ResultAgreement] = []

    async def send_result_agreement(self, agreement: ResultAgreement) -> Sha256Digest:
        self.sent.append(agreement)
        return self.answer if self.answer is not None else Sha256Digest("f" * 64)


def proposer_request() -> ResultAgreement:
    remote = exchange_for(GROUP_B, 100)
    return remote.runtime.open_agreement(remote.own)


def test_the_proposer_sends_and_retains_the_returned_digest() -> None:
    """It cannot compare yet - it holds no opponent contribution."""
    us = exchange_for(GROUP_B, 100)
    transport = FakeTransport(Sha256Digest("a" * 64))
    us.transport = transport
    asyncio.run(us.open_agreement())
    assert us.own_request_sent
    assert us.timestamp == STAMP
    assert us.peer_digest == Sha256Digest("a" * 64)
    assert us.local_digest is None
    assert us.verified is False
    assert len(transport.sent) == 1


def test_the_proposer_verifies_once_its_own_core_becomes_derivable() -> None:
    us = exchange_for(GROUP_B, 100)
    peer = exchange_for(GROUP_A, 200)
    expected = peer.accept_peer_request(proposer_request(), GROUP_B)
    us.transport = FakeTransport(expected)
    asyncio.run(us.open_agreement())
    us.accept_peer_request(peer.runtime.request(STAMP, peer.own), GROUP_A)
    assert us.verified
    assert us.is_agreed


def test_the_non_proposer_verifies_when_its_own_request_returns() -> None:
    us = exchange_for(GROUP_A, 200)
    ours = us.accept_peer_request(proposer_request(), GROUP_B)
    us.transport = FakeTransport(ours)
    asyncio.run(us.send_response(us.timestamp))
    assert us.verified
    assert us.is_agreed


def test_a_returned_digest_that_differs_raises_from_production() -> None:
    us = exchange_for(GROUP_A, 200)
    us.accept_peer_request(proposer_request(), GROUP_B)
    us.transport = FakeTransport(Sha256Digest("b" * 64))
    with pytest.raises(ReportDisagreeError) as raised:
        asyncio.run(us.send_response(us.timestamp))
    assert raised.value.error_id == "E-REPORT-DISAGREE"
    assert us.verified is False
    assert us.is_agreed is False


def test_a_divergent_own_contribution_changes_our_digest() -> None:
    """Structurally valid on both sides, and still a different approval core."""
    us = exchange_for(GROUP_A, 200)
    first = us.accept_peer_request(proposer_request(), GROUP_B)
    them = exchange_for(GROUP_A, 200)
    them.own = contribution_for(GROUP_A, 777)
    second = them.accept_peer_request(proposer_request(), GROUP_B)
    assert first != second


def test_the_workflow_depends_on_the_port_not_the_adapter() -> None:
    import inspect

    from mars777_police.app import result_exchange

    for line in inspect.getsource(result_exchange).splitlines():
        if line.startswith(("import ", "from ")):
            assert "fastmcp" not in line and "pydantic" not in line
            assert ".transport" not in line or "peer_transport" in line
    assert "PeerTransportPort" in inspect.getsource(result_exchange)
