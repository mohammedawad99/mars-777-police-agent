"""Role-keyed scoring for the locked sub-game end events.

App F Table 17 (all FIXED): capture cop 20 / thief 5; survival cop 5 /
thief 10; tie 2 to each side.

``technical_loss`` = 0 / 0 is binding through **Ch 3 Table 2** plus App E #48
and conflict **C-07**; it is deliberately **not** an Appendix-F Table-17 row
and this module never claims that provenance for it.

``tie_score`` is exposed as a value only. App F T17 #5 scopes it to a tied
**cumulative** score against an opponent, and Ch 3 Table 2 has no tie end
event, so no sub-game outcome maps to it here; the series layer owns that
comparison.

``diversity_reward`` (10) is league scope (App F T18 #2) and is intentionally
absent: it must never enter a per-sub-game score.

Scores are addressed by role name, never by tuple position, so a police/thief
value cannot be silently reversed (C-06).
"""

from dataclasses import dataclass
from typing import Final

from .terminal import Outcome


@dataclass(frozen=True, slots=True)
class ScoreLine:
    """Points awarded to each role for one end event."""

    cop: int
    thief: int


CAPTURE_SCORE: Final[ScoreLine] = ScoreLine(cop=20, thief=5)
"""App F T17 #1/#2, FIXED."""

SURVIVAL_SCORE: Final[ScoreLine] = ScoreLine(cop=5, thief=10)
"""App F T17 #3/#4, FIXED."""

TECHNICAL_LOSS_SCORE: Final[ScoreLine] = ScoreLine(cop=0, thief=0)
"""Ch 3 Table 2 + App E #48 (C-07) - not an Appendix-F row."""

TIE_SCORE: Final[ScoreLine] = ScoreLine(cop=2, thief=2)
"""App F T17 #5, FIXED - series/opponent aggregate scope, not a sub-game."""

_TABLE: Final[dict[Outcome, ScoreLine]] = {
    Outcome.CAPTURE: CAPTURE_SCORE,
    Outcome.SURVIVAL: SURVIVAL_SCORE,
    Outcome.TECHNICAL_LOSS: TECHNICAL_LOSS_SCORE,
}


def score_for(outcome: Outcome) -> ScoreLine:
    """Return the role-keyed score for a locked sub-game *outcome*.

    Raises ``KeyError`` for anything outside the locked vocabulary rather than
    guessing a score. ``Outcome`` is a ``StrEnum``, so the equal-comparing raw
    string is rejected too: the caller must pass a real outcome.
    """
    if not isinstance(outcome, Outcome):
        raise KeyError(f"unknown outcome of type {type(outcome).__name__}")
    return _TABLE[outcome]
