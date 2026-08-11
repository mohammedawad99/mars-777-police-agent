"""The session value itself: what it refuses, and what it will never forget.

`InboundSession` is the whole reason the sender guards mean anything, so its
own rules get direct tests rather than only being exercised through a server.
"""

import pytest
from r16_builders import GROUP_A, GROUP_B

from mars777_police.app.protocol_errors import AuthFailureError
from mars777_police.transport.inbound_session import InboundSession


def test_a_fresh_session_is_unauthenticated() -> None:
    session = InboundSession("s1")
    assert not session.is_authenticated
    assert session.peer is None and session.pending is None


def test_requiring_a_peer_on_a_fresh_session_is_an_auth_failure() -> None:
    with pytest.raises(AuthFailureError) as raised:
        InboundSession("s1").require_peer()
    assert raised.value.error_id == "E-AUTH-FAILURE"


def test_binding_authenticates_and_marks_the_write_back() -> None:
    session = InboundSession("s1")
    session.bind(GROUP_B)
    assert session.is_authenticated
    assert session.require_peer() == GROUP_B
    assert session.pending == GROUP_B


def test_a_session_cannot_be_rebound_to_another_peer() -> None:
    """The whole point: proving you are one peer never lets you become another."""
    session = InboundSession("s1", GROUP_B)
    with pytest.raises(AuthFailureError, match="rebound"):
        session.bind(GROUP_A)
    assert session.require_peer() == GROUP_B


def test_rebinding_the_same_identity_is_not_a_change() -> None:
    session = InboundSession("s1", GROUP_B)
    session.bind(GROUP_B)
    assert session.require_peer() == GROUP_B


def test_a_session_carries_its_identity_and_nothing_else() -> None:
    """Not a registry: no runtime, config, declaration or game state fits here."""
    from dataclasses import fields

    session = InboundSession("s1", GROUP_B)
    assert {f.name for f in fields(session)} == {"session_id", "peer", "pending"}
    assert all(isinstance(getattr(session, f.name), str | None) for f in fields(session))
