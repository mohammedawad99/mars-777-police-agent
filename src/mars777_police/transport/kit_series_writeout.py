"""When a group's fourteen files get written, and why nobody announces it.

Routing and series-wide assembly are different jobs that share a gateway. The
gateway routes; this decides whether the series can be written yet.

**Attempted after every part, announced by none.** The parts arrive from two
processes in an order neither controls, and the last one to land is the only one
that knows it was last. So every contribution asks, `assemble` answers `None`
while anything is outstanding, and no caller has to hold a belief about whether
the series is over.
"""

from typing import TYPE_CHECKING

from ..app.series_assembly import SeriesParts

if TYPE_CHECKING:
    from .kit_gateway import KitGroupGateway


def write_series(gateway: "KitGroupGateway") -> tuple[str, ...] | None:
    """Write the fourteen official files if every part has now arrived.

    Attempted after each part rather than announced by a caller who thinks
    the series is over: the parts arrive from two processes in an order
    neither controls, and the last one to land is the only one that knows it
    was last. `assemble` answers `None` while anything is outstanding, so
    this is safe to call as often as it is reached.

    A rehearsal writes nothing. The official set is a counted artefact, and a
    rehearsal that produced one would have produced a record of a game that
    does not count.
    """
    if gateway.write is None or not gateway.counted.is_counted:
        return None
    return gateway.write(parts(gateway))


def parts(gateway: "KitGroupGateway") -> SeriesParts:
    """Everything the group has collected, as the assembler reads it.

    The rows are read raw rather than through `series()`, which refuses an
    incomplete set: this is asked after every contribution, and a series
    mid-flight is the normal case rather than a fault. `SeriesParts.ready`
    makes the completeness judgement once, in one place.
    """
    return SeriesParts(
        declaration=gateway.declaration,
        collected=gateway.artifacts,
        rows=tuple(row for _, row in sorted(gateway.collected.rows.items())),
        settlement=gateway.settlement,
    )
