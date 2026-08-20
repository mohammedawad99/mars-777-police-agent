"""How long one decision takes, measured at the surface production calls.

The number that matters is the time inside `choose_action`, not the time to play
a benchmark game: the tournament budget applies to a decision, and harness
bookkeeping is ours rather than the opponent's problem. So the strategy is
called directly here, on observations taken from a real game, and the harness is
timed separately and reported separately.

**A monotonic clock, and percentiles rather than an average.** A mean hides the
worst case, and the worst case is what a deadline actually meets.
"""

import time
from dataclasses import dataclass

from mars777_police.app.sealed_record_values import ActorRole

from .configs import BenchConfig
from .game import SubGame
from .opponents import opponent
from .runner import OPPONENT_ROLE, OWN_ROLE
from .scenario import start_cells
from .strategy_port import Policy

SAMPLE_TARGET = 200
"""Enough decisions for a stable p95 without turning measurement into the run."""


@dataclass(frozen=True, slots=True)
class Latency:
    """Decision timing, in milliseconds, as a budget conversation needs it."""

    samples: int
    median_ms: float
    p95_ms: float
    max_ms: float

    def as_record(self) -> dict[str, object]:
        """Flat output for a table or a manifest."""
        return {
            "samples": self.samples,
            "median_ms": round(self.median_ms, 4),
            "p95_ms": round(self.p95_ms, 4),
            "max_ms": round(self.max_ms, 4),
        }


def _percentile(ordered: list[float], share: float) -> float:
    index = min(int(share * len(ordered)), len(ordered) - 1)
    return ordered[index]


def measure(strategy: Policy, config: BenchConfig, seed: int) -> Latency:
    """Time `choose_action` over decisions taken from a real, legal game."""
    rival = opponent("evasive", seed, OPPONENT_ROLE)
    police, thief = (strategy, rival) if OWN_ROLE is ActorRole.POLICE else (rival, strategy)
    timings: list[float] = []
    while len(timings) < SAMPLE_TARGET:
        cop_cell, thief_cell = start_cells(config, seed)
        game = SubGame(config, police, thief, cop_cell, thief_cell)
        while game.settled() is None:
            observation = game.observation(OWN_ROLE)
            started = time.perf_counter()
            strategy.choose_action(observation)
            timings.append((time.perf_counter() - started) * 1000.0)
            game.play_round()
        seed += 1
        rival = opponent("evasive", seed, OPPONENT_ROLE)
        police, thief = (strategy, rival) if OWN_ROLE is ActorRole.POLICE else (rival, strategy)
    timings.sort()
    return Latency(len(timings), _percentile(timings, 0.5), _percentile(timings, 0.95), timings[-1])
