"""The KIT semantic layer on its own: what a message means, and when we refuse.

Each refusal below is a pinned one, restated in this project's own error
identities so an operator can grep for the same ids they already know. The
distinction the kit spent two hours learning is kept: **terms absent or
differing** is a constitution disagreement, and a **signature that will not
verify over matching terms** is a serialization fault. Reporting "handshake
failed" for both is what made them indistinguishable.

Omission never refuses, in either direction. Every optional member is checked
only when the peer actually declared it.
"""

import pytest
from kit_builders import NONCE, OUR_GROUP, PEER_GROUP, TERMS, kit_greeting
from kit_wire_vectors import TURN, turn

from mars777_police.app.kit_messages import KitRole
from mars777_police.app.kit_payload import PeerPayload
from mars777_police.app.kit_session import KitSessionContext
from mars777_police.app.protocol_errors import (
    ConfigMismatchError,
    MalformedMessageError,
    StaleMessageError,
)
from mars777_police.protocol.kit_identity import kit_game_id, kit_game_uid, kit_terms_digest
from mars777_police.transport.codec_kit_pregame import decode_kit_greeting
from mars777_police.transport.codec_kit_turn import decode_kit_turn, encode_kit_turn
from mars777_police.transport.kit_envelopes import KitNegotiateMessage, KitTurnMessage

SIGNATURE = kit_terms_digest(TERMS, NONCE)


def context(role: KitRole = KitRole.THIEF, sub_game: int = 1) -> KitSessionContext:
    return KitSessionContext(OUR_GROUP, role, PeerPayload(TERMS), sub_game)


def greeting(**changes: object):
    return kit_greeting(signature=SIGNATURE, **changes)


def test_a_matching_greeting_establishes_the_identity_both_peers_derive() -> None:
    pairing = context().accept(greeting())

    assert pairing.game_id == kit_game_id(OUR_GROUP, PEER_GROUP)
    assert pairing.game_uid == kit_game_uid(TERMS, OUR_GROUP, PEER_GROUP)
    assert pairing.terms_agreed is True
    assert pairing.peer_role is KitRole.POLICE


def test_a_greeting_never_authenticates_anything() -> None:
    """The terms digest is unkeyed content agreement, and nothing else."""
    pairing = context().accept(greeting())

    assert pairing.authenticated is False


def test_terms_that_do_not_value_equal_ours_are_a_constitution_disagreement() -> None:
    with pytest.raises(ConfigMismatchError):
        context().accept(greeting(terms=PeerPayload({"grid_size": 11})))


def test_a_signature_that_will_not_verify_is_named_as_a_serialization_fault() -> None:
    with pytest.raises(ConfigMismatchError):
        context().accept(kit_greeting(signature="c" * 64))


def test_a_declared_uid_that_differs_from_ours_is_refused() -> None:
    with pytest.raises(ConfigMismatchError):
        context().accept(greeting(game_uid="00000000-0000-0000-0000-000000000000"))


def test_a_sub_game_mismatch_belongs_to_a_different_game() -> None:
    with pytest.raises(StaleMessageError):
        context(sub_game=2).accept(greeting())


def test_a_role_collision_can_only_deadlock_and_is_refused() -> None:
    with pytest.raises(StaleMessageError):
        context(role=KitRole.POLICE).accept(greeting())


def test_one_series_carries_one_opponent() -> None:
    """Identical signed terms make a third team's greeting pass every other check."""
    held = context()
    held.accept(greeting())

    with pytest.raises(StaleMessageError):
        held.accept(greeting(group_id="team-bet"))


def test_the_cursor_joins_our_sub_game_to_the_peers_own_step() -> None:
    """The step is the peer's; the sub-game is ours, and never read off the wire."""
    cursor = context(sub_game=4).cursor(9)

    assert (cursor.sub_game, cursor.step) == (4, 9)


def test_a_declared_lock_is_readable_and_an_undeclared_one_is_silence() -> None:
    declared = greeting(locks=(("scent_model", "a" * 64),))

    assert declared.lock("scent_model") == "a" * 64
    assert declared.lock("wire_shape") is None


def test_the_turn_round_trips_through_its_own_codec() -> None:
    assert encode_kit_turn(decode_kit_turn(KitTurnMessage.model_validate(TURN))) == TURN


def test_every_optional_turn_member_survives_a_round_trip() -> None:
    full = turn(
        capture_claim=[2, 4],
        claim_response={"claim": [2, 4], "caught": True},
        win_claim={"type": "survival"},
        barrier_placed=None,
    )

    assert encode_kit_turn(decode_kit_turn(KitTurnMessage.model_validate(full))) == full


def test_a_cell_that_is_not_a_row_and_a_column_is_malformed() -> None:
    with pytest.raises(MalformedMessageError):
        decode_kit_turn(KitTurnMessage.model_validate(turn(barrier_placed=[5, 6, 7])))


def test_a_claim_response_missing_its_honest_answer_is_malformed() -> None:
    with pytest.raises(MalformedMessageError):
        decode_kit_turn(KitTurnMessage.model_validate(turn(claim_response={"claim": [2, 4]})))


def test_a_win_claim_outside_the_pinned_spelling_is_never_guessed_at() -> None:
    with pytest.raises(MalformedMessageError):
        decode_kit_turn(KitTurnMessage.model_validate(turn(win_claim={"type": "capture"})))


def test_an_object_that_is_not_json_native_is_refused_rather_than_coerced() -> None:
    """A digest computed over coerced bytes is a digest the peer never produced."""
    wire = KitNegotiateMessage.model_validate(
        {"terms": {"a": {1, 2}}, "nonce": NONCE, "signature": SIGNATURE, "group_id": PEER_GROUP}
    )

    with pytest.raises(MalformedMessageError):
        decode_kit_greeting(wire)
