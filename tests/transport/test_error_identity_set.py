"""The transport mapping must cover the whole current protocol error set.

Derived from `app.protocol_errors` rather than restated, so a future identity
added or removed there fails this guard instead of silently losing its wire
representation.
"""

import asyncio
import inspect

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError
from peer_ops import RecordingOperations, proposal

from mars777_police.app import protocol_errors
from mars777_police.app.protocol_errors import ConventionMismatchError, PeerProtocolError
from mars777_police.transport.client import wire_json
from mars777_police.transport.codec_pregame import encode_proposal
from mars777_police.transport.server import build_server
from mars777_police.transport.wire_errors import _BY_IDENTITY, TRANSPORT_FAILURE


def current_identities() -> set[str]:
    """Every identity the application layer can actually raise."""
    return {
        value.error_id
        for value in vars(protocol_errors).values()
        if inspect.isclass(value)
        and issubclass(value, PeerProtocolError)
        and value is not PeerProtocolError
    }


def test_the_current_protocol_error_set_is_the_expected_seven() -> None:
    assert current_identities() == {
        "E-PROTO-MALFORMED",
        "E-PROTO-STALE",
        "E-AUTH-FAILURE",
        "E-CONFIG-MISMATCH",
        "E-NET-CONVENTION-MISMATCH",
        "E-REPORT-DISAGREE",
        "E-LOCAL-DEFECT",
    }


def test_the_transport_mapping_covers_every_current_identity() -> None:
    """The guard: adding an identity without a wire mapping fails here."""
    assert set(_BY_IDENTITY) == current_identities()


def test_the_transport_failure_identity_is_separate_and_not_mapped() -> None:
    assert TRANSPORT_FAILURE == "E-TRANSPORT"
    assert TRANSPORT_FAILURE not in _BY_IDENTITY
    assert TRANSPORT_FAILURE not in current_identities()


def test_no_identity_was_invented_by_the_transport() -> None:
    assert set(_BY_IDENTITY) <= current_identities()


@pytest.mark.parametrize("identity", sorted(_BY_IDENTITY))
def test_every_identity_round_trips_through_the_real_tool_boundary(identity: str) -> None:
    operations = RecordingOperations()
    operations.failure = _BY_IDENTITY[identity](identity)

    async def run() -> str:
        async with Client(build_server(operations)) as client:
            with pytest.raises(ToolError) as raised:
                await client.call_tool(
                    "negotiate",
                    {
                        "request": {
                            "kind": "config_proposal",
                            "payload": wire_json(encode_proposal(proposal())),
                        }
                    },
                )
            return str(raised.value)

    crossed = asyncio.run(run())
    assert crossed == identity


def test_the_convention_mismatch_identity_reconstructs_exactly() -> None:
    """The identity R17 mapped but never exercised across the boundary."""
    from mars777_police.transport.wire_errors import inbound

    rebuilt = inbound(ConventionMismatchError.error_id)
    assert type(rebuilt) is ConventionMismatchError
    assert rebuilt.error_id == "E-NET-CONVENTION-MISMATCH"
