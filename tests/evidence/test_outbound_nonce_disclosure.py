"""Disclosing our nonces: from our own records, in one order, once."""

import evidence_builders as build
import pytest
from evidence_builders import SUB_GAME, ScriptedNonces, prepare, producer

from mars777_police.app.outbound_evidence_values import EvidencePhase
from mars777_police.app.peer_final_messages import FinalNonceReveal, NonceRevealEntry
from mars777_police.app.protocol_errors import StaleMessageError


def test_the_batch_carries_one_entry_per_prepared_turn() -> None:
    live = producer()
    for step in (1, 2, 3):
        prepare(live, step)
    batch = live.final_nonce_reveal()
    assert type(batch) is FinalNonceReveal
    assert len(batch.entries) == 3
    assert all(type(entry) is NonceRevealEntry for entry in batch.entries)


def test_every_entry_carries_only_a_cursor_and_a_nonce() -> None:
    import dataclasses

    live = producer()
    prepare(live, 1)
    entry = live.final_nonce_reveal().entries[0]
    assert {f.name for f in dataclasses.fields(entry)} == {"cursor", "nonce"}


def test_the_entries_are_ordered_by_step() -> None:
    live = producer()
    for step in (3, 1, 2):
        prepare(live, step)
    assert [entry.cursor.step for entry in live.final_nonce_reveal().entries] == [1, 2, 3]


def test_every_disclosed_nonce_is_the_one_we_actually_sealed() -> None:
    live = producer(ScriptedNonces(["a" * 32, "b" * 32]))
    prepare(live, 1)
    prepare(live, 2)
    disclosed = {e.cursor.step: e.nonce.value for e in live.final_nonce_reveal().entries}
    assert disclosed == {1: "a" * 32, 2: "b" * 32}


def test_every_cursor_belongs_to_this_sub_game() -> None:
    live = producer()
    prepare(live, 1)
    assert all(e.cursor.sub_game == SUB_GAME for e in live.final_nonce_reveal().entries)


def test_disclosing_closes_turn_preparation() -> None:
    live = producer()
    prepare(live, 1)
    live.final_nonce_reveal()
    assert live.phase is EvidencePhase.NONCES_DISCLOSED
    with pytest.raises(StaleMessageError, match="no turn may be prepared"):
        prepare(live, 2)


def test_a_repeat_disclosure_reproduces_the_same_associations() -> None:
    """Retry must never draw a new nonce."""
    live = producer()
    prepare(live, 1)
    prepare(live, 2)
    first, second = live.final_nonce_reveal(), live.final_nonce_reveal()
    assert first == second
    assert first.entries[0].nonce == second.entries[0].nonce


def test_an_empty_sub_game_discloses_an_empty_batch() -> None:
    assert producer().final_nonce_reveal().entries == ()
    assert build.SUB_GAME == 1


def test_a_capture_row_cannot_arrive_after_the_disclosure_was_rendered() -> None:
    """The document is already out; a row added now would never be in it."""
    from mars777_police.app.capture_transcript import CaptureRecord
    from mars777_police.app.capture_values import CaptureAnswer
    from mars777_police.app.turn_cursor import TurnCursor

    live = producer()
    prepare(live, 1)
    live.final_nonce_reveal()
    late = (CaptureRecord(TurnCursor(build.SUB_GAME, 1), None, CaptureAnswer.NO_QUESTION),)
    live.observe_capture(late)
    assert live.audit_disclosure()["capture"] == [
        {"step": 1, "claim": None, "answer": "NO_QUESTION"}
    ]
    with pytest.raises(StaleMessageError, match="already rendered"):
        live.observe_capture(late)
