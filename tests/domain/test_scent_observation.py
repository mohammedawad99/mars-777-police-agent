"""Rendering an emission from a source, and folding observed emissions back.

Every number here comes from the frozen physics: `emission_of` evolves an empty
field with exactly one source, so what it returns is the deposit map the locked
model produces - clipped, saturated and normalised by the same code a local
field uses. Nothing in this module restates the recurrence.
"""

from decimal import Decimal

from test_scent_field import BOARD, CENTRE, CENTRE_ONLY, PARAMS, RADIAL

from mars777_police.domain.board import Board, Position
from mars777_police.domain.scent import MAX_SCENT_STATE, ScentField
from mars777_police.domain.scent_emission import ScentEmission
from mars777_police.domain.scent_observation import absorbed, emission_of, observed_field

CORNER = Position(0, 0)
EDGE = Position(0, 3)


def rendered(source: Position, kernel: object = RADIAL, board: Board = BOARD) -> object:
    """The emission the locked model gives for one source on one board."""
    return emission_of(board, kernel, source, PARAMS)  # type: ignore[arg-type]


def weighted() -> int:
    """How many of the 25 window offsets the agreed kernel actually deposits on.

    Derived from the kernel rather than counted by hand: the 25 weights are
    agreed, not locked, so a kernel whose outer corners are zero deposits on
    fewer cells and the emission carries only the cells it really touches.
    """
    return sum(1 for row in range(-2, 3) for col in range(-2, 3) if RADIAL.weight_at(row, col) > 0)


def test_an_interior_source_deposits_its_whole_weighted_window() -> None:
    emission = rendered(CENTRE)
    assert len(emission.deposits) == weighted()
    assert emission.at(CENTRE) == Decimal("0.9")
    assert all(
        abs(cell.row - CENTRE.row) <= 2 and abs(cell.col - CENTRE.col) <= 2
        for cell in emission.cells
    )


def test_an_edge_source_is_clipped_to_the_board() -> None:
    emission = rendered(EDGE)
    assert 0 < len(emission.deposits) < weighted(), "rows above the edge fall off the board"
    assert all(BOARD.contains(cell) for cell in emission.cells)


def test_a_corner_source_is_clipped_on_both_axes() -> None:
    emission = rendered(CORNER)
    assert len(emission.deposits) < len(rendered(EDGE).deposits) < weighted()
    assert emission.at(CORNER) == Decimal("0.9")
    assert all(BOARD.contains(cell) for cell in emission.cells)


def test_a_centre_only_kernel_deposits_exactly_one_cell() -> None:
    emission = rendered(CENTRE, CENTRE_ONLY)
    assert emission.cells == (CENTRE,)


def test_the_rendered_emission_is_what_the_emitter_s_own_field_would_receive() -> None:
    """The receiver's absorbed field equals the emitter's own evolved field."""
    theirs = ScentField.zero(BOARD).evolve(RADIAL, (CENTRE,), PARAMS)
    ours = absorbed(ScentField.zero(BOARD), rendered(CENTRE), PARAMS)
    assert ours == theirs


def test_absorbing_decays_the_previous_field_exactly_once() -> None:
    first = absorbed(ScentField.zero(BOARD), rendered(CORNER), PARAMS)
    second = absorbed(first, rendered(CENTRE), PARAMS)
    kept = second.at(CORNER)
    assert kept == Decimal("0.9") * (Decimal(1) - PARAMS.decay), "one decay, not two"


def test_n_records_are_exactly_n_full_turn_transitions() -> None:
    """One decay per record - a half-turn reading would decay twice as often."""
    quiet = ScentEmission()
    once = observed_field(BOARD, (rendered(CENTRE), quiet), PARAMS)
    twice = observed_field(BOARD, (rendered(CENTRE), quiet, quiet), PARAMS)
    kept = Decimal("0.9") * (Decimal(1) - PARAMS.decay)
    assert once.at(CENTRE) == kept
    assert twice.at(CENTRE) == kept * (Decimal(1) - PARAMS.decay)


def test_the_first_observation_sees_no_decay_of_an_empty_past() -> None:
    """A zero field decays to zero, so the first fold is the emission itself."""
    first = observed_field(BOARD, (rendered(CENTRE),), PARAMS)
    assert first.at(CENTRE) == Decimal("0.9")
    assert first == absorbed(ScentField.zero(BOARD), rendered(CENTRE), PARAMS)


def test_a_whole_history_folds_into_one_field() -> None:
    history = (rendered(CORNER), rendered(CENTRE))
    folded = observed_field(BOARD, history, PARAMS)
    stepwise = absorbed(absorbed(ScentField.zero(BOARD), history[0], PARAMS), history[1], PARAMS)
    assert folded == stepwise


def test_an_unobserved_sub_game_folds_to_the_empty_field() -> None:
    assert observed_field(BOARD, (), PARAMS) == ScentField.zero(BOARD)


def test_repeated_emission_saturates_at_the_locked_state_bound() -> None:
    field = observed_field(BOARD, (rendered(CENTRE),) * 4, PARAMS)
    assert field.at(CENTRE) == MAX_SCENT_STATE


def test_the_field_index_of_a_cell_is_reachable_for_the_absorbing_caller() -> None:
    assert ScentField.zero(BOARD).index_of(Position(2, 3)) == (2, 3)
