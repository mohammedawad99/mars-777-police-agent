"""The proof: a real peer `AuditRuntime` verifies what our producer emits.

No fake hash, no test-only commitment implementation, no hand-written document.
The producer seals with `CommitmentRecomputer` and the receiver recomputes with
the same primitive, so a `VERIFIED_OK` here means the writer really is the
inverse of the reader the inbound side already accepted.
"""

import evidence_builders as build
import pytest
from evidence_builders import PEER_GROUP, prepare, producer, receiver

from mars777_police.app.protocol_errors import StaleMessageError
from mars777_police.app.protocol_values import FinalAuditVerdict


def audited(steps: tuple[int, ...]) -> tuple[object, object]:
    """Drive one sub-game end to end: prepare, disclose nonces, disclose log."""
    live = producer()
    prepared = [prepare(live, step) for step in steps]
    peer = receiver(prepared, steps)
    peer.accept_final_nonce_reveal(live.final_nonce_reveal(), PEER_GROUP)
    peer.accept_audit_disclosure(live.audit_disclosure())
    return live, peer


def test_a_real_receiver_verifies_our_produced_disclosure() -> None:
    _, peer = audited((1,))
    assert peer.verdict is FinalAuditVerdict.VERIFIED_OK
    assert peer.verified


def test_a_real_receiver_verifies_every_turn_of_a_multi_turn_sub_game() -> None:
    _, peer = audited((1, 2, 3))
    assert peer.verdict is FinalAuditVerdict.VERIFIED_OK
    assert [cursor.step for cursor in peer.expected] == [1, 2, 3]


def test_a_tampered_copy_of_our_document_does_not_verify() -> None:
    """The receiver's guards fire on our shape exactly as on any other."""
    live = producer()
    prepared = [prepare(live, 1)]
    peer = receiver(prepared, (1,))
    peer.accept_final_nonce_reveal(live.final_nonce_reveal(), PEER_GROUP)
    forged = live.audit_disclosure()
    forged["entries"][0]["hint"] = "a hint we never sealed"  # type: ignore[index]
    peer.accept_audit_disclosure(forged)
    assert peer.verdict is FinalAuditVerdict.TAMPERED


def test_a_fresh_render_after_external_mutation_still_verifies() -> None:
    """Producer authority survives whatever a caller did to an old copy."""
    live = producer()
    prepared = [prepare(live, 1)]
    stale = live.final_nonce_reveal()
    spoiled = live.audit_disclosure()
    spoiled["entries"][0]["commit"] = "0" * 64  # type: ignore[index]
    spoiled["game_id"] = "another-game"
    peer = receiver(prepared, (1,))
    peer.accept_final_nonce_reveal(stale, PEER_GROUP)
    peer.accept_audit_disclosure(live.audit_disclosure())
    assert peer.verdict is FinalAuditVerdict.VERIFIED_OK


def test_the_receiver_refuses_a_batch_that_is_not_this_sub_games() -> None:
    live = producer()
    prepared = [prepare(live, 1), prepare(live, 2)]
    peer = receiver(prepared[:1], (1,))
    with pytest.raises(StaleMessageError, match="played turns"):
        peer.accept_final_nonce_reveal(live.final_nonce_reveal(), PEER_GROUP)


def test_a_barrier_turn_round_trips_through_the_real_receiver() -> None:
    """The other action form, sealed and verified end to end."""
    from mars777_police.app.sealed_record_values import Intent
    from mars777_police.app.turn_cursor import TurnCursor
    from mars777_police.domain.actions import BarrierAction
    from mars777_police.domain.board import Position

    live = producer()
    turn = live.prepare_turn(
        state=build.sealed(1),
        action=BarrierAction(Position(4, 5)),
        intent=Intent.LIE,
        hint="not where you think",
        cursor=TurnCursor(build.SUB_GAME, 1),
    )
    peer = receiver([turn], (1,))
    peer.accept_final_nonce_reveal(live.final_nonce_reveal(), PEER_GROUP)
    peer.accept_audit_disclosure(live.audit_disclosure())
    assert peer.verdict is FinalAuditVerdict.VERIFIED_OK
