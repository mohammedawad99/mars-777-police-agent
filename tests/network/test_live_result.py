"""The public `ResultAgreement` direction, consumed by the real `ResultExchange`.

The weak version of this test would send an agreement and assert that 64 hex
characters came back. That proves the tunnel carries bytes and nothing else - it
is exactly the shape of defect the first R17 CLOSE caught, where a digest guard
existed but nothing in production reached it.

So the digest that returns over the public route is handed to the **production**
workflow. `ResultExchange._verify` calls `require_matching_digest`, which is the
only comparison anywhere in this file: the test asserts the workflow's own
recorded verdict and never compares two digests itself.

**One direction only, and stated plainly.** Our request crosses the public route
and the remote's production digest crosses back. The remote's *own* request
cannot reach us publicly, because that needs a second public hostname this
account cannot issue - so the peer's request #2 is constructed locally, exactly
as the R17 two-process cadence does. The mutual close over two public routes is
R18-R2's, and is not claimed here.
"""

import asyncio

from cadence_ops import contribution_for, exchange_for
from conftest import LivePeer
from live_support import TIMEOUT, requires_live_ngrok
from r16_builders import GROUP_A, GROUP_B, STAMP

from mars777_police.app.protocol_errors import ReportDisagreeError
from mars777_police.app.result_agreement_runtime import ResultAgreementRuntime
from mars777_police.transport.client import PeerClient
from mars777_police.transport.peer_transport import FastMcpPeerTransport

pytestmark = requires_live_ngrok


def proposer_over(endpoint: object) -> object:
    """Our own production workflow, wired to the **public** transport adapter."""
    exchange = exchange_for(GROUP_B, 100)
    exchange.transport = FastMcpPeerTransport(PeerClient(endpoint.url, timeout=TIMEOUT))
    return exchange


def peer_request(timestamp: object) -> object:
    """The message the remote would send us, built from its own runtime.

    Constructed locally only because we have no public inbound route to
    ourselves; the digest it is compared against is still the remote's, computed
    by the remote's production workflow and returned over the public tunnel.
    """
    runtime = exchange_for(GROUP_A, 200).runtime
    return runtime.request(timestamp, contribution_for(GROUP_A, 200))


def test_the_public_result_direction_is_verified_by_production(
    public_peer: LivePeer,
) -> None:
    """One public direction, then every production consequence of it.

    Kept as a single test because each `open_agreement` is one MCP session over
    a metered free tunnel; splitting it would triple the consumption without
    adding a distinct proof.
    """
    import pytest

    _, endpoint, peer = public_peer
    exchange = proposer_over(endpoint)

    asyncio.run(exchange.open_agreement())

    assert exchange.own_request_sent
    assert exchange.peer_digest is not None
    assert len(exchange.peer_digest.value) == 64
    assert peer.state()["peer_request_handled"] is True
    assert peer.state()["local_digest"] == exchange.peer_digest.value
    assert exchange.timestamp == STAMP

    # The returned digest is consumed by production, which performs the only
    # comparison in this file.
    exchange.accept_peer_request(peer_request(exchange.timestamp), GROUP_A)
    assert exchange.local_digest is not None
    assert exchange.verified is True
    assert exchange.gate.is_agreed

    # A genuinely divergent core makes production refuse, with no further traffic.
    divergent_exchange = proposer_over(endpoint)
    divergent_exchange.timestamp = exchange.timestamp
    divergent_exchange.own_request_sent = True
    divergent_exchange.peer_digest = exchange.peer_digest
    divergent = ResultAgreementRuntime(
        GROUP_A,
        exchange.runtime.game_id,
        exchange.runtime.game_uid,
        exchange.runtime.participants,
        exchange.runtime.clock,
    ).request(exchange.timestamp, contribution_for(GROUP_A, 999))
    with pytest.raises(ReportDisagreeError) as raised:
        divergent_exchange.accept_peer_request(divergent, GROUP_A)
    assert raised.value.error_id == "E-REPORT-DISAGREE"
    assert divergent_exchange.verified is False
    assert not divergent_exchange.gate.is_agreed


def test_no_live_helper_can_answer_the_question_it_is_asking() -> None:
    """Read the modules' **code**, not their prose or their own literals.

    A guard that greps its own source matches the very words it forbids - the
    R16 lesson, which is why this reads NAME tokens instead.
    """
    import sys

    import live_ops
    import live_peer
    from r16_source import tokens_of

    for module in (sys.modules[__name__], live_ops, live_peer):
        tokens = tokens_of(module)
        assert "hashlib" not in tokens
        assert "sha256" not in tokens
        assert "require_matching_digest" not in tokens
