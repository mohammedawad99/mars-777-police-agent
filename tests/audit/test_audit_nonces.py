"""The batched nonce disclosure: completeness, uniqueness, ordering, sender.

`FinalNonceReveal` alone can never finish an audit - the disclosed log still has
to supply `state` and `intent`. Every test here stops short of a verdict.
"""

import pytest
from audit_builders import PEER_GROUP, SUB_GAME, nonce_batch, runtime

from mars777_police.app.audit_values import AuditPhase
from mars777_police.app.peer_final_messages import FinalNonceReveal, NonceRevealEntry
from mars777_police.app.protocol_errors import StaleMessageError
from mars777_police.app.protocol_values import NonceValue
from mars777_police.app.turn_cursor import TurnCursor


def test_the_exact_complete_batch_is_accepted() -> None:
    live = runtime()
    live.accept_final_nonce_reveal(nonce_batch(), PEER_GROUP)
    assert live.phase is AuditPhase.AWAITING_DISCLOSURE
    assert len(live.nonces) == 2


def test_nonces_alone_produce_no_verdict() -> None:
    """The whole point of the deferral: the log is still required."""
    live = runtime()
    live.accept_final_nonce_reveal(nonce_batch(), PEER_GROUP)
    assert live.verdict is None
    assert not live.verified


def test_an_empty_batch_is_refused_when_turns_were_played() -> None:
    with pytest.raises(StaleMessageError, match="does not match the played turns"):
        runtime().accept_final_nonce_reveal(FinalNonceReveal(()), PEER_GROUP)


def test_a_missing_cursor_is_refused() -> None:
    with pytest.raises(StaleMessageError, match="played turns"):
        runtime().accept_final_nonce_reveal(nonce_batch((1,)), PEER_GROUP)


def test_an_extra_impossible_cursor_is_refused() -> None:
    extra = FinalNonceReveal(
        (*nonce_batch().entries, NonceRevealEntry(TurnCursor(SUB_GAME, 9), NonceValue("2" * 32)))
    )
    with pytest.raises(StaleMessageError, match="played turns"):
        runtime().accept_final_nonce_reveal(extra, PEER_GROUP)


def test_a_duplicate_cursor_in_one_batch_is_refused() -> None:
    doubled = FinalNonceReveal(nonce_batch((1,)).entries + nonce_batch((1,)).entries)
    with pytest.raises(StaleMessageError, match="repeats a cursor"):
        runtime().accept_final_nonce_reveal(doubled, PEER_GROUP)


def test_a_cursor_from_another_sub_game_is_refused() -> None:
    foreign = FinalNonceReveal(
        (NonceRevealEntry(TurnCursor(2, 1), NonceValue("0" * 32)), *nonce_batch((2,)).entries)
    )
    with pytest.raises(StaleMessageError, match="played turns"):
        runtime().accept_final_nonce_reveal(foreign, PEER_GROUP)


def test_a_batch_from_the_wrong_sender_is_refused() -> None:
    with pytest.raises(StaleMessageError, match="expected peer"):
        runtime().accept_final_nonce_reveal(nonce_batch(), "SOMEONE-ELSE")


def test_a_duplicate_batch_is_refused() -> None:
    live = runtime()
    live.accept_final_nonce_reveal(nonce_batch(), PEER_GROUP)
    with pytest.raises(StaleMessageError, match="cannot arrive"):
        live.accept_final_nonce_reveal(nonce_batch(), PEER_GROUP)


def test_batch_order_does_not_matter_but_the_set_does() -> None:
    """The contract freezes the cursor set, not the wire order of the entries."""
    live = runtime()
    reversed_batch = FinalNonceReveal(tuple(reversed(nonce_batch().entries)))
    live.accept_final_nonce_reveal(reversed_batch, PEER_GROUP)
    assert live.phase is AuditPhase.AWAITING_DISCLOSURE
