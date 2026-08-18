"""Taking one of our half-turns on the pinned wire, and what rides out with it.

One message carries everything the kit's half-turn carries: the sealed commit,
the hint, our own field, the barrier we just declared, the claim we are making,
the answer we owe from their last claim, and - if we are the thief and have
reached the threshold - the survival claim.

**The claim is the cop's own cell.** Under hidden positions a capture is
co-location, so the cop declares where *it* now stands and the thief answers
whether that is where it is. Nothing else about either position travels.

**Survival is claimed, never inferred.** The cop cannot count our steps for us,
so a thief that reaches the threshold and says nothing leaves the cop waiting for
a turn that will never come.

Every decision belongs to somebody else: the action to the strategy, its legality
and effect to `LocalTurnService` through `KitPlayState`, the words to the hint
policy, the digest to the frozen codec through `KitRecordChain`, and the instant
to the clock port. This assembles; it decides nothing.
"""

from dataclasses import dataclass

from ..domain.actions import BarrierAction, PhysicalAction
from ..domain.observation import ScentBeliefSource, observation_of
from ..domain.scent_model import ScentModelAgreement
from .capture_values import CaptureClaim
from .hint_policy import HintPort
from .kit_messages import KitClaimResponse, KitRecord, KitRole, KitTurn
from .kit_play import KitPlayState
from .kit_records import KitRecordChain
from .ports import TimestampPort
from .sealed_record_values import ActorRole
from .strategy_api import StrategyPort
from .sub_game_truth import declared_barriers
from .turn_cursor import TurnCursor
from .turn_service import LocalTurnService


@dataclass(frozen=True, slots=True)
class KitHalfTurn:
    """The state our half-turn left behind, and the message that announces it."""

    state: KitPlayState
    message: KitTurn


@dataclass(frozen=True, slots=True)
class KitHalfTurnMaker:
    """Everything one half-turn needs, assembled once per sub-game."""

    role: KitRole
    actor: ActorRole
    sub_game: int
    strategy: StrategyPort
    turns: LocalTurnService
    hints: HintPort
    model: ScentModelAgreement
    chain: KitRecordChain
    clock: TimestampPort
    survival_threshold: int

    def take(
        self,
        state: KitPlayState,
        *,
        belief: ScentBeliefSource | None = None,
        answer: KitClaimResponse | None = None,
        forced: PhysicalAction | None = None,
    ) -> KitHalfTurn:
        """Decide, apply, seal and announce exactly one half-turn of ours.

        *forced* is the terminal `STAY`. After the game has ended for us we may
        still owe the opponent an answer or a concession, and a real sealed turn
        is how the record chain stays consistent while that answer travels -
        the opponent's audit still reproduces every commit.
        """
        cursor = TurnCursor(self.sub_game, state.step + 1)
        action = forced or self.strategy.choose_action(
            observation_of(state.truth, self.turns.quota, belief)
        )
        spoken = self.hints.choose(cursor, action)
        moved = state.advance(action, self.turns, self.model)
        record = self.chain.seal(
            cursor=cursor,
            role=self.actor,
            action=action,
            intent=spoken.intent,
            hint=spoken.text,
            own_position=moved.truth.own_position,
            barriers=declared_barriers(moved.truth),
        )
        return KitHalfTurn(moved, self._message(moved, record, spoken.text, action, answer))

    def _message(
        self,
        state: KitPlayState,
        record: KitRecord,
        hint: str,
        action: PhysicalAction,
        answer: KitClaimResponse | None,
    ) -> KitTurn:
        """The pinned ten-key half-turn, with only what this role may declare."""
        police = self.role is KitRole.POLICE
        barrier = action.target if type(action) is BarrierAction else None
        return KitTurn(
            state.step,
            self.role,
            hint,
            state.smell_grid(),
            record.commit,
            self.clock.now().value,
            barrier,
            CaptureClaim(state.truth.own_position) if police else None,
            answer,
            not police and state.step >= self.survival_threshold,
        )
