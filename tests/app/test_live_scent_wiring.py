"""The production path: does a real decision actually see the peer's emissions?

A neutral default is what keeps every existing `Observation` construction
working, and it is exactly what could hide a runtime that never wired anything
up - the suite would stay green while the agent stayed blind forever. So this
file exercises the live source rather than the value: it builds the belief the
way the running driver builds it, from the evidence the running runtime holds.

It also pins the two boundaries that make the belief lawful: a decision sees the
turns that already arrived and **not** the one it is still deciding, and a
sub-game starts from nothing rather than inheriting the last one's field.
"""

from decimal import Decimal

from belief_builders import BOARD, FAR, PARAMS, row

from mars777_police.app.scent_interpretation import LiveScentBelief, interpret_scent
from mars777_police.app.scent_records import ScentRecord
from mars777_police.domain.scent_belief import ScentBelief

ZERO = Decimal("0")


class Rows:
    """The narrowest stand-in for what the live sub-game retains."""

    def __init__(self, *rows: ScentRecord) -> None:
        self.rows = rows

    def expected_scent(self) -> tuple[ScentRecord, ...]:
        return self.rows


def source(*rows: ScentRecord) -> LiveScentBelief:
    held = Rows(*rows)
    return LiveScentBelief(lambda: held.expected_scent(), PARAMS)


def test_a_sub_game_with_no_peer_turns_yet_believes_nothing() -> None:
    belief = source().for_board(BOARD)

    assert belief == ScentBelief()
    assert not belief.has_evidence


def test_the_live_source_folds_exactly_what_arrived() -> None:
    belief = source(row(1), row(2)).for_board(BOARD)

    assert belief == interpret_scent(BOARD, (row(1), row(2)), PARAMS)
    assert belief.evidence_count == 2


def test_a_decision_cannot_see_the_turn_it_is_still_deciding() -> None:
    """Round k's own peer emission arrives after the choice; it must not appear."""
    held = Rows(row(1), row(2))
    live = LiveScentBelief(lambda: held.rows, PARAMS)

    during = live.for_board(BOARD)
    held.rows = (*held.rows, row(3, FAR))
    after = live.for_board(BOARD)

    assert during.evidence_count == 2
    assert after.evidence_count == 3
    assert during == interpret_scent(BOARD, (row(1), row(2)), PARAMS)


def test_the_source_is_read_each_time_rather_than_captured_once() -> None:
    """A belief cached at construction would freeze the first turn's view."""
    held = Rows()
    live = LiveScentBelief(lambda: held.rows, PARAMS)

    assert not live.for_board(BOARD).has_evidence
    held.rows = (row(1),)
    assert live.for_board(BOARD).has_evidence


def test_a_new_sub_game_starts_from_nothing() -> None:
    """`g02` gets a fresh audit runtime, so its history begins empty by design."""
    first = source(row(1), row(2)).for_board(BOARD)
    second = source().for_board(BOARD)

    assert first.has_evidence
    assert second == ScentBelief()
