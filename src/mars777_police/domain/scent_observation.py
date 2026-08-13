"""Rendering an emission from a source, and folding observed emissions into a field.

Two operations, both of them thin on purpose: the physics belongs to
`domain.scent` and this module must never restate it (`PRD01-FR-041`, SCENT-002).

* `emission_of` asks the frozen model what one source deposits, by evolving an
  **empty** field with exactly that source. A zero field decays to zero, so what
  comes back is the deposit map itself, already clipped to the board and already
  saturated by the C-10 bound - the same numbers the emitter's own field would
  have received.
* `absorbed` is the receiver's half: it advances the field it keeps for the
  **opponent** by one full turn using the emission it was told, through the same
  single recurrence.

The full-turn boundary is the caller's: Ch 4 decays the environment once a turn
has been completed by both actors, so this module is called once per turn with
the emission that turn produced, and never once per half-turn.
"""

from decimal import Decimal

from .board import Board, Position
from .config_model import ScentParams
from .scent import ScentField
from .scent_emission import ScentDeposit, ScentEmission
from .scent_kernel import ScentKernel


def emission_of(
    board: Board, kernel: ScentKernel, source: Position, params: ScentParams
) -> ScentEmission:
    """The canonical contribution *source* makes under the locked model."""
    field = ScentField.zero(board).evolve(kernel, (source,), params)
    deposits = []
    for row in range(board.rows):
        for col in range(board.cols):
            cell = Position(row + board.start_index, col + board.start_index)
            intensity = field.at(cell)
            if intensity > 0:
                deposits.append(ScentDeposit(cell, intensity))
    return ScentEmission(tuple(deposits))


def absorbed(field: ScentField, emission: ScentEmission, params: ScentParams) -> ScentField:
    """The opponent's field after one whole turn: decay, then what it deposited."""
    deposits: dict[tuple[int, int], Decimal] = {
        field.index_of(one.cell): one.intensity for one in emission.deposits
    }
    return field.absorb(deposits, params)


def observed_field(
    board: Board, emissions: tuple[ScentEmission, ...], params: ScentParams
) -> ScentField:
    """Replay one side's observed **opponent** emissions into the field they imply.

    *emissions* is chronological and holds exactly **one opponent emission per
    completed full turn** - never one per half-turn, and never the two agents'
    emissions mixed into a single field. Each role keeps its own history of what
    the *other* side emitted, so `N` records mean exactly `N` full-turn
    transitions and the fold below cannot silently become a half-turn update.

    A fold rather than a stored, mutated field: the emissions are retained
    evidence anyway, so the field an observer holds is derived from them and two
    observers of the same history cannot end up with different environments.
    """
    field = ScentField.zero(board)
    for emission in emissions:
        field = absorbed(field, emission, params)
    return field
