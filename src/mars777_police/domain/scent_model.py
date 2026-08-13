"""The whole scent model two peers must agree on before a series is played.

SCENT-003 does not ask for a parameter list. It asks the two groups to exchange
the **full emission and decay model together with a concrete numeric example**,
verify that they interpret it identically, and only then lock the agreement
(SCENT-001, E-23). The three Appendix-F scalars cannot carry that: they fix the
centre, the decay and the window, and say nothing about the 25 weights or about
what happens when a re-emission would push the state past its bound - and two
peers who disagree on either would compute different environments while both
believing they follow the source.

So the agreement is this value, and it carries four things:

* **`model_id`** - the interpretation, named. `BOUNDED_SATURATING_RADIAL_V1` is
  PROJECT-CONTRACT: it means the 5x5 radial emission, the Appendix-F centre and
  decay, the C-10 bounded recurrence, `Decimal` arithmetic, and one systemic
  decay per completed full turn.
* **`kernel`** - all 25 weights, validated by the existing `ScentKernel` and by
  nothing new.
* **`params`** - the three Appendix-F FIXED values, through the existing
  `ScentParams` that already refuses anything else.
* **`examples`** - the concrete numbers, as **data**. They are part of the
  agreed core, so changing an expected value changes the model digest; and they
  are executed against the real recurrence rather than believed, because an
  example that contradicts the physics would agree two peers on a fiction.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Final

from .config_model import InvalidScentError, ScentParams, require_decimal
from .scent_kernel import ScentKernel

BOUNDED_SATURATING_RADIAL_V1: Final[str] = "BOUNDED_SATURATING_RADIAL_V1"
"""The one interpretation this project offers. PROJECT-CONTRACT, not Appendix-F.

It names the whole reading: a 5x5 radial emission kernel, centre 0.9, decay
0.10, the C-10 bounded/saturating recurrence
`min(0.9, max(0, (1-rho)*tau + delta))`, canonical `Decimal` arithmetic, and one
systemic decay per completed full turn."""


@dataclass(frozen=True, slots=True)
class ScentExample:
    """One worked number from the agreement: before, deposit, and the result."""

    tau_before: Decimal
    delta: Decimal
    expected: Decimal

    def __post_init__(self) -> None:
        for name, value in (
            ("tau_before", self.tau_before),
            ("delta", self.delta),
            ("expected", self.expected),
        ):
            number = require_decimal(value, f"example {name}")
            if number < 0:
                raise InvalidScentError(f"example {name} must be >= 0, got {number}")


@dataclass(frozen=True, slots=True)
class ScentModelAgreement:
    """The complete model, as the two peers exchange and then lock it."""

    model_id: str
    kernel: ScentKernel
    params: ScentParams
    examples: tuple[ScentExample, ...]

    def __post_init__(self) -> None:
        if self.model_id != BOUNDED_SATURATING_RADIAL_V1:
            raise InvalidScentError(
                f"model_id must be {BOUNDED_SATURATING_RADIAL_V1!r}, got {self.model_id!r}",
            )
        if not isinstance(self.kernel, ScentKernel):
            raise InvalidScentError(
                f"kernel must be a ScentKernel, got {type(self.kernel).__name__}",
            )
        if not isinstance(self.params, ScentParams):
            raise InvalidScentError(
                f"params must be ScentParams, got {type(self.params).__name__}",
            )
        if type(self.examples) is not tuple or not self.examples:
            raise InvalidScentError("an agreement carries at least one worked example")
        for example in self.examples:
            if not isinstance(example, ScentExample):
                raise InvalidScentError(
                    f"an example must be a ScentExample, got {type(example).__name__}",
                )

    @property
    def center_intensity(self) -> Decimal:
        """The Appendix-F centre, through the params that already fix it."""
        return self.params.center_intensity

    @property
    def decay_rate(self) -> Decimal:
        """The Appendix-F decay, through the params that already fix it."""
        return self.params.decay

    @property
    def field_size(self) -> int:
        """The Appendix-F window, through the params that already fix it."""
        return self.params.field_size
