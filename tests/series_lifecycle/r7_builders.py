"""Two real agents playing real sub-games, and the artifacts they leave behind.

Nothing here scripts a digest, a nonce or a verdict: the turns go over the real
transport, the commitments come from the production crypto, and each side's audit
verdict is reached by its own `AuditRuntime` over what it actually witnessed.
"""

import boot_builders as build
import composed_builders as compose
import turn_builders
from r16_builders import GROUP_A, GROUP_B, PROFILES, config
from session_builders import BUDGET, GAME_ID, GAME_UID

from mars777_police.agent_runtime import AgentRuntime
from mars777_police.app.artifact_store import ArtifactStorePort
from mars777_police.app.audit_runtime import AuditRuntime
from mars777_police.app.audit_values import SubGameContext
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
from mars777_police.domain.actions import MoveAction
from mars777_police.domain.board import Position
from mars777_police.domain.config_model import SeriesConfig
from mars777_police.domain.rules import Move
from mars777_police.infra.artifacts import JsonArtifactStore
from mars777_police.protocol.audit_commitment import CommitmentRecomputer
from mars777_police.protocol.config_lock import config_sha256
from mars777_police.series_runtime import SeriesRuntime

CONFIG = config()
DIGEST = Sha256Digest(config_sha256(CONFIG).value)
POSITIONS = {ActorRole.POLICE: Position(2, 3), ActorRole.THIEF: Position(6, 6)}
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


def turn_for(role: ActorRole, cursor: TurnCursor) -> TurnProtocolRuntime:
    """A real turn runtime positioned on one step of one sub-game."""
    runtime = turn_builders.runtime(role)
    runtime.cursor = cursor
    return runtime


def sealed_for(role: ActorRole, step: int = 1) -> SealedState:
    """The own-known snapshot this side seals for one step."""
    return SealedState(DIGEST, POSITIONS[role], (), step, role)


async def one_turn(
    mover: SeriesRuntime, waiter: SeriesRuntime, role: ActorRole, cursor: TurnCursor
) -> bool:
    """Drive one real commit / acknowledge / reveal turn between two agents."""
    prepared = await mover.composition.peer_runner.open_turn(
        state=sealed_for(role, cursor.step),
        action=MoveAction(Move.N),
        intent=Intent.TRUTH,
        hint=HINT,
        cursor=cursor,
    )
    await waiter.composition.peer_runner.acknowledge_peer_turn()
    return await mover.composition.peer_runner.reveal_turn(prepared)


def agents(port_a: int, port_b: int) -> tuple[AgentRuntime, AgentRuntime]:
    """Two composed agents pointed at each other, ready to serve."""
    url_a, url_b = f"http://{build.HOST}:{port_a}/mcp", f"http://{build.HOST}:{port_b}/mcp"
    a = compose.compose(GROUP_A, "group_a", ActorRole.POLICE, url_b)
    b = compose.compose(GROUP_B, "group_b", ActorRole.THIEF, url_a)
    return AgentRuntime(a, build.HOST, port_a), AgentRuntime(b, build.HOST, port_b)
