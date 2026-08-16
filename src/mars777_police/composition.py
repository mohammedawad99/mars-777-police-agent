"""The composition root: one agent's object graph, assembled once.

This is the only module allowed to name every layer, because dependency
assembly is what it does. Nothing inward imports it, so the inward-only rule
`DEPENDENCY_RULES.md` D1 states is unaffected - and D4's "one composition root"
is now satisfied by a module rather than by a comment in a test.

**It constructs; it does not run.** No `asyncio.run`, no `uvicorn.run`, no
session entered, no socket bound, no tunnel opened, no Step-0 sent, no artifact
written. The returned `PeerClient` is deliberately *unentered*: holding one
session across calls is what keeps the remote side's authentication valid, and
deciding when that session opens and closes is the BOOT stage's job, not this
one's.

**`ResultExchange` is absent on purpose.** It is assembled from six completed
sub-games, so at startup there is nothing truthful to build it from. The two
long-lived adapters resolve it through `ActiveRuntimeContext` instead, and
`AgentComposition.complete_result` builds the real one when the series ends.
Fabricating a placeholder here would put invented scores inside the object whose
whole purpose is to hash the true result.
"""

from .app.active_runtime_context import ActiveRuntimeContext
from .app.auth_values import AuthProfile
from .app.baseline_strategy import BaselineStrategy
from .app.config_lock_runtime import ConfigLockRuntime
from .app.config_negotiation_runtime import ConfigNegotiationRuntime
from .app.peer_runner import PeerRunner
from .app.peer_supervision import PeerDeadline, TimeoutPolicy
from .app.pregame_session_runtime import PregameSessionRuntime
from .app.series_audit_gate import SeriesAuditGate
from .app.step0_runtime import Step0Runtime
from .composition_values import AgentComposition, SeriesIdentity
from .domain.scent_model_default import default_scent_model
from .infra.clock import SystemClock
from .infra.settings import RuntimeSettings
from .protocol.config_lock import ConfigLockAuthenticator
from .protocol.declaration import Step0Authenticator
from .protocol.keyed_auth import HmacSha256Provider, KeyedAuthenticator
from .protocol.result_core import ResultDigester
from .transport.client import PeerClient
from .transport.peer_operations import InboundPeerOperations
from .transport.peer_transport import FastMcpPeerTransport
from .transport.server import build_server

PEER_TIMEOUT_SECONDS = 30.0
"""The pre-lock deadline for outbound calls until a config fixes one.

It bounds negotiation only. Once a lock is verified the agreed
`response_timeout_sec` takes over, which is what `PeerDeadline` is for: a
client that demanded a locked config could never make the calls that produce
one, and a client that kept this constant would ignore what the peers agreed.
"""


def keyed_authenticator(settings: RuntimeSettings) -> KeyedAuthenticator:
    """The one provisioned keyed authenticator this process trusts.

    Built from the settings key material and never from a peer's claim: the
    profile is fixed before the first byte arrives, which is what makes an
    algorithm substitution ineffective rather than merely detectable.
    """
    return KeyedAuthenticator(
        AuthProfile.HMAC_SHA256,
        settings.key_id,
        HmacSha256Provider({settings.key_id.value: settings.secret.reveal()}),
    )


def compose_agent(
    settings: RuntimeSettings, identity: SeriesIdentity, group_id: str
) -> AgentComposition:
    """Assemble one agent from the accepted production implementations.

    *group_id* is this repository's own frozen group code; *identity* carries
    the series facts settings deliberately refuses to hold. The first config
    round is built for `identity.first_sub_game` and no other - later rounds go
    through `PregameSessionRuntime.open_round`.
    """
    keyed = keyed_authenticator(settings)
    lock_auth = ConfigLockAuthenticator(keyed)
    step0 = Step0Runtime(group_id, Step0Authenticator(keyed))
    pregame = PregameSessionRuntime(
        step0,
        ConfigNegotiationRuntime(
            group_id,
            identity.first_sub_game,
            identity.token_budget_per_series,
            identity.profiles,
            lock_auth,
            default_scent_model(),
        ),
        ConfigLockRuntime(
            identity.game_id,
            identity.game_uid,
            identity.first_sub_game,
            identity.profiles,
            lock_auth,
            lock_auth,
            default_scent_model(),
        ),
        identity.declaration,
    )
    active = ActiveRuntimeContext()
    inbound = InboundPeerOperations(
        pregame, active.current_turn, active.current_audit, active.current_result
    )
    deadline = PeerDeadline(
        TimeoutPolicy(PEER_TIMEOUT_SECONDS),
        lambda: pregame.config if pregame.locked_evidence is not None else None,
    )
    client = PeerClient(_opponent_url(settings), deadline)
    transport = FastMcpPeerTransport(client)
    series = SeriesAuditGate()
    return AgentComposition(
        build_server(inbound, name=f"{group_id}-{settings.role.value}"),
        client,
        transport,
        PeerRunner(
            transport,
            step0,
            pregame,
            active.current_turn,
            active.current_evidence,
            active.current_result,
            series,
        ),
        inbound,
        pregame,
        active,
        series,
        identity,
        group_id,
        SystemClock(),
        ResultDigester(),
        BaselineStrategy(),
    )


def _opponent_url(settings: RuntimeSettings) -> str:
    """The opponent ingress the operator configured, or a local refusal."""
    opponent = settings.opponent
    if opponent is None:
        raise ValueError("the opponent public endpoint must be configured before composing")
    return opponent.url
