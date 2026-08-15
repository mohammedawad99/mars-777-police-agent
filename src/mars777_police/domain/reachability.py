"""Barrier-aware distance: how far every cell really is, not how far it looks.

A pursuer that measured distance as `|dr| + |dc|` would be drawn straight into a
wall, because a barrier changes what is *near* without changing what is
*adjacent*. BAR-004 makes placements irreversible and impassable to both sides,
so the board a strategy reasons over is a graph, and the only honest distance on
it is the one you can actually walk.

**It owns no geometry.** Bounds, blocked cells and the four cardinal offsets all
belong to `domain.board`, and this module reaches them through
`is_traversable` and `orthogonal_neighbours` rather than restating them. That is
the difference between a distance primitive and a second rules engine: nothing
here can disagree with `domain.rules` about where a piece may stand, because
nothing here decides it.

**Order cannot leak into the answer.** The frontier is a list expanded through
the board's own fixed neighbour order, never a set or a dict, and the returned
depths are read by callers only through `len` and `sum` - both blind to
insertion order. So `PYTHONHASHSEED` cannot move a decision (PRD-01 §19).

An unreachable cell is *absent* rather than carrying a sentinel distance: a
partition is a real fact about the board, and `None`/`inf` in an integer map is
the kind of value that later gets compared by accident.
"""

from .board import Board, Position


def reachable_from(board: Board, origin: Position) -> dict[Position, int]:
    """Return every cell reachable from *origin*, with its walking distance.

    The origin itself sits at distance 0. A cell that cannot be occupied is not
    part of the traversable region, so an origin off the board or on a barrier
    reaches nothing at all - and the caller never asks about one in practice,
    because every destination of a legal move is traversable by definition.
    """
    if not board.is_traversable(origin):
        return {}
    depths = {origin: 0}
    frontier = [origin]
    while frontier:
        further: list[Position] = []
        for cell in frontier:
            step = depths[cell] + 1
            for neighbour in board.orthogonal_neighbours(cell):
                if neighbour in depths or not board.is_traversable(neighbour):
                    continue
                depths[neighbour] = step
                further.append(neighbour)
        frontier = further
    return depths
