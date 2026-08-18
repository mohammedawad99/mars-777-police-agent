"""What a run is allowed to be worth, decided before it starts and never after.

The book requires Step-0 to be cryptographically authenticated with a
pre-supplied key; this project satisfies that with `AuthProfile.HMAC_SHA256`.
The pinned kit sparring peer offers no keyed proof at all - its
`SHA256(canonical(terms)|nonce)` is an **unkeyed content agreement**, which
proves both sides read the same fourteen values and nothing whatever about who
is speaking.

So a development friendly against that peer is authorized to play without the
keyed gate, and is authorized for **nothing else**. This value is where that
authorization is bounded.

**`counted_capable` is derived, not stored.** A stored flag is something a
constructor, an operator or a later edit can set; a property computed from the
run class and the keyed-auth fact is something none of them can. That is the
whole reason this type exists rather than a boolean argument passed around.

**Nothing here is peer-facing.** The pinned wire defines no run-class value, so
`wire_view` is empty by construction: inventing a token to tell an opponent how
seriously we are taking the game would be inventing protocol.
"""

from dataclasses import dataclass
from enum import StrEnum

WireView = dict[str, object]


class RunClass(StrEnum):
    """The two things a run of this agent can be."""

    COUNTED_CAPABLE = "COUNTED_CAPABLE"
    """The source-compliant path: keyed producer authentication is required."""

    KIT_FRIENDLY_ONLY = "KIT_FRIENDLY_ONLY"
    """Development only. The pinned kit's unkeyed agreement is accepted, and the
    run can never be counted, reported or offered as league evidence."""


@dataclass(frozen=True, slots=True)
class RunClassification:
    """One run's class and the auth facts that decide what it may be worth."""

    run_class: RunClass
    keyed_auth_satisfied: bool
    kit_terms_agreement: bool

    @property
    def counted_capable(self) -> bool:
        """Whether this run may ever be counted. False for every friendly."""
        return self.run_class is RunClass.COUNTED_CAPABLE and self.keyed_auth_satisfied

    @property
    def step0_authenticated(self) -> bool:
        """The readiness fact this run contributes, under its own name."""
        return self.keyed_auth_satisfied

    def wire_view(self) -> WireView:
        """What the peer is told about our run class: nothing."""
        return {}

    @classmethod
    def friendly(cls, *, kit_terms_agreement: bool) -> "RunClassification":
        """A development KIT friendly. Keyed auth is not satisfied, by definition."""
        return cls(RunClass.KIT_FRIENDLY_ONLY, False, kit_terms_agreement)

    @classmethod
    def counted(cls, *, keyed_auth_satisfied: bool) -> "RunClassification":
        """A source-compliant run, counted-capable only once the key spoke."""
        return cls(RunClass.COUNTED_CAPABLE, keyed_auth_satisfied, False)
