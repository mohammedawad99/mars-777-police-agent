"""The scent a turn really carried, written into the reveal event that carried it.

The log answers *what happened*, so the emission it records is the one that
crossed the live protocol: our own from the history the transcript retained when
we sent it, the peer's from the `TurnEvidence` we kept when it arrived. Neither
is re-projected from an action, a truth or a model - a log that recomputed its
own evidence would agree with itself no matter what was actually played.

The two histories are gathered by different owners, so they are bound to their
reveals by cursor and never by position in a list, and a counted sub-game whose
reveal has lost its emission refuses to finalize rather than writing a hole where
evidence belongs. Whether an emission was *physically* right is a different
question, and nothing here asks it.
"""

import dataclasses

import scent_log_builders as build
from scent_log_builders import (
    OWN,
    PEER,
    STEPS,
    counted,
    emission,
    legacy,
    records,
    reveals,
)

from mars777_police.app.audit_disclosure_writer import scent_value
from mars777_police.app.log_document import finalized_log
from mars777_police.app.scent_json import deposits_value
from mars777_police.app.scent_records import ScentRecord
from mars777_police.app.turn_cursor import TurnCursor
from mars777_police.app.turn_protocol_state import TurnEvidence


def test_our_own_reveal_carries_the_scent_we_actually_sent() -> None:
    producer, audit = counted()
    written = reveals(finalized_log(producer, audit), OWN)
    assert [one["scent_emission"] for one in written] == [
        deposits_value(record.emission) for record in producer.scent
    ]


def test_the_peer_reveal_carries_the_scent_that_actually_arrived() -> None:
    producer, audit = counted()
    written = reveals(finalized_log(producer, audit), PEER)
    assert [one["scent_emission"] for one in written] == [
        deposits_value(record.emission) for record in audit.expected_scent
    ]


def test_the_own_source_is_the_retained_outbound_history_and_nothing_else() -> None:
    """Change the retained history and the log follows it - no recomputation."""
    producer, audit = counted()
    producer.scent = (ScentRecord(TurnCursor(build.SUB_GAME, 1), emission(2)), *records((2,)))
    (first, _) = reveals(finalized_log(producer, audit), OWN)
    assert first["scent_emission"] == deposits_value(emission(2))


def test_the_peer_source_is_the_live_evidence_and_not_the_disclosure() -> None:
    """`TurnEvidence.scent` is the authority; the document is only checked against it."""
    producer, audit = counted()
    audit.evidence = (
        dataclasses.replace(audit.evidence[0], scent=emission(2, own=False)),
        *audit.evidence[1:],
    )
    (first, _) = reveals(finalized_log(producer, audit), PEER)
    assert first["scent_emission"] == deposits_value(emission(2, own=False))


def test_exactly_one_scent_member_is_written_per_reveal() -> None:
    producer, audit = counted()
    for role in (OWN, PEER):
        written = reveals(finalized_log(producer, audit), role)
        assert len(written) == len(STEPS)
        assert all(list(one).count("scent_emission") == 1 for one in written)


def test_the_commit_and_ack_events_gain_nothing_at_all() -> None:
    producer, audit = counted()
    entries = finalized_log(producer, audit)["entries"]
    assert isinstance(entries, list)
    for entry in entries:
        if entry["phase"] != "reveal":
            assert "scent_emission" not in entry


def test_the_capture_members_of_a_reveal_are_untouched() -> None:
    """One member differs between a counted and a legacy reveal, and only in value."""
    producer, audit = counted()
    with_scent = reveals(finalized_log(producer, audit), OWN)
    without = reveals(finalized_log(*legacy()), OWN)
    for scented, plain in zip(with_scent, without, strict=True):
        assert set(scented) == set(plain), "the event keeps one shape either way"
        differing = {key for key in scented if scented[key] != plain[key]}
        assert differing == {"scent_emission"}
        assert plain["capture_answer"] == scented["capture_answer"] == "NO_QUESTION"


def test_every_intensity_is_canonical_decimal_text_and_never_a_float() -> None:
    producer, audit = counted()
    (first, _) = reveals(finalized_log(producer, audit), OWN)
    deposits = first["scent_emission"]
    assert isinstance(deposits, list) and deposits
    for deposit in deposits:
        assert set(deposit) == {"cell", "intensity"}
        assert isinstance(deposit["intensity"], str)
    values = {deposit["intensity"] for deposit in deposits}
    assert "0.90" in values or "0.9" in values


def test_the_event_discloses_no_position_of_the_emitter() -> None:
    producer, audit = counted()
    for role in (OWN, PEER):
        for written in reveals(finalized_log(producer, audit), role):
            text = str(written)
            for forbidden in ("source", "own_position", "opponent", "true_position", "centre"):
                assert forbidden not in text


def test_a_legacy_sub_game_writes_an_explicit_absence() -> None:
    """Pre-V2 turns carried none, and the log says so rather than staying silent."""
    for role in (OWN, PEER):
        for written in reveals(finalized_log(*legacy()), role):
            assert written["scent_emission"] is None


def test_the_log_and_the_disclosure_spell_one_emission_the_same_way() -> None:
    """Two artifacts, one historical value, one rendering authority."""
    producer, audit = counted()
    (first, _) = reveals(finalized_log(producer, audit), OWN)
    disclosed = scent_value(producer.scent[0])
    assert first["scent_emission"] == disclosed["emission"]


def test_the_evidence_the_log_reads_is_the_evidence_part_1a_froze() -> None:
    """No new collection was introduced for the log to read from."""
    producer, audit = counted()
    assert producer.scent == records()
    assert audit.expected_scent == records(own=False)
    assert all(isinstance(one, TurnEvidence) for one in audit.evidence)
