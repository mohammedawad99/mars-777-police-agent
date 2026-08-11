"""What an unauthenticated, forged or borrowed session cannot do.

Each test drives the real production server. The refusals below are the
application's, reached through the real adapter - not a fixture's opinion.
"""

import asyncio
from collections.abc import Iterator

import peer_ops
import pytest
import session_calls
import turn_builders
from session_process import SessionPeer

from mars777_police.app.protocol_errors import AuthFailureError, ReportDisagreeError
from mars777_police.transport.client import PeerClient
from mars777_police.transport.codec_declaration import encode_step0
from mars777_police.transport.codec_turn import encode_commitment

TIMEOUT = 20.0
POST_STEP0 = [call for call in session_calls.payloads() if call[1] != "step0"]


@pytest.fixture(scope="module")
def peer() -> Iterator[SessionPeer]:
    """One production peer for the tests that never complete a Step-0."""
    with SessionPeer() as running:
        yield running


@pytest.fixture
def fresh() -> Iterator[SessionPeer]:
    """A peer whose pregame runtime has not yet accepted anyone.

    `PregameSessionRuntime` refuses a second Step-0, which is correct - so a
    test that authenticates for real needs its own process.
    """
    with SessionPeer() as running:
        yield running


async def one_call(url: str, tool: str, kind: str, payload: object) -> object:
    """A single call on its own fresh, unauthenticated session."""
    async with PeerClient(url, timeout=TIMEOUT) as client:
        return await client.call(tool, kind, payload)


@pytest.mark.parametrize(("tool", "kind", "payload"), POST_STEP0)
def test_an_unauthenticated_session_cannot_invoke_any_operation(
    peer: SessionPeer, tool: str, kind: str, payload: object
) -> None:
    with pytest.raises(AuthFailureError) as raised:
        asyncio.run(one_call(peer.url, tool, kind, payload))
    assert raised.value.error_id == "E-AUTH-FAILURE"


def test_the_unauthenticated_matrix_covers_eight_kinds(peer: SessionPeer) -> None:
    assert len(POST_STEP0) == 8


def test_a_failed_step0_leaves_the_session_unauthenticated(peer: SessionPeer) -> None:
    """No partial binding: a proof that does not verify authenticates nothing."""

    async def run() -> None:
        async with PeerClient(peer.url, timeout=TIMEOUT) as client:
            with pytest.raises(AuthFailureError):
                await client.call("negotiate", "step0", encode_step0(session_calls.forged_step0()))
            with pytest.raises(AuthFailureError) as raised:
                await client.call(
                    "receive_turn", "commitment", encode_commitment(turn_builders.commitment())
                )
            assert "Step-0" in str(raised.value) or raised.value.error_id == "E-AUTH-FAILURE"

    asyncio.run(run())


def test_a_second_session_cannot_borrow_the_first_sessions_authentication(
    fresh: SessionPeer,
) -> None:
    """Binding is per session; there is no process-wide current sender."""

    async def run() -> None:
        async with PeerClient(fresh.url, timeout=TIMEOUT) as first:
            await first.call("negotiate", "step0", encode_step0(peer_ops.step0_exchange()))
            async with PeerClient(fresh.url, timeout=TIMEOUT) as second:
                with pytest.raises(AuthFailureError):
                    await second.call(
                        "receive_turn",
                        "commitment",
                        encode_commitment(turn_builders.commitment()),
                    )

    asyncio.run(run())


def test_the_binding_persists_across_many_calls_on_one_session(fresh: SessionPeer) -> None:
    """Step-0 once, then several calls - none of them is rejected as unauthenticated.

    Later calls may still meet a turn-phase refusal, which is the point: the
    identity survived, and what answered was the application rather than the gate.
    """

    async def run() -> list[str]:
        outcomes: list[str] = []
        async with PeerClient(fresh.url, timeout=TIMEOUT) as client:
            await client.call("negotiate", "step0", encode_step0(peer_ops.step0_exchange()))
            for _ in range(3):
                try:
                    await client.call(
                        "receive_turn", "commitment", encode_commitment(turn_builders.commitment())
                    )
                    outcomes.append("accepted")
                except AuthFailureError:  # pragma: no cover - the defect this forbids
                    outcomes.append("E-AUTH-FAILURE")
                except Exception as failure:
                    outcomes.append(getattr(failure, "error_id", "unknown"))
        return outcomes

    outcomes = asyncio.run(run())
    assert outcomes[0] == "accepted"
    assert "E-AUTH-FAILURE" not in outcomes


def test_a_result_request_naming_another_group_is_refused_over_the_wire(
    fresh: SessionPeer,
) -> None:
    """The session says one thing and the payload another; production refuses."""
    from mars777_police.transport.codec_final import encode_result_agreement

    async def run() -> None:
        async with PeerClient(fresh.url, timeout=TIMEOUT) as client:
            await client.call("negotiate", "step0", encode_step0(peer_ops.step0_exchange()))
            await client.call(
                "receive_control",
                "result_agreement",
                encode_result_agreement(session_calls.spoofed_agreement()),
            )

    with pytest.raises(ReportDisagreeError) as raised:
        asyncio.run(run())
    assert raised.value.error_id == "E-REPORT-DISAGREE"
