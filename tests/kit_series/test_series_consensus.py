"""The digest two teams settle a series on, anchored to one a real peer accepted.

This is the last exchange of a counted series and the one rule 35 scores: a
series with no agreed result is **0 for both groups**. It is also the exchange
where two conformant implementations most easily produce different bytes for the
same facts, because "canonical JSON" names two different forms and the wrong one
can never match.

The anchor is not synthetic. `EXPECTED` is the digest a real opponent accepted in
a live settlement, and `ROWS` are that series' own six rows.
"""

import json

import pytest

from mars777_police.app.protocol_errors import LocalDefectError
from mars777_police.app.series_consensus import (
    AGGREGATE_KEYS,
    CLAIM,
    ROW_KEYS,
    agrees,
    consensus_bytes,
    consensus_scope,
    consensus_sha256,
    settlement_envelope,
)

OURS = "MaRs-777"
THEIRS = "sparring-s82kma9e"
GAME_ID = "MaRs-777-vs-sparring-s82kma9e"
EXPECTED = "33f1b2032e8ce87e8bd99de82aac5ebb29943571e2ae583ce4ee2d22f2eeaf1c"
"""The digest a real peer accepted. Reproduced, never adjusted to fit."""


def rows() -> list[dict[str, object]]:
    """The six rows of that settled series: we lost every one, 30 to 90."""
    return [
        {
            "sub_game_number": n,
            "roles": (
                {OURS: "police", THEIRS: "thief"} if n % 2 else {OURS: "thief", THEIRS: "police"}
            ),
            "result": "survival" if n % 2 else "capture",
            "score": {OURS: 5, THEIRS: 10 if n % 2 else 20},
        }
        for n in range(1, 7)
    ]


def scope() -> dict[str, object]:
    return consensus_scope(GAME_ID, rows(), OURS, THEIRS)


def test_the_digest_a_real_peer_accepted_is_reproduced() -> None:
    assert consensus_sha256(scope()) == EXPECTED


def test_the_scope_is_the_three_agreed_members() -> None:
    assert set(scope()) == {"game_id", "aggregate", "sub_games"}


def test_the_aggregate_carries_exactly_five_keys() -> None:
    aggregate = scope()["aggregate"]
    assert isinstance(aggregate, dict)
    assert tuple(aggregate) == AGGREGATE_KEYS


def test_each_row_carries_exactly_five_keys_and_never_tie() -> None:
    """`tie` is derivable from `winner_group` and already counted in the aggregate."""
    games = scope()["sub_games"]
    assert isinstance(games, list)
    for row in games:
        assert tuple(row) == ROW_KEYS
        assert "tie" not in row


def test_the_standing_is_derived_rather_than_asserted() -> None:
    aggregate = scope()["aggregate"]
    assert isinstance(aggregate, dict)
    assert aggregate["total_score"] == {OURS: 30, THEIRS: 90}
    assert aggregate["sub_games_won"] == {OURS: 0, THEIRS: 6}
    assert aggregate["winner_group"] == THEIRS
    assert aggregate["series_tie"] is False
    assert aggregate["ties"] == 0


def test_the_spaced_canonical_form_is_the_one_that_is_hashed() -> None:
    """The compact commitment codec agrees with nobody here, and looks fine doing it."""
    spaced = consensus_bytes(scope())
    compact = json.dumps(scope(), sort_keys=True, separators=(",", ":")).encode()
    assert spaced != compact
    assert b'", "' in spaced
    assert consensus_sha256(scope()) == EXPECTED


def test_a_tied_series_awards_both_sides_the_tie_score() -> None:
    """`total_score` is computed, so it can legitimately exceed the row sums."""
    drawn = [
        {
            "sub_game_number": n,
            "roles": {OURS: "police", THEIRS: "thief"},
            "result": "timeout",
            "score": {OURS: 5, THEIRS: 5},
        }
        for n in range(1, 7)
    ]
    aggregate = consensus_scope(GAME_ID, drawn, OURS, THEIRS)["aggregate"]
    assert isinstance(aggregate, dict)
    assert aggregate["series_tie"] is True
    assert aggregate["winner_group"] is None
    assert aggregate["ties"] == 6
    assert aggregate["total_score"] == {OURS: 32, THEIRS: 32}


def test_both_sides_of_one_series_derive_the_same_digest() -> None:
    """Symmetric by construction: neither side's own view enters the bytes."""
    mirrored = [
        {**row, "roles": dict(row["roles"]), "score": dict(row["score"])}  # type: ignore[dict-item]
        for row in rows()
    ]
    assert consensus_sha256(consensus_scope(GAME_ID, mirrored, THEIRS, OURS)) == EXPECTED


@pytest.mark.parametrize(
    "broken",
    [[], "five", "seven", "gap"],
    ids=["none", "five rows", "seven rows", "a missing sub-game"],
)
def test_a_series_that_is_not_six_sub_games_cannot_settle(broken: object) -> None:
    six = rows()
    supplied = {
        "five": six[:5],
        "seven": [*six, six[-1]],
        "gap": [*six[:5], {**six[5], "sub_game_number": 8}],
    }.get(str(broken), [])
    with pytest.raises(LocalDefectError):
        consensus_scope(GAME_ID, supplied, OURS, THEIRS)


def test_a_series_needs_two_distinct_groups() -> None:
    with pytest.raises(LocalDefectError, match="two distinct groups"):
        consensus_scope(GAME_ID, rows(), OURS, OURS)


def test_the_envelope_is_the_four_members_the_peer_reads() -> None:
    envelope = settlement_envelope("thief", EXPECTED)
    assert envelope == {
        "sender": "thief",
        "result_claim": CLAIM,
        "records": [],
        "consensus_sha": EXPECTED,
    }


def test_a_matching_envelope_from_the_other_side_agrees() -> None:
    assert agrees(settlement_envelope("police", EXPECTED), "police", EXPECTED)


@pytest.mark.parametrize(
    "envelope",
    [
        {"sender": "thief", "result_claim": CLAIM, "records": [], "consensus_sha": EXPECTED},
        {"sender": "police", "result_claim": CLAIM, "records": [], "consensus_sha": "b" * 64},
        {"sender": "police", "result_claim": "survival", "records": [], "consensus_sha": EXPECTED},
        {"sender": "police", "result_claim": CLAIM, "records": [{}], "consensus_sha": EXPECTED},
        {},
    ],
    ids=["our own side", "a different digest", "a sub-game claim", "carrying records", "empty"],
)
def test_anything_that_is_not_their_matching_settlement_is_refused(
    envelope: dict[str, object],
) -> None:
    """Every member is checked: a digest alone would settle on the wrong message."""
    assert not agrees(envelope, "police", EXPECTED)
