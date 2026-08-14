"""Mapping one turn's emission between its wire text and its semantic value.

Mapping only. Order, uniqueness, board membership and strict positivity are
`ScentDeposit`/`ScentEmission`'s own rules, so an emission that breaks them never
becomes a value - it becomes this layer's malformed identity, exactly as the
model codec does with a model our physics refuses.

Decimals cross as canonical text through the existing helpers; no `float` is
constructed on either path, and no source cell is carried in either direction.
"""

from ..app.protocol_errors import MalformedMessageError
from ..domain.board import Position
from ..domain.errors import DomainError
from ..domain.scent_emission import ScentDeposit, ScentEmission
from .wire_scalars import decimal_from_text, text_from_decimal
from .wire_scent_turn import ScentDepositWire, ScentEmissionWire


def decode_emission(wire: ScentEmissionWire | None) -> ScentEmission | None:
    """Rebuild the emission, letting the domain refuse anything it must."""
    if wire is None:
        return None
    try:
        return ScentEmission(
            tuple(
                ScentDeposit(_cell(one.cell), decimal_from_text(one.intensity))
                for one in wire.deposits
            )
        )
    except DomainError as failure:
        raise MalformedMessageError(f"scent emission is not valid: {failure}") from None


def _cell(cell: list[int]) -> Position:
    """One `[row, col]` deposit cell, in the frozen coordinate spelling."""
    if len(cell) != 2:
        raise MalformedMessageError("a scent deposit cell must carry exactly [row, col]")
    return Position(cell[0], cell[1])


def encode_emission(emission: ScentEmission) -> ScentEmissionWire:
    """Render the emission; every intensity crosses as canonical decimal text."""
    return ScentEmissionWire(
        deposits=[
            ScentDepositWire(
                cell=[one.cell.row, one.cell.col], intensity=text_from_decimal(one.intensity)
            )
            for one in emission.deposits
        ]
    )
