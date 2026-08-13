"""Real production owners behind the concrete adapter - no application doubles.

Every runtime below is the production class with production crypto injected, so
a refusal in this suite comes from the application rather than from a fixture.
The only test-owned objects are the two lifecycle providers, which is exactly
what Stage 5-R3 established they have to be.
"""

import audit_builders
import cadence_ops
import turn_builders
from peer_ops import authenticator
from r16_builders import COMMIT_A, GAME_ID, GAME_UID, GROUP_A, GROUP_B, PROFILES, config, partial

from mars777_police.app.audit_runtime import AuditRuntime
from mars777_police.app.config_lock_runtime import ConfigLockRuntime
from mars777_police.app.config_negotiation_runtime import ConfigNegotiationRuntime
from mars777_police.app.peer_pregame_messages import (
    ConfigLockContext,
    ConfigLockEvidence,
    ConfigProposal,
)
from mars777_police.app.pregame_session_runtime import PregameSessionRuntime
from mars777_police.app.result_exchange import ResultExchange
from mars777_police.app.step0_runtime import Step0Runtime
from mars777_police.app.turn_protocol_runtime import TurnProtocolRuntime
from mars777_police.domain.scent_model_default import default_scent_model
from mars777_police.protocol.config_lock import ConfigLockAuthenticator
from mars777_police.protocol.declaration import Step0Authenticator
from mars777_police.transport.inbound_session import InboundSession
from mars777_police.transport.peer_operations import InboundPeerOperations

SUB_GAME = 1
BUDGET = config().network_and_league.token_budget_per_series


def locker() -> ConfigLockAuthenticator:
    """The production adapter that is both digest port and lock auth port."""
    return ConfigLockAuthenticator(authenticator())


def pregame() -> PregameSessionRuntime:
    """The production pregame owner, with real Step-0, negotiation and lock."""
    shared = locker()
    return PregameSessionRuntime(
        Step0Runtime(GROUP_A, Step0Authenticator(authenticator())),
        ConfigNegotiationRuntime(
            GROUP_A, SUB_GAME, BUDGET, PROFILES, shared, default_scent_model()
        ),
        ConfigLockRuntime(
            GAME_ID, GAME_UID, SUB_GAME, PROFILES, shared, shared, default_scent_model()
        ),
        partial(GROUP_A, COMMIT_A, "group_a"),
    )


def negotiation_for(sub_game: int) -> ConfigNegotiationRuntime:
    """The negotiation runtime one authoritative round owns."""
    return ConfigNegotiationRuntime(
        GROUP_A, sub_game, BUDGET, PROFILES, locker(), default_scent_model()
    )


def lock_for(sub_game: int) -> ConfigLockRuntime:
    """The lock runtime the same round owns, sharing the production adapter."""
    shared = locker()
    return ConfigLockRuntime(
        GAME_ID, GAME_UID, sub_game, PROFILES, shared, shared, default_scent_model()
    )


def round_of(sub_game: int) -> tuple[ConfigNegotiationRuntime, ConfigLockRuntime]:
    """Both round-scoped runtimes for *sub_game*, built by the caller."""
    return negotiation_for(sub_game), lock_for(sub_game)


def proposal_for(sub_game: int) -> ConfigProposal:
    """A complete proposal naming *sub_game*."""
    return ConfigProposal(sub_game, config(), PROFILES, default_scent_model())


def lock_evidence_for(sub_game: int) -> ConfigLockEvidence:
    """Authenticated lock evidence for *sub_game*, over the real digest."""
    shared = locker()
    context = ConfigLockContext(
        GAME_ID,
        GAME_UID,
        sub_game,
        shared.digest(config()),
        PROFILES,
        shared.scent_model_digest(default_scent_model()),
    )
    return ConfigLockEvidence(context, shared.prove(context))


def exchange() -> ResultExchange:
    """The production `ResultExchange` for our side of the series."""
    return cadence_ops.exchange_for(GROUP_A, 200)


def operations(
    turn: TurnProtocolRuntime | None = None,
    audit: AuditRuntime | None = None,
    session_runtime: PregameSessionRuntime | None = None,
) -> InboundPeerOperations:
    """The concrete production adapter over real owners."""
    live_turn = turn if turn is not None else turn_builders.runtime()
    live_audit = audit if audit is not None else audit_builders.runtime()
    return InboundPeerOperations(
        session_runtime if session_runtime is not None else pregame(),
        lambda: live_turn,
        lambda: live_audit,
        lambda: exchange(),
    )


def bound(peer: str = GROUP_B) -> InboundSession:
    """A session that a successful Step-0 has already authenticated."""
    return InboundSession("session-1", peer)


def unbound() -> InboundSession:
    """A fresh session: no Step-0 has happened on it."""
    return InboundSession("session-2")


def agreed() -> object:
    """The config this side agrees for the current round."""
    return config()
