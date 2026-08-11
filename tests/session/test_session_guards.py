"""Static guards: the sender can only come from the session, never the payload.

`r16_source` reads real code tokens, not prose, so a docstring promising these
properties cannot satisfy them.
"""

from r16_source import code_of, imports_of, tokens_of

from mars777_police.app import pregame_session_runtime as pregame
from mars777_police.transport import inbound_session as session
from mars777_police.transport import peer_operations as adapter

FORBIDDEN_DERIVATIONS = (
    "contribution . group_id",
    "agreed_between",
    "peer_group_id",
    "context . peer_role",
)
"""`code_of` renders one token per space, so these are the spellings that match."""


def test_the_adapter_never_derives_a_sender_from_a_payload() -> None:
    """The exact expressions Stage 5-R3 refused to ship."""
    body = code_of(adapter) + code_of(session)
    for derivation in FORBIDDEN_DERIVATIONS:
        assert derivation not in body


def test_the_pregame_runtime_never_derives_a_sender_from_a_proposal() -> None:
    assert "agreed_between" not in code_of(pregame)
    assert "contribution" not in code_of(pregame)


def test_the_adapter_holds_no_module_level_identity() -> None:
    """No process-global current sender: the binding is per session or nowhere."""
    for module in (adapter, session):
        for name in dir(module):
            if not name.startswith("_"):
                assert not isinstance(getattr(module, name), str | dict | list)


def test_the_session_value_touches_no_framework() -> None:
    """`app` must never meet a FastMCP type, so it never enters this value."""
    for name in ("fastmcp", "Context", "FastMCP", "pydantic"):
        assert name not in tokens_of(session)


def test_the_pregame_runtime_imports_no_transport_and_no_framework() -> None:
    imported = imports_of(pregame)
    assert all("transport" not in name and "infra" not in name for name in imported)
    for name in ("fastmcp", "os", "environ", "socket", "ngrok", "hashlib"):
        assert name not in tokens_of(pregame)


def test_the_pregame_runtime_never_derives_the_next_round_itself() -> None:
    """MODEL A: the round is supplied, never computed - no hidden progression."""
    body = code_of(pregame)
    for progression in ("sub_game + 1", "sub_game += 1", "% 2", "range (", "next ("):
        assert progression not in body
    assert "sub_game" not in tokens_of(adapter)


def test_the_adapter_computes_no_digest_of_its_own() -> None:
    for name in ("hashlib", "sha256", "compute_commitment", "digest", "dumps"):
        assert name not in tokens_of(adapter)


def test_every_gated_method_requires_the_peer_before_resolving_a_runtime() -> None:
    """`require_peer` appears in all eight; `bind` only in `on_step0`."""
    body = code_of(adapter)
    assert body.count("session . require_peer ( )") == 8
    assert body.count("session . bind (") == 1
