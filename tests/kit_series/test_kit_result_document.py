"""The result artifact: the one file that must never be produced optimistically.

Rule 35 scores a series with no agreed result 0 for both groups, so every path
that would write one without a matching bidirectional digest is refused here.
The other property these pin is arithmetic that is easy to get quietly wrong:
`cumulative` counts role totals, which is a different axis from the per-group
standing the consensus aggregate carries.
"""

from typing import Any

import pytest

from mars777_police.app.kit_messages import KitRole
from mars777_police.app.kit_result_document import kit_result_document
from mars777_police.app.kit_settled_row import settled_row
from mars777_police.app.protocol_errors import LocalDefectError
from mars777_police.domain.scoring import score_for
from mars777_police.domain.terminal import Outcome

OURS, THEIRS = "MaRs-777", "s82kma9e"
GAME_ID = f"{OURS}-vs-{THEIRS}"
GAME_UID = "43994252-2e4d-2b5c-9baa-4bf7aef5b5d6"
DIGEST = "9b0e173a79212271dea3f3b546591d7f93fe476ef7e7572aca34f8e88bccc142"


def rows(count: int = 6) -> list[dict[str, Any]]:
    """The rerun-9 shape: we alternate, the thief wins every sub-game."""
    return [
        settled_row(
            sub_game=n,
            ours=OURS,
            theirs=THEIRS,
            our_role=KitRole.POLICE if n % 2 else KitRole.THIEF,
            outcome=Outcome.SURVIVAL,
        )
        for n in range(1, count + 1)
    ]


def document(**changes: Any) -> dict[str, Any]:
    members: dict[str, Any] = {
        "game_id": GAME_ID,
        "game_uid": GAME_UID,
        "rows": rows(),
        "participants": [THEIRS, OURS],
        "github_links": {OURS: "https://example.invalid/mars"},
        "total_tokens": {OURS: 1200, THEIRS: 1300},
        "timestamp": "2026-08-23T18:45:00Z",
        "consensus_sha256": DIGEST,
        "peer_consensus_sha256": DIGEST,
        **changes,
    }
    return dict(kit_result_document(**members))


def test_a_matching_digest_produces_the_result() -> None:
    made = document()
    assert made["series_consensus_sha256"] == DIGEST
    assert made["declaration_ref"] == f"declaration_{GAME_ID}.json"


def test_a_series_the_peer_never_settled_is_refused() -> None:
    """No agreed result means rule 35 scores it 0; a file would assert otherwise."""
    with pytest.raises(LocalDefectError, match="waits for the peer's matching consensus"):
        document(peer_consensus_sha256=None)


def test_a_digest_the_peer_disagrees_with_is_refused() -> None:
    with pytest.raises(LocalDefectError, match="agreed on nothing"):
        document(peer_consensus_sha256="f" * 64)


def test_a_series_short_of_six_rows_is_refused() -> None:
    with pytest.raises(LocalDefectError, match="covers 6 settled rows"):
        document(rows=rows(5))


def test_cumulative_counts_role_totals_not_group_totals() -> None:
    """The axis that is easy to get quietly wrong.

    Every sub-game here is a survival: the thief scores 10 and the cop 5, six
    times, whichever group held which side. Group totals would read 45/45; role
    totals read 30/60, and only the second is what `cumulative` means.
    """
    cumulative = document()["cumulative"]
    assert cumulative["cop_total"] == 30
    assert cumulative["thief_total"] == 60
    assert cumulative["series_outcome"] == "thief"


def test_the_totals_are_the_domain_scoring_summed_over_the_six_rows() -> None:
    """Derived from `score_for`, never from a number written into the test."""
    outcomes = [Outcome.SURVIVAL if n % 2 else Outcome.CAPTURE for n in range(1, 7)]
    mixed = [
        settled_row(
            sub_game=n,
            ours=OURS,
            theirs=THEIRS,
            our_role=KitRole.POLICE if n % 2 else KitRole.THIEF,
            outcome=outcome,
        )
        for n, outcome in enumerate(outcomes, start=1)
    ]
    expected_cop = sum(score_for(outcome).cop for outcome in outcomes)
    expected_thief = sum(score_for(outcome).thief for outcome in outcomes)
    cumulative = document(rows=mixed)["cumulative"]
    assert cumulative["cop_total"] == expected_cop
    assert cumulative["thief_total"] == expected_thief


def test_equal_totals_report_a_tie_rather_than_a_side() -> None:
    """The label follows the comparison; no side is invented when they match."""
    made = kit_result_document(
        game_id=GAME_ID,
        game_uid=GAME_UID,
        rows=rows(),
        participants=[OURS, THEIRS],
        github_links={},
        total_tokens={},
        timestamp="2026-08-23T18:45:00Z",
        consensus_sha256=DIGEST,
        peer_consensus_sha256=DIGEST,
    )
    cumulative = made["cumulative"]
    assert isinstance(cumulative, dict)
    if cumulative["cop_total"] == cumulative["thief_total"]:
        assert cumulative["series_outcome"] == "tie"
    else:
        higher = "cop" if cumulative["cop_total"] > cumulative["thief_total"] else "thief"
        assert cumulative["series_outcome"] == higher


def test_the_rows_are_written_in_sub_game_order() -> None:
    """Contributed by two processes in whatever order they finished."""
    shuffled = list(reversed(rows()))
    numbers = [row["sub_game_number"] for row in document(rows=shuffled)["sub_games"]]
    assert numbers == [1, 2, 3, 4, 5, 6]


def test_both_participants_are_named_in_a_stable_order() -> None:
    """Two teams reading the same series must render the same bytes."""
    assert document()["teams"] == sorted([OURS, THEIRS])
