"""The pinned at-least-once receiver contract, copied for deterministic regression.

Source repository : https://github.com/Imreec/copthief-league-protocol
Pinned commit     : ad6557626587e09146af4283a5e808e7001343c5
Licence           : MIT, (c) 2026 Team ImreEyal and kit contributors.

`vectors/delivery_contract.json`, status **PROMOTED**. Behaviour rather than
bytes, so the kit pins it as a decision table and so do we. Both registered wire
shapes ride HTTP, which is at-least-once: a push whose ack is lost is retried by
a *correct* client, so the same message arrives twice by design.

The two rows that carry the design: dedupe is on the **commit**, never on
`(kind, step)` - a different commit for a played step is tampering evidence and
must stay loud - and the reorder **window is the flood rule**, so no second
threshold sits beside it where nothing could ever reach it.
"""

from typing import Final

STATE: Final = ({1: "c1", 2: "c2"}, 2, 3)
"""`(played, window, next)` - the pinned starting receiver state."""

ARRIVALS: Final = (
    ((3, "c3"), "apply", "the next expected step"),
    ((2, "c2"), "absorb", "redelivery: same commit for a played step, state unchanged"),
    ((2, "cX"), "equivocation", "a DIFFERENT commit for a played step is tampering evidence"),
    ((4, "c4"), "buffer", "one ahead, inside the reorder window"),
    ((5, "c5"), "buffer", "at the window bound"),
    ((6, "c6"), "violation", "past the window - the window IS the flood rule"),
    ((0, "c0"), "discard", "below `next` and never played: it can never become applicable"),
)
"""Every arrival row of the pinned file, with the decision it pins."""

NO_WINDOW_STATE: Final = ({1: "c1", 2: "c2"}, 0, 3)
NO_WINDOW_ARRIVAL: Final = (4, "c4")
NO_WINDOW_DECISION: Final = "violation"
"""A receiver with no reorder window turns an ordinary retry race into a
protocol violation - which App. E rule 35 zeroes on BOTH teams. Zero tolerance
is not a tightening here."""

DEADLINE_RULE: Final = (
    ((100.0, 90.0, False, False), "waiting", "quiet lap, in budget"),
    ((100.0, 90.0, True, True), "waiting", "tolerated traffic does NOT move the deadline"),
    ((100.0, 100.0, True, True), "expired", "expires on a lap where a message DID arrive"),
)
"""`(deadline_at, now, arrived, tolerated) -> decision`. One clock per EXPECTED
message, so a stall burns the sender's budget and never ours - and a receiver
that checks its clock only on an empty poll never checks it under a flood."""

NO_RULES_TOLERANCE: Final = "none of this relaxes commit-reveal"
"""Transport tolerance, no rules tolerance: equivocation still collapses the game."""
