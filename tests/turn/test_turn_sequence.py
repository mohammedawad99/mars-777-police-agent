"""Commitment and acknowledgement: ordering, correlation, and refusal.

Every refusal below is `E-PROTO-STALE`, the identity the error model already
assigns to "duplicate / stale / out-of-order message". No new identity was
needed and none was created.
"""

import pytest
from turn_builders import (
    OTHER_DIGEST,
    OUR_DIGEST,
    PEER_DIGEST,
    START,
    acknowledgement,
    commitment,
    runtime,
)

from mars777_police.app.protocol_errors import StaleMessageError
from mars777_police.app.turn_cursor import TurnCursor
from mars777_police.app.turn_protocol_state import TurnPhase


def test_a_valid_peer_commitment_is_bound_to_its_cursor() -> None:
    live = runtime()
    live.accept_commitment(commitment())
    assert live.peer_commitment is not None
    assert live.peer_commitment.h_commit == PEER_DIGEST
    assert live.peer_commitment.cursor == START
    assert live.phase is TurnPhase.AWAITING_OUR_ACKNOWLEDGEMENT


@pytest.mark.parametrize("cursor", [TurnCursor(2, 1), TurnCursor(1, 2), TurnCursor(3, 7)])
def test_a_commitment_for_another_sub_game_or_step_is_refused(cursor: TurnCursor) -> None:
    with pytest.raises(StaleMessageError) as raised:
        runtime().accept_commitment(commitment(cursor))
    assert raised.value.error_id == "E-PROTO-STALE"


def test_a_second_commitment_in_the_wrong_phase_is_refused() -> None:
    live = runtime()
    live.accept_commitment(commitment())
    with pytest.raises(StaleMessageError, match="cannot arrive"):
        live.accept_commitment(commitment())


def test_a_conflicting_duplicate_commitment_is_refused() -> None:
    """A different digest for the same cursor is still out of phase, not adopted."""
    live = runtime()
    live.accept_commitment(commitment())
    with pytest.raises(StaleMessageError):
        live.accept_commitment(commitment(digest=OTHER_DIGEST))
    assert live.peer_commitment is not None
    assert live.peer_commitment.h_commit == PEER_DIGEST


def test_acknowledging_locks_the_commitment_and_returns_the_message() -> None:
    live = runtime()
    live.accept_commitment(commitment())
    ack = live.acknowledge()
    assert ack.cursor == START
    assert ack.h_commit == PEER_DIGEST
    assert live.phase is TurnPhase.AWAITING_REVEAL


def test_acknowledging_with_nothing_pending_is_refused() -> None:
    with pytest.raises(StaleMessageError, match="nothing to acknowledge"):
        runtime().acknowledge()


def test_acknowledging_twice_is_refused() -> None:
    live = runtime()
    live.accept_commitment(commitment())
    live.acknowledge()
    with pytest.raises(StaleMessageError, match="nothing to acknowledge"):
        live.acknowledge()


def test_an_inbound_acknowledgement_requires_a_registered_local_commitment() -> None:
    with pytest.raises(StaleMessageError, match="no commitment of ours"):
        runtime().accept_acknowledgement(acknowledgement())


def test_an_inbound_acknowledgement_matches_our_registered_digest() -> None:
    live = runtime()
    live.register_local_commitment(commitment(digest=OUR_DIGEST))
    live.accept_acknowledgement(acknowledgement())
    assert live.local_acknowledged


def test_an_acknowledgement_of_a_digest_we_never_sent_is_refused() -> None:
    live = runtime()
    live.register_local_commitment(commitment(digest=OUR_DIGEST))
    with pytest.raises(StaleMessageError, match="committed digest"):
        live.accept_acknowledgement(acknowledgement(digest=OTHER_DIGEST))
    assert not live.local_acknowledged


def test_a_duplicate_inbound_acknowledgement_is_refused() -> None:
    live = runtime()
    live.register_local_commitment(commitment(digest=OUR_DIGEST))
    live.accept_acknowledgement(acknowledgement())
    with pytest.raises(StaleMessageError, match="already acknowledged"):
        live.accept_acknowledgement(acknowledgement())


def test_our_commitment_cannot_be_registered_twice() -> None:
    live = runtime()
    live.register_local_commitment(commitment(digest=OUR_DIGEST))
    with pytest.raises(StaleMessageError, match="already registered"):
        live.register_local_commitment(commitment(digest=OUR_DIGEST))


def test_an_acknowledgement_for_another_cursor_is_refused() -> None:
    live = runtime()
    live.register_local_commitment(commitment(digest=OUR_DIGEST))
    with pytest.raises(StaleMessageError):
        live.accept_acknowledgement(acknowledgement(TurnCursor(1, 9)))
