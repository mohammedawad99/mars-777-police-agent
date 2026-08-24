"""Assembling the group's one result agreement, once a whole series exists.

The strict composition builds a `ResultExchange` the moment a single process
finishes six sub-games, because that process saw all of them. An alternating
group has no such process: the declaration arrives at Step-0, the rows and the
contribution entries arrive from two backends, and only the gateway holds the
set. So the exchange is assembled **late**, here, from parts the gateway already
collects - and until every part is present there is no exchange at all.

**Nothing static is invented per attempt.** The transport, the digest authority
and the clock are built once; only the late facts - the six outcome lines, the
totals, this group's own six contributed commits and token counts - are read
when the builder runs. That is the same split `Composition.complete_result`
already makes on the internal wire.

**The peer speaks the pinned wire, so the transport does too.** The one shared
semantic kind travels as `receive_control` with a `message` argument; the
argument builder decides that from the profile, and no call site here chooses a
shape.
"""

from .app.kit_result_agreement import GroupResultAgreement
from .app.kit_result_document import role_totals, series_outcome_of
from .app.peer_transport import PeerTransportPort
from .app.result_agreement_runtime import ResultAgreementRuntime
from .app.result_core_runtime import participants_of
from .app.result_core_values import CumulativeResult
from .app.result_exchange import ResultExchange
from .app.series_roles_source import series_roles_for
from .counted_result_core import line_of, links_of
from .infra.clock import SystemClock
from .protocol.result_core import ResultDigester


def group_agreement(
    gateway: object,
    transport: PeerTransportPort,
) -> GroupResultAgreement:
    """The group's single result-agreement authority, assembled on demand.

    *gateway* is read rather than mutated: the builder asks it for the merged
    declaration, the six settled rows and this group's six contribution entries,
    and answers `None` while any of them is outstanding.
    """
    digester = ResultDigester()
    clock = SystemClock()

    def build() -> ResultExchange | None:
        declaration = getattr(gateway, "declaration", None)
        if declaration is None or not declaration.teams.is_merged:
            return None
        if not gateway.collected.complete or not gateway.contributed.complete:  # type: ignore[attr-defined]
            return None
        if gateway.settlement.agreed is None:  # type: ignore[attr-defined]
            return None
        group_id = gateway.group_id  # type: ignore[attr-defined]
        ordered = sorted(
            gateway.collected.series(),  # type: ignore[attr-defined]
            key=lambda row: int(row["sub_game_number"]),
        )
        cop, thief = role_totals(ordered)
        runtime = ResultAgreementRuntime(
            group_id,
            declaration.game_id,
            declaration.game_uid,
            participants_of(declaration),
            clock,
        )
        return ResultExchange(
            runtime,
            transport,
            digester,
            declaration,
            tuple(line_of(row) for row in ordered),
            links_of(declaration),
            CumulativeResult(cop, thief, series_outcome_of(cop, thief)),
            gateway.contributed.contribution(group_id),  # type: ignore[attr-defined]
            series_roles_for(declaration, group_id),
        )

    return GroupResultAgreement(build)
