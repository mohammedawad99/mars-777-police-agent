"""The replay window's picture, where historical truth is finally lawful.

`PRD07-FR-023` is explicit: **after** the permitted audit and reveal point,
replay may show what the live view never could - including both agents' true
paths - and that permission does not travel backwards to the live window. So
this frame draws both cells, and says `REPLAY` in its banner so nobody reads a
finished sub-game as the current match.

Verification words are the source's own, and never colour alone: each carries a
glyph and the word itself, so `Verified OK`, `TAMPERED` and `NOT_CHECKABLE`
remain distinguishable to a reader who sees no colour at all.
"""

from ..app.replay_values import ReplayStep, ReplaySummary
from . import palette
from .geometry import BANNER_HEIGHT, MARGIN, BoardGeometry, fit, window_size
from .primitives import Frame, Rect, Text

REPLAY = "REPLAY"
OFFICIAL = "OFFICIAL EVIDENCE"


def _banner(step: ReplayStep, summary: ReplaySummary, width: int) -> tuple[Rect, tuple[Text, ...]]:
    """The mode, the evidence class and the cursor, on two lines that never collide.

    The game identifier is as long as a peer chose to make it, so it gets a line
    of its own rather than a share of one: a heading that ran under the step
    counter would be a picture nobody could read back.
    """
    heading = f"{REPLAY}  |  {OFFICIAL}  |  step {step.number} of {summary.steps}"
    named = f"{summary.game_id}  g{summary.sub_game:02d}"
    return (
        Rect(0, 0, width, BANNER_HEIGHT, palette.PANEL),
        (
            Text(MARGIN, 6, heading, palette.TEXT, 13, True),
            Text(MARGIN, 25, named, palette.MUTED, 11),
        ),
    )


def _board(step: ReplayStep, geometry: BoardGeometry) -> tuple[list[Rect], list[Text]]:
    rects: list[Rect] = []
    texts: list[Text] = []
    for row in range(step.grid_size):
        for col in range(step.grid_size):
            left, top, wide, high = geometry.cell_box(row, col)
            rects.append(Rect(left, top, wide, high, palette.BACKGROUND, palette.GRID))
    for row, col in step.barriers:
        left, top, wide, high = geometry.cell_box(row, col)
        rects.append(Rect(left, top, wide, high, palette.BARRIER))
        texts.append(Text(left + wide // 3, top + high // 4, "#", palette.TEXT, 12, True))
    for cell, colour, mark in _actors(step):
        left, top, wide, high = geometry.cell_box(*cell)
        rects.append(Rect(left, top, wide, high, colour))
        texts.append(Text(left + wide // 4, top + high // 4, mark, palette.BACKGROUND, 12, True))
    return rects, texts


def _actors(step: ReplayStep) -> tuple[tuple[tuple[int, int], str, str], ...]:
    """Where each agent stood, or the one cell they shared.

    A capture puts both on the same square. Drawing two rectangles there would
    paint one over the other and silently lose an agent, so a shared cell is its
    own colour and its own mark.
    """
    if step.police_cell == step.thief_cell:
        return ((step.police_cell, palette.BOTH, "P+T"),)
    return ((step.police_cell, palette.POLICE, "P"), (step.thief_cell, palette.THIEF, "T"))


def _panel(
    step: ReplayStep, summary: ReplaySummary, complete: bool, left: int, width: int, height: int
) -> tuple[Rect, list[Text]]:
    texts = [Text(left + 12, BANNER_HEIGHT + MARGIN + 8, "VERIFICATION", palette.TEXT, 13, True)]
    top = BANNER_HEIGHT + MARGIN + 34
    for turn in step.turns:
        word = turn.check.value
        texts.append(
            Text(
                left + 12,
                top,
                f"{palette.status_glyph(word)} {turn.role:<7}{word}",
                palette.status_colour(word),
                11,
                True,
            )
        )
        top += 18
        texts.append(Text(left + 12, top, f"    {turn.label}", palette.MUTED, 10))
        top += 18
    rows = [
        ("semantic", step.semantic),
        ("sub-game", str(summary.sub_game)),
        ("commitments", summary.crypto.value),
        ("recorded", summary.recorded_result),
        ("audit complete", "yes" if complete else "no"),
        ("evidence", summary.evidence_class),
    ]
    top += 10
    for name, value in rows:
        texts.append(Text(left + 12, top, f"{name:<15}{value}"[:38], palette.MUTED, 11))
        top += 18
    return Rect(left, BANNER_HEIGHT, width, height - BANNER_HEIGHT, palette.PANEL), texts


def replay_frame(
    step: ReplayStep, summary: ReplaySummary, complete: bool, width: int = 0, height: int = 0
) -> Frame:
    """The whole replay picture for one step, for a window or a screenshot."""
    if not width or not height:
        width, height = window_size(step.grid_size)
    geometry = fit(step.grid_size, width, height)
    banner, banner_texts = _banner(step, summary, width)
    rects, texts = _board(step, geometry)
    panel_left = geometry.left + geometry.side + MARGIN
    panel, panel_texts = _panel(step, summary, complete, panel_left, width - panel_left, height)
    return Frame(
        width=width,
        height=height,
        title=f"{REPLAY} - {summary.game_id} g{summary.sub_game:02d} - step {step.number}",
        rects=(Rect(0, 0, width, height, palette.BACKGROUND), banner, panel, *rects),
        texts=(*banner_texts, *texts, *panel_texts),
    )
