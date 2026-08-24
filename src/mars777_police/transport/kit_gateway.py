"""One stable group-facing router, and two private role backends behind it.

`teams.<group>.mcp_endpoint` is **group-level**, not role-level: one MaRs-777
identity, one opponent, one `game_id`, one `game_uid`, one six-sub-game series.
The pinned harness alternates its role every sub-game, so ours must alternate
too - and it does so by routing to a different **backend process**, never by
turning a role repository into a dual-role agent.

**Transport and series routing only.** This owns which backend the next message
belongs to, the live sub-game number, the frozen convention and the handoff
gate. It owns no board, no position, no legality, no strategy, no scent, no
commitment, no audit decision and no score - every one of those stays in the
role backend that already owns it, and this forwards to exactly one of them.

**Routing comes from the contract, not from the connection.** The expected role
is `frozen convention + sub-game number + agreed first assignment`; the peer's
declared role is validated against it. Nothing is inferred from a source port, a
process id, an arrival time or a strategy output, and no message is ever
broadcast to both backends.
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

from ..app.counted_mode import CountedRun, rehearsal
from ..app.declaration_values import Declaration
from ..app.kit_contribution_entries import ContributionCollector, accept
from ..app.kit_handoff import SeriesHandoff
from ..app.kit_messages import KitRole
from ..app.kit_result_agreement import GroupResultAgreement
from ..app.kit_series_rows import SeriesRowCollector
from ..app.official_artifacts import OfficialArtifactCollector
from ..app.protocol_errors import StaleMessageError
from ..app.series_assembly import SeriesParts
from ..app.series_result_owner import SeriesResultOwner
from .kit_envelopes import KIT_ARGUMENT_NAMES, KIT_OK, KitJson, KitNegotiateMessage, parse_kit
from .kit_series_writeout import write_series

Forward = Callable[[str, KitJson], Awaitable[None]]
"""Send one already-built KIT call to one backend, over a real transport."""


@dataclass(slots=True)
class KitGroupGateway:
    """The group's one ingress: it routes, and it decides nothing about a game."""

    handoff: SeriesHandoff
    routes: dict[KitRole, Forward]
    deadline: float
    artifacts: OfficialArtifactCollector = field(default_factory=OfficialArtifactCollector)
    """The group's per-sub-game official documents, from whichever backend built each.

    Kept beside the rows and for the same reason: this is the only part of the
    group both backends can reach. It stores documents and judges none of them.
    """

    counted: CountedRun = field(default_factory=rehearsal)
    """What this run is worth. Only a counted run writes the official set."""

    declaration: Declaration | None = field(default=None)
    """The merged Step-0 declaration, once one has arrived. Series-wide, like the result."""

    write: "Callable[[SeriesParts], tuple[str, ...] | None] | None" = field(default=None)
    """How the group writes its fourteen files, or `None` when it does not write."""

    settlement: SeriesResultOwner = field(default_factory=SeriesResultOwner)
    """The consensus digest the g06 owner agreed, and the result it licenses.

    Held here for the third time for the same reason: the group's series-wide
    facts have no other place both backends can reach."""

    group_id: str = field(default="")
    """Which participant this group is. Supplied by composition, never imported."""

    agreement: "GroupResultAgreement | None" = field(default=None)
    """The group's one result-agreement authority, or `None` for a rehearsal."""

    contributed: ContributionCollector = field(default_factory=ContributionCollector)

    collected: SeriesRowCollector = field(default_factory=SeriesRowCollector)
    """The group's finished rows, from both backends. It judges none of them."""

    async def negotiate(self, message: KitJson) -> dict[str, bool]:
        """Assign a sub-game to the backend that will play it, then acknowledge.

        The acknowledgement means **assigned**. A greeting for the next
        sub-game waits here - bounded - until the previous one has actually
        settled, because answering `ok` for a greeting nobody will act on makes
        the opponent burn its whole connect budget on our own politeness.
        """
        greeting = parse_kit(KitNegotiateMessage, message)
        number = (
            self.handoff.sub_game
            if greeting.sub_game_number is None
            else (greeting.sub_game_number)
        )
        expected = self.handoff.role_of(number)
        self._require_complementary(greeting.role, expected)
        await self.handoff.await_assignable(number, self.deadline)
        self.handoff.open(number)
        await self._forward("negotiate", message)
        return KIT_OK

    async def receive_turn(self, message: KitJson) -> dict[str, bool]:
        """Route a half-turn to the one backend that owns the live sub-game."""
        await self._forward("receive_turn", message)
        return KIT_OK

    async def submit_audit(self, payload: KitJson) -> dict[str, bool]:
        """Route a disclosure to the backend that played the sub-game settling."""
        await self._forward("submit_audit", payload)
        return KIT_OK

    async def receive_control(self, message: KitJson) -> dict[str, bool]:
        """Route a status signal. It settles nothing and moves no cursor."""
        await self._forward("receive_control", message)
        return KIT_OK

    def contribute(self, row: KitJson) -> None:
        """Take one finished row from the backend that played it."""
        self.collected.record(row)
        write_series(self)

    def contribute_entry(self, sub_game: int, role: KitRole, commit: str, tokens: int) -> None:
        """Take one backend's participant-owned entry, admitted before it is stored."""
        first = self.handoff.first_role
        accept(
            self.contributed, self.declaration, self.group_id, first, role, sub_game, commit, tokens
        )

    def contribute_artifact(self, kind: str, sub_game: int, document: KitJson) -> None:
        """Take one official per-sub-game document from the backend that built it.

        Held here for the same reason the rows are: a two-process group plays
        three sub-games in each process and still owes one set of fourteen files,
        so the halves have to meet where both backends can reach.
        """
        self.artifacts.record(kind, sub_game, document)
        write_series(self)

    def series_settled(self, consensus_sha256: str) -> None:
        """Take the digest the g06 owner agreed, then try to write the series."""
        self.settlement.settle(consensus_sha256)
        write_series(self)

    def official_artifact(self, kind: str, sub_game: int) -> KitJson | None:
        """One collected document, for whichever process writes the series out."""
        return self.artifacts.get(kind, sub_game)

    def series_rows(self) -> tuple[KitJson, ...]:
        """The group's six finished rows, for the backend that settles the series."""
        return self.collected.series()

    def settle(self, sub_game: int) -> None:
        """The backend playing *sub_game* reports it owes nothing more for it.

        Signalled, never inferred: a peer that is thinking and a sub-game that
        has finished look identical from the outside, and the difference decides
        whether the next greeting is answered by the right backend.
        """
        if sub_game != self.handoff.sub_game:
            raise StaleMessageError(
                f"sub-game {sub_game} is not the live one ({self.handoff.sub_game})",
            )
        self.handoff.begin_settlement()
        self.handoff.settled()

    def _require_complementary(self, declared: str | None, expected: KitRole) -> None:
        """The peer must take the side our schedule does not. Omission is silence."""
        if declared is None:
            return
        if KitRole(declared) is expected:
            raise StaleMessageError(
                f"role collision: our schedule takes {expected.value!r} in this sub-game"
                f" and the peer declared it too; the two sides of a game are complementary",
            )

    async def _forward(self, tool: str, body: KitJson) -> None:
        """Hand the call to exactly one backend - never to both, never to neither."""
        role = self.handoff.role
        forward = self.routes.get(role)
        if forward is None:
            raise StaleMessageError(f"no {role.value} backend is registered for this series")
        await forward(tool, {KIT_ARGUMENT_NAMES[tool]: body})
