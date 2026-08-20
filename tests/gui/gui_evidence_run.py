"""One real sub-game, kept whole: the live view of it and the log it left behind.

Both submission screenshots come from the same thirty-five-round sub-game two
composed agents actually played - so the live picture and the replay picture are
two views of one true match rather than two unrelated fixtures. Nothing here
scripts a move, chooses an outcome or writes a game value.
"""

import asyncio
from pathlib import Path

import autonomous_builders as harness
from r16_builders import GAME_ID

from mars777_police.app.artifact_store import log_name
from mars777_police.app.live_view_feed import LiveViewFeed
from mars777_police.app.live_view_sink import LatestSnapshot
from mars777_police.app.live_view_values import LiveViewSnapshot
from mars777_police.app.replay_session import ReplaySession
from mars777_police.app.sealed_record_values import ActorRole
from mars777_police.compose_replay import open_replay
from mars777_police.domain.terminal import Outcome

GAME = "MaRs-777-vs-GROUP-XY"
"""The two development identities the harness composes. Not a tournament match."""


def play(root: Path, box: LatestSnapshot) -> tuple[Outcome, int]:
    """Play one whole natural sub-game with the live view attached to the police."""
    built = harness.driver_for

    def attach(series: object, role: ActorRole) -> object:
        driver = built(series, role)  # type: ignore[arg-type]
        if role is ActorRole.POLICE:
            driver.feed = LiveViewFeed(box, role.value, GAME)
        return driver

    harness.driver_for = attach  # type: ignore[assignment]
    try:
        a, b = harness.pair_for(root)
        return asyncio.run(harness.autonomous(a, b))
    finally:
        harness.driver_for = built  # type: ignore[assignment]


def artifacts(root: Path) -> tuple[Path, Path]:
    """The police log and config this run wrote, found by their own names."""
    police = root / "police"
    log = next(police.glob(log_name(GAME_ID, 1)))
    config = next(police.glob(f"config_{GAME_ID}_g01.json"))
    return log, config


def played(root: Path) -> tuple[LiveViewSnapshot, Path, Path]:
    """The last lawful live view, and the official artifacts of the same sub-game."""
    box = LatestSnapshot()
    play(root, box)
    seen = box.take()
    assert seen is not None, "a played sub-game must have published at least one turn"
    log, config = artifacts(root)
    return seen, log, config


def session(root: Path) -> ReplaySession:
    """A replay over the log this run produced, through the ordinary composition."""
    log, config = artifacts(root)
    return open_replay(log, config, root)
