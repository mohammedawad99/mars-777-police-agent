"""What to draw, decided without knowing what will draw it.

Layout is arithmetic and policy; rendering is a toolkit. Keeping them apart is
what lets every geometry, label and privacy rule be tested headlessly, and lets
the same frame be drawn into an interactive window or rasterised to the
screenshot `DOC-001` asks for - from one source of truth rather than two.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class Rect:
    """A filled rectangle, optionally outlined."""

    left: int
    top: int
    width: int
    height: int
    fill: str
    outline: str | None = None

    @property
    def right(self) -> int:
        """The x coordinate one pixel past the rectangle."""
        return self.left + self.width

    @property
    def bottom(self) -> int:
        """The y coordinate one pixel past the rectangle."""
        return self.top + self.height


@dataclass(frozen=True, slots=True)
class Text:
    """A single line of text anchored at its top-left corner."""

    left: int
    top: int
    value: str
    fill: str
    size: int = 12
    bold: bool = False


@dataclass(frozen=True, slots=True)
class Frame:
    """One complete picture: its extent, its title, and what is on it."""

    width: int
    height: int
    title: str
    rects: tuple[Rect, ...] = field(default=())
    texts: tuple[Text, ...] = field(default=())

    def labels(self) -> tuple[str, ...]:
        """Every word this frame puts on screen, for tests that read it."""
        return tuple(text.value for text in self.texts)
