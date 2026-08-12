"""The whole live cadence, driven through production objects only.

No FastMCP, no transport, no test-double `PeerOperations` - the point of Stage
5-R1 is that this sequence now runs on production application code, which is
what Stage 4E-R18-R1-CR2 found missing.

**No primitive-regression test lives here.** `tests/protocol/test_commitment_digest`
already pins `compute_commitment` against known-answer vectors over the full
eight-field sealed record, which is stronger than anything this module would add
and is what Stage 5-R2 will rely on. Duplicating it would create a second place
to update when the primitive is touched. The runtime below never calls it.
"""

from turn_builders import advanced, commitment, legal_reveal, runtime, truth

from mars777_police.app.turn_cursor import TurnCursor
from mars777_police.app.turn_protocol_state import TurnPhase


def test_the_full_live_turn_runs_on_production_objects_alone() -> None:
    live = runtime()
    assert live.phase is TurnPhase.AWAITING_COMMITMENT

    live.accept_commitment(commitment())
    assert live.phase is TurnPhase.AWAITING_OUR_ACKNOWLEDGEMENT

    ack = live.acknowledge()
    assert ack.h_commit == commitment().h_commit
    assert live.phase is TurnPhase.AWAITING_REVEAL

    assert live.accept_reveal(legal_reveal()).accepted is True
    assert live.phase is TurnPhase.CONSUMED
    assert len(live.evidence) == 1
    assert live.truth.completed_steps == 0  # their move is theirs; ours never advanced


def test_our_own_outbound_turn_material_is_tracked_separately() -> None:
    """Two directions, two slots - the peer's commitment is not ours."""
    live = advanced(runtime())
    assert live.peer_commitment is not None
    assert live.local_commitment is None
    assert not live.local_acknowledged


def test_both_directions_can_be_in_flight_without_colliding() -> None:
    """Our commitment and the peer's are independent facts on independent clocks."""
    live = runtime()
    live.register_local_commitment(commitment(digest=commitment().h_commit))
    live.accept_commitment(commitment())
    assert live.local_commitment is not None
    assert live.peer_commitment is not None
    assert live.local_commitment is not live.peer_commitment


def test_the_runtime_starts_from_real_domain_truth() -> None:
    live = runtime()
    assert live.truth == truth()
    assert live.cursor == TurnCursor(1, 1)
