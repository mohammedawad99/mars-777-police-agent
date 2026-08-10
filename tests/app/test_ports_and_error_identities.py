"""The port contracts and the error identities R16 is allowed to use.

Two rules are asserted rather than assumed: **no error id was created**, and
**no port performs I/O, reaches the protocol package or returns key material**.
"""

import inspect
from typing import Protocol, get_type_hints

from r16_source import code_of, imports_of

from mars777_police.app import ports, protocol_errors
from mars777_police.app.artifact_values import UtcTimestamp
from mars777_police.app.protocol_errors import (
    AuthFailureError,
    ConfigMismatchError,
    ConventionMismatchError,
    LocalDefectError,
    MalformedMessageError,
    PeerProtocolError,
    ReportDisagreeError,
    StaleMessageError,
)

FROZEN_IDS = {
    "E-PROTO-MALFORMED",
    "E-PROTO-STALE",
    "E-AUTH-FAILURE",
    "E-CONFIG-MISMATCH",
    "E-NET-CONVENTION-MISMATCH",
    "E-REPORT-DISAGREE",
    "E-LOCAL-DEFECT",
}

PORTS = (
    "Step0AuthPort",
    "ConfigDigestPort",
    "ConfigLockAuthPort",
    "ResultDigestPort",
    "TimestampPort",
)


def test_every_error_carries_an_existing_frozen_identity() -> None:
    defined = {
        value.error_id
        for value in vars(protocol_errors).values()
        if inspect.isclass(value)
        and issubclass(value, PeerProtocolError)
        and value is not PeerProtocolError
    }
    assert defined == FROZEN_IDS


def test_no_error_identity_was_invented() -> None:
    for error in (
        MalformedMessageError,
        StaleMessageError,
        AuthFailureError,
        ConfigMismatchError,
        ConventionMismatchError,
        ReportDisagreeError,
        LocalDefectError,
    ):
        assert error.error_id in FROZEN_IDS
        assert error.error_id.startswith("E-")


def test_a_protocol_error_is_not_a_value_error() -> None:
    """Malformed *construction* is a `ValueError`; a protocol outcome is not."""
    assert not issubclass(PeerProtocolError, ValueError)
    assert issubclass(AuthFailureError, PeerProtocolError)


def test_no_error_type_holds_state_or_key_material() -> None:
    code = code_of(protocol_errors)
    for forbidden in ("key", "secret", "token", "nonce"):
        assert forbidden not in code
    assert imports_of(protocol_errors) == {"typing"}


def test_the_five_ports_exist_and_are_protocols() -> None:
    for name in PORTS:
        assert Protocol in getattr(ports, name).__mro__


def test_no_port_method_is_async() -> None:
    """`async` is an I/O property; nothing in the application runtime does I/O."""
    for name in PORTS:
        for member in vars(getattr(ports, name)).values():
            assert not inspect.iscoroutinefunction(member)


def test_no_port_signature_mentions_bytes_or_key_material() -> None:
    code = code_of(ports)
    for forbidden in ("bytes", "key_material", "secret", "private_key", "canonical"):
        assert forbidden not in code


def test_the_ports_module_imports_neither_transport_nor_the_protocol_package() -> None:
    for imported in imports_of(ports):
        assert "protocol." not in imported
        assert imported.lstrip(".") not in {"socket", "asyncio", "fastmcp", "httpx"}


def test_the_timestamp_port_returns_the_frozen_timestamp_type() -> None:
    assert get_type_hints(ports.TimestampPort.now)["return"] is UtcTimestamp
