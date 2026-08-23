"""Writing the one artifact that describes the series rather than a part of it.

The declaration is produced at a different moment from every other official
file: not when a sub-game ends, but the instant Step-0 merges both halves into
one authenticated document. That is the earliest point at which it exists and
the last point at which it is still only about the series - so it is written
there, once, and never rebuilt from a later view.

**Written from the merged document, never from our own half.** Our launch
document holds only the subtree we authored; the artifact has to carry both
participants, because a reader checking role attribution needs the opponent's
repository commits as much as ours. Writing the pre-merge document would
produce a file that validates and describes half a pairing.

**Once.** A redelivered Step-0 merges to the same document and must not rewrite
the artifact - the store refuses a differing rewrite anyway, but recording that
intent here means a duplicate never even reaches it.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from .artifact_store import ArtifactDocument, ArtifactStorePort, declaration_name
from .declaration_values import Declaration
from .protocol_errors import LocalDefectError

Render = Callable[[Declaration], ArtifactDocument]


@dataclass(slots=True)
class SeriesDeclarationWriter:
    """The declaration artifact, written when Step-0 first merges both halves."""

    store: ArtifactStorePort
    render: Render
    written: str | None = field(default=None)
    """The name written, or `None` while no merged declaration has arrived."""

    def write(self, declaration: Declaration) -> str:
        """Write the merged declaration once and return the name it took."""
        teams = declaration.teams
        if not teams.is_merged:
            raise LocalDefectError(
                "the declaration artifact carries both participants;"
                " this one holds a single subtree and describes half a pairing",
            )
        name = declaration_name(declaration.game_id)
        if self.written is not None:
            if self.written != name:  # pragma: no cover - one series, one game id
                raise LocalDefectError(f"already wrote {self.written}, refusing {name}")
            return self.written
        document: dict[str, Any] = dict(self.render(declaration))
        self.store.store(name, document)
        self.written = name
        return name
