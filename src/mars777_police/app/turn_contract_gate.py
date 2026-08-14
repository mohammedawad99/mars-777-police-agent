"""Refusing a peer whose turn contract is not the one this build speaks.

Stage 5-R8 changed what a `Reveal` answers with: a `TurnOutcome` instead of a
legality `bool`. Nothing in a request shows which a peer implements, and finding
out at the first reveal would mean finding out mid-game - so the posture both
sides echo is checked while a config can still be refused, before `CONFIG_LOCKED`.

The legacy `STRICT_COUNTED_MATCH` keeps its old meaning rather than being quietly
redefined, and the two lecturer-compatibility postures describe artefact and tool
naming, not this turn exchange - none of them is accepted for counted play until
a real adapter proves the whole exchange.

Stage 5-R8 moved the current contract on again: `..._TURN_OUTCOME_SCENT_V2` is
everything V1 promised **plus** the live `ScentEmission` on the reveal. V1 is
still parsed and still means what it always meant; it is simply no longer enough
for counted play, because a series whose peers cannot exchange scent cannot play
the game Ch 4 describes.
"""

from .interop_profiles import COUNTED_TURN_PROFILE, CompatibilityProfile, InteropProfileSet
from .protocol_errors import ConfigMismatchError


def require_counted_turn_contract(profiles: InteropProfileSet) -> None:
    """Raise unless *profiles* names the turn contract this build implements."""
    posture = profiles.compatibility_profile
    if posture is not CompatibilityProfile.STRICT_COUNTED_MATCH_TURN_OUTCOME_SCENT_V2:
        raise ConfigMismatchError(
            f"counted play needs {COUNTED_TURN_PROFILE};"
            f" {posture.value} speaks a different turn contract",
        )
