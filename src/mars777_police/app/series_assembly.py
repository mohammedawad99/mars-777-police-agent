"""The moment a group's fourteen official files become one set on disk.

Every part has arrived by now and each arrived from somewhere different: the
declaration from Step-0, the configs and logs from whichever backend played each
sub-game, the rows from both, and the consensus digest from whichever backend
owned sub-game six. This is where they stop being contributions and become a
series.

**Assembly is attempted, not demanded.** A group whose parts are still arriving
is not in error - it is mid-series - so `assemble` answers `None` rather than
raising, and only says so once everything is present. The refusals belong to the
writer, which is asked exactly once and refuses a set that is short.

**The declaration is not rewritten.** It went to disk when Step-0 merged,
because that is when it existed; the store refuses a differing rewrite and the
writer would otherwise be handed a fifteenth file to place. So the assembled set
counts it rather than producing it again.
"""

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from .counted_series_writer import CountedSeriesWriter
from .declaration_values import Declaration
from .kit_schedule import SUB_GAMES
from .official_artifacts import OfficialArtifactCollector
from .series_result_owner import SeriesResultOwner

ReportingFields = Callable[[Declaration, Sequence[Mapping[str, Any]], str], Mapping[str, object]]
"""Renders the members the normal reporting gate reads, or is absent.

A port rather than a computation, because the canonical result digest lives in
`protocol` and this module is `app`: the composition root is the only layer that
may reach both, so it supplies this and `app` stays where the rules are."""


@dataclass(frozen=True, slots=True)
class SeriesParts:
    """Everything the group has collected, from every process that produced it."""

    declaration: Declaration | None
    collected: OfficialArtifactCollector
    rows: Sequence[Mapping[str, Any]]
    settlement: SeriesResultOwner

    @property
    def ready(self) -> bool:
        """Whether every part a counted series needs has actually arrived."""
        return (
            self.declaration is not None
            and self.declaration.teams.is_merged
            and self.collected.complete
            and len(self.rows) == SUB_GAMES
            and self.settlement.agreed is not None
        )


def assemble(
    parts: SeriesParts,
    writer: CountedSeriesWriter,
    *,
    declaration_document: Any,
    total_tokens: Mapping[str, int],
    timestamp: str,
    reporting_fields: ReportingFields | None = None,
) -> tuple[str, ...] | None:
    """Write the whole set once every part is present, or answer `None`.

    `None` is not a failure. A group mid-series has parts outstanding by
    definition, and treating that as an error would make every sub-game boundary
    look like a fault.

    *reporting_fields* renders what the normal reporting gate reads -
    `mutual_agreement`, `result_sha256` and `reported_by`. It is asked **after**
    `SeriesResultOwner.result`, which refuses a series whose settlement never
    agreed, so those members can only ever describe an agreement that actually
    happened. A caller that supplies none writes the result without them, and
    that result is correctly ineligible to report.
    """
    if not parts.ready:
        return None
    declared = parts.declaration
    if declared is None:  # pragma: no cover - `ready` already established it
        return None
    result = dict(
        parts.settlement.result(
            declaration=declared,
            rows=parts.rows,
            total_tokens=total_tokens,
            timestamp=timestamp,
        )
    )
    if reporting_fields is not None:
        result.update(reporting_fields(declared, parts.rows, timestamp))
    return writer.write(
        declaration=declaration_document(declared),
        collected=parts.collected,
        result=result,
    )
