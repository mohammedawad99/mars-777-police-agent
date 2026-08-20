"""The live window's picture: local truth only, and a belief that says so.

`GUI-001` allows own position, sensed scent, received hints and a belief
heatmap. `GUI-002` forbids the full objective board state outright - the
sanction is disqualification for an illegal advantage - so **no opponent cell is
drawn, because none is carried**: the snapshot this reads is projected from the
same `Observation` the strategy is restricted to.

`GUI-003` requires the belief heatmap and a turn-state banner, and
`PRD07-FR-005` requires belief to be labelled as an estimate. Every heated cell
therefore carries its own number, and the legend names it `belief (estimate)` -
a reader is never invited to mistake warmth for a sighting.
"""

from ..app.live_view_values import LIVE, LiveViewSnapshot
from . import palette
from .geometry import BANNER_HEIGHT, MARGIN, PANEL_WIDTH, BoardGeometry, fit, window_size
from .primitives import Frame, Rect, Text

BELIEF_LABEL = "belief (estimate) - not a sighting"


def _banner(snapshot: LiveViewSnapshot, width: int) -> tuple[Rect, tuple[Text, ...]]:
    """The turn-state banner `GUI-003` requires, naming the mode first."""
    heading = f"{LIVE}  |  {snapshot.role}  |  {snapshot.game_id}  g{snapshot.sub_game:02d}"
    state = f"step {snapshot.step}  |  {snapshot.phase}"
    return (
        Rect(0, 0, width, BANNER_HEIGHT, palette.PANEL),
        (
            Text(MARGIN, 10, heading, palette.TEXT, 14, True),
            Text(width - PANEL_WIDTH, 10, state, palette.MUTED, 12),
        ),
    )


def _cells(snapshot: LiveViewSnapshot, geometry: BoardGeometry) -> tuple[list[Rect], list[Text]]:
    """The grid, the barriers, the belief heat, and our own cell."""
    rects: list[Rect] = []
    texts: list[Text] = []
    strongest = max((float(one[2]) for one in snapshot.belief), default=0.0)
    for row in range(snapshot.grid_size):
        for col in range(snapshot.grid_size):
            left, top, wide, high = geometry.cell_box(row, col)
            rects.append(Rect(left, top, wide, high, palette.BACKGROUND, palette.GRID))
    for row, col, intensity in snapshot.belief:
        left, top, wide, high = geometry.cell_box(row, col)
        rects.append(Rect(left, top, wide, high, palette.belief_shade(float(intensity), strongest)))
        texts.append(Text(left + 4, top + 4, str(intensity)[:4], palette.TEXT, 9))
    for row, col in snapshot.barriers:
        left, top, wide, high = geometry.cell_box(row, col)
        rects.append(Rect(left, top, wide, high, palette.BARRIER))
        texts.append(Text(left + wide // 3, top + high // 4, "#", palette.TEXT, 12, True))
    left, top, wide, high = geometry.cell_box(*snapshot.own_cell)
    rects.append(Rect(left, top, wide, high, palette.OWN))
    texts.append(Text(left + wide // 3, top + high // 4, "ME", palette.BACKGROUND, 11, True))
    return rects, texts


def _panel(
    snapshot: LiveViewSnapshot, left: int, width: int, height: int
) -> tuple[Rect, list[Text]]:
    """What is lawfully known, in words, beside the board."""
    rows = [
        ("role", snapshot.role),
        ("sub-game", str(snapshot.sub_game)),
        ("step", str(snapshot.step)),
        ("phase", snapshot.phase),
        ("own cell", str(snapshot.own_cell)),
        ("barriers", str(len(snapshot.barriers))),
        ("barrier quota", str(snapshot.barrier_quota)),
        ("belief cells", str(len(snapshot.belief))),
        ("last action", snapshot.last_action or "-"),
        ("hint", (snapshot.hint or "-")[:28]),
        ("terminal", snapshot.terminal or "-"),
    ]
    top_of_panel = BANNER_HEIGHT + MARGIN + 8
    heading = Text(left + 12, top_of_panel, "LOCAL TRUTH ONLY", palette.TEXT, 13, True)
    texts = [heading]
    top = BANNER_HEIGHT + MARGIN + 34
    for name, value in rows:
        texts.append(Text(left + 12, top, f"{name:<14}{value}", palette.MUTED, 11))
        top += 18
    texts.append(Text(left + 12, top + 10, BELIEF_LABEL, palette.BELIEF, 11, True))
    texts.append(Text(left + 12, top + 28, "opponent position: never shown", palette.MUTED, 11))
    return Rect(left, BANNER_HEIGHT, width, height - BANNER_HEIGHT, palette.PANEL), texts


def live_frame(snapshot: LiveViewSnapshot, width: int = 0, height: int = 0) -> Frame:
    """The whole live picture, for a window or for a screenshot."""
    if not width or not height:
        width, height = window_size(snapshot.grid_size)
    geometry = fit(snapshot.grid_size, width, height)
    banner, banner_texts = _banner(snapshot, width)
    rects, texts = _cells(snapshot, geometry)
    panel_left = geometry.left + geometry.side + MARGIN
    panel, panel_texts = _panel(snapshot, panel_left, width - panel_left, height)
    return Frame(
        width=width,
        height=height,
        title=f"{LIVE} - {snapshot.role} - {snapshot.game_id}",
        rects=(Rect(0, 0, width, height, palette.BACKGROUND), banner, panel, *rects),
        texts=(*banner_texts, *texts, *panel_texts),
    )
