"""What the live turn keeps for the audit, and what it deliberately never touches.

Stage 5-R2 will rebuild the sealed record and recompute `H_commit`. This runtime
retains only what makes that possible later - the digest it was given and the
action and hint it saw - and performs no cryptography itself.
"""

import pytest
from r16_source import imports_of, tokens_of
from turn_builders import PEER_DIGEST, START, advanced, illegal_reveal, legal_reveal, runtime

from mars777_police.app import turn_protocol_runtime
from mars777_police.app.protocol_errors import PeerProtocolError


def test_completed_turns_associate_the_digest_with_what_was_revealed() -> None:
    live = advanced(runtime())
    live.accept_reveal(legal_reveal())
    (record,) = live.evidence
    assert record.cursor == START
    assert record.h_commit == PEER_DIGEST
    assert record.action == legal_reveal().action
    assert record.hint == "heading north"
    assert record.legal is True


def test_an_illegal_turn_is_still_recorded_for_the_audit() -> None:
    """The audit needs every revealed turn, not only the ones the game accepted."""
    live = advanced(runtime())
    live.accept_reveal(illegal_reveal())
    (record,) = live.evidence
    assert record.legal is False
    assert record.h_commit == PEER_DIGEST


def test_the_runtime_never_performs_commitment_cryptography() -> None:
    """The R1-R1 ruling, asserted from the module's own code tokens.

    Reading NAME tokens rather than source text is deliberate: a guard that greps
    its own file matches the very words it forbids.
    """
    tokens = tokens_of(turn_protocol_runtime)
    for forbidden in ("compute_commitment", "commitment_matches", "sha256", "hashlib"):
        assert forbidden not in tokens


def test_the_runtime_needs_no_nonce_state_or_intent() -> None:
    """Ordinary reveal opens nothing: those three stay secret until the audit."""
    tokens = tokens_of(turn_protocol_runtime)
    for absent in ("nonce", "NonceValue", "SealedState", "Intent"):
        assert absent not in tokens


def test_the_runtime_imports_no_transport_infrastructure_or_environment() -> None:
    imported = imports_of(turn_protocol_runtime)
    for forbidden in ("fastmcp", "os", "subprocess", "socket", "urllib"):
        assert forbidden not in imported
    assert all(not name.startswith("infra") for name in imported)
    assert all("transport" not in name for name in imported)


def test_every_protocol_refusal_uses_an_existing_peer_identity() -> None:
    """No new error identity was introduced by this runtime."""
    live = runtime()
    with pytest.raises(PeerProtocolError) as raised:
        live.accept_reveal(legal_reveal())
    assert raised.value.error_id == "E-PROTO-STALE"
