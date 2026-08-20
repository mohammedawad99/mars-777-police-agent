"""The benchmark configuration corpus, built only from source-legal values.

Appendix F classifies every parameter, and the class decides whether a benchmark
may vary it at all:

* **FIXED** - *"binding, unchangeable; deviation disqualifies"*. Never varied.
  Table 15 #1 movement set, Table 16 #1-#3 the whole scent model (0.9 source
  strength, 0.10 decay, 5x5 field), Table 17 scoring, Table 18 #1 six sub-games.
* **MINIMUM** - *"negotiable only in the direction that makes the game harder …
  never easing below the example value"*, and absent an agreement the example
  value is the default. So a benchmark may raise these and must include the
  example: Table 13 #1 grid **7x7**, Table 15 #2 quota **14**, #3 max moves
  **35**, #4 survival threshold **35**.
* **NEGOTIABLE** - free by agreement: Table 13 #5/#6 the two start cells.

**5x5 is not in this corpus and cannot be.** Table 13 #1 makes 7x7 a MINIMUM,
`domain.config_model.MIN_GRID_SIZE` refuses anything smaller, and a benchmark
measuring a board the tournament forbids would be measuring a different game.
"""

from dataclasses import dataclass
from typing import Final

from mars777_police.domain.barriers import BarrierQuota
from mars777_police.domain.board import Board, Position
from mars777_police.domain.terminal import TurnLimits

GRID_MINIMUM: Final[int] = 7
QUOTA_MINIMUM: Final[int] = 14
MOVES_MINIMUM: Final[int] = 35


@dataclass(frozen=True, slots=True)
class BenchConfig:
    """One legal board and its legal limits, named for a result record."""

    name: str
    grid: int
    quota: int
    horizon: int
    police_start: tuple[int, int]
    thief_start: tuple[int, int]
    fixed_starts: bool = False
    """When set, every seed uses these cells - the Appendix F example geometry."""

    def board(self) -> Board:
        """An empty board of this size. Barriers accumulate during the game."""
        return Board(rows=self.grid, cols=self.grid, blocked=frozenset())

    def limits(self) -> TurnLimits:
        """The horizon, applied to both the ceiling and the survival threshold."""
        return TurnLimits(max_moves=self.horizon, survival_threshold=self.horizon)

    def barrier_quota(self) -> BarrierQuota:
        """The police's placement budget for this configuration."""
        return BarrierQuota(max_barriers=self.quota)

    def cop_cell(self) -> Position:
        """Where the police begins, as Table 13 #6 permits by agreement."""
        return Position(*self.police_start)

    def thief_cell(self) -> Position:
        """Where the thief begins, as Table 13 #5 permits by agreement."""
        return Position(*self.thief_start)


def _centre(grid: int) -> tuple[int, int]:
    """The middle cell, which Table 13 #5 gives as the thief's example start."""
    return (grid // 2, grid // 2)


def corpus() -> tuple[BenchConfig, ...]:
    """Every configuration family the baseline is measured on.

    Three board sizes at and above the MINIMUM, plus one raised quota and one
    raised horizon. Opening cells are chosen per seed by `scenario.start_cells`,
    because Table 13 rows 5 and 6 are NEGOTIABLE and the seed has to select
    *something* - see that module for why. One entry keeps Appendix F's own
    illustrated geometry fixed, so the source's example is measured rather than
    averaged away.
    """
    return (
        BenchConfig("grid7", 7, QUOTA_MINIMUM, MOVES_MINIMUM, (0, 0), _centre(7)),
        BenchConfig("grid9", 9, QUOTA_MINIMUM, MOVES_MINIMUM, (0, 0), _centre(9)),
        BenchConfig("grid11", 11, QUOTA_MINIMUM, MOVES_MINIMUM, (0, 0), _centre(11)),
        BenchConfig("grid7-quota22", 7, 22, MOVES_MINIMUM, (0, 0), _centre(7)),
        BenchConfig("grid9-horizon45", 9, QUOTA_MINIMUM, 45, (0, 0), _centre(9)),
        BenchConfig("appendixF-example", 7, QUOTA_MINIMUM, MOVES_MINIMUM, (0, 0), _centre(7), True),
    )


def digest_source() -> str:
    """The corpus rendered as stable text, so the manifest can hash it."""
    return "\n".join(
        f"{one.name}|{one.grid}|{one.quota}|{one.horizon}"
        f"|{one.police_start}|{one.thief_start}|{one.fixed_starts}"
        for one in corpus()
    )
