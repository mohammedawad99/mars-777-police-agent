"""The production clock renders exactly the frozen lexical form, in UTC.

`UtcTimestamp` owns validation, so these tests assert the *rendering* decisions
this module actually makes: truncation rather than rounding, conversion of an
offset instant to UTC, and refusal of a naive one.
"""

from datetime import UTC, datetime, timedelta, timezone

import pytest

from mars777_police.app.artifact_values import UtcTimestamp
from mars777_police.app.ports import TimestampPort
from mars777_police.infra.clock import SystemClock, utc_now


def at(moment: datetime) -> UtcTimestamp:
    return SystemClock(lambda: moment).now()


def test_the_production_clock_satisfies_the_timestamp_port() -> None:
    port: TimestampPort = SystemClock()
    assert isinstance(port.now(), UtcTimestamp)


def test_a_known_instant_renders_in_the_frozen_form() -> None:
    stamped = at(datetime(2026, 8, 7, 1, 2, 3, tzinfo=UTC))
    assert stamped == UtcTimestamp("2026-08-07T01:02:03Z")
    assert len(stamped.value) == 20
    assert stamped.value.endswith("Z") and "T" in stamped.value


def test_two_distinct_instants_render_distinctly() -> None:
    first = at(datetime(2026, 8, 7, 0, 0, 0, tzinfo=UTC))
    second = at(datetime(2026, 8, 7, 0, 0, 1, tzinfo=UTC))
    assert first != second
    assert first.value == "2026-08-07T00:00:00Z"
    assert second.value == "2026-08-07T00:00:01Z"


@pytest.mark.parametrize("micros", [1, 499999, 500000, 999999])
def test_sub_second_precision_is_truncated_never_rounded(micros: int) -> None:
    """Rounding up would stamp a moment the process has not reached yet."""
    stamped = at(datetime(2026, 8, 7, 1, 2, 3, micros, tzinfo=UTC))
    assert stamped.value == "2026-08-07T01:02:03Z"
    assert "." not in stamped.value


def test_an_offset_instant_is_converted_to_utc() -> None:
    east = timezone(timedelta(hours=3))
    stamped = at(datetime(2026, 8, 7, 4, 2, 3, tzinfo=east))
    assert stamped == UtcTimestamp("2026-08-07T01:02:03Z")
    assert "+" not in stamped.value


def test_a_naive_source_is_refused() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        at(datetime(2026, 8, 7, 1, 2, 3))


def test_the_real_source_is_timezone_aware_utc() -> None:
    moment = utc_now()
    assert moment.tzinfo is not None
    assert moment.utcoffset() == timedelta(0)


def test_the_default_clock_reads_real_time_and_still_validates() -> None:
    stamped = SystemClock().now()
    assert isinstance(stamped, UtcTimestamp)
    assert stamped.value.startswith("20") and stamped.value.endswith("Z")
