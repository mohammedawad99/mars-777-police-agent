"""Building the six rows a settlement hashes, from facts each backend already has.

Two things here are digest-breaking if wrong and invisible if untested: the
outcome word's **case**, and which group each score belongs to when we played
thief. Both are checked against a series that was actually settled with a real
opponent.
"""

import json
from pathlib import Path

import pytest

from mars777_police.app.kit_messages import KitRole
from mars777_police.app.kit_series_rows import ROW_MEMBERS, SeriesRowCollector
from mars777_police.app.kit_settled_row import settled_row
from mars777_police.app.protocol_errors import StaleMessageError
from mars777_police.app.series_consensus import consensus_scope, consensus_sha256
from mars777_police.domain.terminal import Outcome

OURS = "MaRs-777"
THEIRS = "sparring-s82kma9e"
GAME_ID = "MaRs-777-vs-sparring-s82kma9e"
SETTLED = "33f1b2032e8ce87e8bd99de82aac5ebb29943571e2ae583ce4ee2d22f2eeaf1c"
PRESERVED = Path("/tmp/mars777-s82kma9e-interop/PRESERVED-rerun-3-settlement/rerun3_scope.json")


def played() -> list[dict[str, object]]:
    """That series as our two backends saw it: police on odd, thief on even."""
    return [
        settled_row(
            sub_game=n,
            ours=OURS,
            theirs=THEIRS,
            our_role=KitRole.POLICE if n % 2 else KitRole.THIEF,
            outcome=Outcome.SURVIVAL if n % 2 else Outcome.CAPTURE,
        )
        for n in range(1, 7)
    ]


def test_production_rows_reproduce_a_digest_a_real_peer_accepted() -> None:
    assert consensus_sha256(consensus_scope(GAME_ID, played(), OURS, THEIRS)) == SETTLED


def test_the_outcome_word_is_lower_case_on_the_wire() -> None:
    """`SURVIVAL` and `survival` are two different series to a digest."""
    assert {row["result"] for row in played()} == {"survival", "capture"}
    assert Outcome.SURVIVAL.value == "SURVIVAL"


def test_the_scores_land_on_the_group_that_earned_them() -> None:
    """As thief in a capture we score 5 and the opponent 20, not the reverse."""
    thief_row = played()[1]
    assert thief_row["roles"] == {OURS: "thief", THEIRS: "police"}
    assert thief_row["score"] == {OURS: 5, THEIRS: 20}
    police_row = played()[0]
    assert police_row["roles"] == {OURS: "police", THEIRS: "thief"}
    assert police_row["score"] == {OURS: 5, THEIRS: 10}


def test_a_row_carries_exactly_what_a_settlement_reads() -> None:
    assert tuple(played()[0]) == ROW_MEMBERS


def test_the_collector_returns_the_six_rows_in_order() -> None:
    collector = SeriesRowCollector()
    for row in reversed(played()):
        collector.record(row)
    assert collector.complete
    assert [row["sub_game_number"] for row in collector.series()] == [1, 2, 3, 4, 5, 6]


def test_an_incomplete_series_cannot_settle_and_says_what_is_missing() -> None:
    collector = SeriesRowCollector()
    for row in played()[:4]:
        collector.record(row)
    assert not collector.complete
    with pytest.raises(StaleMessageError, match=r"sub-games \[5, 6\]"):
        collector.series()


def test_a_sub_game_settles_once_and_is_never_overwritten() -> None:
    """A late or duplicated report must not change a digest already agreed."""
    collector = SeriesRowCollector()
    collector.record(played()[0])
    with pytest.raises(StaleMessageError, match="settles once"):
        collector.record(played()[0])


def test_a_row_missing_a_member_settles_nothing() -> None:
    collector = SeriesRowCollector()
    incomplete = {key: value for key, value in played()[0].items() if key != "score"}
    with pytest.raises(StaleMessageError, match="missing"):
        collector.record(incomplete)


@pytest.mark.parametrize("number", [0, 7, -1])
def test_a_row_outside_the_series_is_refused(number: int) -> None:
    collector = SeriesRowCollector()
    with pytest.raises(StaleMessageError, match="outside"):
        collector.record({**played()[0], "sub_game_number": number})


@pytest.mark.skipif(not PRESERVED.exists(), reason="the preserved settlement is not on this host")
def test_the_scope_is_byte_identical_to_the_one_that_was_settled() -> None:
    built = consensus_scope(GAME_ID, played(), OURS, THEIRS)
    assert built == json.loads(PRESERVED.read_text(encoding="utf-8"))
