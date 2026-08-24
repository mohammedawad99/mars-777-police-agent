"""A valid agreement may arrive before this side is ready, and that is not a fault.

Both peers finish sub-game six at different moments and the proposer sends the
instant its own settlement completes, so a correct, authenticated request can
reach a receiver that is still publishing its sixth contribution entry. A live
four-process rehearsal produced exactly that, and refusing it would have lost an
agreement neither side got wrong.

The rule these pin: wait **boundedly** for our own half, then process the same
request; on timeout refuse explicitly and mutate nothing. Malformed and
unauthenticated requests are refused before any wait, because a sender that got
it wrong must not be made to hold a connection open.
"""

import asyncio
import time

import pytest
from counted_result_builders import GROUP_B

from mars777_police.app.kit_result_agreement import GroupResultAgreement
from mars777_police.app.protocol_errors import StaleMessageError


class Ready:
    """An exchange that answers with a fixed digest and records its calls."""

    def __init__(self) -> None:
        self.calls = 0
        self.peer_request_handled = False
        self.local_digest: object | None = None

    def accept_peer_request(self, agreement: object, sender_id: str) -> object:
        self.calls += 1
        self.peer_request_handled = True
        self.local_digest = _Digest()
        return self.local_digest


class _Digest:
    value = "e" * 64


def late(after: int) -> GroupResultAgreement:
    """An authority whose own half assembles only after *after* readiness checks."""
    state = {"checks": 0, "exchange": Ready()}

    def build() -> object | None:
        state["checks"] += 1  # type: ignore[operator]
        return state["exchange"] if state["checks"] > after else None  # type: ignore[operator]

    holder = GroupResultAgreement(build=build)  # type: ignore[arg-type]
    holder.poll = 0.01
    return holder


def test_an_early_valid_request_succeeds_once_our_half_assembles() -> None:
    """The same request is processed - not refused, and not answered twice."""
    holder = late(after=3)

    digest = asyncio.run(holder.accept(object(), GROUP_B, 5.0))  # type: ignore[arg-type]

    assert digest.value == "e" * 64  # type: ignore[union-attr]
    assert holder.exchange.calls == 1  # type: ignore[union-attr]


def test_an_early_request_mutates_nothing_while_it_waits() -> None:
    """Nothing is touched until our own half exists; a timeout leaves it untouched."""
    holder = late(after=10_000)

    with pytest.raises(StaleMessageError, match="not ready"):
        asyncio.run(holder.accept(object(), GROUP_B, 0.05))  # type: ignore[arg-type]

    assert holder.is_agreed is False
    assert holder.exchange is None


def test_the_wait_is_bounded_and_refuses_rather_than_hanging() -> None:
    """Bounded by the window the pairing already agreed, never open-ended."""
    holder = late(after=10_000)
    started = time.monotonic()

    with pytest.raises(StaleMessageError, match="may be retried"):
        asyncio.run(holder.accept(object(), GROUP_B, 0.2))  # type: ignore[arg-type]

    assert time.monotonic() - started < 3.0


def test_a_repeat_of_an_answered_request_is_idempotent() -> None:
    """A retried transport failure gets the same digest, not a second pass."""
    holder = late(after=0)

    first = asyncio.run(holder.accept(object(), GROUP_B, 1.0))  # type: ignore[arg-type]
    second = asyncio.run(holder.accept(object(), GROUP_B, 1.0))  # type: ignore[arg-type]

    assert first is second
    assert holder.exchange.calls == 1  # type: ignore[union-attr]


def test_a_never_ready_group_never_becomes_agreed() -> None:
    """Timing out leaves the agreement incomplete, so reporting stays ineligible."""
    holder = late(after=10_000)

    with pytest.raises(StaleMessageError):
        asyncio.run(holder.accept(object(), GROUP_B, 0.05))

    assert holder.is_agreed is False
