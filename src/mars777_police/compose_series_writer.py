"""How a counted group writes its fourteen files, assembled once at composition.

Separated from the gateway composition because it answers a different question:
that one decides which objects exist, this one decides what happens when the
last part of a series arrives. Keeping them apart also keeps each within the
project's line budget without either becoming a list of imports.
"""

from collections.abc import Callable

from .app.counted_series_writer import CountedSeriesWriter
from .app.series_assembly import SeriesParts, assemble
from .artifact_documents import declaration_document
from .infra.artifacts import JsonArtifactStore
from .infra.clock import SystemClock
from .infra.settings import RuntimeSettings
from .launch_input import read_launch_document
from .operator_requests import PublicGatewayRequest

__all__ = ["series_writer"]


def series_writer(
    settings: RuntimeSettings, request: PublicGatewayRequest
) -> Callable[[SeriesParts], tuple[str, ...] | None] | None:
    """How this group writes its fourteen files, or `None` when it writes none.

    A rehearsal gets `None`: the official set is a counted artefact, and a
    rehearsal that produced one would have produced the record of a game that
    does not count. The game id comes from the declaration rather than being
    assembled here, because the declaration is the thing both sides agreed.
    """
    if not request.counted or request.launch is None:
        return None
    declaration = read_launch_document(request.launch).identity.declaration
    writer = CountedSeriesWriter(JsonArtifactStore(settings.artifact_root), declaration.game_id)

    def write(parts: SeriesParts) -> tuple[str, ...] | None:
        return assemble(
            parts,
            writer,
            declaration_document=declaration_document,
            total_tokens={},
            timestamp=SystemClock().now().value,
        )

    return write
