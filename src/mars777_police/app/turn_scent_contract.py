"""Holding a reveal to the turn contract the two peers actually agreed.

`require_claim_shape` already refuses a capture declaration the posture does not
allow; this is the same kind of guard for the other unsealed member. The postures
were compared before `CONFIG_LOCKED`, so by the time a reveal arrives the shape
is settled: a V2 session without an emission, or a pre-V2 session carrying one,
is a **malformed message** - not a game event, not a technical loss and not
tampering. Classifying it as anything else would let a broken encoder look like
a cheating opponent.

Nothing here reads the emission's contents. Whether the deposits are the ones the
sender's real trajectory would produce is a question only the final audit can
ask, once the trajectory has been disclosed.
"""

from .interop_profiles import COUNTED_TURN_PROFILE, CompatibilityProfile
from .peer_turn_messages import Reveal
from .protocol_errors import MalformedMessageError

SCENT_POSTURE = CompatibilityProfile.STRICT_COUNTED_MATCH_TURN_OUTCOME_SCENT_V2
"""The one posture whose reveals carry a live emission."""


def require_scent_shape(reveal: Reveal, posture: CompatibilityProfile) -> None:
    """Raise unless *reveal* carries exactly what *posture* promised."""
    present = reveal.scent_emission is not None
    if posture is SCENT_POSTURE:
        if not present:
            raise MalformedMessageError(
                f"{COUNTED_TURN_PROFILE} requires a scent emission on every reveal",
            )
        return
    if present:
        raise MalformedMessageError(
            f"a reveal under {posture.value} carries no scent emission",
        )
