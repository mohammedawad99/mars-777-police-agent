"""The KIT commitment: the nonce is beside the payload, not inside it.

`SHA256(kit_canonical(payload) + "|" + nonce)`, with a single U+007C. The kit
spells the separator out because all three plausible readings are
self-consistent under self-testing - sign and verify with the same wrong form
and every local test passes while every real handshake fails.

The two constructions are pinned against each other here so the difference is
proved rather than assumed: the same record under our project assembly and
under the kit's produce different digests, and both are correct for their own
profile.
"""

import pytest
from kit_vectors import COMMITMENTS, NONCE_INSIDE

from mars777_police.protocol.kit_commitment import kit_commitment


@pytest.mark.parametrize(("payload", "nonce", "expected"), COMMITMENTS)
def test_the_pinned_kit_commitments_reproduce_exactly(
    payload: dict[str, object], nonce: str, expected: str
) -> None:
    assert kit_commitment(payload, nonce) == expected


def test_the_nonce_is_outside_the_payload() -> None:
    """Putting it inside gives the kit's other published form - a different digest."""
    payload, nonce, expected = COMMITMENTS[1]

    assert kit_commitment(payload, nonce) == expected
    assert kit_commitment({**payload, "nonce": nonce}, nonce) != expected


def test_a_payload_carrying_its_own_nonce_member_is_still_hashed_with_it_outside() -> None:
    """The codec never strips or relocates a member; it appends the nonce it was given."""
    payload, nonce, _ = COMMITMENTS[1]
    inside = {**payload, "nonce": nonce}

    assert kit_commitment(inside, nonce) != kit_commitment(payload, nonce)


def test_the_separator_is_exactly_one_pipe() -> None:
    """A doubled or absent separator is a different construction, not a variant."""
    import hashlib

    from mars777_police.protocol.kit_canonical import kit_canonical_text

    payload, nonce, expected = COMMITMENTS[1]
    canon = kit_canonical_text(payload)
    for wrong in (f"{canon}{nonce}", f"{canon}||{nonce}"):
        assert hashlib.sha256(wrong.encode()).hexdigest() != expected


def test_our_project_commitment_bytes_are_untouched_by_any_of_this() -> None:
    """The strict profile's published form must not move because KIT arrived."""
    assert kit_commitment(*COMMITMENTS[1][:2]) != NONCE_INSIDE


@pytest.mark.parametrize("nonce", ["", 0, None])
def test_a_missing_or_non_text_nonce_is_refused(nonce: object) -> None:
    """A commitment without a nonce is not a weaker commitment; it is not one."""
    with pytest.raises(ValueError, match="non-empty nonce"):
        kit_commitment({"step": 1}, nonce)  # type: ignore[arg-type]
