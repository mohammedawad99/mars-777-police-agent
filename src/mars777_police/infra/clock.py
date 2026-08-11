"""The production `TimestampPort`: the one place the runtime reads wall time.

`TimestampPort` is consulted by exactly one caller - the deterministic result
proposer, once per agreement attempt - and the non-proposer echoes what it
receives, so this clock is deliberately tiny and has no other job.

**Wall time, not the deadline clock.** `CONCURRENCY_MODEL.md` keeps watchdog and
deadline timers on their own monotonic abstraction, which must not be replaced
by this one: a wall clock can step backwards across an NTP correction, which is
harmless for stamping an artifact and wrong for measuring a timeout. The two
stay separate.

`UtcTimestamp` owns the lexical contract - exactly `YYYY-MM-DDTHH:MM:SSZ`, second
precision - so this module formats and lets that type validate rather than
re-stating the rule. Sub-second precision is **truncated, never rounded**: a
timestamp that jumped forward into the next second would be a moment the process
had not yet reached.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime

from ..app.artifact_values import UtcTimestamp

FORM = "%Y-%m-%dT%H:%M:%SZ"


def utc_now() -> datetime:
    """The real instant, always timezone-aware."""
    return datetime.now(UTC)


@dataclass(frozen=True, slots=True)
class SystemClock:
    """The production timestamp source.

    *source* is a narrow injected callable rather than a clock framework: it
    exists so a test can supply two known instants and assert the exact rendered
    form, and for no other reason.
    """

    source: Callable[[], datetime] = field(default=utc_now)

    def now(self) -> UtcTimestamp:
        """Return the current instant in the frozen lexical form."""
        moment = self.source()
        if moment.tzinfo is None:
            raise ValueError("the clock source must return a timezone-aware datetime")
        return UtcTimestamp(moment.astimezone(UTC).strftime(FORM))
