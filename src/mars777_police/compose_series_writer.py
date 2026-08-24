"""How a counted group writes its fourteen files, assembled once at composition.

Separated from the gateway composition because it answers a different question:
that one decides which objects exist, this one decides what happens when the
last part of a series arrives. Keeping them apart also keeps each within the
project's line budget without either becoming a list of imports.

**This is also where an alternating counted series would become reportable.**
The fixed-role path reaches `SeriesDriver._report` because one process plays the
whole series; an alternating one never does, because the group's two backends
each hold three sub-games and only the gateway holds the series. So the gateway
hands the written artifact to the same `send_game_report` an operator would type.

**Eligibility comes from the agreement authority, never from here.** The result
carries `mutual_agreement`, `result_sha256` and `reported_by` only once
`ResultExchange.is_agreed` holds - both directions completed, both participants'
own contributions present, and both independently computed digests equal. Until
then no member is rendered, the normal gate refuses the result, and nothing is
mailed. That is the honest state of a series whose result nobody agreed.
"""

from collections.abc import Callable, Mapping
from pathlib import Path

from . import GROUP_CODE
from .app.artifact_store import result_name
from .app.counted_series_writer import CountedSeriesWriter
from .app.kit_result_agreement import GroupResultAgreement
from .app.series_assembly import ReportingFields, SeriesParts, assemble
from .artifact_documents import declaration_document
from .compose_report import send_game_report
from .infra.artifacts import JsonArtifactStore
from .infra.clock import SystemClock
from .infra.settings import RuntimeSettings
from .launch_input import read_launch_document
from .operator_requests import PublicGatewayRequest

__all__ = ["reporting_fields_for", "series_writer"]

Reporter = Callable[[Path], object]
"""Who delivers a finished counted result. Injected so a test never mails."""


def reporting_fields_for(agreement: GroupResultAgreement | None) -> ReportingFields | None:
    """What the normal reporting gate reads, or `None` when nothing can supply it.

    Rendered from the agreement authority and nowhere else: `mutual_agreement`
    is `True` only because `ResultExchange.is_agreed` is, which needs both
    directions completed and both independently computed digests equal.
    `result_sha256` is the digest that exchange already computed over the
    approval core, and `total_tokens` is derived from the two participant-owned
    contributions inside it. An agreement that has not completed renders no
    members at all, so the result stays correctly ineligible.
    """
    if agreement is None:
        return None

    def build(declaration: object, rows: object, timestamp: str) -> Mapping[str, object]:
        exchange = agreement.exchange
        if exchange is None or not exchange.is_agreed or exchange.local_digest is None:
            return {}
        core = exchange.approval_core()
        return {
            "result_sha256": exchange.local_digest.value,
            "mutual_agreement": True,
            "reported_by": GROUP_CODE,
            "total_tokens": {
                core.participants.group_a: core.total_tokens.group_a,
                core.participants.group_b: core.total_tokens.group_b,
            },
        }

    return build


def series_writer(
    settings: RuntimeSettings,
    request: PublicGatewayRequest,
    reporter: Reporter = send_game_report,
    agreement: "GroupResultAgreement | None" = None,
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
    game_id = declaration.game_id
    writer = CountedSeriesWriter(JsonArtifactStore(settings.artifact_root), game_id)

    def write(parts: SeriesParts) -> tuple[str, ...] | None:
        if agreement is not None and not agreement.is_agreed:
            # The result is the last of the fourteen and the only one that waits
            # on a fact neither side owns alone. Writing the set before the
            # agreement completed would produce a result nobody had agreed, and
            # the store refuses to rewrite it afterwards.
            return None
        written = assemble(
            parts,
            writer,
            declaration_document=declaration_document,
            total_tokens={},
            timestamp=SystemClock().now().value,
            reporting_fields=reporting_fields_for(agreement),
        )
        if written is not None:
            _report(settings.artifact_root / result_name(game_id), reporter)
        return written

    return write


def _report(result: Path, reporter: Reporter) -> None:
    """Hand the written result to the reporter, and let nothing it says matter.

    The series is over and all fourteen files are on disk before this runs, so a
    provider refusal is a delivery problem and may never rewrite a result, a
    score or an audit. An **ineligible** result is refused here too, by the same
    normal gate an operator's command uses - a result no peer agreed is not
    mailed, and the refusal is contained rather than propagated into the series.

    Sending twice is prevented by the durable delivery record `send_game_report`
    already consults, not by anything remembered here: a gateway restarted after
    a successful report must not mail the series again.
    """
    try:
        reporter(result)
    except Exception:
        return
