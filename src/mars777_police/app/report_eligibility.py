"""When a result may become an email, decided by authorities that already exist.

Appendix E rule 35 is the gate: *"agree with the opponent on the result, and
each group sends a separate completion report; non-reporting by one of the
groups, or a contradictory report, causes disqualification of the game and a
grade of 0 for both groups."* Rule 36 puts the mutual log audit before that
agreement. So a report is eligible **after** the agreement, never before, and
this module asks rather than decides.

**Nothing here recomputes a game fact.** Who won, the scores, the outcome and
the agreement are settled by `ResultExchange`, `result_core` and the protocol
machine; the artifact was written only because `persist_result` already refused
to write it without a mutual agreement. This module reads the phase, reads the
digest, and refuses with a sentence when either is absent.
"""

from .protocol_values import Sha256Digest
from .report_values import GameReport, ReportIneligibleError
from .state_machine import ProtocolPhase

REPORTABLE: ProtocolPhase = ProtocolPhase.REPORT_READY
"""The single phase a report may be sent from.

`STATE_MACHINE.md` reaches it from `FINAL_AUDIT` only, and `FINAL_AUDIT` is
entered only after six sub-games and their mutual audits. It is terminal, so a
report can never be sent from a series that is still running.
"""


def require_reportable(phase: ProtocolPhase) -> None:
    """Refuse unless the series has actually reached the reporting phase."""
    if phase is not REPORTABLE:
        raise ReportIneligibleError(
            f"a game report waits for {REPORTABLE.value}; this series is at {phase.value}"
        )


def report_for(
    *,
    phase: ProtocolPhase,
    agreed: bool,
    game_id: str,
    group_id: str,
    role: str,
    result_sha256: Sha256Digest | None,
    attachment_name: str,
    attachment: bytes,
) -> GameReport:
    """The report for an agreed result, or a refusal naming what is missing.

    *agreed* is `ResultExchange.is_agreed` - this side's record that both
    digests matched - and it is asked for rather than assumed because a report
    without it is exactly what rule 35 sanctions.
    """
    require_reportable(phase)
    if not agreed:
        raise ReportIneligibleError(
            "a game report waits for a mutual agreement on the result; this side has none"
        )
    if result_sha256 is None:
        raise ReportIneligibleError("an agreed result always carries its own digest")
    return GameReport(
        game_id=game_id,
        group_id=group_id,
        role=role,
        result_sha256=result_sha256.value,
        attachment_name=attachment_name,
        attachment=attachment,
    )
