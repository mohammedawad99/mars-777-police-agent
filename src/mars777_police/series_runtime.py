"""One series, from Step-0 to the four official files it leaves behind.

R6 made the composed agent live; this makes it *play a series* - six sub-games
and the fourteen official files they produce. It coordinates the owners R5
composed and copies none of them: the cursor stays in `LocalOrchestrator`, the
score in `domain.scoring`, the verdicts in `SeriesAuditGate`, the digest in
`ResultExchange`, the bytes in the artifact store.

**Every artifact waits for the fact it reports** - the declaration for a merged
Step-0, a config for the lock this side verified, a log for its verdict, and the
result for six sub-games, an audit and a mutual agreement. No placeholder."""

from dataclasses import dataclass, field

from .agent_runtime import AgentRuntime, RuntimeState
from .app import artifact_store as artifacts
from .app.audit_runtime import AuditRuntime
from .app.orchestrator import LocalOrchestrator
from .app.outbound_evidence_runtime import OutboundEvidenceRuntime
from .app.protocol_errors import LocalDefectError
from .app.result_core_runtime import SubGameOutcomeLine
from .app.result_exchange import ResultExchange
from .app.series_record import contribution_of, cumulative_of, links_of, outcome_line
from .app.state_machine import ProtocolPhase
from .app.sub_game_closure import closed_sub_game
from .app.token_accounting import TokenAccountingPort
from .app.turn_protocol_runtime import TurnProtocolRuntime
from .artifact_documents import config_document, declaration_document, result_document
from .composition_values import AgentComposition
from .domain.negotiated_config import NegotiatedConfig
from .domain.terminal import Outcome


@dataclass(slots=True)
class SeriesRuntime:
    """The production owner of one six-sub-game series and its official files."""

    agent: AgentRuntime
    store: artifacts.ArtifactStorePort
    tokens: TokenAccountingPort
    orchestrator: LocalOrchestrator
    lines: tuple[SubGameOutcomeLine, ...] = field(default=())

    @property
    def composition(self) -> AgentComposition:
        """The exact graph R5 composed and R6 started; never rebuilt here."""
        return self.agent.composition

    @property
    def game_id(self) -> str:
        """The identity every official artifact of this series is written under."""
        return self.composition.identity.game_id

    @property
    def sub_game(self) -> int:
        """The current sub-game - delegated, because the orchestrator owns it."""
        return self.orchestrator.sub_game

    async def start(self) -> None:
        """Join the opponent and send our Step-0 - the deliberate connect point."""
        if self.agent.state is RuntimeState.SERVING:
            await self.agent.connect()
        composition = self.composition
        await composition.peer_runner.send_step0(composition.identity.declaration)
        self._advance(ProtocolPhase.STEP0_NEGOTIATION)

    def record_declaration(self) -> artifacts.StoredArtifact:
        """Write the merged declaration - ours alone would name one participant."""
        if self.composition.pregame.peer is None:
            raise LocalDefectError("the declaration artifact waits for the peer's Step-0")
        merged = declaration_document(self.composition.pregame.declaration)
        return self.store.store(artifacts.declaration_name(self.game_id), merged)

    def lock_config(self, config: NegotiatedConfig) -> artifacts.StoredArtifact:
        """Record the config this sub-game locked, once the lock actually happened.

        The phase machine negotiates once per series - no edge returns from
        `READY` - so only the first sub-game moves it, and the document is built
        first: a sub-game with no verified lock leaves the phase where it was.
        """
        pregame = self.composition.pregame
        if pregame.config is None:
            raise LocalDefectError("a config artifact needs a config this side agreed")
        if pregame.config != config:
            raise LocalDefectError("the config offered for the record is not the locked one")
        document = config_document(config, pregame)
        if self.orchestrator.machine.phase is ProtocolPhase.STEP0_NEGOTIATION:
            self._advance(
                ProtocolPhase.CONFIG_NEGOTIATION, ProtocolPhase.CONFIG_LOCKED, ProtocolPhase.READY
            )
        return self.store.store(artifacts.config_name(self.game_id, self.sub_game), document)

    def open_sub_game(self, evidence: OutboundEvidenceRuntime, audit: AuditRuntime) -> None:
        """Bind this sub-game's evidence and audit owners, for both directions."""
        if evidence.context.sub_game != self.sub_game or audit.context.sub_game != self.sub_game:
            raise LocalDefectError(f"the runtimes are not sub-game {self.sub_game}'s")
        self.composition.runtime_context.bind_sub_game(evidence, audit)

    def close_turn(self, turn: TurnProtocolRuntime) -> None:
        """Carry what a finished turn witnessed **about the peer** into its audit.

        Our own capture rows do not travel here: `PeerRunner` adopted them when
        the peer's answer actually arrived, the only moment they may be written.
        """
        audit = self.composition.runtime_context.current_audit()
        audit.observe(turn.evidence, turn.acks, turn.capture.inbound)

    def close_sub_game(self, outcome: Outcome) -> artifacts.StoredArtifact:
        """Review, record and finalize this sub-game, then move the cursor."""
        context = self.composition.runtime_context
        evidence, audit = context.current_evidence(), context.current_audit()
        if len(self.lines) != self.sub_game - 1:
            raise LocalDefectError(f"sub-game {self.sub_game} was already recorded")
        pregame = self.composition.pregame
        closed = closed_sub_game(evidence, audit, pregame.config, pregame.lock.scent_model, outcome)
        stored = self.store.store(artifacts.log_name(self.game_id, self.sub_game), closed.document)
        self.composition.series_audit.record(audit)
        self.lines = (*self.lines, outcome_line(self.sub_game, closed.outcome))
        self._advance(ProtocolPhase.SUBGAME_COMPLETE)
        last = self.orchestrator.is_last_sub_game
        self._advance(ProtocolPhase.SERIES_COMPLETE if last else ProtocolPhase.READY)
        return stored

    def build_result(self) -> ResultExchange:
        """Late-build the result owner, once six sub-games and their audits exist."""
        composition = self.composition
        declared = composition.pregame.declaration
        exchange = composition.complete_result(
            lines=self.lines,
            links=links_of(declared),
            cumulative=cumulative_of(self.lines),
            own=contribution_of(declared, composition.group_id, self.lines, self.tokens),
        )
        exchange.require_series_audit(composition.series_audit)
        self._advance(ProtocolPhase.FINAL_AUDIT)
        return exchange

    def persist_result(self) -> artifacts.StoredArtifact:
        """Write the official result - only after the agreement actually completed."""
        exchange = self.composition.runtime_context.current_result()
        if not exchange.is_agreed:
            raise LocalDefectError("the result artifact waits for a mutual agreement")
        self._advance(ProtocolPhase.REPORT_READY)
        document = result_document(exchange, self.composition.group_id)
        return self.store.store(artifacts.result_name(self.game_id), document)

    def _advance(self, *targets: ProtocolPhase) -> None:
        """Move the one orchestrator; the cursor rule is its decision, not ours."""
        for target in targets:
            self.orchestrator = self.orchestrator.advance(target).orchestrator
