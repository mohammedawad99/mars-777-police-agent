"""The at-least-once receiver contract, as one decision and no policy.

Both registered wire shapes ride HTTP, which is at-least-once: a push whose ack
is lost is retried by a **correct** client, so the same message arrives twice by
design and not only on bad networks. The pinned kit therefore publishes this as
a decision table (`vectors/delivery_contract.json`, PROMOTED), and this is that
table - a pure function, so it can be pinned row by row against the kit's own.

**Dedupe is on the commit, never on `(kind, step)`.** A redelivery carries the
same commit for a played step and is absorbed, changing nothing. The *same step
under a different commit* is equivocation - tampering evidence - and a key that
ignored the commit would collapse the second silently into the first.

**The window is the flood rule.** A second threshold beside it would be
unreachable by construction, so there is none. A receiver with **no** window
turns an ordinary retry race into a protocol violation, which App. E rule 35
zeroes on both teams; zero tolerance is not a tightening.

Transport tolerance, **no rules tolerance**: nothing here relaxes commit-reveal,
and an equivocation still collapses the game.
"""

from dataclasses import dataclass
from enum import StrEnum


class DeliveryDecision(StrEnum):
    """What a receiver does with one arrival, and the whole vocabulary."""

    APPLY = "apply"
    """The next expected step: apply it now."""

    ABSORB = "absorb"
    """A redelivery of a played step under the same commit. State unchanged."""

    EQUIVOCATION = "equivocation"
    """A played step under a *different* commit. Tampering, and it stays loud."""

    BUFFER = "buffer"
    """One or more ahead, inside the window: hold and replay in step order."""

    VIOLATION = "violation"
    """Past the window."""

    DISCARD = "discard"
    """Below `expected` and never played, so it can never become applicable."""


@dataclass(frozen=True, slots=True)
class DeliveryState:
    """What the contract is decided against: what played, how far ahead, what next."""

    played: dict[int, str]
    """`{step: commit}` - every step already applied, keyed by the commit that sealed it."""

    window: int
    """How many out-of-order steps may be buffered; `0` means none."""

    expected: int
    """The next step this receiver will apply. It only advances past accepted steps."""


def decide(state: DeliveryState, step: int, commit: str) -> DeliveryDecision:
    """The pinned decision for one arrival against *state*."""
    seen = state.played.get(step)
    if seen is not None:
        return DeliveryDecision.ABSORB if seen == commit else DeliveryDecision.EQUIVOCATION
    if step == state.expected:
        return DeliveryDecision.APPLY
    if step < state.expected:
        return DeliveryDecision.DISCARD
    if step <= state.expected + state.window:
        return DeliveryDecision.BUFFER
    return DeliveryDecision.VIOLATION
