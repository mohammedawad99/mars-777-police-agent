"""Deadlines and liveness come from the locked config, not from a constant.

Two clocks that must not be confused: the **per-call response timeout** bounds
one request, the **watchdog** bounds peer progress. Neither is tested by waiting
- the clock is injected, so the threshold is proved in microseconds.
"""

from dataclasses import replace

import pytest
from r16_builders import config

from mars777_police.app.peer_supervision import (
    WATCHDOG_TIMEOUT,
    TimeoutPolicy,
    Watchdog,
    WatchdogTimeoutError,
)
from mars777_police.app.protocol_errors import LocalDefectError, PeerProtocolError
from mars777_police.domain.config_league_sections import NetworkAndLeagueTerms
from mars777_police.transport.client import PeerClient

WINDOW = 12.5
ENDPOINT = "http://127.0.0.1:9/mcp"


def tuned(response: int = 45, watchdog: int = 90):
    """A locked config whose timeouts are deliberately not the baselines."""
    return replace(
        config(),
        network_and_league=NetworkAndLeagueTerms(response, watchdog, 6, 10, 2, 10, 200000),
    )


def test_the_post_lock_timeout_is_the_negotiated_value() -> None:
    policy = TimeoutPolicy(WINDOW)
    assert policy.for_config(tuned(45)) == 45.0
    assert policy.for_config(tuned(17)) == 17.0


def test_the_client_carries_the_negotiated_timeout_not_a_baseline() -> None:
    """The whole point: 30 is a baseline, and this config never says 30."""
    client = PeerClient.for_locked_config(ENDPOINT, tuned(45), TimeoutPolicy(WINDOW))
    assert client.timeout == 45.0
    assert client.timeout != 30.0


def test_a_differently_negotiated_timeout_reaches_the_client_unchanged() -> None:
    for agreed in (17, 45, 120):
        client = PeerClient.for_locked_config(ENDPOINT, tuned(agreed), TimeoutPolicy(WINDOW))
        assert client.timeout == float(agreed)


def test_pre_lock_calls_use_the_injected_negotiation_window() -> None:
    """No number is named here; the window is the state's, injected."""
    client = PeerClient.for_bootstrap(ENDPOINT, TimeoutPolicy(WINDOW))
    assert client.timeout == WINDOW


def test_no_transport_or_supervision_module_hard_codes_thirty() -> None:
    """Read the code, not the prose that explains the code.

    Both modules discuss the Appendix-F baseline of 30 in their docstrings -
    exactly the text a substring grep mistakes for a defect. Stripping literals
    and comments leaves only the numbers the code actually uses.
    """
    import inspect
    import io
    import tokenize

    from mars777_police.app import peer_supervision
    from mars777_police.transport import client as client_module

    for module in (peer_supervision, client_module):
        numbers = {
            token.string
            for token in tokenize.generate_tokens(io.StringIO(inspect.getsource(module)).readline)
            if token.type == tokenize.NUMBER
        }
        assert "30" not in numbers
        assert numbers <= {"0", "1"}


def test_a_nonsensical_negotiation_window_is_a_local_defect() -> None:
    for bad in (0.0, -1.0):
        with pytest.raises(LocalDefectError):
            TimeoutPolicy(bad)


def test_the_watchdog_threshold_comes_from_the_locked_config() -> None:
    watchdog = Watchdog.for_config(tuned(45, 90), now=lambda: 0.0)
    assert watchdog.limit_seconds == 90.0


def test_the_watchdog_expires_only_past_its_threshold() -> None:
    """Injected clock: the threshold is proved without waiting for it."""
    clock = {"t": 0.0}
    watchdog = Watchdog.for_config(tuned(45, 60), now=lambda: clock["t"])
    clock["t"] = 60.0
    watchdog.check(last_progress=0.0)
    assert not watchdog.is_expired(0.0)
    clock["t"] = 60.5
    assert watchdog.is_expired(0.0)
    with pytest.raises(WatchdogTimeoutError) as raised:
        watchdog.check(last_progress=0.0)
    assert raised.value.error_id == WATCHDOG_TIMEOUT == "E-TIMEOUT-WATCHDOG"


def test_recorded_peer_progress_moves_the_deadline_with_it() -> None:
    """The frozen rule only: the gap is measured from the last progress."""
    clock = {"t": 0.0}
    watchdog = Watchdog.for_config(tuned(45, 60), now=lambda: clock["t"])
    clock["t"] = 100.0
    assert watchdog.is_expired(0.0)
    assert not watchdog.is_expired(50.0)


def test_the_watchdog_decides_no_sanction_and_accuses_no_peer() -> None:
    """Expiry is a local signal; escalation belongs to the game layer."""
    assert not issubclass(WatchdogTimeoutError, PeerProtocolError)
    import inspect

    from mars777_police.app import peer_supervision

    code = inspect.getsource(peer_supervision)
    for forbidden in ("technical_loss", "TECHNICAL_LOSS", "score", "sanction ="):
        assert forbidden not in code


def test_the_watchdog_identity_never_enters_the_peer_error_mapping() -> None:
    """It crosses no wire, so it is not a transport-known identity."""
    from mars777_police.transport.wire_errors import _BY_IDENTITY

    assert WATCHDOG_TIMEOUT not in _BY_IDENTITY
