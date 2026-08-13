"""Deciding whether two peers hold the same agreed scent model.

SCENT-003 asks the exchange to establish *identical interpretation*, so this
compares three independent readings of the same question and requires all three
to agree: the values, the exact rendering both sides must produce, and the
content digest each side derives for itself. They are redundant on purpose - a
single reading that silently stopped working would take a mismatched model with
it - and all three are computed before the decision, so none can go unexercised
behind a short circuit.

A peer's own digest is never consulted: a digest that travels with the model it
covers proves nothing about that model, and this checkpoint deliberately carries
no peer-supplied digest at all.
"""

from dataclasses import dataclass

from ..domain.scent_model import ScentModelAgreement
from .ports import ConfigDigestPort


@dataclass(frozen=True, slots=True)
class ScentModelComparison:
    """The three readings, kept apart so a caller can say which one failed."""

    same_values: bool
    same_rendering: bool
    same_digest: bool

    @property
    def agreed(self) -> bool:
        """Whether every reading says the two sides hold the same model."""
        return self.same_values and self.same_rendering and self.same_digest


def compare_models(
    ours: ScentModelAgreement, theirs: ScentModelAgreement, digests: ConfigDigestPort
) -> ScentModelComparison:
    """Read the two models three ways, always all three."""
    return ScentModelComparison(
        ours == theirs,
        digests.scent_model_rendering(ours) == digests.scent_model_rendering(theirs),
        digests.scent_model_digest(ours) == digests.scent_model_digest(theirs),
    )
