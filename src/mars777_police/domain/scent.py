"""Deterministic scent (pheromone) physics.

SCENT-002 / PRD01-FR-040…043: ``tau(t+1) = max(0, (1 - rho) * tau(t) + delta_tau)``
with App F T16 parameters (0.9 / 0.10 / 5x5, all FIXED, from ``config_model``).
Only the lower clamp is locked, so a re-emission may legitimately exceed 0.9.
The 25 kernel weights are **not** locked - Ch 4 p.43/Figure 4 give only a
radial fall-off - so an agreed kernel is *validated* against that description
(equal squared radius => equal weight; farther ring never stronger) and never
hard-coded from the illustrative figure. Values are ``Decimal`` from strings in a fixed context
(PRD-01 §27 leaves floats-vs-fixed-point open): 0.9 -> 0.81 is exact on every
platform. Field *interpretation* is out of scope.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Context, Decimal, localcontext
from typing import Final

from .board import Board, Position
from .config_model import FIXED_CENTER_INTENSITY, InvalidScentError, ScentParams
from .scent_kernel import HALF, ScentKernel

MAX_SCENT_STATE: Final[Decimal] = FIXED_CENTER_INTENSITY
"""Upper bound of the scent state, 0.9 (Ch 4 §4.3 state domain; conflict C-10).

A source-defined state-domain invariant, deliberately **not** a config field:
it is never negotiated and never written to an official artifact.
"""

SCENT_CONTEXT: Final[Context] = Context(prec=28, rounding=ROUND_HALF_EVEN)
"""Explicit context, so an ambient decimal context cannot change results."""


@dataclass(frozen=True, slots=True)
class ScentField:
    """An immutable dense scent field over the board, stored row-major."""

    rows: int
    cols: int
    start_index: int
    values: tuple[tuple[Decimal, ...], ...]

    def __post_init__(self) -> None:
        for row in self.values:
            for value in row:
                if not isinstance(value, Decimal):
                    raise InvalidScentError(
                        f"scent value must be a Decimal, got {type(value).__name__}",
                    )
                if not value.is_finite():
                    raise InvalidScentError("scent value must be finite")
                if value < 0 or value > MAX_SCENT_STATE:
                    raise InvalidScentError(
                        f"scent value {value} is outside [0, {MAX_SCENT_STATE}]",
                    )

    @classmethod
    def zero(cls, board: Board) -> "ScentField":
        """Return an all-zero field shaped like *board*."""
        if not isinstance(board, Board):
            raise InvalidScentError("board must be a Board")
        row = tuple(Decimal(0) for _ in range(board.cols))
        return cls(board.rows, board.cols, board.start_index, (row,) * board.rows)

    def at(self, position: Position) -> Decimal:
        """Return the intensity at *position*."""
        row, col = self._index(position)
        return self.values[row][col]

    def evolve(
        self,
        kernel: ScentKernel,
        sources: Iterable[Position],
        params: ScentParams,
    ) -> "ScentField":
        """Return the next field: decay, emission, then saturation at both ends.

        ``min(0.9, max(0, (1-rho)*tau + delta))`` - the lower clamp is written
        in the source, the upper one is the C-10 resolution of its explicit
        [0, 0.9] state domain. Below the bound the recurrence stays exactly
        additive. Values are normalised so equal fields share one
        representation (FR-043).
        """
        if not isinstance(kernel, ScentKernel) or not isinstance(params, ScentParams):
            raise InvalidScentError("evolve needs a ScentKernel and ScentParams")
        return self._advance(self._deposits(kernel, sources), params)

    def absorb(self, deposits: dict[tuple[int, int], Decimal], params: ScentParams) -> "ScentField":
        """Return the next field for a deposit map somebody else already rendered.

        The same single step as `evolve`, for the receiver that was *told* the
        emission instead of computing it from a source it is not allowed to
        know. The recurrence lives in `_advance` and exists exactly once, so the
        two entry points cannot drift apart (SCENT-002 / PRD01-FR-040).
        """
        if not isinstance(params, ScentParams):
            raise InvalidScentError("absorbing an emission needs ScentParams")
        return self._advance(deposits, params)

    def _advance(
        self, deposits: dict[tuple[int, int], Decimal], params: ScentParams
    ) -> "ScentField":
        """`min(0.9, max(0, (1-rho)*tau + delta))` - the one recurrence, once."""
        zero = Decimal(0)
        with localcontext(SCENT_CONTEXT):
            retained = Decimal(1) - params.decay
            grid = tuple(
                tuple(
                    min(
                        MAX_SCENT_STATE,
                        max(zero, retained * value + deposits.get((r, c), zero)),
                    ).normalize()
                    for c, value in enumerate(row)
                )
                for r, row in enumerate(self.values)
            )
        return ScentField(self.rows, self.cols, self.start_index, grid)

    def _deposits(
        self,
        kernel: ScentKernel,
        sources: Iterable[Position],
    ) -> dict[tuple[int, int], Decimal]:
        """Sum kernel weights per cell, in canonical source order, clipped to the board."""
        deposits: dict[tuple[int, int], Decimal] = {}
        with localcontext(SCENT_CONTEXT):
            for row, col in sorted(self._index(source) for source in sources):
                for d_row in range(-HALF, HALF + 1):
                    for d_col in range(-HALF, HALF + 1):
                        cell = (row + d_row, col + d_col)
                        if 0 <= cell[0] < self.rows and 0 <= cell[1] < self.cols:
                            current = deposits.get(cell, Decimal(0))
                            deposits[cell] = current + kernel.weight_at(d_row, d_col)
        return deposits

    def index_of(self, position: Position) -> tuple[int, int]:
        """The field-local `(row, col)` of *position*, refusing a cell outside it."""
        return self._index(position)

    def _index(self, position: Position) -> tuple[int, int]:
        if not isinstance(position, Position):
            raise InvalidScentError(f"expected a Position, got {type(position).__name__}")
        row = position.row - self.start_index
        col = position.col - self.start_index
        if not (0 <= row < self.rows and 0 <= col < self.cols):
            raise InvalidScentError(f"cell [{position.row},{position.col}] is outside the field")
        return row, col
