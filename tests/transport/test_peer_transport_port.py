"""The frozen outbound port exists in `app`, and the FastMCP adapter satisfies it.

Two directions that must not be confused: `PeerOperations` is what a peer asks
of us, `PeerTransportPort` is what we ask of a peer. This file proves the second
is a real application-facing abstraction rather than a concrete client wearing a
clean signature.
"""

import inspect
from pathlib import Path

import pytest
from peer_ops import agreement, step0_exchange

from mars777_police.app import peer_transport
from mars777_police.app.peer_transport import PeerTransportPort
from mars777_police.transport.client import PeerClient
from mars777_police.transport.handlers import PeerOperations
from mars777_police.transport.peer_transport import FastMcpPeerTransport

OPERATIONS = [
    "send_step0",
    "send_config_proposal",
    "send_config_lock",
    "send_commitment",
    "send_acknowledgement",
    "send_reveal",
    "send_final_nonce_reveal",
    "send_audit_disclosure",
    "send_result_agreement",
]


def transport() -> FastMcpPeerTransport:
    return FastMcpPeerTransport(PeerClient("http://127.0.0.1:9/mcp", timeout=1.0))


def test_the_port_is_a_protocol_owned_by_the_application_layer() -> None:
    from typing import Protocol

    assert Protocol in PeerTransportPort.__mro__
    assert peer_transport.__name__.endswith("app.peer_transport")


def test_the_port_declares_exactly_the_nine_frozen_operations() -> None:
    declared = sorted(name for name in vars(PeerTransportPort) if name.startswith("send_"))
    assert declared == sorted(OPERATIONS)


def test_the_fastmcp_adapter_structurally_satisfies_the_port() -> None:
    """Structural conformance, statically enforced below and checked here."""
    adapter: PeerTransportPort = transport()
    for name in OPERATIONS:
        assert inspect.iscoroutinefunction(getattr(adapter, name))


def test_a_static_conformance_check_accepts_the_adapter_without_a_cast() -> None:
    def require_transport_port(port: PeerTransportPort) -> PeerTransportPort:
        return port

    assert require_transport_port(transport()) is not None


def test_the_port_module_imports_no_framework_type() -> None:
    """The application must be testable, and portable, without the framework."""
    source = inspect.getsource(peer_transport)
    for line in source.splitlines():
        if line.startswith(("import ", "from ")):
            assert "fastmcp" not in line
            assert "pydantic" not in line
            assert "transport." not in line.replace("peer_transport", "")


def test_no_wire_dto_appears_in_the_port_signatures() -> None:
    from typing import get_type_hints

    for name in OPERATIONS:
        hints = get_type_hints(getattr(PeerTransportPort, name))
        for annotation in hints.values():
            assert "Wire" not in str(annotation)
            assert "pydantic" not in str(annotation)


def test_the_port_is_the_mirror_of_the_inbound_protocol_not_an_alias() -> None:
    """Opposite directions, same nine operations, different names."""
    inbound = sorted(name for name in vars(PeerOperations) if name.startswith("on_"))
    assert len(inbound) == len(OPERATIONS) == 9
    assert PeerTransportPort is not PeerOperations
    assert set(inbound).isdisjoint(OPERATIONS)


def test_the_application_layer_never_imports_transport() -> None:
    """The direction is transport -> app, never the reverse."""
    src = Path(inspect.getfile(peer_transport)).resolve().parents[1]
    offenders = [
        str(path.relative_to(src))
        for path in (src / "app").rglob("*.py")
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.startswith(("import ", "from ")) and ".transport" in line
    ]
    assert offenders == []


def test_the_adapter_exposes_the_endpoint_and_holds_no_game_state() -> None:
    adapter = transport()
    assert adapter.url == "http://127.0.0.1:9/mcp"
    for absent in ("config", "cursor", "phase", "score", "truth", "contribution"):
        assert not hasattr(adapter, absent)


@pytest.mark.parametrize("value", [step0_exchange(), agreement()])
def test_the_adapter_accepts_semantic_values_not_dtos(value: object) -> None:
    """The caller hands over project values; encoding is the adapter's job."""
    assert not hasattr(value, "model_dump")
