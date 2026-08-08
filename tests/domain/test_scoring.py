"""Unit tests for the role-keyed scoring table.

App F Table 17 (FIXED): capture 20/5, survival 5/10, tie 2 each.
`technical_loss` 0/0 is binding through Ch 3 Table 2 + App E #48 and conflict
**C-07** — it is deliberately NOT an Appendix-F row. `diversity_reward` (10)
is league scope and must never enter sub-game scoring.
"""

import dataclasses

import pytest

from mars777_police.domain import scoring
from mars777_police.domain.scoring import (
    CAPTURE_SCORE,
    SURVIVAL_SCORE,
    TECHNICAL_LOSS_SCORE,
    TIE_SCORE,
    ScoreLine,
    score_for,
)
from mars777_police.domain.terminal import Outcome


def test_capture_scores() -> None:
    assert CAPTURE_SCORE.cop == 20
    assert CAPTURE_SCORE.thief == 5


def test_survival_scores() -> None:
    assert SURVIVAL_SCORE.cop == 5
    assert SURVIVAL_SCORE.thief == 10


def test_technical_loss_is_zero_to_both() -> None:
    assert TECHNICAL_LOSS_SCORE.cop == 0
    assert TECHNICAL_LOSS_SCORE.thief == 0


def test_tie_is_two_each() -> None:
    assert TIE_SCORE.cop == 2
    assert TIE_SCORE.thief == 2


@pytest.mark.parametrize(
    ("outcome", "expected"),
    [
        (Outcome.CAPTURE, CAPTURE_SCORE),
        (Outcome.SURVIVAL, SURVIVAL_SCORE),
        (Outcome.TECHNICAL_LOSS, TECHNICAL_LOSS_SCORE),
    ],
)
def test_score_for_maps_every_sub_game_outcome(outcome: Outcome, expected: ScoreLine) -> None:
    assert score_for(outcome) == expected


def test_score_for_covers_the_whole_outcome_vocabulary() -> None:
    for outcome in Outcome:
        assert isinstance(score_for(outcome), ScoreLine)


def test_score_for_rejects_a_non_outcome() -> None:
    with pytest.raises(KeyError):
        score_for("CAPTURE")  # type: ignore[arg-type]


def test_roles_cannot_be_silently_reversed() -> None:
    # Values are addressed by role name, never by tuple position.
    assert ScoreLine(cop=20, thief=5) != ScoreLine(cop=5, thief=20)
    assert ScoreLine(cop=5, thief=20) != CAPTURE_SCORE
    assert ScoreLine(cop=10, thief=5) != SURVIVAL_SCORE
    names = tuple(f.name for f in dataclasses.fields(ScoreLine))
    assert names == ("cop", "thief")


def test_score_line_is_immutable_and_hashable() -> None:
    with pytest.raises(dataclasses.FrozenInstanceError):
        CAPTURE_SCORE.cop = 99  # type: ignore[misc]
    assert len({ScoreLine(cop=2, thief=2), TIE_SCORE}) == 1


def test_tie_is_not_a_sub_game_outcome() -> None:
    # App F T17 #5 scopes tie to a tied CUMULATIVE score against an opponent;
    # Ch 3 Table 2 has no tie end-event, so no sub-game outcome maps to it.
    assert "TIE" not in {o.value for o in Outcome}
    assert TIE_SCORE not in {score_for(o) for o in Outcome}


def test_diversity_reward_is_absent_from_sub_game_scoring() -> None:
    exported = set(dir(scoring))
    assert "diversity_reward" not in exported
    assert "DIVERSITY_REWARD" not in exported
    assert not any("diversity" in name.lower() for name in exported)


def test_no_appendix_f_provenance_is_claimed_for_technical_loss() -> None:
    doc = scoring.__doc__ or ""
    assert "C-07" in doc
    assert "Table 2" in doc or "Ch 3" in doc


def test_scores_are_integers_not_floats() -> None:
    for line in (CAPTURE_SCORE, SURVIVAL_SCORE, TECHNICAL_LOSS_SCORE, TIE_SCORE):
        assert isinstance(line.cop, int) and not isinstance(line.cop, bool)
        assert isinstance(line.thief, int) and not isinstance(line.thief, bool)
