"""Proving a `result_agreement` that arrives on a session proving nothing.

`RESULT_CONTRACT.md` R13-R1-8 requires *the authenticated sender identity*.
Holding it in one Streamable-HTTP session is this project's own choice, and a
peer whose client opens a session per call satisfies the property while failing
the choice. So such a request carries its own keyed proof.

This suite is the proof half: what verifies, and every way one does not. The
binding half - which identity a verified request is then answered as - is
`test_result_series_binding.py`.
"""

import hashlib
import hmac

import pytest
from counted_result_builders import merged
from result_auth_builders import KEY, KEY_ID, VECTOR, authority, keyed, payload, proof_over, sides

from mars777_police.app.auth_values import AuthProfile, AuthProof, KeyId
from mars777_police.app.protocol_errors import AuthFailureError
from mars777_police.app.series_result_authority import authenticated_sender
from mars777_police.protocol.canonical import canonical_json_bytes
from mars777_police.protocol.declaration import step0_core
from mars777_police.protocol.keyed_auth import STEP0_CONTEXT


def test_the_published_vector_reproduces_through_production() -> None:
    """The vector the pairing exchanged, pinned so it cannot drift silently."""
    assert proof_over(payload()).value == VECTOR
    assert (
        hmac.new(KEY, b"result" + canonical_json_bytes(payload()), hashlib.sha256).hexdigest()
        == VECTOR
    )


def test_a_session_binding_wins_and_needs_no_request_proof() -> None:
    """Our own client keeps working: a bound session is the stricter evidence."""
    declaration = merged()
    ours, theirs = sides(declaration)
    assert authenticated_sender(theirs, payload(), None, declaration, ours, authority()) == theirs


def test_a_fresh_session_with_no_proof_is_refused() -> None:
    declaration = merged()
    ours, _ = sides(declaration)
    with pytest.raises(AuthFailureError) as failure:
        authenticated_sender(None, payload(), None, declaration, ours, authority())
    assert "must carry its own keyed proof" in str(failure.value)


def test_a_proof_over_other_bytes_is_refused() -> None:
    """One token changed after signing; the tag no longer covers what arrived."""
    declaration = merged()
    ours, theirs = sides(declaration)
    signed = proof_over(payload(theirs, tokens=1200))

    with pytest.raises(AuthFailureError) as failure:
        authenticated_sender(
            None, payload(theirs, tokens=1201), signed, declaration, ours, authority()
        )
    assert "does not verify" in str(failure.value)


def test_a_proof_under_a_key_we_did_not_provision_is_refused() -> None:
    declaration = merged()
    ours, theirs = sides(declaration)
    body = payload(theirs)
    foreign = proof_over(body, key_id="somebody-elses-key", key=b"a different secret entirely")

    with pytest.raises(AuthFailureError):
        authenticated_sender(None, body, foreign, declaration, ours, authority())


def test_a_proof_naming_another_key_id_is_refused_even_with_the_right_tag() -> None:
    """`key_id` is compared against the provisioned expectation, never selected by."""
    declaration = merged()
    ours, theirs = sides(declaration)
    body = payload(theirs)
    mislabelled = AuthProof(AuthProfile.HMAC_SHA256, KeyId("other-id"), proof_over(body).value)

    with pytest.raises(AuthFailureError):
        authenticated_sender(None, body, mislabelled, declaration, ours, authority())


def test_a_proof_declaring_another_profile_is_refused() -> None:
    """The verifier is fixed before the first byte; a message cannot choose it."""
    declaration = merged()
    ours, theirs = sides(declaration)
    swapped = AuthProof(AuthProfile.ED25519, KeyId(KEY_ID), "a" * 128)

    with pytest.raises(AuthFailureError):
        authenticated_sender(None, payload(theirs), swapped, declaration, ours, authority())


def test_a_step0_proof_cannot_be_replayed_as_a_result_proof() -> None:
    """Domain separation: same key, different context, neither verifies as the other."""
    declaration = merged()
    ours, theirs = sides(declaration)
    step0 = keyed().prove(STEP0_CONTEXT, step0_core(declaration, theirs))

    with pytest.raises(AuthFailureError):
        authenticated_sender(None, payload(theirs), step0, declaration, ours, authority())
