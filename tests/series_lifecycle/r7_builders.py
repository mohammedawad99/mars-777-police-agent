"""Two real agents playing real sub-games, and the artifacts they leave behind.

Nothing here scripts a digest, a nonce or a verdict: the turns go over the real
transport, the commitments come from the production crypto, and each side's audit
verdict is reached by its own `AuditRuntime` over what it actually witnessed.
"""

import dataclasses

import boot_builders as build
import composed_builders as compose
import turn_builders
from r16_builders import GROUP_A, GROUP_B, PROFILES, config
from session_builders import BUDGET, GAME_ID, GAME_UID

from mars777_police.agent_runtime import AgentRuntime
from mars777_police.app.artifact_store import ArtifactStorePort
from mars777_police.app.audit_runtime import AuditRuntime
from mars777_police.app.audit_values import SubGameContext
from mars777_police.app.capture_values import CaptureClaim, TurnOutcome
from mars777_police.app.config_lock_runtime import ConfigLockRuntime
from mars777_police.app.config_negotiation_runtime import ConfigNegotiationRuntime
from mars777_police.app.orchestrator import LocalOrchestrator
from mars777_police.app.outbound_evidence_runtime import OutboundEvidenceRuntime
from mars777_police.app.outbound_evidence_values import LocalEvidenceContext
from mars777_police.app.protocol_values import Sha256Digest
from mars777_police.app.sealed_record_values import ActorRole, Intent, SealedState
from mars777_police.app.token_accounting import SeriesTokenLedger
from mars777_police.app.turn_cursor import TurnCursor
from mars777_police.app.turn_protocol_runtime import TurnProtocolRuntime
from mars777_police.domain.actions import BarrierAction, MoveAction, PhysicalAction
from mars777_police.domain.board import Board, Position
from mars777_police.domain.config_model import GridConfig, SeriesConfig
from mars777_police.domain.config_sections import BoardAndAgentsTerms
from mars777_police.domain.rules import Move, destination_of
from mars777_police.domain.truth import LocalTruth
from mars777_police.infra.artifacts import JsonArtifactStore
from mars777_police.protocol.audit_commitment import CommitmentRecomputer
from mars777_police.protocol.config_lock import config_sha256
from mars777_police.series_runtime import SeriesRuntime

CONFIG = dataclasses.replace(
    config(),
    board_and_agents=BoardAndAgentsTerms(7, 2, Position(0, 0), Position(0, 1), "top-left", 0),
)
"""The locked config for a lifecycle run: the two start cells are neighbours.

Adjacency is what makes the capture routes reachable at all - BAR-004 lets the
police place only on its own cell or one beside it, so a thief that starts four
cells away cannot be captured by a barrier in the first turn of a sub-game."""

DIGEST = Sha256Digest(config_sha256(CONFIG).value)
POSITIONS = {
    ActorRole.POLICE: CONFIG.board_and_agents.cop_start,
    ActorRole.THIEF: CONFIG.board_and_agents.thief_start,
}
"""Where each side really starts - the cells this series' config locked.

The final audit replays the disclosed game against them, so a lifecycle fixture
that opened somewhere else would be disclosing a game that never happened."""

ACTIONS = {ActorRole.POLICE: MoveAction(Move.S), ActorRole.THIEF: MoveAction(Move.E)}
"""One legal opening move each, from the corner cells the config locks."""

HINT = "heading north"


def store_for(root: object) -> JsonArtifactStore:
    """A real artifact store rooted where the test says, never at the cwd."""
    return JsonArtifactStore(root)  # type: ignore[arg-type]


def series_for(agent: AgentRuntime, store: ArtifactStorePort) -> SeriesRuntime:
    """One series owner over a real composed, running agent."""
    return SeriesRuntime(agent, store, SeriesTokenLedger(), LocalOrchestrator.start(SeriesConfig()))


def _round(group_id: str, sub_game: int) -> tuple[ConfigNegotiationRuntime, ConfigLockRuntime]:
    """This side's real negotiation and lock runtimes for one sub-game."""
    from session_builders import locker

    shared = locker()
    return (
        ConfigNegotiationRuntime(group_id, sub_game, BUDGET, PROFILES),
        ConfigLockRuntime(GAME_ID, GAME_UID, sub_game, PROFILES, shared, shared),
    )


