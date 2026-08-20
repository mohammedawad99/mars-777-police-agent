"""What the whole replay may claim, given what each record established.

Two questions the projection cannot answer record by record: which single status
describes a whole sub-game, and whether the audit `REPLAY-002` asks for was
actually completed. Both are arithmetic over the four frozen words, kept apart
from the walker so the walker only walks.
"""

from .replay_values import ReplayCheck, ReplaySummary


def worst_check(checks: list[ReplayCheck]) -> ReplayCheck:
    """The strongest thing the whole replay may claim, never stronger.

    A mismatch outranks an absence, because an accusation that was actually
    established is not softened by evidence that was merely missing. An absence
    outranks every verified record, because one step nobody can check means the
    audit `REPLAY-002` asks for was not completed. `NOT_APPLICABLE` outranks
    nothing: a record with no commitment to check has nothing to fail.
    """
    for status in (ReplayCheck.TAMPERED, ReplayCheck.NOT_CHECKABLE):
        if status in checks:
            return status
    return (
        ReplayCheck.VERIFIED_OK
        if ReplayCheck.VERIFIED_OK in checks
        else (ReplayCheck.NOT_APPLICABLE)
    )


def audit_complete(summary: ReplaySummary) -> bool:
    """Whether every source-required applicable commitment was actually checked.

    Derived rather than stored: `Verified OK` already means every applicable
    record was recomputed and matched, so a caller needs no new field to tell a
    complete audit from an incomplete one.
    """
    return summary.crypto is ReplayCheck.VERIFIED_OK
