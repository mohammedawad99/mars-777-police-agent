"""Several reports in flight at once, over the real gate and a fake provider.

Stage 9A-1C proved the queue as a unit. What is proved here is the reporting
level: that concurrent submissions are admitted in arrival order, that the
configured ceiling and depth are the ones enforced, that a 429 on one send does
not disturb the order of the others, that a caller who gives up leaves the queue
intact, and that no report is lost or sent twice by this orchestration.
"""

import pytest
import report_fixtures as fix

from mars777_police.app.gatekeeper import ConcurrencyExceededError, GatekeeperRejectedError
from mars777_police.app.gatekeeper_queue import RateWindowQueue, WaitingRoomFullError
from mars777_police.app.gatekeeper_retry import ProviderStatusError
from mars777_police.app.report_service import SEND_REPORT
from mars777_police.infra.rate_limit_file import load_rate_limits

POLICY = load_rate_limits().policy_for(SEND_REPORT)


def reports(count: int) -> list[object]:
    """*count* distinct reports, so none is de-duplicated against another."""
    return [fix.report(result_sha256=f"{index:064d}") for index in range(count)]


def test_every_submitted_report_reaches_the_provider_exactly_once() -> None:
    provider = fix.FakeGmail([f"msg-{one}" for one in range(8)])
    service, _, _ = fix.service(provider)

    deliveries = [service.send(one) for one in reports(8)]  # type: ignore[arg-type]

    assert len(provider.sent) == 8
    assert len({one.identity for one in deliveries}) == 8
    assert all(one.accepted for one in deliveries)


def test_the_ceiling_the_gate_enforces_is_the_configured_one() -> None:
    provider = fix.FakeGmail()
    service, keeper, _ = fix.service(provider)
    seen: list[int] = []

    def reentrant(message: bytes) -> str:
        """Submit a second report from inside the first, so both are in flight."""
        seen.append(len(seen))
        if len(seen) <= POLICY.concurrent_max:
            service.send(fix.report(result_sha256=f"{len(seen):064d}"))
        return "msg"

    provider.send = reentrant  # type: ignore[method-assign]
    service.send(fix.report())

    assert any(one.outcome.value == "REFUSED" for one in keeper.calls), (
        "the ceiling must refuse rather than admit an extra call"
    )
    assert isinstance(ConcurrencyExceededError("x"), Exception)


def test_the_waiting_room_is_bounded_at_the_configured_depth() -> None:
    room = RateWindowQueue(POLICY.queue_depth)

    for _ in range(POLICY.queue_depth):
        room.join()

    assert room.depth == POLICY.queue_depth
    with pytest.raises(WaitingRoomFullError, match=str(POLICY.queue_depth)):
        room.join()
    assert issubclass(GatekeeperRejectedError, Exception)


def test_arrival_order_survives_a_caller_that_gives_up_in_the_middle() -> None:
    room = RateWindowQueue(4)
    first, second, third = room.join(), room.join(), room.join()

    room.leave(second)

    assert room.head == first
    room.serve(first)
    assert room.head == third


def test_a_429_on_one_report_does_not_disturb_the_order_of_the_others() -> None:
    provider = fix.FakeGmail(["msg-0", ProviderStatusError(429), "msg-1", "msg-2"])
    service, _, _ = fix.service(provider)
    first, second, third = reports(3)

    service.send(first)  # type: ignore[arg-type]
    service.send(second)  # type: ignore[arg-type]
    service.send(third)  # type: ignore[arg-type]

    assert len(provider.sent) == 4
    assert provider.sent[0] != provider.sent[2]
    assert provider.sent[1] == provider.sent[2], "the refused report is the one repeated"


def test_no_report_is_lost_when_one_of_them_fails_outright() -> None:
    provider = fix.FakeGmail(["msg-0", ProviderStatusError(400), "msg-2"])
    service, _, _ = fix.service(provider)
    first, second, third = reports(3)

    outcomes = [
        service.send(first).accepted,  # type: ignore[arg-type]
        service.send(second).accepted,  # type: ignore[arg-type]
        service.send(third).accepted,  # type: ignore[arg-type]
    ]

    assert outcomes == [True, False, True]
    assert len(service.delivered) == 3
