"""One role backend playing only the sub-games the schedule gives it.

This repository is the **Police** implementation and stays that way: it plays
the sub-games whose scheduled role is `POLICE`, refuses any other, and never
imports, borrows or emulates the Thief. Alternation happens one level up, in
the group gateway that routes each sub-game to the backend that owns it.

**Driven by the routed greeting, not by a clock.** A backend waits until the
gateway hands it a greeting for one of its own sub-games; only then does it send
its own greeting, play, disclose, and report that it owes nothing more -
explicitly, because a peer that is thinking looks exactly like one that finished.

**Fresh per sub-game, series-wide where the contract says so.** Board, scent,
private truth and message history are rebuilt for every gNN; the identity, the
opponent, the convention and the agreed terms are the series'.
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

from .app.commitment_codecs import CommitmentCodec
from .app.config_rules import limits_of
from .app.friendly_backend_evidence import BackendWitness
from .app.kit_backend_maker import half_turn_maker
from .app.kit_backend_settlement import BackendSettlement, row_of
from .app.kit_friendly import KitFriendlySession
from .app.kit_greeting import KitPairing
from .app.kit_half_turn import KitHalfTurnMaker
from .app.kit_messages import KitResultClaim, KitRole
from .app.kit_peer_audit import peer_chain_verified
from .app.kit_play import KitPlayState
from .app.kit_records import KitRecordChain
from .app.kit_schedule import require_ours, schedule_for
from .app.kit_session import KitSessionContext
from .app.kit_settlement import plays_final_sub_game
from .app.kit_sub_game import KitSubGame
from .app.nonce_source import NonceSourcePort
from .app.ports import TimestampPort
from .app.protocol_errors import LocalDefectError
from .app.run_class import RunClass
from .app.sealed_record_values import ActorRole
from .app.strategy_api import StrategyPort
from .domain.negotiated_config import NegotiatedConfig
from .domain.scent_model import ScentModelAgreement
from .domain.terminal import Outcome
from .transport.peer_transport import FastMcpPeerTransport

Settled = Callable[[int], Awaitable[None]]
"""Report to the group gateway that this sub-game owes nothing more."""
_CLAIM = {one: KitResultClaim(one.value.lower()) for one in Outcome}
"""Our end event in the kit's own spelling; the vocabularies coincide exactly."""


@dataclass(slots=True)
class KitRoleBackend:
    """This repository's role, playing its own rows of one alternating series."""

    context: KitSessionContext
    friendly: KitFriendlySession
    transport: FastMcpPeerTransport
    settled: Settled
    config: NegotiatedConfig
    role: ActorRole
    strategy: StrategyPort
    model: ScentModelAgreement
    nonces: NonceSourcePort
    clock: TimestampPort
    codec: CommitmentCodec
    deadline: float
    first_role: KitRole
    outcomes: dict[int, Outcome] = field(default_factory=dict)
    chains: dict[int, KitRecordChain] = field(default_factory=dict)
    verified: dict[int, bool] = field(default_factory=dict)
    witnessed: BackendWitness = field(default_factory=BackendWitness)
    settlement: BackendSettlement = field(default_factory=BackendSettlement)
    """Where finished rows go, where the series comes back, and the agreed window."""

    def __post_init__(self) -> None:
        if self.friendly.classification.run_class is not RunClass.KIT_FRIENDLY_ONLY:
            raise LocalDefectError("this backend plays development friendlies and nothing else")
        if self.context.our_role is not self.kit_role:
            raise LocalDefectError("the session context does not carry this repository's role")

    @property
    def kit_role(self) -> KitRole:
        """This repository's role, in the kit's spelling. It never changes."""
        return KitRole(self.role.value)

    @property
    def ours(self) -> tuple[int, ...]:
        """The sub-game numbers the frozen schedule gives this role backend."""
        return tuple(
            number
            for number, role in enumerate(schedule_for(self.first_role), start=1)
            if role is self.kit_role
        )

    async def run(self) -> dict[int, Outcome]:
        """Play every sub-game this backend owns, then stay for the settlement.

        Returning the moment the last sub-game is disclosed is what left a real
        series unsettled: both backends exited, the port the gateway forwards
        `submit_audit` to was dead, and the peer's series-consensus retry had
        nowhere to land. A series with no mutual settlement is scored **0 for
        both groups**, so the backend that owns the final sub-game waits for it.
        """
        for number in self.ours:
            self.outcomes[number] = await self.play_sub_game(number)
        if plays_final_sub_game(self.ours):
            await self.settlement.settle(
                self._pairing(),
                self.kit_role,
                self._send_settlement,
                self.friendly.take_settlement,
            )
        return self.outcomes

    async def play_sub_game(self, number: int) -> Outcome:
        """Wait to be handed the sub-game, play it, disclose, and hand it back."""
        require_ours(number, self.ours, self.kit_role)
        self.context.sub_game_number = number
        inbox = self.friendly.open_sub_game()
        await self.friendly.await_greeting(self.deadline)
        await self.transport.send_kit(self.context.our_greeting(self.nonces.fresh().value, number))
        chain = KitRecordChain(self.codec, self.nonces)
        self.chains[number] = chain
        game = KitSubGame(
            maker=self._maker(number, chain),
            inbox=inbox,
            send=self.transport.send_kit,
            role=self.kit_role,
            limits=limits_of(self.config),
            deadline=self.deadline,
            state=KitPlayState.opening(self.config, self.role),
        )
        outcome = await game.play()
        self.witnessed.steps[number] = game.state.step
        await self.transport.send_kit(chain.reveal(self.kit_role, _CLAIM[outcome]))
        reveal = await self.friendly.await_audit(self.deadline)
        self.verified[number] = peer_chain_verified(reveal, number, self.codec)
        self.witnessed.record(number, reveal)
        await self.settlement.contribute(row_of(self._pairing(), number, self.kit_role, outcome))
        await self.settled(number)
        return outcome

    def _pairing(self) -> KitPairing:
        """The pairing a greeting established, or a refusal saying none did."""
        pairing = self.friendly.pairing
        if pairing is None:  # pragma: no cover - a played sub-game always has one
            raise LocalDefectError("a settled series needs the pairing a greeting established")
        return pairing

    def _maker(self, number: int, chain: KitRecordChain) -> KitHalfTurnMaker:
        """This sub-game's half-turn maker, from the locked configuration."""
        return half_turn_maker(
            role=self.kit_role,
            actor=self.role,
            sub_game=number,
            strategy=self.strategy,
            model=self.model,
            chain=chain,
            clock=self.clock,
            config=self.config,
        )

    async def _send_settlement(self, envelope: dict[str, object]) -> bool:
        """Reach for the transport only when there is a settlement to send."""
        return await self.transport.send_settlement(envelope)
