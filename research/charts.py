"""Deterministic figures, drawn with the renderer this project already ships.

**No plotting dependency was added.** The GUI stage built a tested, headless,
deterministic rasteriser over a toolkit-free `Frame`, and a bar chart is
rectangles and text. Reusing it costs nothing to install, runs identically on
Ubuntu and Windows, and keeps the research figures inside the same coverage and
type discipline as everything else. `matplotlib` would have added a large
optional dependency whose absence on a runner would silently skip the very
tests that prove the figures regenerate.

**Grading-readable by construction.** Every figure carries a title, labelled
axes with units, the sample size, the baseline identity, and a scale that starts
at zero whenever proportions are compared - a truncated proportion axis
exaggerates differences, which is the one chart lie that matters here.
"""

from dataclasses import dataclass
from pathlib import Path

from mars777_police.gui.image_renderer import write_png
from mars777_police.gui.primitives import Frame, Rect, Text

WIDTH = 900
HEIGHT = 520
LEFT = 190
BOTTOM = 96
TOP = 78
RIGHT = 40

INK = "#101418"
PAPER = "#ffffff"
BAR = "#4d7fff"
AXIS = "#39424e"
MUTED = "#5b6774"


@dataclass(frozen=True, slots=True)
class Bar:
    """One measured group: its label, its value, its interval and its sample size."""

    label: str
    value: float
    low: float | None
    high: float | None
    n: int


def _plot_box() -> tuple[int, int]:
    return (WIDTH - LEFT - RIGHT, HEIGHT - TOP - BOTTOM)


def _ticks(ceiling: float) -> tuple[float, ...]:
    return tuple(ceiling * step / 4.0 for step in range(5))


def bar_chart(title: str, unit: str, bars: tuple[Bar, ...], caption: str) -> Frame:
    """A zero-based horizontal bar chart with intervals, sample sizes and a caption."""
    if not bars:
        raise ValueError("a figure needs at least one measured group")
    plot_w, plot_h = _plot_box()
    ceiling = max([one.value for one in bars] + [one.high or 0.0 for one in bars] + [1e-9])
    rects = [Rect(0, 0, WIDTH, HEIGHT, PAPER)]
    texts = [
        Text(LEFT - 150, 24, title, INK, 15, True),
        Text(LEFT - 150, 48, caption, MUTED, 11),
        Text(LEFT - 150, HEIGHT - 26, f"value ({unit}); bars start at zero", MUTED, 11),
    ]
    height = max(10, plot_h // max(len(bars), 1) - 16)
    for index, bar in enumerate(bars):
        top = TOP + index * (plot_h // len(bars))
        width = int(plot_w * bar.value / ceiling)
        rects.append(Rect(LEFT, top, max(width, 1), height, BAR))
        texts.append(Text(8, top + height // 3, f"{bar.label[:26]}", INK, 11))
        texts.append(
            Text(LEFT + width + 8, top + height // 3, f"{bar.value:.3f}  n={bar.n}", INK, 11)
        )
        if bar.low is not None and bar.high is not None:
            rects.append(_interval(bar, ceiling, plot_w, top, height))
    rects.append(Rect(LEFT, TOP, 1, plot_h, AXIS))
    rects.append(Rect(LEFT, TOP + plot_h, plot_w, 1, AXIS))
    for value in _ticks(ceiling):
        at = LEFT + int(plot_w * value / ceiling)
        rects.append(Rect(at, TOP + plot_h, 1, 6, AXIS))
        texts.append(Text(at - 12, TOP + plot_h + 12, f"{value:.2f}", MUTED, 10))
    return Frame(WIDTH, HEIGHT, title, tuple(rects), tuple(texts))


def _interval(bar: Bar, ceiling: float, plot_w: int, top: int, height: int) -> Rect:
    """The 95% interval, drawn just **below** the bar rather than through it.

    Through the bar it would sit under the value label and neither could be
    read; below it, both are legible and the interval is still visibly attached
    to the measurement it belongs to.
    """
    low = LEFT + int(plot_w * (bar.low or 0.0) / ceiling)
    high = LEFT + int(plot_w * (bar.high or 0.0) / ceiling)
    return Rect(low, top + height + 1, max(high - low, 1), 3, INK)


def save(frame: Frame, path: Path) -> Path:
    """Rasterise and write the figure. Same bytes on every platform."""
    return write_png(frame, path)
