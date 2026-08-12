"""The gate: no post-Step-0 operation reaches a runtime on an unbound session.

This is the security property Stage 5-R3 stopped for. It is proved per method,
including for the four whose application owner never reads a sender - those are
exactly the ones that would otherwise process a stranger's valid-looking message.
"""

from typing import Any

import pytest
import session_builders as build
from peer_ops import (
    acknowledgement,
    agreement,
    audit_document,
    commitment,
    final_nonce,
    lock_evidence,
    proposal,
    reveal,
)

from mars777_police.app.protocol_errors import AuthFailureError

GATED: list[tuple[str, Any]] = [
    ("on_config_proposal", proposal()),
    ("on_config_lock", lock_evidence()),
    ("on_commitment", commitment()),
    ("on_acknowledgement", acknowledgement()),
    ("on_reveal", reveal()),
    ("on_final_nonce_reveal", final_nonce()),
    ("on_audit_disclosure", audit_document()),
    ("on_result_agreement", agreement()),
]


@pytest.mark.parametrize(("method", "value"), GATED)
def test_every_post_step0_operation_refuses_an_unbound_session(method: str, value: object) -> None:
    with pytest.raises(AuthFailureError) as raised:
        getattr(build.operations(), method)(value, build.unbound())
    assert raised.value.error_id == "E-AUTH-FAILURE"


def test_the_gated_matrix_covers_every_operation_except_step0() -> None:
    """Eight of nine; Step-0 is the one that establishes the identity."""
    assert len(GATED) == 8
    assert "on_step0" not in {name for name, _ in GATED}


def test_the_gate_runs_before_the_lifecycle_provider_is_resolved() -> None:
    """An unauthenticated caller must not even cause a runtime to be resolved."""
    resolved: list[str] = []

    def turn_provider() -> Any:
        resolved.append("turn")
        raise AssertionError("the provider must not be reached")

    def audit_provider() -> Any:
        resolved.append("audit")
        raise AssertionError("the provider must not be reached")

    from mars777_police.transport.peer_operations import InboundPeerOperations

    adapter = InboundPeerOperations(build.pregame(), turn_provider, audit_provider, build.exchange)
    for method, value in GATED:
        with pytest.raises(AuthFailureError):
            getattr(adapter, method)(value, build.unbound())
    assert resolved == []
