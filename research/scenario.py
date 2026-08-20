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
from typing import Final

from mars777_police.domain.board import Position

from .configs import BenchConfig
from .opponents import seed_matters

SCENARIO_VERSION: Final[str] = "scenario-1"
"""Raised only when the identity's meaning changes, never for a new run."""


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


def space_size(config: BenchConfig) -> int:
    """How many distinct opening pairs this configuration legally has.

    One when the geometry is fixed; otherwise every ordered pair of distinct
    cells, because the board starts empty so every cell is traversable.
    """
    if config.fixed_starts:
        return 1
    cells = config.grid * config.grid
    return cells * (cells - 1)


def openings(
    config: BenchConfig, seeds: tuple[int, ...]
) -> tuple[tuple[int, Position, Position], ...]:
    """Distinct openings for *config*, drawn **without replacement**.

    Sixty-four seeds that collide onto twenty openings are twenty observations,
    not sixty-four, so a colliding seed is skipped rather than counted. When the
    legal space is smaller than the request - the fixed reference geometry has
    exactly one opening - the result is the whole space and the caller learns
    the real `N` from its length rather than from what it asked for.
    """
    seen: set[tuple[Position, Position]] = set()
    found: list[tuple[int, Position, Position]] = []
    for seed in seeds:
        if len(seen) >= space_size(config):
            break
        police, thief = start_cells(config, seed)
        if (police, thief) in seen:
            continue
        seen.add((police, thief))
        found.append((seed, police, thief))
    return tuple(found)


def scenario_id(
    role: str, family: str, config: BenchConfig, seed: int, police: Position, thief: Position
) -> str:
    """The canonical identity of one deterministic experimental condition.

    Everything that can make two games genuinely different is in it: the role
    under evaluation, the opponent family, the board geometry and limits, both
    opening cells, and the seed **only when that family's behaviour actually
    depends on it**. Nothing that cannot change a game is in it - no path, no
    timestamp, no row number - because those would make identical games look
    like independent observations, which is exactly the error this identity
    exists to prevent.
    """
    material = "|".join(
        (
            SCENARIO_VERSION,
            role,
            family,
            config.name,
            str(config.grid),
            str(config.quota),
            str(config.horizon),
            f"{police.row},{police.col}",
            f"{thief.row},{thief.col}",
            str(seed) if seed_matters(family) else "-",
        )
    )
    return hashlib.sha256(material.encode()).hexdigest()
