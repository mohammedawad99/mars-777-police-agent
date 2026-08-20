"""The exploration progression, drawn as a curve over the order things were tried.

**This is not a learning curve.** Nothing here trains, and no weight is updated
between points: each point is a separate candidate, replayed over the same frozen
scenarios, and the x axis is the order the ideas were tried rather than time,
epochs or gradient steps. Calling it a training loss would be a false claim about
the method, so the axis label says what it actually is.

**Rejected candidates stay on the curve.** A progression that showed only the
winners would draw a rising line out of a search that in fact went down twice,
and the shape of the search is the evidence.

**The y axis carries a real zero.** The plotted quantity is a signed difference,
so the no-change line is drawn where zero is; shifting the origin to force a
zero-based axis would flatten a collapse and a gain into the same bar height.
"""

from dataclasses import dataclass
from itertools import pairwise

from mars777_police.gui.primitives import Frame, Rect, Text

from .charts import AXIS, BAR, HEIGHT, INK, LEFT, MUTED, PAPER, RIGHT, TOP, WIDTH

BOTTOM = 110
DOT = 7
DROP = "#c2453c"
"""A rejected point is drawn in a different colour, not omitted."""


@dataclass(frozen=True, slots=True)
class Point:
    """One candidate in the order it was tried."""

    label: str
    value: float
    kept: bool


def _box() -> tuple[int, int]:
    return (WIDTH - LEFT - RIGHT, HEIGHT - TOP - BOTTOM)


def _at(index: int, value: float, span: float, count: int) -> tuple[int, int]:
    """Map an ordinal position and a signed value onto the canvas."""
    plot_w, plot_h = _box()
    step = plot_w // max(count - 1, 1)
    middle = TOP + plot_h // 2
    return (LEFT + index * step, middle - int((plot_h // 2) * value / span))


def progression(title: str, unit: str, points: tuple[Point, ...], caption: str) -> Frame:
    """A zero-based curve over an ordinal axis, marking what was kept."""
    if not points:
        raise ValueError("a progression needs at least one candidate")
    plot_w, plot_h = _box()
    span = max([abs(one.value) for one in points] + [1e-9]) * 1.3
    rects = [Rect(0, 0, WIDTH, HEIGHT, PAPER)]
    texts = [
        Text(40, 24, title, INK, 15, True),
        Text(40, 48, caption, MUTED, 11),
        Text(
            40,
            HEIGHT - 26,
            f"y: {unit}, zero line marked; x: order tried, not time or epochs",
            MUTED,
            11,
        ),
    ]
    places = [_at(index, one.value, span, len(points)) for index, one in enumerate(points)]
    for start, end in pairwise(places):
        rects.extend(_segment(start, end))
    for (x, y), one in zip(places, points, strict=True):
        rects.append(Rect(x - DOT // 2, y - DOT // 2, DOT, DOT, BAR if one.kept else DROP))
        texts.append(Text(x - 26, y - 22, f"{one.value:+.4f}", INK, 11))
        texts.append(Text(x - 26, TOP + plot_h + 14, one.label[:16], INK, 11))
        texts.append(Text(x - 26, TOP + plot_h + 30, "kept" if one.kept else "rejected", MUTED, 10))
    rects.append(Rect(LEFT, TOP, 1, plot_h, AXIS))
    rects.append(Rect(LEFT, TOP + plot_h // 2, plot_w, 1, AXIS))
    texts.append(Text(LEFT - 92, TOP + plot_h // 2 - 6, "no change (0.0000)", MUTED, 10))
    return Frame(WIDTH, HEIGHT, title, tuple(rects), tuple(texts))


def _segment(start: tuple[int, int], end: tuple[int, int]) -> list[Rect]:
    """A straight line as a run of one-pixel rectangles, so no drawing library is needed."""
    (x0, y0), (x1, y1) = start, end
    span = max(abs(x1 - x0), abs(y1 - y0), 1)
    return [
        Rect(x0 + (x1 - x0) * step // span, y0 + (y1 - y0) * step // span, 2, 2, AXIS)
        for step in range(span + 1)
    ]
