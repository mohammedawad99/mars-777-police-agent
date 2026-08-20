"""Real values for the graphical tests: a lawful observation and a played log.

Nothing here draws anything and nothing here invents game state. The observation
is built by `observation_of`, the same projection the driver decides from, and
the log is the one two composed agents actually wrote.
"""

from decimal import Decimal
from pathlib import Path

from mars777_police.app.live_view_values import LiveViewSnapshot, snapshot_of
from mars777_police.domain.barriers import BarrierQuota
from mars777_police.domain.board import Board, Position
from mars777_police.domain.observation import Observation, observation_of
from mars777_police.domain.scent import ScentField
from mars777_police.domain.scent_belief import ScentBelief
from mars777_police.domain.truth import LocalTruth

GRID = 8
QUOTA = BarrierQuota(max_barriers=14)


def board(*blocked: tuple[int, int]) -> Board:
    """An eight-by-eight board with exactly the barriers named."""
    return Board(rows=GRID, cols=GRID, blocked=frozenset(Position(*one) for one in blocked))


def belief(*cells: tuple[int, int, str]) -> ScentBelief:
    """A folded belief with evidence on exactly the cells named."""
    weights = {(row, col): value for row, col, value in cells}
    grid = tuple(
        tuple(Decimal(weights.get((row, col), "0")) for col in range(GRID)) for row in range(GRID)
    )
    return ScentBelief(ScentField(GRID, GRID, 0, grid), 1)


def observation(scent: ScentBelief | None = None, own: tuple[int, int] = (0, 0)) -> Observation:
    """One lawful observation, projected the way a real turn projects it."""
    truth = LocalTruth(board=board((2, 2), (2, 3)), own_position=Position(*own))
    source = None if scent is None else _Fixed(scent)
    return observation_of(truth, QUOTA, source)


class _Fixed:
    """A belief source that answers the same folded belief for any board."""

    def __init__(self, held: ScentBelief) -> None:
        self.held = held

    def for_board(self, board: Board) -> ScentBelief:
        """The belief this fixture was built with."""
        return self.held


def snapshot(
    scent: ScentBelief | None = None, own: tuple[int, int] = (0, 0), **rest: object
) -> LiveViewSnapshot:
    """The live snapshot a real turn would publish for `observation()`."""
    fields: dict[str, object] = {
        "role": "POLICE",
        "game_id": "MaRs-777-vs-peer",
        "sub_game": 1,
        "step": 3,
        "phase": "TURN",
    }
    fields.update(rest)
    return snapshot_of(observation(scent, own), **fields)  # type: ignore[arg-type]


def evidence_root() -> Path:
    """Where the committed graphical evidence lives, relative to the repository."""
    return Path(__file__).resolve().parents[2] / "docs" / "evidence" / "gui"
