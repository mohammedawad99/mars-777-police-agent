"""What this side may believe about the opponent, and what it may never know.

Ch 6 §6.4 fixes the epistemic premise: *"neither of them sees the opponent's
real position"*. Scent is the legal partial evidence that premise permits - a
field of intensities this side observed, never a cell the opponent occupies. So
this value carries a **field** and nothing that names a position as truth: there
is no `opponent_position` to read, and no arithmetic here produces one.

**Neutral is a value, not `None`.** A sub-game opens with no evidence at all,
and a strategy that had to branch on `None` before every comparison would grow a
nullable path into every policy. The empty belief answers zero everywhere and
says so.
"""

import dataclasses
from decimal import Decimal

import pytest
from test_scent_field import BOARD, CENTRE, PARAMS, RADIAL

from mars777_police.domain.board import Position
from mars777_police.domain.config_model import InvalidScentError
from mars777_police.domain.scent import ScentField
from mars777_police.domain.scent_belief import ScentBelief
from mars777_police.domain.scent_observation import emission_of, observed_field

ZERO = Decimal("0")


def _field(*sources: Position) -> ScentField:
    """A real observed field, folded by the frozen physics and nothing else."""
    return observed_field(
        BOARD, tuple(emission_of(BOARD, RADIAL, s, PARAMS) for s in sources), PARAMS
    )


def test_the_neutral_belief_answers_zero_everywhere() -> None:
    belief = ScentBelief()

    assert not belief.has_evidence
    for row in range(BOARD.rows):
        for col in range(BOARD.cols):
            assert belief.intensity_at(Position(row, col)) == ZERO


def test_the_neutral_belief_is_shareable_because_it_is_immutable() -> None:
    """A default that could be mutated would leak one turn's belief into another."""
    with pytest.raises(dataclasses.FrozenInstanceError):
        ScentBelief().evidence_count = 3  # type: ignore[misc]


def test_a_belief_built_from_evidence_reports_the_observed_field() -> None:
    belief = ScentBelief(_field(CENTRE), 1)

    assert belief.has_evidence
    assert belief.intensity_at(CENTRE) > ZERO


def test_intensity_is_the_fields_own_number_and_never_recomputed() -> None:
    """The value read is the physics' value - no scaling, rounding or clamping."""
    observed = _field(CENTRE)
    belief = ScentBelief(observed, 1)

    for row in range(BOARD.rows):
        for col in range(BOARD.cols):
            cell = Position(row, col)
            assert belief.intensity_at(cell) == observed.at(cell)


def test_a_cell_off_the_board_is_not_a_belief_question() -> None:
    """Legality is the domain's, not this value's: it answers about real cells."""
    with pytest.raises(InvalidScentError):
        ScentBelief(_field(CENTRE), 1).intensity_at(Position(-1, -1))


def test_the_value_exposes_no_opponent_position() -> None:
    """The structural guard: belief is a field, never a truth cell."""
    forbidden = ("opponent_position", "true_position", "estimated_opponent_position", "target_cell")
    surface = set(dir(ScentBelief)) | set(getattr(ScentBelief, "__slots__", ()))

    assert not [name for name in forbidden if name in surface]


def test_evidence_count_is_how_many_turns_were_folded() -> None:
    assert ScentBelief().evidence_count == 0
    assert ScentBelief(_field(CENTRE), 1).evidence_count == 1
    assert ScentBelief(_field(CENTRE, CENTRE), 2).evidence_count == 2


def test_two_beliefs_over_the_same_evidence_are_equal() -> None:
    """Determinism at the value level: same history, same belief, every run."""
    assert ScentBelief(_field(CENTRE), 1) == ScentBelief(_field(CENTRE), 1)
