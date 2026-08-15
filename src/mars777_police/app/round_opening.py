"""Opening the round a series is on, whether or not it is already open.

`open_next_round` builds the *next* round and `PregameSessionRuntime.open_round`
resets everything a round owns - which is exactly right when a sub-game ends,
and exactly wrong when the round asked for is the one already in progress. Two
independent processes make that second case real: whichever finishes Step-0
first opens its round and proposes immediately, so the other side can hold an
authenticated proposal *before* its own driver opens. Re-opening then discarded
`seen`, `opening` and the milestones, and since a peer proposes once per round,
the discarded signal never came again.

So the decision lives here, at the caller, and neither `open_round` nor any
guard changes: **the round the series is already on is left exactly as the
protocol left it**, and only a genuine transition opens a fresh one.

**Round identity, our candidate and peer convergence are three different
things.** This establishes the first two and never the third: nothing here
marks a proposal seen, verifies a lock or sets a milestone. Those remain what
authenticated inbound protocol does, and a peer that disagrees is still refused
later by `ConfigLockRuntime` with `E-CONFIG-MISMATCH`.
"""

from ..domain.negotiated_config import NegotiatedConfig
from .pregame_rounds import open_next_round
from .pregame_session_runtime import PregameSessionRuntime
from .protocol_errors import LocalDefectError


def current_sub_game(pregame: PregameSessionRuntime) -> int:
    """The sub-game this session's round runtimes are both built for.

    A disagreement is refused rather than resolved: picking one of two halves of
    a half-opened round would seal evidence under an identity the other half
    never agreed to, and nothing here can know which is the intended one.
    """
    if pregame.negotiation.sub_game != pregame.lock.sub_game:
        raise LocalDefectError(
            f"a round needs one sub-game, got negotiation {pregame.negotiation.sub_game}"
            f" and lock {pregame.lock.sub_game}",
        )
    return pregame.negotiation.sub_game


def open_round_for(pregame: PregameSessionRuntime, sub_game: int, config: NegotiatedConfig) -> None:
    """Make *sub_game* the open round and *config* this side's candidate for it.

    Idempotent for the round already open, so a driver may open before or after
    the peer's first message without either order losing anything.
    """
    if current_sub_game(pregame) != sub_game:
        open_next_round(pregame, sub_game)
    adopt_candidate(pregame, config)


def adopt_candidate(pregame: PregameSessionRuntime, config: NegotiatedConfig) -> None:
    """Register our own candidate once, and refuse to swap it afterwards.

    A **local** ownership invariant, deliberately not peer convergence: two
    different candidates for one round would mean this side proposed one config
    and locked another, which is our own defect long before a peer could
    disagree. What the *peer* proposes is still judged by the negotiation and
    lock runtimes, and a mismatch there is still `E-CONFIG-MISMATCH`.
    """
    held = pregame.config
    if held is None:
        pregame.adopt_config(config)
        return
    if held != config:
        raise LocalDefectError(
            f"sub-game {pregame.negotiation.sub_game} was already opened with a different"
            " local config candidate",
        )
