"""What a live window is allowed to show, and why that set is not a judgement.

`GUI-001` requires the live interface to display **local truth only** - own
position, sensed scent, received hints, a belief heatmap - and `GUI-002` forbids
the full objective board state outright, on pain of disqualification for an
illegal advantage. So the safest possible whitelist is not one invented for the
window: it is `Observation`, the value the **strategy itself** is restricted to.

**If the live view shows exactly what the agent may decide from, it cannot leak
an advantage the agent does not already lawfully hold.** `Observation` carries
the board's public barriers, our own cell, our own quota and the belief folded
from what the opponent *disclosed* - and by construction carries no opponent
position at all.

The belief is carried as a **labelled estimate**, never as a position:
`PRD07-FR-005` requires it to be visually and semantically marked as belief, and
a value named `belief` holding intensities per cell cannot be mistaken for a
sighting.
"""

from dataclasses import dataclass, field
from decimal import Decimal

from ..domain.board import Position
from ..domain.observation import Observation

LIVE = "LIVE"
"""The mode banner a live window must carry, so no reader mistakes it for replay."""


@dataclass(frozen=True, slots=True)
class LiveViewSnapshot:
    """One lawful moment of local truth, ready to draw and safe to show."""

    role: str
    game_id: str
    sub_game: int
    step: int
    phase: str
    grid_size: int
    own_cell: tuple[int, int]
    barriers: tuple[tuple[int, int], ...]
    belief: tuple[tuple[int, int, str], ...] = field(default=())
    barrier_quota: int = 0
    """The locked maximum, which is a public configured term rather than a secret."""
    last_action: str | None = None
    hint: str | None = None
    terminal: str | None = None

    @property
    def has_belief(self) -> bool:
        """Whether any peer emission has been folded into this estimate yet."""
        return bool(self.belief)


def belief_cells(observation: Observation) -> tuple[tuple[int, int, str], ...]:
    """Every cell the folded belief has evidence for, as decimal text.

    Text rather than float: the belief's own values are `Decimal`, and rendering
    them through binary floating point would show a number the agent never held.
    """
    if not observation.scent.has_evidence:
        return ()
    board = observation.board
    found: list[tuple[int, int, str]] = []
    for row in range(board.rows):
        for col in range(board.cols):
            intensity = observation.scent.intensity_at(Position(row, col))
            if intensity > Decimal(0):
                found.append((row, col, str(intensity)))
    return tuple(found)


def snapshot_of(
    observation: Observation,
    *,
    role: str,
    game_id: str,
    sub_game: int,
    step: int,
    phase: str,
    last_action: str | None = None,
    hint: str | None = None,
    terminal: str | None = None,
) -> LiveViewSnapshot:
    """Project one lawful observation into the value a live window may draw."""
    board = observation.board
    return LiveViewSnapshot(
        role=role,
        game_id=game_id,
        sub_game=sub_game,
        step=step,
        phase=phase,
        grid_size=board.rows,
        own_cell=(observation.own_position.row, observation.own_position.col),
        barriers=tuple(sorted((one.row, one.col) for one in board.blocked)),
        belief=belief_cells(observation),
        barrier_quota=observation.quota.max_barriers,
        last_action=last_action,
        hint=hint,
        terminal=terminal,
    )
