"""Who decides what this side says, and how honestly it means it.

Ch 6 §6.2 puts the strategy seam *"immediately after decoding the incoming
hint, and before packing the outgoing Commit"*, and `strategy_api` deliberately
kept language out of that port: deciding where to go and deciding what to say
are two policies, and a seam carrying both would make swapping either one a
change to the other. This is the second seam, the same size as the first.

**The validator owns the outgoing hint, not the catalogue.** A candidate is
offered, not sent: `validate_hint` decides, and a sentence that broke App E #27
could not reach `Reveal.hint` even if a future catalogue proposed one. That is
why the unsafe path is exercised by a test rather than trusted to authorship.

**Honest `intent`, and only because the text is honest.** Every production
sentence asserts what `LocalTurnService.apply` has already established, so
`Intent.TRUTH` is a statement about this turn rather than a default. A future
catalogue that says something false must classify it `Intent.LIE`; deception in
the *content* is legal (PRD04-FR-015) and misclassifying it is not
(PRD04-FR-016).

**Zero tokens, no network, no model.** Nothing here calls a provider, and
`SeriesTokenLedger` is never charged: a sub-game that spent nothing reports 0
because it truly spent nothing.
"""

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from ..domain.actions import PhysicalAction
from .hint_templates import TruthfulCatalogue
from .hint_validator import validate_hint
from .sealed_record_values import ActorRole, Intent
from .turn_cursor import TurnCursor

SAFE = "Legal."
"""The one-word sentence that fits every cap a series may lawfully lock.

The floor of `hint_max_words` is 1, so the fallback has to be sayable in one
word. It is true for the same reason every catalogue entry is.
"""


@dataclass(frozen=True, slots=True)
class SpokenHint:
    """One turn's verbal half: the text, and how honestly it is meant."""

    text: str
    intent: Intent


class HintCatalogue(Protocol):
    """Offers sentences for an action; it proposes and never sends."""

    def texts(self, action: PhysicalAction) -> tuple[str, ...]:
        """The candidate sentences for *action*, in preference order."""
        ...


@runtime_checkable
class HintPort(Protocol):
    """Chooses this agent's next spoken hint. It never chooses a move."""

    def choose(self, cursor: TurnCursor, action: PhysicalAction) -> SpokenHint:
        """Return the hint to seal beside *action* at *cursor*."""
        ...


@dataclass(frozen=True, slots=True)
class TemplateHintPolicy:
    """The T0 policy: deterministic templates, validated before they are spoken."""

    role: ActorRole
    hint_max_words: int
    catalogue: HintCatalogue = field(default_factory=TruthfulCatalogue)

    def choose(self, cursor: TurnCursor, action: PhysicalAction) -> SpokenHint:
        """The longest lawful sentence this turn's budget allows.

        Variety comes from the step and the role, both of which the peer already
        knows - the step from the cursor it answers, the role from the sealed
        record - so rotating over them tells it nothing it did not have. The
        cell we stand on is deliberately not an input: a template index chosen
        by position would be a coordinate channel written in words.
        """
        offered = [
            outcome.text
            for candidate in self.catalogue.texts(action)
            if (outcome := validate_hint(candidate, self.hint_max_words)).accepted
            and outcome.text is not None
        ]
        if not offered:
            return SpokenHint(SAFE, Intent.TRUTH)
        turn = cursor.step - 1 + (1 if self.role is ActorRole.THIEF else 0)
        return SpokenHint(offered[turn % len(offered)], Intent.TRUTH)
