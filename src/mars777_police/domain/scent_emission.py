"""One turn's scent contribution, as a value that carries no position of its own.

Ch 4 has both agents emit scent around themselves and each agent read the
**opponent's** map, and combine it with what the opponent said. In a refereed
simulator that is free - one process holds the world. Two isolated peers hold no
shared world at all, so the observation has to travel, and this is what travels
(C-14, JDEC-017).

**It is the field contribution, not its source.** There is no centre member, no
source cell and no role: what the receiver gets is the deterministic emission
the locked model produces, clipped to the board. The centre is *inferable* from
a full 5x5 window - the book gives the opponent's map on purpose, and an
observation you can reason about is the point - but nothing here is a truth
claim about where anybody is, and no field of this type is the opponent's
position.

**Canonical or refused.** The cells are ordered by `(row, col)`, unique, on the
board and strictly positive. A representation that is merely equivalent is not
accepted: the final audit re-renders the emission from the disclosed trajectory
and compares it exactly, so two spellings of one emission would be two answers
to one question.
"""

from dataclasses import dataclass
from decimal import Decimal

from .board import Position
from .config_model import InvalidScentError


@dataclass(frozen=True, slots=True)
class ScentDeposit:
    """One cell of an emission, and how much scent it receives."""

    cell: Position
    intensity: Decimal

    def __post_init__(self) -> None:
        if not isinstance(self.cell, Position):
            raise InvalidScentError(
                f"a deposit needs a Position, got {type(self.cell).__name__}",
            )
        if not isinstance(self.intensity, Decimal) or not self.intensity.is_finite():
            raise InvalidScentError("a deposit intensity must be a finite Decimal")
        if self.intensity <= 0:
            raise InvalidScentError(f"a deposit carries a positive intensity, got {self.intensity}")

    @property
    def order(self) -> tuple[int, int]:
        """The canonical sort key: row first, then column."""
        return (self.cell.row, self.cell.col)


@dataclass(frozen=True, slots=True)
class ScentEmission:
    """The whole contribution one action makes to the emitter's scent field."""

    deposits: tuple[ScentDeposit, ...] = ()

    def __post_init__(self) -> None:
        if type(self.deposits) is not tuple:
            raise InvalidScentError(
                f"deposits must be a tuple, got {type(self.deposits).__name__}",
            )
        seen: list[tuple[int, int]] = []
        for deposit in self.deposits:
            if not isinstance(deposit, ScentDeposit):
                raise InvalidScentError(
                    f"a deposit must be a ScentDeposit, got {type(deposit).__name__}",
                )
            if seen and deposit.order <= seen[-1]:
                raise InvalidScentError(
                    f"deposits must be ordered by (row, col) and unique, got {deposit.order}"
                    f" after {seen[-1]}",
                )
            seen.append(deposit.order)

    @property
    def cells(self) -> tuple[Position, ...]:
        """The cells this emission touches, in the one canonical order."""
        return tuple(deposit.cell for deposit in self.deposits)

    def at(self, cell: Position) -> Decimal:
        """What this emission deposits on *cell* - zero where it deposits nothing."""
        for deposit in self.deposits:
            if deposit.cell == cell:
                return deposit.intensity
        return Decimal(0)
