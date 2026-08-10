"""The two completion gates: four facts, and no shortcut through any of them.

Both participant orders matter, because the proposer follows the byte-wise lower
`group_id` **value** and the fixture deliberately places that value in the
`group_b` slot.
"""

import pytest

from mars777_police.app.protocol_values import Sha256Digest
from mars777_police.app.result_agreement_gates import MutualAgreementGate

OURS = Sha256Digest("a" * 64)
THEIRS = Sha256Digest("b" * 64)


@pytest.mark.parametrize("is_proposer", [True, False])
def test_both_sides_agree_once_all_four_facts_hold(is_proposer: bool) -> None:
    assert MutualAgreementGate(is_proposer, OURS, OURS, True, True).is_agreed


@pytest.mark.parametrize(
    ("local", "peer", "sent", "handled"),
    [
        (None, OURS, True, True),
        (OURS, None, True, True),
        (OURS, OURS, False, True),
        (OURS, OURS, True, False),
        (None, None, False, False),
    ],
)
def test_no_single_direction_is_enough(
    local: Sha256Digest | None,
    peer: Sha256Digest | None,
    sent: bool,
    handled: bool,
) -> None:
    assert not MutualAgreementGate(True, local, peer, sent, handled).is_agreed


def test_unequal_digests_never_agree_however_complete_the_exchange() -> None:
    assert not MutualAgreementGate(True, OURS, THEIRS, True, True).is_agreed
    assert not MutualAgreementGate(False, OURS, THEIRS, True, True).is_agreed


def test_the_gate_exposes_no_peer_visible_flag() -> None:
    """`mutual_agreement` is local state, never a field on a message."""
    from mars777_police.app import peer_messages

    assert not hasattr(peer_messages, "MutualAgreementGate")
    assert not hasattr(MutualAgreementGate(True, OURS, OURS, True, True), "accepted")
