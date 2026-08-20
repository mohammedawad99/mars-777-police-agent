"""Drawing the reconstructed board for a human, and nothing else.

The viewer is required to let a grader watch a game replay step by step, so the
board has to be readable at a glance. It is deliberately textual: the graphical
interface is a separate requirement with its own stage, and it will consume the
same projection rather than a second one.

Symbols, documented once and used everywhere:

* `P` - the police
* `T` - the thief
* `#` - a barrier
* `.` - an empty cell
* `!` - both agents on one cell, which the capture rules make meaningful
"""

from .replay_values import ReplayStep

POLICE = "P"
THIEF = "T"
BARRIER = "#"
EMPTY = "."
TOGETHER = "!"

LEGEND = f"{POLICE} police   {THIEF} thief   {BARRIER} barrier   {EMPTY} empty   {TOGETHER} both"


def symbol_at(step: ReplayStep, row: int, col: int) -> str:
    """The one character that describes this cell after *step*."""
    here = (row, col)
    if step.police_cell == here and step.thief_cell == here:
        return TOGETHER
    if step.police_cell == here:
        return POLICE
    if step.thief_cell == here:
        return THIEF
    if here in step.barriers:
        return BARRIER
    return EMPTY


def board_lines(step: ReplayStep) -> tuple[str, ...]:
    """The board after *step*, one string per row, plus a legend."""
    rows = [
        " ".join(symbol_at(step, row, col) for col in range(step.grid_size))
        for row in range(step.grid_size)
    ]
    return (*rows, LEGEND)
