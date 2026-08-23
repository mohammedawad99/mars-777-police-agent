"""What the police actually believed, and what its gate did with that belief.

This module exists because a benchmark delta says a change helped without saying
why, and a candidate accepted on an unexplained delta is a candidate nobody can
defend. It measures the mechanism directly: how much belief the police holds at
a decision, how hot the cell it is about to step onto is, and how often the
shipped gate refuses a lawful placement because of that cell.

Read only. Nothing here chooses an action, and no diagnostic value is fed back
into a strategy - a policy that consulted these counters would be tuning itself
on its own instrumentation.
"""

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from mars777_police.app.sealed_record_values import ActorRole
from mars777_police.domain.actions import BarrierAction
from mars777_police.domain.barriers import is_placeable
from mars777_police.domain.board import Position
from mars777_police.domain.observation import Observation

from .candidates.pursuit import belief_cells
from .configs import BenchConfig, corpus
from .game import SubGame
from .opponents import FAMILIES, opponent
from .records import write_json
from .scenario import start_cells
from .strategy_port import Policy

ZERO = Decimal(0)

SAMPLED = range(50, 62)
"""Seeds sampled per family. Enough games for a stable share, few enough that a
diagnostic never becomes the benchmark it is explaining."""


@dataclass(frozen=True, slots=True)
class Belief:
    """One opponent family's belief picture, summed over its sampled games."""

    family: str
    steps: int
    belief_steps: int
    blocked_steps: int
    mean_landing_scent: float
    mean_mass: float
    lawful_targets: int
    starved_steps: int
    """Decisions carrying belief where no lawful placement existed at all.

    Reported separately because it is not a gate decision: the policy could not
    have placed whatever its threshold said, and folding it into `blocked` would
    credit the gate with a refusal the board made."""

    def as_record(self) -> dict[str, object]:
        """Flat output for a table or a manifest."""
        return {
            "family": self.family,
            "steps": self.steps,
            "belief_steps": self.belief_steps,
            "blocked_steps": self.blocked_steps,
            "blocked_share": round(
                self.blocked_steps / max(self.belief_steps - self.starved_steps, 1), 4
            ),
            "starved_steps": self.starved_steps,
            "mean_landing_scent": round(self.mean_landing_scent, 4),
            "mean_mass": round(self.mean_mass, 4),
            "lawful_targets": self.lawful_targets,
        }


def _landing_scent(view: Observation, mass: tuple[tuple[Position, Decimal], ...]) -> Decimal:
    """Evidence at the cell the shipped gate compares against."""
    found = dict(mass)
    return found.get(view.own_position, ZERO)


def _lawful(view: Observation) -> int:
    board = view.board
    cells = ((row, col) for row in range(board.rows) for col in range(board.cols))
    return sum(
        1
        for row, col in cells
        if is_placeable(board, view.own_position, _position(row, col), view.quota)
    )


def _position(row: int, col: int):  # type: ignore[no-untyped-def]
    from mars777_police.domain.board import Position

    return Position(row, col)


def observe(strategy: Policy, config: BenchConfig, family: str, seeds: range) -> Belief:
    """Play sampled games and count what the belief and the gate did."""
    steps = belief_steps = blocked = targets = starved = 0
    scent_total = mass_total = ZERO
    for seed in seeds:
        police, thief = start_cells(config, seed)
        game = SubGame(config, strategy, opponent(family, seed), police, thief)
        while game.settled() is None:
            view = game.observation(ActorRole.POLICE)
            mass = belief_cells(view)
            steps += 1
            if mass:
                belief_steps += 1
                landing = _landing_scent(view, mass)
                scent_total += landing
                mass_total += sum(weight for _, weight in mass)
                lawful = _lawful(view)
                targets += lawful
                starved += int(lawful == 0)
                blocked += int(_gate_refused(strategy, view, lawful))
            game.play_round()
    return Belief(
        family,
        steps,
        belief_steps,
        blocked,
        float(scent_total / max(belief_steps, 1)),
        float(mass_total / max(belief_steps, 1)),
        targets,
        starved,
    )


def _gate_refused(strategy: Policy, view: Observation, targets: int) -> bool:
    """Whether the shipped gate refused a placement it actually had room to make.

    Asked of the policy itself rather than reimplemented here. This function used
    to carry the pre-9B-2 rule - "no target's support strictly exceeds the cell
    the mover is stepping onto" - and its docstring called that "the shipped
    gate's own test". Stage 9B-2 replaced that rule with an absolute floor and
    this diagnostic was never updated, so it went on reporting a gate that no
    longer existed. A measurement of a rule nobody ships is worse than none: it
    reads as evidence. Restating a gate beside the gate is the mistake, so the
    fix is not to restate a newer one but to stop restating it at all.

    *targets* is required because "did not place" has three causes and only one
    of them is the gate: belief may be absent, there may be no lawful target at
    all, or every lawful target may have fallen short of the floor. The caller
    has already established belief; this excludes the second, so what remains is
    the gate.
    """
    if targets == 0:
        return False
    return not isinstance(strategy.choose_action(view), BarrierAction)


def report(strategy: Policy, config: BenchConfig, families: tuple[str, ...], out: Path) -> Path:
    """Write one belief record per family. Development evidence only."""
    found: dict[str, object] = {
        "label": "DEVELOPMENT RESEARCH - not final holdout, not a production promotion",
        "config": config.name,
        "families": [observe(strategy, config, one, SAMPLED).as_record() for one in families],
    }
    return write_json(found, out)


def write_belief(root: Path) -> Path:
    """Measure what the shipped policy believed and what its gate did about it."""
    from mars777_police.app.competitive_strategy import CompetitiveStrategy

    return report(CompetitiveStrategy(), corpus()[1], FAMILIES, root / "candidates" / "belief.json")
