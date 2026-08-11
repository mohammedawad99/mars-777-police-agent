"""Rendering our disclosure: the reader's exact shape, from our evidence only."""

import evidence_builders as build
import pytest
from evidence_builders import GAME_ID, GAME_UID, SUB_GAME, prepare, producer

from mars777_police.app.audit_disclosure import turns
from mars777_police.app.audit_disclosure_writer import action_value
from mars777_police.app.outbound_evidence_values import EvidencePhase
from mars777_police.app.protocol_errors import StaleMessageError
from mars777_police.domain.actions import BarrierAction, MoveAction
from mars777_police.domain.board import Position
from mars777_police.domain.rules import Move


def disclosed() -> dict[str, object]:
    """One prepared turn, disclosed the way the protocol sequences it."""
    live = producer()
    prepare(live, 1)
    live.final_nonce_reveal()
    return live.audit_disclosure()


def test_the_document_carries_the_four_identity_members() -> None:
    document = disclosed()
    assert document["game_id"] == GAME_ID
    assert document["game_uid"] == GAME_UID
    assert document["sub_game"] == SUB_GAME
    assert document["config_sha256"] == build.CONFIG.value


def test_the_document_is_json_native_throughout() -> None:
    """No semantic object, no path, no bytes - `dict`/`list`/`str`/`int` only."""
    import json

    document = disclosed()
    assert json.loads(json.dumps(document)) == document


def test_every_entry_matches_the_readers_exact_field_set() -> None:
    entry = disclosed()["entries"][0]  # type: ignore[index]
    assert set(entry) == {
        "step",
        "sub_game",
        "role",
        "move",
        "intent",
        "hint",
        "commit",
        "state",
    }
    assert set(entry["state"]) == {"config_sha256", "self_pos", "barriers", "step", "role"}


def test_the_reader_parses_our_document_without_adaptation() -> None:
    """The writer is the inverse of the accepted parser, field for field."""
    parsed = turns(disclosed())
    assert len(parsed) == 1
    assert parsed[0].move == MoveAction(Move.N)
    assert parsed[0].self_pos == build.POS[1]


def test_no_locally_derived_verdict_field_is_emitted() -> None:
    document = disclosed()
    entry = document["entries"][0]  # type: ignore[index]
    assert "audit" not in document
    assert "verified" not in entry


def test_a_barrier_action_renders_its_exact_cell() -> None:
    assert action_value(BarrierAction(Position(4, 5))) == {"kind": "BARRIER", "value": [4, 5]}


def test_an_unknown_action_type_is_refused_rather_than_guessed() -> None:
    with pytest.raises(ValueError, match="MoveAction or BarrierAction"):
        action_value("not an action")  # type: ignore[arg-type]


def test_the_disclosure_cannot_precede_the_nonce_reveal() -> None:
    live = producer()
    prepare(live, 1)
    with pytest.raises(StaleMessageError, match="follows the final nonce reveal"):
        live.audit_disclosure()


def test_the_runtime_is_terminal_after_disclosure() -> None:
    live = producer()
    prepare(live, 1)
    live.final_nonce_reveal()
    live.audit_disclosure()
    assert live.phase is EvidencePhase.COMPLETE
    with pytest.raises(StaleMessageError):
        prepare(live, 2)


def test_mutating_a_returned_document_cannot_change_the_next_render() -> None:
    """The producer's authority is its immutable records, not what it handed out."""
    live = producer()
    prepare(live, 1)
    live.final_nonce_reveal()
    first = live.audit_disclosure()
    first["game_id"] = "some-other-game"
    first["entries"][0]["commit"] = "0" * 64  # type: ignore[index]
    first["entries"].clear()  # type: ignore[union-attr]
    again = live.audit_disclosure()
    assert again["game_id"] == GAME_ID
    assert len(again["entries"]) == 1  # type: ignore[arg-type]


def test_two_renders_are_semantically_identical() -> None:
    live = producer()
    prepare(live, 1)
    live.final_nonce_reveal()
    assert live.audit_disclosure() == live.audit_disclosure()
