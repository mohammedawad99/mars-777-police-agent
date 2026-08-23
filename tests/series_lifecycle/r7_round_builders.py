"""Real series runtimes, and the config round each sub-game opens with.

Nothing is faked: two composed agents negotiate and lock a real configuration
through production, so what every later builder starts from is a state the
system actually reached.
"""

import dataclasses

import boot_builders as build
import composed_builders as compose
from r16_builders import GROUP_A, GROUP_B, PROFILES, config
from session_builders import BUDGET, GAME_ID, GAME_UID

from mars777_police.agent_runtime import AgentRuntime
from mars777_police.app.artifact_store import ArtifactStorePort
from mars777_police.app.config_lock_runtime import ConfigLockRuntime
from mars777_police.app.config_negotiation_runtime import ConfigNegotiationRuntime
from mars777_police.app.kit_messages import KitRole
from mars777_police.app.orchestrator import LocalOrchestrator
from mars777_police.app.sealed_record_values import ActorRole
from mars777_police.app.series_roles import alternating
from mars777_police.app.token_accounting import SeriesTokenLedger
from mars777_police.domain.board import Position
from mars777_police.domain.config_model import SeriesConfig
from mars777_police.domain.config_sections import BoardAndAgentsTerms
from mars777_police.domain.scent_model_default import default_scent_model
from mars777_police.infra.artifacts import JsonArtifactStore
from mars777_police.series_runtime import SeriesRuntime

CONFIG = dataclasses.replace(
    config(),
    board_and_agents=BoardAndAgentsTerms(7, 2, Position(0, 0), Position(0, 1), "top-left", 0),
)
"""The locked config for a lifecycle run: the two start cells are neighbours.

Adjacency is what makes the capture routes reachable at all - BAR-004 lets the
police place only on its own cell or one beside it, so a thief that starts four
cells away cannot be captured by a barrier in the first turn of a sub-game."""
"""Where each side really starts - the cells this series' config locked.

The final audit replays the disclosed game against them, so a lifecycle fixture
that opened somewhere else would be disclosing a game that never happened."""
"""One legal opening move each, from the corner cells the config locks."""


def store_for(root: object) -> JsonArtifactStore:
    """A real artifact store rooted where the test says, never at the cwd."""
    return JsonArtifactStore(root)  # type: ignore[arg-type]


def series_for(agent: AgentRuntime, store: ArtifactStorePort) -> SeriesRuntime:
    """One series owner over a real composed, running agent."""
    return SeriesRuntime(
        agent,
        store,
        SeriesTokenLedger(),
        LocalOrchestrator.start(SeriesConfig()),
        roles=alternating(GROUP_A, KitRole.POLICE, GROUP_B),
    )


def _round(group_id: str, sub_game: int) -> tuple[ConfigNegotiationRuntime, ConfigLockRuntime]:
    """This side's real negotiation and lock runtimes for one sub-game."""
    from session_builders import locker

    shared = locker()
    return (
        ConfigNegotiationRuntime(
            group_id, sub_game, BUDGET, PROFILES, shared, default_scent_model()
        ),
        ConfigLockRuntime(
            GAME_ID, GAME_UID, sub_game, PROFILES, shared, shared, default_scent_model()
        ),
    )


def open_config(series: SeriesRuntime, group_id: str, sub_game: int) -> None:
    """Open the round on the real pregame runtime and adopt the agreed config."""
    pregame = series.composition.pregame
    pregame.open_round(*_round(group_id, sub_game))
    pregame.adopt_config(CONFIG)


def lock_round(a: SeriesRuntime, b: SeriesRuntime) -> None:
    """Exchange and verify both sides' real lock evidence for the open round.

    The config artifact reports a lock, so the lifecycle has to perform one:
    each side verifies the other's evidence through its own production runtime.
    """
    ours, theirs = a.composition.pregame, b.composition.pregame
    ours.accept_lock(theirs.prepare_lock())
    theirs.accept_lock(ours.prepare_lock())


def agents(port_a: int, port_b: int) -> tuple[AgentRuntime, AgentRuntime]:
    """Two composed agents pointed at each other, ready to serve."""
    url_a, url_b = f"http://{build.HOST}:{port_a}/mcp", f"http://{build.HOST}:{port_b}/mcp"
    a = compose.compose(GROUP_A, ActorRole.POLICE, url_b)
    b = compose.compose(GROUP_B, ActorRole.THIEF, url_a)
    return AgentRuntime(a, build.HOST, port_a), AgentRuntime(b, build.HOST, port_b)
