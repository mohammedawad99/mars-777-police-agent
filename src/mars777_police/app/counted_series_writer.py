"""Writing one counted series' fourteen official files, and refusing thirteen.

The set is exact: one declaration, six configs, six logs, one result. A group
that writes some of them has not produced a counted series - it has produced
evidence that one was attempted - so this writes the whole set or none of it.

**Order is not decoration.** The declaration is written first because it is the
only file that describes the series rather than a part of it, and the result is
written last because it is the only one that waits on a fact neither side owns
alone. In between, each sub-game's config precedes its log, matching the order
the sub-game actually produced them.

**Nothing here decides whether a document is sound.** Its own builder already
refused to produce it otherwise - a config that does not cohere with its terms
agreement and a log whose commitments do not reproduce were never documents.
This owns the set, its completeness and its names.

**Names come from `artifact_store`**, which is the one authority for them, so a
reader that knows the naming rule can find every file without being told.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from .artifact_store import (
    ArtifactDocument,
    ArtifactStorePort,
    config_name,
    declaration_name,
    log_name,
    result_name,
)
from .kit_schedule import SUB_GAMES
from .official_artifacts import CONFIG, LOG, OfficialArtifactCollector
from .protocol_errors import LocalDefectError

OFFICIAL_FILES = 2 + 2 * SUB_GAMES
"""Fourteen. Reporting-delivery evidence is deliberately not one of them."""


@dataclass(slots=True)
class CountedSeriesWriter:
    """The group's official artifact set, written once the series has earned it."""

    store: ArtifactStorePort
    game_id: str

    def write(
        self,
        *,
        declaration: Mapping[str, Any],
        collected: OfficialArtifactCollector,
        result: Mapping[str, Any] | None,
    ) -> tuple[str, ...]:
        """Write the complete set and return every name written, in order.

        *result* is `None` until both sides agreed one. That is not a partial
        success to be written anyway: rule 35 scores an unagreed series 0 for
        both groups, and a result file asserting an agreement that never
        happened would be the one artifact nobody could defend.
        """
        collected.require_complete()
        if not declaration:
            raise LocalDefectError("a counted series is written from a merged declaration")
        if result is None:
            raise LocalDefectError(
                "the result artifact waits for a mutual agreement; the series has none",
            )
        written = [self._put(declaration_name(self.game_id), declaration)]
        for number in range(1, SUB_GAMES + 1):
            written.append(
                self._put(config_name(self.game_id, number), self._one(collected, CONFIG, number))
            )
            written.append(
                self._put(log_name(self.game_id, number), self._one(collected, LOG, number))
            )
        written.append(self._put(result_name(self.game_id), result))
        if len(written) != OFFICIAL_FILES:  # pragma: no cover - arithmetic, kept as a guard
            raise LocalDefectError(f"wrote {len(written)} official files, not {OFFICIAL_FILES}")
        return tuple(written)

    def _one(self, collected: OfficialArtifactCollector, kind: str, number: int) -> dict[str, Any]:
        found = collected.get(kind, number)
        if found is None:  # pragma: no cover - require_complete already refused
            raise LocalDefectError(f"the {kind} for sub-game {number} never arrived")
        return found

    def _put(self, name: str, document: Mapping[str, Any]) -> str:
        stored: ArtifactDocument = dict(document)
        self.store.store(name, stored)
        return name
