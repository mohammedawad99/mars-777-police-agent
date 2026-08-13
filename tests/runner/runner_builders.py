"""One production side: real inbound server, real outbound runner, real owners."""

from collections.abc import Callable
from dataclasses import dataclass, field

import audit_builders
import evidence_builders as evidence
import turn_builders
from cadence_ops import exchange_for
from live_server import LiveServer
from peer_ops import authenticator
from r16_builders import COMMIT_A, GAME_ID, GAME_UID, GROUP_A, PROFILES, config, partial

from mars777_police.app.audit_runtime import AuditRuntime
from mars777_police.app.config_lock_runtime import ConfigLockRuntime
from mars777_police.app.config_negotiation_runtime import ConfigNegotiationRuntime
from mars777_police.app.declaration_values import Declaration
from mars777_police.app.outbound_evidence_runtime import OutboundEvidenceRuntime
from mars777_police.app.outbound_evidence_values import LocalEvidenceContext
from mars777_police.app.peer_runner import PeerRunner
from mars777_police.app.peer_transport import PeerTransportPort
from mars777_police.app.pregame_session_runtime import PregameSessionRuntime
from mars777_police.app.result_exchange import ResultExchange
from mars777_police.app.sealed_record_values import ActorRole
from mars777_police.app.series_audit_gate import SeriesAuditGate
from mars777_police.app.step0_runtime import Step0Runtime
from mars777_police.app.turn_protocol_runtime import TurnProtocolRuntime
from mars777_police.domain.scent_model_default import default_scent_model
from mars777_police.protocol.audit_commitment import CommitmentRecomputer
from mars777_police.protocol.config_lock import ConfigLockAuthenticator
from mars777_police.protocol.declaration import Step0Authenticator
from mars777_police.protocol.secure_nonce import SecretsNonceSource
from mars777_police.transport.peer_operations import InboundPeerOperations

SUB_GAME = 1


def pregame_for(group_id: str, slot: str) -> PregameSessionRuntime:
    """The production pregame owner for one side of the series."""
    shared = ConfigLockAuthenticator(authenticator())
    budget = config().network_and_league.token_budget_per_series
    return PregameSessionRuntime(
        Step0Runtime(group_id, Step0Authenticator(authenticator())),
        ConfigNegotiationRuntime(
            group_id, SUB_GAME, budget, PROFILES, shared, default_scent_model()
        ),
        ConfigLockRuntime(
            GAME_ID, GAME_UID, SUB_GAME, PROFILES, shared, shared, default_scent_model()
        ),
        partial(group_id, COMMIT_A, slot),
    )


@dataclass(slots=True)
class Side:
    """One peer: its inbound server, its owners, and its outbound runner."""

    group_id: str
    turn: TurnProtocolRuntime
    audit: AuditRuntime
    producer: OutboundEvidenceRuntime
    pregame: PregameSessionRuntime
    results: ResultExchange
    """One result exchange per side, shared by its inbound server and its runner."""

    own: Declaration
    """Our single-subtree snapshot: what Step-0 sends, before any merge."""

    gate: SeriesAuditGate = field(default_factory=SeriesAuditGate)
    url: str = ""
    """This side's ingress, filled in once its server is running."""

    def operations(self) -> InboundPeerOperations:
        """The production inbound adapter over this side's real owners."""
        return InboundPeerOperations(
            self.pregame, lambda: self.turn, lambda: self.audit, lambda: self.results
        )

    def runner(self, transport: PeerTransportPort, results: object | None = None) -> PeerRunner:
        """The production outbound runner over the same real owners."""
        return PeerRunner(
            transport,
            self.pregame.step0,
            self.pregame,
            lambda: self.turn,
            lambda: self.producer,
            (lambda: results) if results is not None else (lambda: self.results),
            self.gate,
        )


def side(group_id: str, slot: str, role: ActorRole) -> Side:
    """Build one production side with a fresh turn, audit and evidence runtime."""
    return Side(
        group_id,
        turn_builders.runtime(role),
        audit_builders.runtime(),
        OutboundEvidenceRuntime(
            LocalEvidenceContext(GAME_ID, GAME_UID, SUB_GAME, evidence.CONFIG, role),
            SecretsNonceSource(),
            CommitmentRecomputer(),
        ),
        pregame_for(group_id, slot),
        exchange_for(group_id, 200 if group_id == GROUP_A else 100),
        partial(group_id, COMMIT_A, slot),
    )


def server_for(peer: Side) -> LiveServer:
    """That side's real inbound FastMCP server."""
    return LiveServer(peer.operations(), f"r4-{peer.group_id}")


Provider = Callable[[], object]


def audit_over(turn: TurnProtocolRuntime, peer_group_id: str, peer_role: ActorRole) -> AuditRuntime:
    """The audit runtime for what this side actually witnessed the peer play."""
    from mars777_police.app.audit_values import SubGameContext

    return AuditRuntime(
        SubGameContext(GAME_ID, GAME_UID, SUB_GAME, evidence.CONFIG, peer_role, peer_group_id),
        turn.evidence,
        CommitmentRecomputer(),
        capture=turn.capture.inbound,
    )
