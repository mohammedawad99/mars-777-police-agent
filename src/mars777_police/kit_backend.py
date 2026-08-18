"""One role backend playing only the sub-games the schedule gives it.

This repository is the **Police** implementation and stays that way: it plays
the sub-games whose scheduled role is `POLICE`, refuses any other, and never
imports, borrows or emulates the Thief. Alternation happens one level up, in
the group gateway that routes each sub-game to the backend that owns it.

**Driven by the routed greeting, not by a clock.** A backend waits until the
gateway hands it a greeting for one of its own sub-games; only then does it send
its own greeting, play, disclose, and report that it owes nothing more. The
report is explicit because settlement cannot be inferred - a peer that is
thinking looks exactly like a sub-game that has finished.

**Fresh per sub-game, series-wide where the contract says so.** Board, scent,
private truth and message history are rebuilt for every gNN; the identity, the
opponent, the convention and the agreed terms are the series', and are held by
the session context that outlives each sub-game.
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

from .app.commitment_codecs import CommitmentCodec
from .app.config_rules import hints_of, limits_of, rules_of
from .app.kit_friendly import KitFriendlySession
from .app.kit_half_turn import KitHalfTurnMaker
from .app.kit_messages import KitResultClaim, KitRole
from .app.kit_peer_audit import peer_chain_verified
from .app.kit_play import KitPlayState
from .app.kit_records import KitRecordChain
from .app.kit_schedule import schedule_for
from .app.kit_session import KitSessionContext
from .app.kit_sub_game import KitSubGame
from .app.nonce_source import NonceSourcePort
from .app.ports import TimestampPort
from .app.protocol_errors import LocalDefectError
from .app.run_class import RunClass
from .app.sealed_record_values import ActorRole
from .app.strategy_api import StrategyPort
from .app.turn_service import LocalTurnService
from .domain.negotiated_config import NegotiatedConfig
from .domain.scent_model import ScentModelAgreement
from .domain.terminal import Outcome
from .transport.peer_transport import FastMcpPeerTransport

Settled = Callable[[int], Awaitable[None]]
"""Report to the group gateway that this sub-game owes nothing more."""

_CLAIM = {
    Outcome.CAPTURE: KitResultClaim.CAPTURE,
    Outcome.SURVIVAL: KitResultClaim.SURVIVAL,
    Outcome.TECHNICAL_LOSS: KitResultClaim.TECHNICAL_LOSS,
}


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

    def require_ours(self, sub_game: int) -> None:
        """Refuse a sub-game the schedule did not give us, structurally."""
        if sub_game not in self.ours:
            raise LocalDefectError(
                f"sub-game {sub_game} is not this {self.kit_role.value} backend's;"
                f" this repository plays {self.ours} and never the other side",
            )

    async def run(self) -> dict[int, Outcome]:
        """Play every sub-game this backend owns, in order, and report each."""
        for number in self.ours:
            self.outcomes[number] = await self.play_sub_game(number)
        return self.outcomes

    async def play_sub_game(self, number: int) -> Outcome:
        """Wait to be handed the sub-game, play it, disclose, and hand it back."""
        self.require_ours(number)
        self.context.sub_game_number = number
        inbox = self.friendly.open_sub_game()
        await self.friendly.await_greeting(self.deadline)
        await self.transport.send_kit(self.context.our_greeting(self.nonces.fresh().value, number))
        chain = KitRecordChain(self.codec, self.nonces)
        self.chains[number] = chain
        outcome = await KitSubGame(
            maker=self._maker(number, chain),
            inbox=inbox,
            send=self.transport.send_kit,
            role=self.kit_role,
            limits=limits_of(self.config),
            deadline=self.deadline,
            state=KitPlayState.opening(self.config, self.role),
        ).play()
        await self.transport.send_kit(chain.reveal(self.kit_role, _CLAIM[outcome]))
        reveal = await self.friendly.await_audit(self.deadline)
        self.verified[number] = peer_chain_verified(reveal, number, self.codec)
        await self.settled(number)
        return outcome

    def _maker(self, number: int, chain: KitRecordChain) -> KitHalfTurnMaker:
        """One sub-game's half-turn maker, from the terms the pairing agreed."""
        limits = limits_of(self.config)
        return KitHalfTurnMaker(
            role=self.kit_role,
            actor=self.role,
            sub_game=number,
            strategy=self.strategy,
            turns=LocalTurnService(limits, rules_of(self.config).quota),
            hints=hints_of(self.config, self.role),
            model=self.model,
            chain=chain,
            clock=self.clock,
            survival_threshold=limits.survival_threshold,
        )
