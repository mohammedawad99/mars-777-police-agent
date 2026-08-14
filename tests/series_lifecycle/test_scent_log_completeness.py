"""A counted sub-game may not write a log with a hole where its evidence belongs.

The two scent histories are gathered by different owners than the reveal events
they belong to - ours by the transcript when we sent, the peer's by the evidence
when it arrived - so they are bound back by cursor and never by position in a
list. A row that names another turn cannot stand in for a missing one, and two
rows naming the same turn are refused rather than resolved to whichever came
last.

*Counted* is established by the histories themselves: a session that negotiated
the scent-carrying turn contract emitted on every reveal, one that did not
emitted nowhere. Under it, the signal that a reveal completed is the same one the
capture row already uses, so a reveal that completed and lost its emission stops
the log rather than quietly writing an absence that would read as "carried none".
"""

import dataclasses

import pytest
import scent_log_builders as build
from scent_log_builders import OWN, capture, counted, emission, records, reveals

from mars777_police.app.log_document import finalized_log
from mars777_police.app.protocol_errors import LocalDefectError
from mars777_police.app.scent_records import ScentRecord
from mars777_police.app.turn_cursor import TurnCursor


def test_a_counted_reveal_that_lost_its_own_history_refuses_to_finalize() -> None:
    producer, audit = counted()
    producer.scent = records((1,))
    with pytest.raises(LocalDefectError, match="step 2 completed a counted reveal"):
        finalized_log(producer, audit)


def test_a_counted_reveal_that_lost_the_peer_history_refuses_to_finalize() -> None:
    producer, audit = counted()
    audit.evidence = (
        dataclasses.replace(audit.evidence[0], scent=None),
        *audit.evidence[1:],
    )
    with pytest.raises(LocalDefectError, match="step 1 completed a counted reveal"):
        finalized_log(producer, audit)


def test_two_rows_for_one_step_are_refused_rather_than_silently_resolved() -> None:
    producer, audit = counted()
    producer.scent = (*records(), ScentRecord(TurnCursor(build.SUB_GAME, 1), emission(2)))
    with pytest.raises(LocalDefectError, match="names one step twice"):
        finalized_log(producer, audit)


def test_a_row_for_another_turn_cannot_stand_in_for_a_missing_one() -> None:
    """Cursor binding: step 2's emission does not become step 1's."""
    producer, audit = counted()
    producer.scent = records((2,))
    with pytest.raises(LocalDefectError, match="step 1 completed a counted reveal"):
        finalized_log(producer, audit)


def test_a_sealed_turn_that_was_never_revealed_needs_no_scent() -> None:
    """The completeness signal is the reveal itself, exactly as capture already is."""
    producer, audit = counted()
    producer.capture, producer.scent = capture((1,)), records((1,))
    written = reveals(finalized_log(producer, audit), OWN)
    assert written[1]["capture_answer"] is None and written[1]["scent_emission"] is None
