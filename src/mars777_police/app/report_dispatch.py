"""Who reports a finished series, expressed as a port rather than a mailer.

Appendix E rule 32 requires the result of every legal game to be reported
**automatically**, and rule 35 makes each group's own report the condition for
being credited at all. The series owner therefore has to be able to trigger a
report - but it must not learn what Gmail, OAuth or an attachment is, or the
orchestration layer would depend on a provider.

So the dependency runs one way only: the series owner calls this port, the
composition root supplies something that satisfies it, and the reporting service
behind it is the same one the operator command uses.

**Group ownership needs no arbitration.** Every profile set this project
composes fixes `SeriesConvention.FIXED_ROLE`, and a config lock is refused
unless the peer agreed the same convention - so exactly one MaRs-777 process
plays a counted series and exactly one can ever reach the dispatch point. The
process that finished the series *is* the group's single reporter.
"""

from collections.abc import Callable
from pathlib import Path

ReportDispatchPort = Callable[[Path], None]
"""Report one persisted, agreed result, named by the artifact that was written."""


def no_report(result: Path) -> None:
    """The default: a series given no reporter reports nothing.

    Deliberately silent rather than raising. A development or test series is a
    legitimate thing to run, and it is the counted composition's job to supply a
    real reporter - proved structurally, so absence there fails a test rather
    than a match.
    """
