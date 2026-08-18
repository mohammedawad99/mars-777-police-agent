"""A peer's committed payload, kept as it arrived - and ours, built to be read.

Two values with opposite jobs. `PeerPayload` holds whatever JSON a lawful peer
sealed, unchanged, so its digest can be recomputed over the bytes it actually
produced; it makes no claim that the contents mean anything. `kit_payload`
builds *our* record, which is deliberately richer than the kit's minimum
because we already hold the evidence and disclosing it costs us nothing.

The asymmetry is the design. We are generous about what we reveal and strict
about what we assume: a peer that seals four keys is lawful, and our verifier
must not require the seven we happen to send.
"""

import pytest

from mars777_police.app.kit_payload import PeerPayload, kit_payload
from mars777_police.app.sealed_record_values import ActorRole, Intent
from mars777_police.app.turn_cursor import TurnCursor
from mars777_police.domain.actions import BarrierAction, MoveAction
from mars777_police.domain.board import Position
from mars777_police.domain.rules import Move

CURSOR = TurnCursor(2, 5)


def test_a_peer_payload_keeps_exactly_what_arrived() -> None:
    raw = {"step": 1, "move": "MOVE:S", "hint": "quiet here"}

    assert PeerPayload(raw).value == raw


def test_a_peer_payload_is_a_copy_the_sender_cannot_later_change() -> None:
    """A dict retained by reference could be mutated after its digest was checked."""
    raw: dict[str, object] = {"step": 1}
    held = PeerPayload(raw)
    raw["step"] = 99

    assert held.value == {"step": 1}


def test_a_peer_payload_refuses_anything_outside_the_json_domain() -> None:
    with pytest.raises(ValueError):
        PeerPayload({"when": object()})


def test_a_peer_payload_needs_no_key_of_ours() -> None:
    """The whole point: four lawful keys, none of them ours, still accepted."""
    lean = PeerPayload({"step": 3, "sender": "thief", "hint": "", "commit_note": "x"})

    assert lean.value["step"] == 3


def test_a_peer_payload_reads_a_field_without_inventing_one() -> None:
    held = PeerPayload({"step": 3, "intent": "lie"})

    assert held.text("intent") == "lie"
    assert held.text("move") is None
    assert held.whole("step") == 3
    assert held.whole("sub_game") is None


def test_a_field_of_the_wrong_type_reads_as_absent_rather_than_coerced() -> None:
    """A coercion here would manufacture evidence the peer never sealed."""
    held = PeerPayload({"step": "3", "intent": 7})

    assert held.whole("step") is None
    assert held.text("intent") is None


def test_our_payload_carries_the_evidence_we_already_hold() -> None:
    built = kit_payload(
        cursor=CURSOR,
        role=ActorRole.POLICE,
        action=MoveAction(Move.N),
        intent=Intent.TRUTH,
        hint="I chose a legal action.",
        own_position=Position(4, 3),
        barriers=(Position(1, 1),),
    )

    assert built == {
        "step": 5,
        "sub_game": 2,
        "role": "police",
        "move": "MOVE:N",
        "intent": "truth",
        "hint": "I chose a legal action.",
        "position": [4, 3],
        "barriers": [[1, 1]],
    }


def test_our_payload_spells_a_barrier_placement_distinctly() -> None:
    built = kit_payload(
        cursor=CURSOR,
        role=ActorRole.POLICE,
        action=BarrierAction(Position(2, 2)),
        intent=Intent.TRUTH,
        hint="Legal.",
        own_position=Position(2, 3),
        barriers=(),
    )

    assert built["move"] == "BARRIER:[2, 2]"
    assert built["barriers"] == []


def test_our_payload_never_carries_the_nonce() -> None:
    """Under the KIT codec the nonce is appended, not sealed inside."""
    built = kit_payload(
        cursor=CURSOR,
        role=ActorRole.THIEF,
        action=MoveAction(Move.S),
        intent=Intent.LIE,
        hint="",
        own_position=Position(0, 0),
        barriers=(),
    )

    assert "nonce" not in built


def test_our_payload_is_json_native_and_hashable_by_a_peer() -> None:
    from mars777_police.protocol.kit_commitment import kit_commitment

    built = kit_payload(
        cursor=CURSOR,
        role=ActorRole.THIEF,
        action=MoveAction(Move.E),
        intent=Intent.TRUTH,
        hint="east",
        own_position=Position(1, 1),
        barriers=(),
    )

    assert kit_commitment(built, "a" * 32) == kit_commitment(built, "a" * 32)


def test_a_nested_list_is_copied_element_by_element() -> None:
    """Barriers arrive as lists of lists; a shallow copy would share their rows."""
    rows: list[list[int]] = [[1, 1]]
    held = PeerPayload({"barriers": rows})
    rows[0][0] = 99

    assert held.value == {"barriers": [[1, 1]]}
