"""Agent lifecycle: bounded start, log-derived API address, guaranteed stop.

The one thing that must never happen is an orphan: a tunnel still advertising a
public URL after the process that owned it is gone. Every failure path here is
asserted to have terminated the child.
"""

import subprocess
from pathlib import Path

import pytest
from fake_agent import NOISE_LINE, SESSION_LINE, WEB_LINE, FakeAgent, StubbornTimeoutError
from net_fakes import FakeClock
from r16_source import tokens_of

from mars777_police.app.public_ingress import PublicIngressError
from mars777_police.infra.ngrok_process import NgrokProcess, spawn
from mars777_police.infra.ngrok_settings import NgrokSettings

EXE = Path("/opt/ngrok")


def settings(**kwargs: object) -> NgrokSettings:
    return NgrokSettings(EXE, **kwargs)  # type: ignore[arg-type]


def process(agent: FakeAgent, clock: FakeClock | None = None) -> NgrokProcess:
    clock = clock or FakeClock()
    return NgrokProcess(settings(), spawner=lambda argv: agent, monotonic=clock.monotonic)


def test_the_argv_carries_no_credential_and_requests_json_logging() -> None:
    argv = settings(config_paths=(Path("/x/ngrok.yml"),)).argv(8801)
    assert argv[:3] == ("/opt/ngrok", "http", "8801")
    assert "--config" in argv and "/x/ngrok.yml" in argv
    assert argv[-4:] == ("--log", "stdout", "--log-format", "json")
    joined = " ".join(argv).lower()
    for forbidden in ("authtoken", "token", "api_key", "secret"):
        assert forbidden not in joined


def test_settings_refuse_a_non_path_executable_and_impossible_bounds() -> None:
    with pytest.raises(ValueError, match="executable"):
        NgrokSettings("/opt/ngrok")  # type: ignore[arg-type]
    for bad in ({"startup_seconds": 0.0}, {"discovery_seconds": -1.0}, {"poll_seconds": 1}):
        with pytest.raises(ValueError, match="wait bound"):
            settings(**bad)  # type: ignore[arg-type]


def test_the_api_base_is_read_from_the_structured_log_not_a_banner() -> None:
    agent = FakeAgent(lines=[NOISE_LINE, "[]", SESSION_LINE, WEB_LINE])
    assert process(agent).start(8801) == "http://127.0.0.1:4040"


def test_a_provider_refusal_stops_the_child_and_is_sanitized() -> None:
    agent = FakeAgent(lines=['{"lvl":"eror","err":"authtoken is invalid"}'])
    with pytest.raises(PublicIngressError) as raised:
        process(agent).start(8801)
    assert "authtoken" not in str(raised.value)
    assert "<redacted" in str(raised.value)
    assert agent.terminated == 1


def test_a_silent_agent_times_out_and_is_stopped() -> None:
    agent = FakeAgent(lines=[])
    with pytest.raises(PublicIngressError, match="in time"):
        process(agent).start(8801)
    assert agent.terminated == 1


def test_an_agent_that_never_reports_the_web_service_times_out() -> None:
    clock = FakeClock()
    agent = FakeAgent(lines=[SESSION_LINE] * 3)

    def creeping() -> float:
        clock.now += 20.0
        return clock.now

    runner = NgrokProcess(settings(), spawner=lambda argv: agent, monotonic=creeping)
    with pytest.raises(PublicIngressError, match="in time"):
        runner.start(8801)
    assert agent.terminated == 1


def test_stop_is_idempotent_and_clears_the_recorded_api_base() -> None:
    agent = FakeAgent()
    runner = process(agent)
    runner.start(8801)
    assert runner.is_running and runner.api_base is not None
    runner.stop()
    runner.stop()
    assert agent.terminated == 1 and agent.killed == 0
    assert runner.api_base is None and not runner.is_running


def test_a_stubborn_agent_is_escalated_to_a_kill(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(subprocess, "TimeoutExpired", StubbornTimeoutError)
    agent = FakeAgent(stubborn=True)
    runner = process(agent)
    runner.start(8801)
    runner.stop()
    assert agent.terminated == 1 and agent.killed == 1


def test_the_real_spawner_uses_an_argument_list_and_never_a_shell() -> None:
    """Read the module's **code**, not its prose - the R16 lesson, applied again."""
    from mars777_police.infra import ngrok_process

    tokens = tokens_of(ngrok_process)
    assert "shell" not in tokens
    assert "argv" in tokens
    assert spawn.__module__.endswith("infra.ngrok_process")
