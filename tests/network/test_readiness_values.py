"""The local readiness vocabulary, and the boundary it must never cross.

These three tokens are named by PRD-05 as reasons a **local** gate refuses to
start. Promoting them to peer identities would blame the opponent for our own
tunnel, so the separation is asserted structurally rather than trusted.
"""

import pytest

from mars777_police.app import protocol_errors
from mars777_police.app.protocol_errors import PeerProtocolError
from mars777_police.app.public_readiness_values import (
    CHECK_ORDER,
    CheckOutcome,
    PublicReadinessReason,
    PublicReadinessVerdict,
    ReadinessCheck,
)


def test_the_three_frozen_reason_tokens_are_exactly_the_prd_ones() -> None:
    assert [reason.value for reason in PublicReadinessReason] == [
        "E-NET-NOT-PUBLIC",
        "E-NET-STALE-ENDPOINT",
        "E-NET-CONVENTION-UNSET",
    ]


def test_the_reasons_are_not_peer_protocol_errors() -> None:
    assert not issubclass(PublicReadinessReason, PeerProtocolError)
    identities = {
        value.error_id
        for value in vars(protocol_errors).values()
        if isinstance(value, type) and issubclass(value, PeerProtocolError)
    }
    for reason in PublicReadinessReason:
        assert reason.value not in identities


def test_the_peer_identity_for_a_convention_mismatch_is_untouched() -> None:
    """`E-NET-CONVENTION-MISMATCH` stays a peer error; the local tokens do not join it."""
    assert protocol_errors.ConventionMismatchError.error_id == "E-NET-CONVENTION-MISMATCH"
    assert "E-NET-CONVENTION-MISMATCH" not in {r.value for r in PublicReadinessReason}


def test_there_are_exactly_ten_checks_in_requirement_order() -> None:
    assert len(CHECK_ORDER) == 10
    assert [check.value for check in CHECK_ORDER] == list("abcdefghij")


def test_a_passing_check_may_not_carry_a_refusal_reason() -> None:
    with pytest.raises(ValueError, match="passing check"):
        CheckOutcome(ReadinessCheck.LOCAL_SERVER_BOUND, True, PublicReadinessReason.NOT_PUBLIC)


def test_a_check_outcome_refuses_a_non_boolean_verdict() -> None:
    with pytest.raises(ValueError, match="bool"):
        CheckOutcome(ReadinessCheck.LOCAL_SERVER_BOUND, 1)  # type: ignore[arg-type]


def full(passed: bool) -> PublicReadinessVerdict:
    return PublicReadinessVerdict(tuple(CheckOutcome(check, passed) for check in CHECK_ORDER))


def test_a_verdict_must_carry_all_ten_checks_in_order() -> None:
    with pytest.raises(ValueError, match="ten"):
        PublicReadinessVerdict((CheckOutcome(ReadinessCheck.LOCAL_SERVER_BOUND, True),))
    with pytest.raises(ValueError, match="ten"):
        PublicReadinessVerdict(tuple(CheckOutcome(c, True) for c in reversed(CHECK_ORDER)))


def test_ready_requires_every_check_and_failures_are_listed_in_order() -> None:
    assert full(True).is_ready
    assert full(True).failures == ()
    assert not full(False).is_ready
    assert len(full(False).failures) == 10


def test_reasons_are_deduplicated_and_omitted_where_the_prd_names_none() -> None:
    outcomes = []
    for index, check in enumerate(CHECK_ORDER):
        reason = PublicReadinessReason.NOT_PUBLIC if index < 3 else None
        outcomes.append(CheckOutcome(check, False, reason))
    verdict = PublicReadinessVerdict(tuple(outcomes))
    assert verdict.reasons == (PublicReadinessReason.NOT_PUBLIC,)
    assert full(True).reasons == ()
