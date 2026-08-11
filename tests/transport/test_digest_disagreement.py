"""A genuine digest disagreement is a typed failure, not a quiet `False`.

Before this stage the mismatch produced `is_agreed = False` and nothing else -
a peer whose approval core genuinely differed looked the same as a direction
that had simply not finished yet. `E-REPORT-DISAGREE` is the frozen identity for
that, and it now has a production branch.
"""

import pytest
from peer_ops import RESULT_DIGEST

from mars777_police.app.protocol_errors import ReportDisagreeError
from mars777_police.app.protocol_values import Sha256Digest
from mars777_police.app.result_agreement_gates import MutualAgreementGate, require_matching_digest

OURS = Sha256Digest("a" * 64)
THEIRS = Sha256Digest("b" * 64)


def test_matching_digests_are_accepted_silently() -> None:
    require_matching_digest(OURS, OURS)


def test_a_digest_mismatch_raises_the_frozen_identity() -> None:
    with pytest.raises(ReportDisagreeError) as raised:
        require_matching_digest(OURS, THEIRS)
    assert raised.value.error_id == "E-REPORT-DISAGREE"
    assert str(raised.value) == "E-REPORT-DISAGREE"


def test_the_mismatch_is_not_reported_as_a_boolean() -> None:
    """The defect this closes: `False` alone blamed nobody."""
    with pytest.raises(ReportDisagreeError):
        require_matching_digest(OURS, THEIRS)
    assert not MutualAgreementGate(True, OURS, THEIRS, True, True).is_agreed


def test_the_gate_still_reports_incompleteness_for_its_own_reasons() -> None:
    """A direction that has not finished is not an accusation."""
    assert not MutualAgreementGate(True, OURS, None, True, True).is_agreed
    assert not MutualAgreementGate(True, OURS, OURS, False, True).is_agreed
    assert MutualAgreementGate(True, OURS, OURS, True, True).is_agreed


def test_neither_side_agrees_when_the_digests_differ() -> None:
    proposer = MutualAgreementGate(True, OURS, THEIRS, True, True)
    other = MutualAgreementGate(False, THEIRS, OURS, True, True)
    assert not proposer.is_agreed
    assert not other.is_agreed


def test_no_new_identity_was_introduced_for_the_mismatch() -> None:
    from mars777_police.transport.wire_errors import _BY_IDENTITY

    assert ReportDisagreeError.error_id in _BY_IDENTITY
    assert RESULT_DIGEST.value != THEIRS.value
