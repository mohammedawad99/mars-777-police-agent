"""The one place every external **provider** call passes through.

Guideline §5.1 asks for a central gatekeeper owning rate limiting, queueing,
retries and monitoring for external API calls. This is it, and its scope is
stated as narrowly as it is implemented: **provider services**, not the peer.

**Peer gameplay is deliberately outside.** `receive_turn`, `submit_audit` and
`receive_control` keep their protocol-specific authorities - the locked session
deadline, commitment-keyed delivery dedupe, the narrow startup budget and the
network-failure policy. A generic resend there would re-send a turn the opponent
has already applied, which Appendix E rule 35 classifies as a protocol
violation, and a generic queue would break lockstep ordering. A structural test
holds that boundary; this docstring is not the guard.

**Every operation has a named policy**, read from the versioned configuration
file - there is no "execute anything with a retry count the caller chose".
"""

import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TypeVar

from ..shared.rate_limits import RateLimitConfig, RateLimitPolicy
from .gatekeeper_events import CallOutcome, GatekeeperCall
from .gatekeeper_queue import RateWindowQueue, WaitingRoomFullError
from .gatekeeper_retry import wait_before_retry, would_retry
from .gatekeeper_windows import RollingWindows

T = TypeVar("T")


class GatekeeperRejectedError(Exception):
    """Backpressure: the waiting room for this operation is full."""


class ConcurrencyExceededError(Exception):
    """This operation already has as many calls in flight as it may have."""


@dataclass(slots=True)
class Gatekeeper:
    """Rate, concurrency, queueing, retries and observation, in one place."""

    config: RateLimitConfig
    monotonic: Callable[[], float] = time.monotonic
    sleeper: Callable[[float], None] = time.sleep
    calls: list[GatekeeperCall] = field(default_factory=list)
    _rooms: dict[str, RateWindowQueue] = field(default_factory=dict)
    _windows: dict[str, RollingWindows] = field(default_factory=dict)
    _in_flight: dict[str, int] = field(default_factory=dict)

    def call(self, operation: str, run: Callable[[], T]) -> T:
        """Run *run* under the policy governing *operation*."""
        policy = self.config.policy_for(operation)
        started = self.monotonic()
        if self._in_flight.get(operation, 0) >= policy.concurrent_max:
            self._record(operation, CallOutcome.REFUSED, 0, False, False, started)
            raise ConcurrencyExceededError(
                f"{operation} already has {policy.concurrent_max} calls in flight"
            )
        queued = self._admit(operation, policy, started)
        self._in_flight[operation] = self._in_flight.get(operation, 0) + 1
        try:
            return self._attempt(operation, policy, run, queued, started)
        finally:
            self._in_flight[operation] -= 1

    def _admit(self, operation: str, policy: RateLimitPolicy, started: float) -> bool:
        """Wait in the bounded queue until this operation's windows allow a call."""
        room = self._room(operation, policy)
        windows = self._window(operation, policy)
        try:
            ticket = room.join()
        except WaitingRoomFullError as full:
            self._record(operation, CallOutcome.REJECTED, 0, True, True, started)
            raise GatekeeperRejectedError(str(full)) from full
        queued = False
        try:
            while True:
                wait = windows.wait_seconds()
                if wait <= 0 and room.turn_of(ticket):
                    return queued
                queued = True
                self.sleeper(max(wait, 0.0))
        finally:
            room.leave(ticket)

    def _attempt(
        self,
        operation: str,
        policy: RateLimitPolicy,
        run: Callable[[], T],
        queued: bool,
        started: float,
    ) -> T:
        windows = self._window(operation, policy)
        attempts = 0
        while True:
            attempts += 1
            windows.stamp()
            try:
                answer = run()
            except BaseException as failure:
                if attempts > policy.max_retries or not would_retry(policy, failure):
                    self._record(operation, CallOutcome.FAILED, attempts, queued, queued, started)
                    raise
                self.sleeper(wait_before_retry(policy, failure, attempts))
                continue
            self._record(operation, CallOutcome.SUCCEEDED, attempts, queued, queued, started)
            return answer

    def _room(self, operation: str, policy: RateLimitPolicy) -> RateWindowQueue:
        if operation not in self._rooms:
            self._rooms[operation] = RateWindowQueue(policy.queue_depth)
        return self._rooms[operation]

    def _window(self, operation: str, policy: RateLimitPolicy) -> RollingWindows:
        if operation not in self._windows:
            self._windows[operation] = RollingWindows(
                policy.requests_per_minute, policy.requests_per_hour, self.monotonic
            )
        return self._windows[operation]

    def _record(
        self,
        operation: str,
        outcome: CallOutcome,
        attempts: int,
        queued: bool,
        throttled: bool,
        started: float,
    ) -> None:
        self.calls.append(
            GatekeeperCall(
                operation=operation,
                outcome=outcome,
                attempts=attempts,
                queued=queued,
                throttled=throttled,
                elapsed_seconds=self.monotonic() - started,
            )
        )
