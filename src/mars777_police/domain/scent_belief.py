"""What this side may believe about the opponent - and nothing it may not know.

Ch 6 §6.4 states the premise the whole game rests on: *"the two sides are
entirely symmetric: **neither of them sees the opponent's real position**"*.
Scent is the legal partial evidence that premise allows, so a belief is a
**field of intensities this side observed**, never a cell the opponent stands
on. That distinction lives here as a shape rather than as prose: there is no
member an estimated position could be stored in, and nothing here derives one.

**A reading, not a second physics.** The field arrives already folded by
`domain.scent_observation`, and `intensity_at` returns the number that field
holds - unscaled, unrounded and unclamped. Restating any part of the recurrence
here would create the second decay implementation `PRD01-FR-041` forbids.

**Neutral is a value, not `None`.** A sub-game opens having heard nothing, and a
policy forced to branch on `None` before every comparison would carry a nullable
path into every decision. The default answers zero everywhere and reports that
it is speaking from no evidence, so the no-evidence case is ordinary rather than
special - and because it is frozen, one shared neutral cannot become another
turn's belief.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Final

from .board import Position
from .scent import ScentField

NO_EVIDENCE: Decimal = Decimal("0")
"""What an unobserved cell is worth: the field's own zero, named once."""


@dataclass(frozen=True, slots=True)
class ScentBelief:
    """The opponent-scent evidence this side has legally observed so far."""

    observed: ScentField | None = None
    evidence_count: int = 0

    @property
    def has_evidence(self) -> bool:
        """Whether any peer emission has been folded into this belief yet."""
        return self.evidence_count > 0

    def intensity_at(self, position: Position) -> Decimal:
        """How strong the observed evidence is at *position*.

        Zero before anything has been heard, and afterwards exactly what the
        folded field holds. A cell outside the board is not a question this
        value answers - `ScentField` refuses it, and refusing is right: a
        strategy asking about a cell that does not exist has a defect that
        silently returning zero would hide.
        """
        if self.observed is None:
            return NO_EVIDENCE
        return self.observed.at(position)


NO_SCENT: Final[ScentBelief] = ScentBelief()
"""The one neutral belief, shared because it is frozen and answers zero.

A sub-game that has heard nothing, and every `Observation` built before scent
existed, mean the same thing - so they are the same value rather than one
allocation per caller. Nothing can mutate it into someone else's belief.
"""
