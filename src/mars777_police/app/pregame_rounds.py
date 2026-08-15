"""Opening the next sub-game's config round from the one before it.

`PregameSessionRuntime.open_round` has always been the authority - *"the round
comes from the caller, already built, so nothing here guesses a `sub_game`"* -
and until now nothing in production built one. This does, and it does it the
only way that cannot drift: by taking the round runtimes the session already
holds and changing the single field that differs.

Both are `frozen` collaborator holders with no mutable state of their own, so
`replace` reproduces them exactly - the same profiles, the same digest port, the
same authenticator, the same agreed scent model. **Nothing is reconstructed.**
No key is read, no authenticator is rebuilt, no digest is recomputed, and no
`NegotiatedConfig` field is invented. The per-round *mutable* facts - `opening`,
`seen`, the adopted config and the verified evidence - are reset by `open_round`
itself, which is why they are not touched here either.

One function, because one thing changes between `g01` and `g02`.
"""

from dataclasses import replace

from .pregame_session_runtime import PregameSessionRuntime


def open_next_round(pregame: PregameSessionRuntime, sub_game: int) -> None:
    """Move *pregame* on to *sub_game*, keeping every series-scoped collaborator.

    The series survives the round: the declaration, the authenticated peer and
    the frozen scent model are the session's, not this round's, so a later
    sub-game negotiates under the same identity it started with.
    """
    pregame.open_round(
        replace(pregame.negotiation, sub_game=sub_game),
        replace(pregame.lock, sub_game=sub_game),
    )
