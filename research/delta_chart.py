"""Signed differences, drawn around a zero line rather than a shifted origin.

**Why not the zero-based bar chart this project already has.** That chart is
right for a proportion, where zero is a real floor. A paired *difference* is
signed, and forcing it onto a zero-based axis means shifting every value by a
constant - which draws a collapse of -4.9 points and a gain of +7.2 points as
two nearly identical bars, because both are dominated by the shift. The reader
then sees "all four candidates are about the same", which is the opposite of
what the measurement says.

So the zero line is drawn where zero actually is, losses extend left, gains
extend right, and the axis is symmetric so a loss and a gain of equal size are
equally long.
"""

from dataclasses import dataclass

from mars777_police.gui.primitives import Frame, Rect, Text

from .charts import AXIS, BAR, HEIGHT, INK, MUTED, PAPER, WIDTH

DROP = "#c2453c"
LEFT = 150
RIGHT = 150
TOP = 84
BOTTOM = 104


@dataclass(frozen=True, slots=True)
class Delta:
    """One candidate's paired difference and its interval."""

    label: str
    value: float
    low: float | None
    """Absent when the sample was too small to bootstrap. Then no interval is
    drawn, rather than a zero-width one that would read as high precision."""
    high: float | None
    n: int
    kept: bool
    """Whether the bar is drawn as a survivor. Colour only."""
    status: str = ""
    """The verdict word, when the bar *is* a candidate. Opponent families and
    configurations are not candidates, so they carry no verdict and get none."""


def _span(deltas: tuple[Delta, ...]) -> float:
    reach = [abs(one.value) for one in deltas]
    reach += [abs(one.low) for one in deltas if one.low is not None]
    reach += [abs(one.high) for one in deltas if one.high is not None]
    return max([*reach, 1e-9]) * 1.15


def diverging(title: str, unit: str, deltas: tuple[Delta, ...], caption: str) -> Frame:
    """A symmetric signed-difference chart with a real zero line."""
    if not deltas:
        raise ValueError("a figure needs at least one measured candidate")
    plot_w, plot_h = WIDTH - LEFT - RIGHT, HEIGHT - TOP - BOTTOM
    span = _span(deltas)
    middle = LEFT + plot_w // 2
    scale = (plot_w // 2) / span
    rects = [Rect(0, 0, WIDTH, HEIGHT, PAPER)]
    texts = [
        Text(30, 24, title, INK, 15, True),
        Text(30, 48, caption, MUTED, 11),
        Text(30, HEIGHT - 26, f"{unit}; zero line = no change from baseline", MUTED, 11),
    ]
    height = max(10, plot_h // len(deltas) - 18)
    for index, one in enumerate(deltas):
        top = TOP + index * (plot_h // len(deltas))
        width = max(int(abs(one.value) * scale), 1)
        start = middle if one.value >= 0 else middle - width
        rects.append(Rect(start, top, width, height, BAR if one.kept else DROP))
        rects.extend(_interval(one, middle, scale, top + height + 2))
        texts.append(Text(12, top + height // 3, one.label[:20], INK, 11))
        texts.append(Text(_label_at(one, middle, scale), top + height // 3, _say(one), INK, 11))
    rects.append(Rect(middle, TOP - 8, 1, plot_h + 8, AXIS))
    texts.extend(_axis(middle, scale, span, TOP + plot_h))
    return Frame(WIDTH, HEIGHT, title, tuple(rects), tuple(texts))


def _say(one: Delta) -> str:
    said = f"{one.value:+.4f}  n={one.n}"
    return f"{said}  {one.status.lower()}" if one.status else said


def _label_at(one: Delta, middle: int, scale: float) -> int:
    """Text sits outside the bar, on the side the bar grew, and never off-canvas."""
    width = int(abs(one.value) * scale)
    at = middle + width + 8 if one.value >= 0 else middle - width - 8 - 150
    return max(4, min(at, WIDTH - 152))


def _interval(one: Delta, middle: int, scale: float, top: int) -> list[Rect]:
    """No interval is drawn when none was estimated."""
    if one.low is None or one.high is None:
        return []
    low = middle + int(one.low * scale)
    return [Rect(low, top, max(int((one.high - one.low) * scale), 1), 3, INK)]


def _axis(middle: int, scale: float, span: float, bottom: int) -> list[Text]:
    marks = []
    for step in (-1.0, -0.5, 0.0, 0.5, 1.0):
        value = span * step
        marks.append(
            Text(middle + int(value * scale) - 16, bottom + 14, f"{value:+.3f}", MUTED, 10)
        )
    return marks
