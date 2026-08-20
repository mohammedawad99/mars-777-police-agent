"""What a seed actually selects: a distinct, legal opening geometry.

The first benchmark this stage ran produced win rates of exactly `0` and exactly
`1/3`, and the reason was worth more than the numbers: **the seed changed
nothing**. Every policy in the corpus is a deterministic function of the board,
its own cell and its own belief, so sixty-four seeds replayed one game and the
confidence intervals treated sixty-four copies of one observation as sixty-four
observations. Measured directly, the seed altered the outcome in **0 of 42**
(family, configuration) cells.

So the seed now selects the one thing Appendix F leaves free and a benchmark
genuinely wants to vary: **the two opening cells**. Table 13 rows 5 and 6 are
`NEGOTIABLE` - *"the parties may agree any value"* - so varying them stays
inside the rules, and it varies the scenario rather than the physics.

One configuration keeps the source's own example geometry - police in the corner,
thief in the centre - so Appendix F's illustrated opening is measured too rather
than averaged away.
"""

import hashlib

from mars777_police.domain.board import Position

from .configs import BenchConfig


def _index(seed: int, slot: int, size: int) -> int:
    material = f"scenario/v1/{seed}/{slot}".encode()
    return int.from_bytes(hashlib.sha256(material).digest()[:8], "big") % size


def start_cells(config: BenchConfig, seed: int) -> tuple[Position, Position]:
    """The police and thief opening cells for this configuration and seed.

    Distinct by construction: the two actors never begin on the same square, and
    the search walks forward deterministically rather than drawing again, so the
    result depends on nothing but the seed.
    """
    if config.fixed_starts:
        return (config.cop_cell(), config.thief_cell())
    size = config.grid * config.grid
    first = _index(seed, 0, size)
    second = _index(seed, 1, size)
    if second == first:
        second = (second + 1) % size
    return (_cell(first, config.grid), _cell(second, config.grid))


def _cell(index: int, grid: int) -> Position:
    return Position(index // grid, index % grid)
