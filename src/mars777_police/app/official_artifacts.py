"""The group's official per-sub-game documents, gathered from both backends.

A two-process group plays three sub-games in each process, but a counted series
leaves **one** set of fourteen files. The per-sub-game halves therefore have to
meet somewhere, and the only place both backends can reach is the gateway - the
same reason `SeriesRowCollector` lives there.

**It collects and it judges nothing.** Whether a config artifact coheres with
its terms agreement, and whether a log's commitments reproduce, are decisions
their own builders already made before the document existed. This owns which
documents have arrived, that none arrived twice, and whether the set is complete.

**A document settles once.** A second one for the same sub-game is refused
rather than overwritten, exactly as a settled row is: a late or duplicated
contribution silently replacing an earlier one would change a record both sides
may already have agreed, and the replacement would leave no trace.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from .kit_schedule import SUB_GAMES
from .protocol_errors import StaleMessageError

CONFIG = "config"
LOG = "log"
KINDS = (CONFIG, LOG)
"""The two per-sub-game families. The declaration and result are series-wide."""

PER_SERIES = len(KINDS) * SUB_GAMES
"""Twelve: six configs and six logs. The other two files are not collected here."""


@dataclass(slots=True)
class OfficialArtifactCollector:
    """One series' per-sub-game official documents, from whichever backend built them."""

    documents: dict[tuple[str, int], dict[str, Any]] = field(default_factory=dict)

    def record(self, kind: str, sub_game: int, document: Mapping[str, Any]) -> None:
        """Keep one official document, or refuse what cannot be one."""
        if kind not in KINDS:
            raise StaleMessageError(f"{kind!r} is not an official per-sub-game family {KINDS}")
        if type(sub_game) is not int or not 1 <= sub_game <= SUB_GAMES:
            raise StaleMessageError(f"sub-game {sub_game} is outside a {SUB_GAMES}-sub-game series")
        if not document:
            raise StaleMessageError(f"the {kind} for sub-game {sub_game} carries nothing")
        key = (kind, sub_game)
        if key in self.documents:
            raise StaleMessageError(
                f"the {kind} for sub-game {sub_game} was already contributed; it settles once",
            )
        self.documents[key] = dict(document)

    def get(self, kind: str, sub_game: int) -> dict[str, Any] | None:
        """The document for one family and sub-game, or `None` if it never arrived."""
        found = self.documents.get((kind, sub_game))
        return None if found is None else dict(found)

    @property
    def complete(self) -> bool:
        """Whether all twelve per-sub-game documents have been contributed."""
        return len(self.documents) == PER_SERIES

    @property
    def missing(self) -> tuple[tuple[str, int], ...]:
        """What the set still lacks, named so an operator can see which half is late."""
        return tuple(
            (kind, number)
            for kind in KINDS
            for number in range(1, SUB_GAMES + 1)
            if (kind, number) not in self.documents
        )

    def require_complete(self) -> None:
        """Refuse to treat an incomplete series as one, and say what is absent."""
        absent = self.missing
        if absent:
            raise StaleMessageError(
                f"the series is missing {len(absent)} of {PER_SERIES} documents: {absent}",
            )
