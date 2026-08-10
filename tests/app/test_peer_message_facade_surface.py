"""What the peer-message façade publishes, and what it must keep hidden.

Split out of `test_peer_message_module_layout.py` at Stage 4E-R15, which owns
*where values are defined* and the import direction between those modules. This
file owns the complementary question: which names the façade exposes. A family
belongs on it once implemented; the support values a family is built from never
do, and neither does any serialization or crypto surface.
"""

import pytest

from mars777_police.app import peer_final_messages, peer_messages


@pytest.mark.parametrize("family", ["MoveValidation", "FinalAudit", "Declaration"])
def test_the_facade_names_no_non_family(family: str) -> None:
    """``MoveValidation`` and ``FinalAudit`` were ruled out as families entirely
    (C-11, C-12); ``Declaration`` is declaration subject data, not a family.
    ``ResultAgreement`` left this list at Stage 4E-R15 because it is now
    implemented - the guard tracks what may never appear, not what is pending.
    """
    assert not hasattr(peer_messages, family)


def test_the_facade_exposes_result_agreement_without_its_support_values() -> None:
    """The family is public; the values it is built from are not."""
    assert peer_messages.ResultAgreement is peer_final_messages.ResultAgreement
    for support in ("ResultContribution", "ResultContributionEntry", "ParticipantTokenUsage"):
        assert not hasattr(peer_messages, support)


def test_the_facade_carries_no_serialization_or_crypto_surface() -> None:
    for forbidden in ("hashlib", "sha256", "hexdigest", "compute", "json", "enum", "dataclass"):
        assert not hasattr(peer_messages, forbidden)
