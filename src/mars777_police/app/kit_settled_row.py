"""One finished sub-game, in the shape a series settlement hashes.

The settlement scope reads four things per row: which sub-game, which side each
group took, the outcome word, and the two scores. Producing them here - from the
outcome the backend already settled and the project's own scoring table - keeps
the digest derived from facts rather than from a second telling of them.

**The scores are our scoring authority's, not a copy of the peer's table.** If
the two ever disagreed the digests would differ and settlement would fail
loudly, which is the correct outcome: a silent agreement on numbers we did not
compute would be worse than a refusal.

**The outcome word is lowercased for the wire.** Our `Outcome` spells its
members in upper case and the settlement scope carries the kit's lower-case
spelling; the digest is over characters, so `"SURVIVAL"` and `"survival"` are
two different series as far as a settlement is concerned.
"""

from typing import Any

from ..domain.scoring import score_for
from ..domain.terminal import Outcome
from .kit_greeting import KitPairing
from .kit_messages import KitRole


def settled_row(
    *, sub_game: int, ours: str, theirs: str, our_role: KitRole, outcome: Outcome
) -> dict[str, Any]:
    """The finished row for *sub_game*, from this side's role and outcome."""
    line = score_for(outcome)
    police, thief = line.cop, line.thief
    we_were_police = our_role is KitRole.POLICE
    return {
        "sub_game_number": sub_game,
        "roles": {
            ours: our_role.value,
            theirs: (KitRole.THIEF if we_were_police else KitRole.POLICE).value,
        },
        "result": outcome.value.lower(),
        "score": {
            ours: police if we_were_police else thief,
            theirs: thief if we_were_police else police,
        },
    }


def row_of(
    pairing: "KitPairing", sub_game: int, our_role: "KitRole", outcome: "Outcome"
) -> dict[str, Any]:
    """One finished sub-game as a settlement reads it, from the pairing's own names."""
    return settled_row(
        sub_game=sub_game,
        ours=pairing.our_group,
        theirs=pairing.peer_group,
        our_role=our_role,
        outcome=outcome,
    )
