"""Running an agreement's worked examples against the real recurrence.

SCENT-003 wants the exchange to prove *identical interpretation*, and a number
written beside a model proves nothing on its own - a peer could state `0.81` and
implement something else. So an example is executed here through the frozen
`ScentField` physics, on a one-cell field, and compared to what the agreement
claims. An agreement whose own examples contradict the code that will produce
the environment is refused before it can be locked.

The recurrence is not restated: the deposit is handed to `absorb`, which shares
`_advance` with `evolve`, so this checks the same arithmetic a real turn uses.
"""

from decimal import Decimal

from .board import Board, Position
from .config_model import InvalidScentError
from .scent import ScentField
from .scent_model import ScentExample, ScentModelAgreement

ONE_CELL: Board = Board(rows=1, cols=1)
"""The smallest board an example needs: one cell, no geometry to argue about."""

ORIGIN: Position = Position(0, 0)


def outcome_of(example: ScentExample, agreement: ScentModelAgreement) -> Decimal:
    """What the frozen recurrence actually produces for this example."""
    before = ScentField(1, 1, 0, ((example.tau_before,),))
    return before.absorb({(0, 0): example.delta}, agreement.params).at(ORIGIN)


def require_truthful_examples(agreement: ScentModelAgreement) -> None:
    """Refuse an agreement whose stated numbers the physics does not produce."""
    for index, example in enumerate(agreement.examples):
        produced = outcome_of(example, agreement)
        if produced != example.expected:
            raise InvalidScentError(
                f"example {index} claims {example.expected} but the model produces {produced}",
            )
