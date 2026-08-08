"""The agreed 5x5 scent emission kernel and its radial contract.

Ch 4 p.43 and Figure 4 describe the emission field only as a radial fall-off
from the emitting cell, and App F Table 16 locks just the centre (0.9) and the
window (5x5). The 25 weights are therefore **agreed**, not locked, so this
module validates a proposed kernel against the source description instead of
hard-coding the illustrative figure:

* the centre is exactly 0.9;
* weights are finite and non-negative;
* cells at the same **integer squared radius** carry the same intensity;
* a farther ring is never stronger than a nearer one (non-increasing, since
  the source fixes no particular curve).

Integer squared radius only - no sqrt and no floating-point geometry. Split
from ``domain.scent`` to honour the <=150-line rule (PRD-01 §27); same layer,
same inward dependency direction, same responsibility.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal
from typing import Final

from .config_model import (
    FIXED_CENTER_INTENSITY,
    FIXED_FIELD_SIZE,
    InvalidScentError,
    require_decimal,
)

HALF: Final[int] = FIXED_FIELD_SIZE // 2


@dataclass(frozen=True, slots=True)
class ScentKernel:
    """An agreed 5x5 emission kernel validated against the locked constraints."""

    weights: tuple[tuple[Decimal, ...], ...]

    @classmethod
    def from_rows(cls, rows: Sequence[Sequence[object]]) -> "ScentKernel":
        """Build a kernel from rows of decimal strings or Decimals."""
        if isinstance(rows, str) or not isinstance(rows, Sequence):
            raise InvalidScentError("kernel must be a sequence of rows")
        if len(rows) != FIXED_FIELD_SIZE:
            raise InvalidScentError(f"kernel must have {FIXED_FIELD_SIZE} rows")
        built = []
        for row in rows:
            if isinstance(row, str) or not isinstance(row, Sequence):
                raise InvalidScentError("kernel row must be a sequence")
            if len(row) != FIXED_FIELD_SIZE:
                raise InvalidScentError(f"kernel rows need {FIXED_FIELD_SIZE} weights")
            built.append(tuple(_weight(value) for value in row))
        kernel = cls(weights=tuple(built))
        if kernel.center != FIXED_CENTER_INTENSITY:
            raise InvalidScentError(f"kernel centre must be {FIXED_CENTER_INTENSITY}")
        kernel._require_radial()
        return kernel

    def _require_radial(self) -> None:
        """Enforce the radial fall-off the source describes for the emission field.

        Integer squared radius only - no sqrt, no floating-point geometry.
        Equal radius means equal intensity, and a farther ring is never
        stronger than a nearer one. Equality between adjacent rings is allowed:
        the source fixes no particular curve.
        """
        rings: dict[int, Decimal] = {}
        for d_row in range(-HALF, HALF + 1):
            for d_col in range(-HALF, HALF + 1):
                radius = d_row * d_row + d_col * d_col
                weight = self.weight_at(d_row, d_col)
                seen = rings.setdefault(radius, weight)
                if seen != weight:
                    raise InvalidScentError(
                        f"cells at squared radius {radius} must share one intensity",
                    )
        previous: Decimal | None = None
        for radius in sorted(rings):
            weight = rings[radius]
            if previous is not None and weight > previous:
                raise InvalidScentError(
                    f"squared radius {radius} is stronger than a nearer ring",
                )
            previous = weight

    @property
    def center(self) -> Decimal:
        """Return the weight deposited on the emitting cell."""
        return self.weights[HALF][HALF]

    def weight_at(self, d_row: int, d_col: int) -> Decimal:
        """Return the weight at an offset from the emitting cell (-2..+2)."""
        if abs(d_row) > HALF or abs(d_col) > HALF:
            raise InvalidScentError(f"offset ({d_row},{d_col}) is outside the kernel")
        return self.weights[d_row + HALF][d_col + HALF]


def _weight(value: object) -> Decimal:
    weight = require_decimal(value, "kernel weight", allow_str=True)
    if weight < 0:
        raise InvalidScentError("kernel weights must be non-negative")
    return weight
