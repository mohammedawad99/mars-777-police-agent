"""Two production sides wired to each other in-process, with no network.

The driver's contract is about *ordering* - commit before acknowledging, adopt
after the peer's reveal, validate against the step's start board - and ordering
is exactly what a real socket makes hard to observe. So these two sides speak
through a loopback that hands each message straight to the peer's live turn
runtime: every owner is the production one, only the wire is removed.

`ActiveRuntimeContext` is on both ends deliberately. Production resolves the
current turn through it, so a harness that let the runner and the inbound path
read different runtimes would be testing a wiring nobody ships.
"""

import asyncio
from dataclasses import dataclass, field

import runner_builders as build
from r16_builders import GROUP_A, GROUP_B

from mars777_police.app.active_runtime_context import ActiveRuntimeContext
from mars777_police.app.capture_values import TurnOutcome
from mars777_police.app.hint_policy import TemplateHintPolicy
from mars777_police.app.outbound_evidence_runtime import OutboundEvidenceRuntime
from mars777_police.app.peer_runner import PeerRunner
from mars777_police.app.peer_turn_messages import Acknowledgement, Commitment, Reveal
from mars777_police.app.pregame_session_runtime import PregameSessionRuntime
from mars777_police.app.sealed_record_values import ActorRole
from mars777_police.app.sub_game_driver import SubGameDriver
from mars777_police.app.turn_service import LocalTurnService
from mars777_police.domain.barriers import BarrierQuota
from mars777_police.domain.board import Board, Position
from mars777_police.domain.terminal import TurnLimits
from mars777_police.domain.truth import LocalTruth

GRID = 7
LIMITS = TurnLimits(max_moves=35, survival_threshold=35)
QUOTA = BarrierQuota(max_barriers=14)
STARTS = {ActorRole.POLICE: Position(0, 0), ActorRole.THIEF: Position(0, 1)}
HINT_WORDS = 15


def board(*blocked: Position) -> Board:
    """The locked geometry, carrying exactly the barriers named."""
    return Board(rows=GRID, cols=GRID, blocked=frozenset(blocked))


@dataclass(slots=True)
class Loopback:
    """Delivers each outbound message straight into the peer's live runtime."""

    peer: "Peer | None" = field(default=None)
    reject: bool = field(default=False)
    """Answer our reveal with `accepted=False`, as a peer whose board disagrees."""

    async def _turn(self) -> object:
        """Yield first: a real transport always does, and the driver relies on it."""
        assert self.peer is not None
        await asyncio.sleep(0)
        return self.peer.context.current_turn()

    async def send_commitment(self, commitment: Commitment) -> None:
        (await self._turn()).accept_commitment(commitment)  # type: ignore[attr-defined]

    async def send_acknowledgement(self, acknowledgement: Acknowledgement) -> None:
        (await self._turn()).accept_acknowledgement(acknowledgement)  # type: ignore[attr-defined]

    async def send_reveal(self, reveal: Reveal) -> TurnOutcome:
        turn = await self._turn()
        answered = turn.accept_reveal(reveal)  # type: ignore[attr-defined]
        if self.reject:
            return TurnOutcome(False, answered.capture)
        return answered  # type: ignore[no-any-return]


@dataclass(slots=True)
class Peer:
    """One production side: real pregame, evidence, runner and driver."""

    role: ActorRole
    context: ActiveRuntimeContext
    pregame: PregameSessionRuntime
    producer: OutboundEvidenceRuntime
    runner: PeerRunner
    loopback: Loopback
    driver: SubGameDriver


def peer(
    role: ActorRole,
    group_id: str,
    slot: str,
    strategy: object,
    start: Position | None = None,
) -> Peer:
    """Build one side around *strategy*, with its own context and evidence."""
    side = build.side(group_id, slot, role)
    context = ActiveRuntimeContext()
    loopback = Loopback()
    runner = PeerRunner(
        loopback,  # type: ignore[arg-type]
        side.pregame.step0,
        side.pregame,
        context.current_turn,
        lambda: side.producer,
        context.current_result,
        side.gate,
    )
    driver = SubGameDriver(
        strategy=strategy,  # type: ignore[arg-type]
        runner=runner,
        context=context,
        role=role,
        turns=LocalTurnService(limits=LIMITS, quota=QUOTA),
        config_sha256=side.producer.context.config_sha256,
        hints=TemplateHintPolicy(role=role, hint_max_words=HINT_WORDS),
        sub_game=side.producer.context.sub_game,
        truth=LocalTruth(board=board(), own_position=start or STARTS[role]),
        deadline=5.0,
    )
    return Peer(role, context, side.pregame, side.producer, runner, loopback, driver)


def facing(
    police_strategy: object,
    thief_strategy: object,
    police_start: Position | None = None,
    thief_start: Position | None = None,
) -> tuple[Peer, Peer]:
    """Two sides pointed at each other through the loopback."""
    a = peer(ActorRole.POLICE, GROUP_A, "group_a", police_strategy, police_start)
    b = peer(ActorRole.THIEF, GROUP_B, "group_b", thief_strategy, thief_start)
    a.loopback.peer, b.loopback.peer = b, a
    a.driver.open()
    b.driver.open()
    return a, b
