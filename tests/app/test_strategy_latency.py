"""A move must be decided far inside the agreed response window, deterministically.

The peers agreed 30 seconds for a response, and that budget covers the whole
round trip - transport, the peer's own work, and ours. A strategy that merely
fits would leave nothing for the rest, so what is asserted here is a large
margin rather than a pass.

The bound is deliberately loose compared to what the strategy actually costs:
this runs on whatever machine a grader or CI happens to use, and a tight bound
would fail for reasons that say nothing about the code. Measured on the agreed
7x7 board the production policy decides in well under a millisecond; the guard
sits two orders of magnitude above that, so it catches a combinatorial
regression and nothing else.

**No move may depend on a network or a paid service.** A decision that reached
for an LLM would be non-deterministic, unbounded in latency, and unreplayable -
and the project forbids delegating legality anyway. That is asserted structurally
rather than by timing.
"""

import time
from decimal import Decimal

import pytest

from mars777_police.app.baseline_strategy import BaselineStrategy
from mars777_police.app.competitive_strategy import CompetitiveStrategy
from mars777_police.app.strategy_api import StrategyPort
from mars777_police.domain.barriers import BarrierQuota
from mars777_police.domain.board import Board, Position
from mars777_police.domain.observation import Observation
from mars777_police.domain.scent import ScentField
from mars777_police.domain.scent_belief import ScentBelief

AGREED_BOARD = 7
"""`grid_size` in the frozen contract. The size a counted move is decided on."""

BUDGET_MS = 250.0
"""Two orders of magnitude above measured cost, and 120x inside the 30s window."""

RUNS = 200
FORBIDDEN_IMPORTS = ("httpx", "requests", "urllib", "openai", "anthropic", "socket")


def view(size: int = AGREED_BOARD, blocked_every: int = 0) -> Observation:
    blocked = frozenset(
        Position(r, c)
        for r in range(size)
        for c in range(size)
        if blocked_every and (r * size + c) % blocked_every == 0 and (r, c) != (0, 0)
    )
    shape = Board(rows=size, cols=size, blocked=blocked)
    grid = tuple(
        tuple(Decimal(str(((r * size + c) % 7) / 7)) for c in range(shape.cols))
        for r in range(shape.rows)
    )
    return Observation(
        board=shape,
        own_position=Position(0, 0),
        quota=BarrierQuota(14),
        scent=ScentBelief(ScentField(shape.rows, shape.cols, 0, grid), 1),
    )


def percentiles(strategy: StrategyPort, observed: Observation) -> tuple[float, float]:
    times: list[float] = []
    for _ in range(RUNS):
        start = time.perf_counter()
        strategy.choose_action(observed)
        times.append((time.perf_counter() - start) * 1000)
    times.sort()
    return times[len(times) // 2], times[min(len(times) - 1, int(len(times) * 0.95))]


@pytest.mark.parametrize(
    "strategy",
    [CompetitiveStrategy(), BaselineStrategy()],
    ids=["competitive", "baseline"],
)
def test_a_move_is_decided_far_inside_the_agreed_window(strategy: StrategyPort) -> None:
    _, p95 = percentiles(strategy, view())
    assert p95 < BUDGET_MS, f"p95 {p95:.3f}ms exceeds the {BUDGET_MS}ms guard"


@pytest.mark.parametrize(
    "strategy",
    [CompetitiveStrategy(), BaselineStrategy()],
    ids=["competitive", "baseline"],
)
def test_a_crowded_board_does_not_explode_combinatorially(strategy: StrategyPort) -> None:
    """The shape a lookahead regression would show up in first."""
    _, p95 = percentiles(strategy, view(blocked_every=5))
    assert p95 < BUDGET_MS


def test_the_same_state_always_decides_the_same_move() -> None:
    """Deterministic: a replay that disagreed with the log would be unauditable."""
    observed = view()
    chosen = {repr(CompetitiveStrategy().choose_action(observed)) for _ in range(25)}
    assert len(chosen) == 1


def test_no_move_reaches_a_network_or_a_paid_service() -> None:
    """Structural, not timed: a decision must never leave this process."""
    from pathlib import Path

    for name in ("competitive_strategy.py", "baseline_strategy.py"):
        source = (
            Path(__file__).resolve().parents[2] / "src" / "mars777_police" / "app" / name
        ).read_text(encoding="utf-8")
        for banned in FORBIDDEN_IMPORTS:
            assert f"import {banned}" not in source, f"{name} reaches for {banned}"