def open_config(series: SeriesRuntime, group_id: str, sub_game: int) -> None:
    """Open the round on the real pregame runtime and adopt the agreed config."""
    pregame = series.composition.pregame
    pregame.open_round(*_round(group_id, sub_game))
    pregame.adopt_config(CONFIG)


def evidence_for(role: ActorRole, sub_game: int) -> OutboundEvidenceRuntime:
    """Our own evidence owner for one sub-game, over the production nonce source."""
    from mars777_police.protocol.secure_nonce import SecretsNonceSource

    context = LocalEvidenceContext(GAME_ID, GAME_UID, sub_game, DIGEST, role)
    return OutboundEvidenceRuntime(context, SecretsNonceSource(), CommitmentRecomputer())


def audit_for(peer_role: ActorRole, peer_group: str, sub_game: int) -> AuditRuntime:
    """The audit owner for one sub-game; its evidence arrives as turns finish."""
    context = SubGameContext(GAME_ID, GAME_UID, sub_game, DIGEST, peer_role, peer_group)
    return AuditRuntime(context, (), CommitmentRecomputer())


def board() -> Board:
    """The empty geometry this series' config locked."""
    terms = CONFIG.board_and_agents
    return GridConfig.from_grid_size(terms.grid_size, terms.axis_start_index).to_board()


def turn_for(
    role: ActorRole, cursor: TurnCursor, truth: LocalTruth | None = None
) -> TurnProtocolRuntime:
    """A real turn runtime positioned on one step of one sub-game.

    Its own truth is the locked board and this side's locked start cell, so the
    answer a live turn gives about capture is about the same game the final
    audit later replays. Pass *truth* to carry a sub-game's adopted barriers
    from one turn into the next - a role a later stage will own.
    """
    runtime = turn_builders.runtime(role)
    runtime.cursor = cursor
    runtime.truth = truth or LocalTruth(board=board(), own_position=POSITIONS[role])
    return runtime


def sealed_for(role: ActorRole, step: int = 1) -> SealedState:
    """The own-known snapshot this side seals for one step."""
    return SealedState(DIGEST, POSITIONS[role], (), step, role)


def moved(cell: Position, action: PhysicalAction) -> Position:
    """Where a side stands after that action - a barrier leaves it where it was."""
    if isinstance(action, MoveAction):
        return destination_of(cell, action.move)
    return cell


def placed(walls: tuple[Position, ...], action: PhysicalAction) -> tuple[Position, ...]:
    """The public barrier set after that action, in placement order."""
    if isinstance(action, BarrierAction):
        return (*walls, action.target)
    return walls


async def one_turn(
    mover: SeriesRuntime,
    waiter: SeriesRuntime,
    role: ActorRole,
    cursor: TurnCursor,
    action: PhysicalAction | None = None,
    claim: CaptureClaim | None = None,
    cell: Position | None = None,
    barriers: tuple[Position, ...] = (),
) -> TurnOutcome:
    """Drive one real commit / acknowledge / reveal turn between two agents.

    *cell* and *barriers* are what this side seals about itself, so a caller
    playing more than one step has to carry the real ones forward - the final
    audit replays them against the placements both sides actually revealed.
    """
    prepared = await mover.composition.peer_runner.open_turn(
        state=SealedState(DIGEST, cell or POSITIONS[role], barriers, cursor.step, role),
        action=action or ACTIONS[role],
        intent=Intent.TRUTH,
        hint=HINT,
        cursor=cursor,
        claim=claim,
    )
    await waiter.composition.peer_runner.acknowledge_peer_turn()
    return await mover.composition.peer_runner.reveal_turn(prepared)


def agents(port_a: int, port_b: int) -> tuple[AgentRuntime, AgentRuntime]:
    """Two composed agents pointed at each other, ready to serve."""
    url_a, url_b = f"http://{build.HOST}:{port_a}/mcp", f"http://{build.HOST}:{port_b}/mcp"
    a = compose.compose(GROUP_A, "group_a", ActorRole.POLICE, url_b)
    b = compose.compose(GROUP_B, "group_b", ActorRole.THIEF, url_a)
    return AgentRuntime(a, build.HOST, port_a), AgentRuntime(b, build.HOST, port_b)
