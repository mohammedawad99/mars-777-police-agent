"""The one local fact result agreement waits on: did every sub-game verify?

Stage 5-R4 stopped here. `ResultAgreementRuntime.require_audit` has always taken
a single verdict and has never had a caller, because the audit owner is
per-sub-game while the result agreement is **one message for the whole series** -
`ResultContribution` carries exactly six entries. `STATE_MACHINE.md` puts
FINAL_AUDIT after "series complete" and has it *"recompute every `H_commit`"*, so
the prerequisite was always series-wide. Nothing held six outcomes. This does.

**It consumes real audits, not claims.** `record` takes a completed
`AuditRuntime` and reads the sub-game from that runtime's own context, so a
caller chooses *when* to record a finished audit but never *what* it decided or
*which* sub-game it belongs to.

**It keeps the outcome, not the runtime.** `AuditOutcome` is frozen; the runtime
is not. Holding the runtime would mean asking a mutable object again later and
getting a different answer than the one that was recorded.

**Missing is never success.** Five verified sub-games and one absent produce no
verdict at all - not `VERIFIED_OK` - because a series nobody finished auditing is
not a series that passed. The vocabulary stays exactly `Verified OK` / `TAMPERED`:
incompleteness is the absence of a verdict, never a third one.
"""

from dataclasses import dataclass, field

from .audit_runtime import AuditRuntime
from .audit_values import AuditOutcome, AuditPhase
from .protocol_errors import LocalDefectError, StaleMessageError
from .protocol_values import FinalAuditVerdict
from .result_values import SUB_GAME_SEQUENCE

REQUIRED_SUB_GAMES = frozenset(SUB_GAME_SEQUENCE)
"""The six sub-games a series must audit - the same 1…6 a contribution covers."""


@dataclass(slots=True)
class SeriesAuditGate:
    """One series' local audit outcomes, and the verdict they add up to."""

    outcomes: dict[int, AuditOutcome] = field(default_factory=dict)

    def record(self, audit: AuditRuntime) -> None:
        """Snapshot one completed sub-game audit under its own sub-game.

        The runtime must have finished: an audit still awaiting a disclosure has
        decided nothing, and recording it would let an unfinished sub-game count
        toward a completed series.
        """
        if audit.phase is not AuditPhase.COMPLETE or audit.outcome is None:
            raise StaleMessageError("only a completed sub-game audit may be recorded")
        sub_game = audit.context.sub_game
        if sub_game not in REQUIRED_SUB_GAMES:
            raise LocalDefectError(f"sub-game {sub_game} is not part of this series")
        if sub_game in self.outcomes:
            raise LocalDefectError(f"sub-game {sub_game} was already audited")
        self.outcomes[sub_game] = audit.outcome

    @property
    def audited(self) -> tuple[int, ...]:
        """The sub-games recorded so far, in ascending order."""
        return tuple(sorted(self.outcomes))

    @property
    def complete(self) -> bool:
        """Whether all six required sub-game audits have been recorded."""
        return set(self.outcomes) == REQUIRED_SUB_GAMES

    @property
    def verdict(self) -> FinalAuditVerdict | None:
        """The series verdict, or `None` while any sub-game is unaudited.

        `None` is the honest answer to an incomplete series, and it is exactly
        what `require_audit` already refuses - so an unfinished series cannot
        reach result agreement by default, only by passing.
        """
        if not self.complete:
            return None
        if all(outcome.verified for outcome in self.outcomes.values()):
            return FinalAuditVerdict.VERIFIED_OK
        return FinalAuditVerdict.TAMPERED
