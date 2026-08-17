"""The pre-written sentences this agent has to choose from.

Ch 6 §6.5.1 names the template provider the book's own default - *"pre-written
sentences, selected in Python code - zero tokens, no network dependency. This
is the recommended path."* This is that catalogue: no network, no model, no
randomness, and nothing here decides a move.

**Every sentence is true.** `PeerRunner.open_turn` projects the action through
`LocalTurnService.apply`, which raises on anything our own rules refuse, so by
the time a hint is chosen "I acted legally" is already established fact. That is
what lets the policy classify these as `Intent.TRUTH` honestly rather than by
default - Ch 5 p.51 requires the classification to be honest even when the text
is a bluff, and the way to keep that promise is to only claim what is settled.

**Keyed by action class, because that is what stays true.** A sentence about
moving must not accompany a barrier placement, or the text would be false while
claiming to be truthful. Both lists end in a one-word rung: `hint_max_words` is
NEGOTIABLE with a floor of 1 (App F T14 #2), and a series that locked 1 must
still be playable rather than vetoed by the language layer.

Nothing here reads a position, a nonce, a digest or the opponent, and the
catalogue is ordered rather than indexed by any of them - a template chosen by
where we stand would be the coordinate channel App E #27 forbids, wearing words.
"""

from typing import Final

from ..domain.actions import BarrierAction, PhysicalAction

_MOVED: Final[tuple[str, ...]] = (
    "My move follows the rules we agreed.",
    "I played inside the locked configuration.",
    "I moved where the rules allow.",
    "This turn respects the limits we both signed.",
    "I chose a legal action.",
    "Legal move.",
    "Legal.",
)
"""What is true of a move: it was legal under the config both sides locked."""

_PLACED: Final[tuple[str, ...]] = (
    "I placed a barrier where the rules allow.",
    "My placement respects the quota we agreed.",
    "That barrier is declared exactly as it stands.",
    "I chose a legal action.",
    "Legal placement.",
    "Legal.",
)
"""What is true of a placement: lawful cell, quota respected, openly declared."""


class TruthfulCatalogue:
    """The production catalogue: ordered sentences per action class."""

    def texts(self, action: PhysicalAction) -> tuple[str, ...]:
        """The sentences that are true of *action*, longest first.

        Longest first so a roomy cap is spent on the most informative sentence
        the budget allows, and a narrow one still finds a rung further down.
        """
        return _PLACED if type(action) is BarrierAction else _MOVED
