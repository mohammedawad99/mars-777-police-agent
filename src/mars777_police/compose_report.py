"""Assembling the one path a game report takes, from a stored result to Gmail.

Nothing is decided here. The result artifact is read through the same defensive
reader the Replay Viewer uses, its agreement is checked by `report_source`, its
eligibility by `report_eligibility`, its message by `report_message`, its
admission by the Gatekeeper that already exists, and its delivery by the Gmail
adapter. This module joins those six and adds no rule of its own.

**The Gmail provider is initialised only when a report is actually sent.** No
strict series, KIT run, replay or GUI path reaches this module, so an operator
who never reports never needs a credential - and a missing credential can never
stop a game.
"""

from dataclasses import dataclass
from pathlib import Path

from .app.artifact_store import result_name
from .app.gatekeeper import Gatekeeper
from .app.report_eligibility import report_for
from .app.report_service import SEND_REPORT, ReportService
from .app.report_source import reportable_facts
from .app.report_values import GameReport, ReportDelivery
from .app.state_machine import ProtocolPhase
from .identity import ROLE
from .infra.gmail_credentials import credentials_path, load_credentials
from .infra.gmail_sender import GmailSender
from .infra.rate_limit_file import load_rate_limits
from .infra.replay_files import read_document
from .infra.report_evidence import (
    EVIDENCE_DIRECTORY,
    accepted_identity,
    evidence_document,
    write_evidence,
)


@dataclass(frozen=True, slots=True)
class ReportOutcome:
    """What one reporting run did, and where it recorded having done it."""

    report: GameReport
    delivery: ReportDelivery
    evidence: Path


def read_report(result: Path, root: Path | None = None) -> GameReport:
    """Build the report a stored result artifact makes eligible, or refuse it."""
    document = read_document(result, root)
    game_id, group_id, digest = reportable_facts(document, str(result))
    return report_for(
        phase=ProtocolPhase.REPORT_READY,
        agreed=True,
        game_id=game_id,
        group_id=group_id,
        role=ROLE.value,
        result_sha256=digest,
        attachment_name=result_name(game_id),
        attachment=result.read_bytes(),
    )


def send_game_report(result: Path, root: Path | None = None) -> ReportOutcome:
    """Send the report for *result* through the gate, and record the outcome.

    **Sent once, across restarts too.** `ReportService` already refuses a second
    send inside one process; this also reads the durable delivery record, because
    an agent restarted after a successful report would otherwise mail the
    lecturer the same series again - and Appendix E rule 35 penalises a
    contradictory report with 0 for *both* groups.

    The comparison is on the report identity, the agreed result digest: a
    different agreed result under the same `game_id` is a different report and is
    still sent.
    """
    report = read_report(result, root)
    already = accepted_identity(result.parent, report.game_id)
    if already == report.identity:
        settled = ReportDelivery(report.identity, True)
        return ReportOutcome(report, settled, result.parent / EVIDENCE_DIRECTORY)
    sender = GmailSender(load_credentials(credentials_path()))
    keeper = Gatekeeper(load_rate_limits())
    service = ReportService(sender, keeper.call)
    delivery = service.send(report)
    document = evidence_document(delivery, report.game_id, SEND_REPORT)
    evidence = write_evidence(result.parent, report.game_id, document)
    return ReportOutcome(report, delivery, evidence)
