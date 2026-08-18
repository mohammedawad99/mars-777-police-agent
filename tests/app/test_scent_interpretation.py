"""Turning the emissions a peer actually sent into a belief a policy may read.

PRD-01 owns the physics and PRD-04 owns the reading of it, so this layer folds
and never computes: `observed_field` is the single accumulated-field authority
and there is no second decay, deposit, saturation or kernel anywhere below.

Three properties matter more than the arithmetic. The fold is **per full turn**,
because Ch 4 decays the environment once both actors have completed a turn and
one row per half-turn would age the field twice as fast. The parameters are the
**series-locked** ones, not the project defaults, so a model the peers agreed is
the model that governs what we believe. And the evidence is **only what already
arrived**: a decision cannot see the emission of the turn it is still deciding.
"""

from decimal import Decimal

import pytest
from belief_builders import BOARD, CENTRE, FAR, PARAMS, row

from mars777_police.app.scent_interpretation import interpret_scent
from mars777_police.app.scent_records import ScentRecord
from mars777_police.app.turn_cursor import TurnCursor
from mars777_police.domain.board import Position
from mars777_police.domain.config_model import ScentParams
from mars777_police.domain.scent_belief import ScentBelief
from mars777_police.domain.scent_observation import observed_field

ZERO = Decimal("0")

# App F T16 makes every `ScentParams` member FIXED - `__post_init__` refuses any
# value but the locked constant - so a "non-default legal model" is not
# constructible. The equivalent guarantee is structural and pinned below: the
# interpreter has no default to fall back to, and the live source carries the
# authenticated model's own parameters through.


def test_no_evidence_yields_the_neutral_belief() -> None:
    belief = interpret_scent(BOARD, (), PARAMS)

    assert belief == ScentBelief()
    assert not belief.has_evidence
    assert belief.intensity_at(CENTRE) == ZERO


def test_the_fold_is_the_existing_domain_authority() -> None:
    """Same answer as `observed_field` - because it *is* `observed_field`."""
    history = (row(1), row(2))
    expected = observed_field(BOARD, tuple(r.emission for r in history), PARAMS)

    belief = interpret_scent(BOARD, history, PARAMS)

    for cell in (CENTRE, FAR, Position(1, 1)):
        assert belief.intensity_at(cell) == expected.at(cell)


def test_one_row_is_one_full_turn_of_decay() -> None:
    """Each row ages the field exactly once - never twice per network event.

    The second emission is deliberately somewhere else, because a source that
    keeps depositing on the same cell saturates at the C-10 bound and would hide
    the decay this test exists to see. Read at the cell the peer has now left,
    one row means one full turn of ageing and no more.
    """
    once = interpret_scent(BOARD, (row(1, CENTRE),), PARAMS)
    twice = interpret_scent(BOARD, (row(1, CENTRE), row(2, FAR)), PARAMS)
    direct = observed_field(BOARD, (row(1, CENTRE).emission, row(2, FAR).emission), PARAMS)

    assert once.evidence_count == 1
    assert twice.evidence_count == 2
    assert twice.intensity_at(CENTRE) == direct.at(CENTRE)
    assert twice.intensity_at(CENTRE) < once.intensity_at(CENTRE)


def test_rows_are_folded_in_step_order_whatever_order_they_arrive_in() -> None:
    """Insertion-order trap: the field is a history, not a set."""
    ordered = interpret_scent(BOARD, (row(1, CENTRE), row(2, FAR)), PARAMS)
    shuffled = interpret_scent(BOARD, (row(2, FAR), row(1, CENTRE)), PARAMS)

    assert ordered == shuffled


def test_the_interpreter_has_no_parameters_of_its_own_to_fall_back_on() -> None:
    """The locked model must be supplied; nothing here may default to one.

    App F T16 fixes every `ScentParams` member, so two peers cannot disagree by
    value - but they could disagree by *provenance* if this layer ever built its
    own. A signature with no default makes that unwriteable rather than unlikely.
    """
    import inspect

    parameter = inspect.signature(interpret_scent).parameters["params"]

    assert parameter.default is inspect.Parameter.empty
    assert parameter.annotation is ScentParams


def test_the_supplied_parameters_are_the_ones_that_govern() -> None:
    """Whatever the caller locked is what folds - never a value read here."""
    history = (row(1), row(2))

    belief = interpret_scent(BOARD, history, PARAMS)

    assert belief.intensity_at(CENTRE) == observed_field(
        BOARD, tuple(r.emission for r in history), PARAMS
    ).at(CENTRE)


def test_interpretation_is_deterministic_across_repeated_calls() -> None:
    history = (row(1), row(2), row(3))

    assert interpret_scent(BOARD, history, PARAMS) == interpret_scent(BOARD, history, PARAMS)


def test_interpretation_reads_no_position_and_no_role_from_the_rows() -> None:
    """A `ScentRecord` carries a cursor and an emission; only the emission folds."""
    same = interpret_scent(BOARD, (ScentRecord(TurnCursor(1, 1), row(1).emission),), PARAMS)
    other = interpret_scent(BOARD, (ScentRecord(TurnCursor(1, 9), row(1).emission),), PARAMS)

    assert same.intensity_at(CENTRE) == other.intensity_at(CENTRE)


@pytest.mark.parametrize("cell", [CENTRE, FAR, Position(2, 3)])
def test_the_physics_output_is_unchanged_by_being_interpreted(cell: Position) -> None:
    """AC-011: interpretation reads the field; it never rewrites a value."""
    history = (row(1), row(2))
    before = observed_field(BOARD, tuple(r.emission for r in history), PARAMS)

    interpret_scent(BOARD, history, PARAMS)
    after = observed_field(BOARD, tuple(r.emission for r in history), PARAMS)

    assert before.at(cell) == after.at(cell)
