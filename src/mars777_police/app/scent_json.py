"""The one JSON-safe spelling of a `ScentEmission`, for every artifact that keeps one.

Two official documents now carry the same historical emission: the audit
disclosure the peer verifies, and the log event the replayer reads. They must
spell it identically - a cell written `[row, col]` in one and an object in the
other, or an intensity that is text here and a number there, would be two
representations of one fact, and the correspondence Part 1A froze would only
hold for one of them.

So the deposits are rendered exactly once, here, and both writers delegate. The
intensity goes through the shared `decimal_text` authority, so a trailing zero
survives and no binary float is ever written; the deposits keep the order the
domain already validated, because `ScentEmission` refuses any other.
"""

from ..domain.scent_emission import ScentEmission
from .decimal_text import text_from_decimal

Emission = ScentEmission | None
"""What one reveal deposited, where a reveal that carried nothing says so."""


def deposits_value(emission: ScentEmission) -> list[dict[str, object]]:
    """Every deposit of *emission*, in the canonical order it already holds.

    A pure projection: no cell is recomputed, no intensity is rounded, and
    nothing about where the emitter stood is written - the deposits are the
    whole value.
    """
    return [
        {
            "cell": [deposit.cell.row, deposit.cell.col],
            "intensity": text_from_decimal(deposit.intensity),
        }
        for deposit in emission.deposits
    ]


def scent_fields(emission: Emission) -> dict[str, object]:
    """The log event's scent member, in the spelling the disclosure also uses.

    `null` where the reveal carried none: a pre-V2 turn, or a turn that was
    sealed and never revealed. Written on every reveal event, so an absent
    member never has to be told apart from an older writer's omission.
    """
    return {"scent_emission": None if emission is None else deposits_value(emission)}
