"""One deterministic sub-game, adjudicated by the authorities production uses.

**No second engine.** Legality and both trajectories are decided by
`app.semantic_replay.Replay` - the same engine the live audit and the Replay
Viewer use; capture by `domain.terminal`'s own predicates; the end event by
`evaluate_terminal`; the lawful view by `observation_of`; the scent by the
locked model. What this module adds is the one thing none of them do: it asks
two strategies for an action and feeds their answers in.

**Capture is modelled exactly as the counted path produces it, which is
narrower than the rulebook allows.** `SubGameDriver.play_round` never passes a
`claim` to `open_turn`, and `StrategyPort` cannot express one - its return type
is `MoveAction | BarrierAction`. So no shipped strategy can declare a contact
capture, and the only captures reachable are `BAR-003` (a barrier placed on the
thief's cell) and `GAME-005` (a thief left with no traversable neighbour).
Modelling contact capture here would flatter the police with wins production
cannot obtain, and the research would be measuring a different game.

**Both actors commit against the same start state**, exactly as JDEC-016 §4
requires: each observes the board the round opened with, and both effects apply
afterwards.
"""

from dataclasses import dataclass, field

from mars777_police.app.sealed_record_values import ActorRole
from mars777_police.app.semantic_replay import PlayedTurn, Replay
from mars777_police.app.semantic_values import SemanticRules
from mars777_police.domain.actions import BarrierAction, PhysicalAction
from mars777_police.domain.board import Position
from mars777_police.domain.observation import Observation, observation_of
from mars777_police.domain.terminal import Outcome, evaluate_terminal, is_trapped
from mars777_police.domain.truth import LocalTruth

from .configs import BenchConfig
from .scent import ScentTrail
from .strategy_port import Policy


class IllegalResearchActionError(Exception):
    """A policy returned something the production authorities refuse."""


@dataclass(slots=True)
class SubGame:
    """Two policies, one board, and the production rules between them."""

    config: BenchConfig
    police: Policy
    thief: Policy
    cop_start: Position | None = None
    thief_start: Position | None = None
    """The opening cells this game uses. `None` means the configuration's own."""
    replay: Replay = field(init=False)
    trail: ScentTrail = field(init=False)
    captured: bool = field(default=False)
    steps: int = field(default=0)
    barriers_placed: int = field(default=0)

    def __post_init__(self) -> None:
        rules = SemanticRules(
            self.config.board(),
            self.config.barrier_quota(),
            self.cop_start or self.config.cop_cell(),
            self.thief_start or self.config.thief_cell(),
        )
        self.replay = Replay(rules)
        self.trail = ScentTrail(self.config)

    def observation(self, role: ActorRole) -> Observation:
        """The lawful view for *role*: its own truth, quota and folded belief."""
        truth = LocalTruth(self.replay.board, self.replay.cell_of(role))
        return observation_of(truth, self.config.barrier_quota(), self.trail.source_for(role))

    def _turn(self, role: ActorRole, action: PhysicalAction) -> PlayedTurn:
        walls = tuple(sorted(self.replay.board.blocked, key=lambda one: (one.row, one.col)))
        return PlayedTurn(self.steps + 1, role, self.replay.cell_of(role), walls, action)

    def play_round(self) -> None:
        """One lockstep round: both decide from the start state, then both apply."""
        police_action = self.police.choose_action(self.observation(ActorRole.POLICE))
        thief_action = self.thief.choose_action(self.observation(ActorRole.THIEF))
        turns = (
            self._turn(ActorRole.POLICE, police_action),
            self._turn(ActorRole.THIEF, thief_action),
        )
        finding = self.replay.check(turns)
        if not finding.consistent:
            raise IllegalResearchActionError(f"a research policy produced {finding.verdict.value}")
        thief_cell = self.replay.cell_of(ActorRole.THIEF)
        if isinstance(police_action, BarrierAction):
            self.barriers_placed += 1
            self.captured = self.captured or police_action.target == thief_cell
        self.trail.record(turns)
        self.replay.apply(turns)
        self.steps += 1
        self.captured = self.captured or is_trapped(
            self.replay.board, self.replay.cell_of(ActorRole.THIEF)
        )

    def settled(self) -> Outcome | None:
        """The end event, decided by the production terminal authority."""
        return evaluate_terminal(
            captured=self.captured, step=self.steps, limits=self.config.limits()
        )

    def play(self) -> Outcome:
        """Play to a natural terminal and report what the domain decided."""
        while True:
            outcome = self.settled()
            if outcome is not None:
                return outcome
            self.play_round()
