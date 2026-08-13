"""The model this project proposes, and the exact standing of every number in it.

**Provenance, stated once and precisely.** The 5x5 window and the 0.9 centre are
Appendix-F Table 16, FIXED. The decay 0.10 is Appendix-F, FIXED. The radial
*shape* is what Ch 4 p.43 describes. The twenty-four **off-centre weights below
are a PROJECT DEFAULT adopted from the illustrative Figure 4** - under the
book's own authority rule a figure is illustrative, so none of them is
SOURCE-MUST, Appendix-F, or lecturer-mandated. They are our proposal, and they
become binding only because both peers exchange, verify and cryptographically
lock this exact model (SCENT-001 / SCENT-003).

The two examples are the concrete numbers SCENT-003 asks the exchange to carry:

* `0.9` decaying with no new deposit gives `0.81` - the source's own recurrence,
  exactly, with no rounding to argue about;
* `0.9` re-emitted onto `0.9` gives `0.9` - the **C-10** reading of the source's
  explicit `[0, 0.9]` state domain. That is the one interpretation two honest
  peers could otherwise differ on, and it is precisely why it travels as data.

Nothing here validates anything itself: `ScentKernel` checks the radial
contract, `ScentParams` checks the three FIXED values, and the examples are run
against the real `ScentField` recurrence by `scent_model_examples`.
"""

from decimal import Decimal
from typing import Final

from .config_model import ScentParams
from .scent_kernel import ScentKernel
from .scent_model import BOUNDED_SATURATING_RADIAL_V1, ScentExample, ScentModelAgreement

FIGURE_4_WEIGHTS: Final[tuple[tuple[str, ...], ...]] = (
    ("0.04", "0.14", "0.20", "0.14", "0.04"),
    ("0.14", "0.42", "0.62", "0.42", "0.14"),
    ("0.20", "0.62", "0.90", "0.62", "0.20"),
    ("0.14", "0.42", "0.62", "0.42", "0.14"),
    ("0.04", "0.14", "0.20", "0.14", "0.04"),
)
"""PROJECT-DEFAULT, adopted from the **illustrative** Figure 4. Not SOURCE-MUST.

Decimal text, never floats: `0.20` and `0.62` have no exact binary spelling, and
the digest that locks this model is taken over these characters."""

DECAY_EXAMPLE: Final[ScentExample] = ScentExample(Decimal("0.9"), Decimal("0"), Decimal("0.81"))
"""Source-aligned: `(1 - 0.10) * 0.9 + 0 = 0.81`, exact in `Decimal`."""

SATURATION_EXAMPLE: Final[ScentExample] = ScentExample(
    Decimal("0.9"), Decimal("0.9"), Decimal("0.9")
)
"""The C-10 interpretation pin: the state domain is `[0, 0.9]`, so a
re-emission saturates instead of growing. No new conflict id - C-10 remains the
provenance authority for the bound."""


def default_kernel() -> ScentKernel:
    """The Figure-4 kernel, validated by the existing radial authority."""
    return ScentKernel.from_rows(FIGURE_4_WEIGHTS)


def default_scent_model() -> ScentModelAgreement:
    """The complete model this side proposes and expects the opponent to echo."""
    return ScentModelAgreement(
        BOUNDED_SATURATING_RADIAL_V1,
        default_kernel(),
        ScentParams(),
        (DECAY_EXAMPLE, SATURATION_EXAMPLE),
    )
