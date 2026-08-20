"""What the series document says, and what it refuses to say.

A friendly run has to be readable as a friendly run. These pin the two things it
declares **absent** - counted authentication and mutual result agreement - and
the things it will not invent: a group total, a winner, an agreement, or a sixth
sub-game that was never played.
"""

import pytest
from r16_builders import GAME_ID, GAME_UID, GROUP_A, GROUP_B

from mars777_police.app.friendly_evidence import (
    series_document,
    sub_game_document,
)
from mars777_police.app.friendly_evidence_values import (
    FriendlySeriesEvidence,
    FriendlySubGameEvidence,
)
from mars777_police.app.kit_messages import KitRole
from mars777_police.app.protocol_errors import LocalDefectError
from mars777_police.app.run_class import RunClassification
from mars777_police.domain.terminal import Outcome

SCHEDULE = (
    KitRole.POLICE,
    KitRole.THIEF,
    KitRole.POLICE,
    KitRole.THIEF,
    KitRole.POLICE,
    KitRole.THIEF,
)


def row(number: int) -> FriendlySubGameEvidence:
    return FriendlySubGameEvidence(
        sub_game=number,
        role=SCHEDULE[number - 1],
        outcome=Outcome.SURVIVAL,
        steps=34 + number % 2,
        our_commits=tuple(f"{number:02d}{index:062d}" for index in range(2)),
        peer_chain_verified=True,
        peer_result_claim="survival",
        peer_records=35,
        semantic_statuses=(("scent_truthfulness", "NOT_CHECKABLE"),),
    )


def evidence(rows: int = 6) -> FriendlySeriesEvidence:
    return FriendlySeriesEvidence(
        classification=RunClassification.friendly(kit_terms_agreement=True),
        game_id=GAME_ID,
        game_uid=GAME_UID,
        our_group=GROUP_A,
        peer_group=GROUP_B,
        schedule=SCHEDULE,
        rows=tuple(row(number) for number in range(1, rows + 1)),
    )


def test_the_series_document_says_which_two_things_are_absent() -> None:
    """The two facts a KIT friendly can never establish, named rather than omitted."""
    document = series_document(evidence())

    assert document["keyed_step0_authentication"] == "ABSENT"
    assert document["mutual_result_agreement"] == "ABSENT"
    assert document["evidence_class"] == "DEVELOPMENT_EVIDENCE"
    assert document["counted_eligible"] is False


def test_no_agreement_is_fabricated_anywhere_in_the_evidence() -> None:
    """`mutual_agreement` and `result_sha256` are the counted result's, not ours."""
    rendered = repr(series_document(evidence())) + repr(sub_game_document(row(1)))

    assert "mutual_agreement" not in rendered
    assert "result_sha256" not in rendered
    assert "peer_approved" not in rendered


def test_no_authentication_is_fabricated_anywhere_in_the_evidence() -> None:
    rendered = repr(series_document(evidence()))

    assert "step0_authenticated" not in rendered
    assert "auth_proof" not in rendered


def test_one_series_identity_across_all_six_rows() -> None:
    document = series_document(evidence())

    assert document["game_id"] == GAME_ID
    assert document["game_uid"] == GAME_UID
    assert document["group_id"] == GROUP_A
    assert document["opponent_group_id"] == GROUP_B
    assert len(document["sub_games"]) == 6


def test_the_six_role_contributions_merge_into_one_series_not_two() -> None:
    """Police and Thief are role contributors to one group series."""
    document = series_document(evidence())
    rows = document["sub_games"]

    assert [one["role"] for one in rows] == [one.value for one in SCHEDULE]
    assert sorted(one["sub_game"] for one in rows) == [1, 2, 3, 4, 5, 6]
    assert document["series_convention"] == "REFERENCE_ODD_EVEN_ALTERNATION"


def test_a_series_that_did_not_play_six_is_refused_rather_than_padded() -> None:
    with pytest.raises(LocalDefectError):
        series_document(evidence(rows=5))


def test_the_scores_come_from_the_one_existing_scoring_authority() -> None:
    """No second result engine: `outcome_line` and `cumulative_of`, unchanged."""
    document = series_document(evidence())

    assert document["sub_games"][0]["cop_score"] == 5
    assert document["sub_games"][0]["thief_score"] == 10
    assert document["role_totals"] == {"cop": 30, "thief": 60}


def test_no_group_total_or_winner_is_invented_for_an_alternating_series() -> None:
    """The counted result defines role totals; a group total under alternation is
    a number no contract fixes, so none is published."""
    document = series_document(evidence())

    assert "winner_group" not in document
    assert "group_total" not in document
    assert "diversity_reward" not in document


def test_a_not_checkable_status_is_carried_through_unchanged() -> None:
    document = sub_game_document(row(1))

    assert document["semantic_statuses"] == {"scent_truthfulness": "NOT_CHECKABLE"}
