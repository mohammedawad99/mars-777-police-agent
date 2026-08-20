"""Colours, and the words that must accompany every one of them.

Status is never carried by colour alone: `GUI-003` puts a belief map and a
turn-state banner in front of a grader, and a reader who cannot separate two
hues must still be able to tell `Verified OK` from `TAMPERED`. So every status
here is a colour **and** a glyph **and** a word, and the drawing code uses all
three.
"""

from typing import Final

BACKGROUND: Final[str] = "#101418"
PANEL: Final[str] = "#1b2027"
GRID: Final[str] = "#39424e"
TEXT: Final[str] = "#e8edf2"
MUTED: Final[str] = "#9aa7b4"

OWN: Final[str] = "#4da3ff"
BARRIER: Final[str] = "#7a8794"
BELIEF: Final[str] = "#ff8c42"
POLICE: Final[str] = "#4da3ff"
THIEF: Final[str] = "#f2c14e"
BOTH: Final[str] = "#c04df2"
"""One cell holding both agents. A third colour, because two stacked would hide one."""

VERIFIED: Final[str] = "#3fbf7f"
TAMPERED: Final[str] = "#ff5c5c"
UNCHECKABLE: Final[str] = "#f2c14e"
INAPPLICABLE: Final[str] = "#9aa7b4"

STATUS: Final[dict[str, tuple[str, str]]] = {
    "Verified OK": (VERIFIED, "[OK]"),
    "TAMPERED": (TAMPERED, "[!!]"),
    "NOT_CHECKABLE": (UNCHECKABLE, "[??]"),
    "NOT_APPLICABLE": (INAPPLICABLE, "[--]"),
}
"""Colour **and** glyph for each verification word, so neither stands alone."""


def status_colour(word: str) -> str:
    """The colour for a verification word, muted when the word is unknown."""
    return STATUS.get(word, (MUTED, "[??]"))[0]


def status_glyph(word: str) -> str:
    """The shape for a verification word, so colour is never the only signal."""
    return STATUS.get(word, (MUTED, "[??]"))[1]


def belief_shade(intensity: float, strongest: float) -> str:
    """A warm shade proportional to *intensity*, always labelled by its number.

    Returned as a hex string rather than a name: the heatmap needs a gradient,
    and the cell also carries its numeric value, so the shade is an aid rather
    than the information itself.
    """
    share = 0.0 if strongest <= 0 else max(0.0, min(1.0, intensity / strongest))
    red = int(60 + 195 * share)
    green = int(50 + 90 * share)
    return f"#{red:02x}{green:02x}42"
