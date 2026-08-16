"""Disagreement across two processes, detected by production - not by the test.

The test supplies a structurally valid but divergent contribution and then does
nothing further: `ResultExchange` assembles, hashes, sends, receives and
compares, and raises `E-REPORT-DISAGREE` itself. Neither side records a verified
direction, and neither mutual state completes.
"""

import asyncio
import json
from pathlib import Path

import pytest
from cadence_ops import contribution_for, exchange_for
from peer_process import CadencePeer
from r16_builders import GROUP_A, GROUP_B

from mars777_police.app.artifact_values import UtcTimestamp
from mars777_police.app.peer_supervision import PeerDeadline, TimeoutPolicy
from mars777_police.app.protocol_errors import ReportDisagreeError
from mars777_police.transport.client import PeerClient
from mars777_police.transport.peer_transport import FastMcpPeerTransport

TIMEOUT = 20.0


def transport_to(url: str) -> FastMcpPeerTransport:
    return FastMcpPeerTransport(PeerClient(url, PeerDeadline(TimeoutPolicy(TIMEOUT))))


@pytest.fixture
def opponent(tmp_path: Path) -> object:
    with CadencePeer(GROUP_B, tmp_path / "p.json", base=100) as peer:
        yield peer


def diverging_peer(url: str) -> object:
    """Our half, which will send a contribution it did not hash against.

    Structurally valid on both sides - six ascending entries, one commit, the
    same timestamp - and yet the two approval cores differ, which is exactly the
    condition the digest comparison exists to catch.
    """
    us = exchange_for(GROUP_A, 200)
    us.transport = transport_to(url)
    remote = exchange_for(GROUP_B, 100)
    us.accept_peer_request(remote.runtime.open_agreement(remote.own), GROUP_B)
    us.own = contribution_for(GROUP_A, 777)
    return us


def test_a_true_digest_disagreement_is_raised_by_production(opponent: object) -> None:
    us = diverging_peer(opponent.url)
    with pytest.raises(ReportDisagreeError) as raised:
        asyncio.run(us.send_response(us.timestamp))
    assert raised.value.error_id == "E-REPORT-DISAGREE"
    assert str(raised.value) == "E-REPORT-DISAGREE"


def test_neither_side_records_completion_after_a_disagreement(opponent: object) -> None:
    us = diverging_peer(opponent.url)
    with pytest.raises(ReportDisagreeError):
        asyncio.run(us.send_response(us.timestamp))
    assert us.verified is False
    assert us.is_agreed is False
    remote = json.loads(Path(opponent.status).read_text(encoding="utf-8"))
    assert remote["is_agreed"] is False
    assert remote["verified"] is False


def test_a_wrong_echoed_timestamp_is_a_separate_report_disagreement(
    opponent: object,
) -> None:
    """Two distinct conditions, one shared identity - neither collapses."""
    us = exchange_for(GROUP_A, 200)
    us.transport = transport_to(opponent.url)
    with pytest.raises(ReportDisagreeError):
        asyncio.run(us.send_response(UtcTimestamp("2026-08-07T02:00:00Z")))


def test_no_failure_is_reported_as_a_boolean(opponent: object) -> None:
    us = diverging_peer(opponent.url)
    with pytest.raises(ReportDisagreeError):
        asyncio.run(us.send_response(us.timestamp))
    assert us.verified is not True
