"""What one agent is composed from, and what composing it yields.

The outermost layer: these values may name every layer, because assembling the
graph is exactly their job. Nothing inward imports them.

`SeriesIdentity` carries what `RuntimeSettings` deliberately does not. That
settings value refuses to hold `game_id`/`game_uid` - series identity is
established at Step-0, not read from an operator's environment - so the caller
that already knows the series states it here, explicitly, including which
sub-game is the **first** round. Nothing infers a next one.
"""

from dataclasses import dataclass

from fastmcp import FastMCP

from .app.active_runtime_context import ActiveRuntimeContext
from .app.declaration_values import Declaration
from .app.interop_profiles import InteropProfileSet
from .app.peer_runner import PeerRunner
from .app.peer_transport import PeerTransportPort
from .app.ports import ResultDigestPort, TimestampPort
from .app.pregame_session_runtime import PregameSessionRuntime
from .app.result_agreement_runtime import ResultAgreementRuntime
from .app.result_core_runtime import SubGameOutcomeLine, participants_of
from .app.result_core_values import CumulativeResult
from .app.result_exchange import ResultExchange
from .app.result_identity_values import GithubLinks
from .app.result_values import ResultContribution
from .app.series_audit_gate import SeriesAuditGate
from .transport.client import PeerClient
from .transport.peer_operations import InboundPeerOperations


@dataclass(frozen=True, slots=True)
class SeriesIdentity:
    """The series facts a process must be told, because settings cannot know them.

    `first_sub_game` is explicit on purpose: composition builds exactly the round
    it is given, and every later round arrives through
    `PregameSessionRuntime.open_round`.
    """

    game_id: str
    game_uid: str
    first_sub_game: int
    declaration: Declaration
    profiles: InteropProfileSet
    token_budget_per_series: int

    def __post_init__(self) -> None:
        for name in ("game_id", "game_uid"):
            if not getattr(self, name):
                raise ValueError(f"{name} must be non-empty")
        if type(self.first_sub_game) is not int or self.first_sub_game < 1:
            raise ValueError(f"first_sub_game must be a positive int, got {self.first_sub_game!r}")


@dataclass(frozen=True, slots=True)
class AgentComposition:
    """One assembled agent: the objects a later BOOT stage has to drive.

    Deliberately not every object that was built. The crypto primitives, codecs
    and round runtimes are reachable through the owners that hold them, and
    exposing them here would invite a caller to use one directly instead of
    through the owner that validates its inputs.

    Nothing here is running. The server is constructed, the client is unentered,
    and no session, socket or tunnel exists yet.
    """

    server: FastMCP
    peer_client: PeerClient
    peer_transport: PeerTransportPort
    peer_runner: PeerRunner
    inbound_operations: InboundPeerOperations
    pregame: PregameSessionRuntime
    runtime_context: ActiveRuntimeContext
    series_audit: SeriesAuditGate
    identity: SeriesIdentity
    group_id: str
    clock: TimestampPort
    digester: ResultDigestPort

    def complete_result(
        self,
        *,
        lines: tuple[SubGameOutcomeLine, ...],
        links: GithubLinks,
        cumulative: CumulativeResult,
        own: ResultContribution,
    ) -> ResultExchange:
        """Build the series-final result owner, once its inputs actually exist.

        Every argument is something only a finished series knows - the outcome
        lines, the totals, our six contributed commits and token counts. The
        static half (transport, digest, clock, identity, the merged declaration)
        was assembled at composition time, so the caller supplies the late facts
        and nothing else. The result is bound here, so the inbound and outbound
        paths see the same object without either being handed it separately.
        """
        declaration = self.pregame.declaration
        runtime = ResultAgreementRuntime(
            self.group_id,
            self.identity.game_id,
            self.identity.game_uid,
            participants_of(declaration),
            self.clock,
        )
        exchange = ResultExchange(
            runtime,
            self.peer_transport,
            self.digester,
            declaration,
            lines,
            links,
            cumulative,
            own,
        )
        self.runtime_context.bind_result(exchange)
        return exchange
