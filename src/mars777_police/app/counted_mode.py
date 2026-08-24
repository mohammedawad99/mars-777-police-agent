"""Whether this process may produce a counted series, decided once at startup.

Two runs of the same code differ in what their output is worth, and nothing
about a running process makes that visible. So the distinction is a value
carried from the operator's own command, not inferred from a launch document, an
endpoint, a secret's presence or how far a series got.

**Structurally hard to confuse, on purpose.** A rehearsal and a counted run are
one flag apart in intent and irreversible in consequence: a rehearsal that
reported would mail a lecturer a result nobody agreed to count, and a counted
run that did not report would lose a played series. So the two are separate
members of an enum rather than a boolean, every counted-only capability asks
this value rather than reading a flag beside it, and the questions are phrased
so that forgetting to ask fails closed.

**Reporting is the sharpest edge**, which is why `may_report` exists rather than
callers comparing modes themselves. A future third mode would otherwise silently
inherit whichever branch `!= REHEARSAL` happened to give it.
"""

from dataclasses import dataclass
from enum import StrEnum

from .protocol_errors import LocalDefectError


class CountedMode(StrEnum):
    """What a run of this agent is allowed to be worth."""

    REHEARSAL = "REHEARSAL"
    """Authenticated, interoperable, and worth nothing. Never reports."""

    COUNTED = "COUNTED"
    """The league encounter. Reports exactly once, after mutual agreement."""


@dataclass(frozen=True, slots=True)
class CountedRun:
    """One run's mode, and the counted-only questions callers must ask it."""

    mode: CountedMode

    @property
    def is_counted(self) -> bool:
        """Whether this run may produce a counted series at all."""
        return self.mode is CountedMode.COUNTED

    @property
    def may_report(self) -> bool:
        """Whether this run may ever send the final report.

        Asked rather than derived by comparing modes at each call site: a third
        mode added later would otherwise inherit whichever branch `!= REHEARSAL`
        happened to give it, and reporting is the one capability where guessing
        wrong is irreversible.
        """
        return self.mode is CountedMode.COUNTED

    def require_counted(self, capability: str) -> None:
        """Refuse a counted-only capability in a rehearsal, naming which one."""
        if not self.is_counted:
            raise LocalDefectError(
                f"{capability} belongs to a counted run; this one is a"
                f" {self.mode.value.lower()} and can never be counted or reported",
            )

    def require_rehearsal(self, capability: str) -> None:
        """Refuse a rehearsal-only capability in a counted run."""
        if self.is_counted:
            raise LocalDefectError(
                f"{capability} belongs to a rehearsal; this run is counted",
            )


def rehearsal() -> CountedRun:
    """The default a process gets when nobody asked for a counted run."""
    return CountedRun(CountedMode.REHEARSAL)


def counted() -> CountedRun:
    """A counted run. Only an explicit operator decision reaches this."""
    return CountedRun(CountedMode.COUNTED)
