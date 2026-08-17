"""One sub-game, played by this agent instead of by a test.

Ch 8 §8.3 defines the orchestrator as the component that *"initializes the
connections, **activates the decision module**, coordinates between components
… but **does not itself contain decision logic**. Its role is to coordinate, not
to execute."* This is that coordinator for one sub-game: it asks the strategy,
hands the answer to the owners that already exist, and decides nothing about the
game itself. Legality stays in `LocalTurnService`, capture in `capture_rules`,
scent in `PeerRunner.open_turn`, the end event in `domain.terminal`.

**Three ordering rules carry the whole design** (JDEC-016 §4: `state.self_pos`
and `state.barriers` are pre-action, both actors of a step are checked against
that same start state, and the step's effects apply afterwards):

* **R1 - commit before acknowledging.** `open_turn` projects our emission from
  the board we started the round with. Acknowledging first would let the peer's
  step-`k` reveal fold their barrier into that board, and the audit would then
  recompute a different emission than the one we sent.
* **R2 - the peer's reveal before our adoption.** `observe_reveal` answers the
  capture question from `truth.own_position`. Adopting first would answer from
  the cell we moved *to*, while the audit recomputes from the cell we sealed -
  a disagreement scored as dishonesty rather than as the mistake it is.
* **R3 - apply against `start_truth`.** Our action was lawful on `B_k`. Applying
  it to a board that has since gained the peer's barrier would let their
  same-step move retroactively make our committed action illegal.

**One authoritative truth.** `start_truth` is not a second owner - it is the
value the single authoritative `LocalTruth` had when the round opened, held for
the length of one round and replaced once. `completed_steps` keeps its Stage-3C
meaning, accepted local actions, which under lockstep is also the round number.
"""

import asyncio
from dataclasses import dataclass, field

from ..domain.actions import PhysicalAction
from ..domain.observation import observation_of
from ..domain.terminal import Outcome, evaluate_terminal
from ..domain.truth import LocalTruth
from .active_runtime_context import ActiveRuntimeContext
from .hint_policy import HintPort
from .peer_runner import PeerRunner
from .protocol_errors import LocalDefectError
from .protocol_values import Sha256Digest
from .sealed_record_values import ActorRole, SealedState
from .strategy_api import StrategyPort
from .sub_game_truth import caught_in, declared_barriers, merged_truth
from .turn_cursor import TurnCursor
from .turn_protocol_runtime import TurnProtocolRuntime
from .turn_service import LocalTurnService


@dataclass(slots=True)
class SubGameDriver:
    """Plays one sub-game to its natural end and reports the end event."""

    strategy: "StrategyPort"
    runner: PeerRunner
    context: ActiveRuntimeContext
    role: ActorRole
    turns: LocalTurnService
    config_sha256: Sha256Digest
    hints: HintPort
    sub_game: int
    truth: LocalTruth
    deadline: float
    captured: bool = field(default=False)

    def open(self) -> TurnProtocolRuntime:
        """Bind the runtime for the round we are about to play, and return it.

        Called **before** either peer commits, because a commitment arriving
        while nothing is bound is refused as stale - so the next round is bound
        as soon as this one is adopted, not when it is played, and a faster peer
        finds our runtime already waiting. **Never past the end:** `play_round`
        binds only while `settled()` is `None`, so a finished sub-game leaves the
        terminal round bound and no cursor the game never reached.
        """
        turn = TurnProtocolRuntime(
            role=self.role,
            turns=self.turns,
            truth=self.truth,
            cursor=TurnCursor(self.sub_game, self.truth.completed_steps + 1),
        )
        self.context.bind_turn(turn)
        return turn

    def settled(self) -> Outcome | None:
        """The end event this sub-game has reached, or `None` while it continues.

        `domain.terminal` decides it, from a capture only the answering side
        could have reported and a step count only our own accepted actions moved.
        """
        return evaluate_terminal(
            captured=self.captured,
            step=self.truth.completed_steps,
            limits=self.turns.limits,
        )

    async def play_sub_game(self) -> Outcome:
        """Play rounds until the domain says the sub-game is over, then say so."""
        while True:
            settled = self.settled()
            if settled is not None:
                return settled
            await self.play_round()

    async def play_round(self) -> None:
        """One lockstep round: decide, seal, exchange, and adopt exactly once."""
        turn = self.context.current_turn()
        start, cursor = self.truth, turn.cursor
        action = self.strategy.choose_action(observation_of(start, self.turns.quota))
        spoken = self.hints.choose(cursor, action)
        prepared = await self.runner.open_turn(
            state=SealedState(
                self.config_sha256,
                start.own_position,
                declared_barriers(start),
                cursor.step,
                self.role,
            ),
            action=action,
            intent=spoken.intent,
            hint=spoken.text,
            cursor=cursor,
        )
        await self._await(turn.milestones.peer_committed)
        await self.runner.acknowledge_peer_turn()
        await self._await(turn.milestones.acknowledged)
        answered = await self.runner.reveal_turn(prepared)
        await self._await(turn.milestones.peer_revealed)
        if not answered.accepted:
            raise LocalDefectError(f"the peer could not accept our {cursor} action")
        self.truth = self.adopt(turn, action, start)
        self.captured = self.captured or caught_in(turn)
        if self.settled() is None:
            self.open()

    def adopt(
        self, turn: TurnProtocolRuntime, action: PhysicalAction, start: LocalTruth
    ) -> LocalTruth:
        """Make our own accepted action authoritative, once and against `B_k`."""
        if self.truth.completed_steps != turn.cursor.step - 1:
            raise LocalDefectError(f"{turn.cursor} was already adopted by this driver")
        return merged_truth(self.turns.apply(start, action).truth, turn.truth)

    async def _await(self, arrived: asyncio.Event) -> None:
        """Suspend until the inbound path records it, within the agreed deadline."""
        await asyncio.wait_for(arrived.wait(), self.deadline)
