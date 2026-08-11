"""The BOOT input boundary refuses everything it should, and leaks nothing.

The secret assertions are the ones that matter most: a settings object is the
most likely thing to end up in a log line or a debugger frame, so `repr` and any
refusal message are checked to be free of key material rather than trusted to be.

Fixture values are obviously non-credential placeholders - a realistic-looking
key here would trip a secret scan and teach the wrong habit.
"""

import pytest

from mars777_police.app.auth_values import KeyId
from mars777_police.app.public_endpoint_values import LocalPeerEndpoint, OpponentPublicPeerEndpoint
from mars777_police.app.sealed_record_values import ActorRole
from mars777_police.infra.settings import (
    AUTH_SECRET,
    BIND_HOST,
    BIND_PORT,
    KEY_IDENTIFIER,
    OPPONENT_ENDPOINT,
    ROLE,
    AuthSecret,
    RuntimeSettings,
    SettingsError,
    load_runtime_settings,
)

SECRET_PLACEHOLDER = "not-a-real-key"
OPPONENT = "https://opponent.example/mcp"


NAMES = {
    "ROLE": ROLE,
    "BIND_HOST": BIND_HOST,
    "BIND_PORT": BIND_PORT,
    "KEY_IDENTIFIER": KEY_IDENTIFIER,
    "AUTH_SECRET": AUTH_SECRET,
    "OPPONENT_ENDPOINT": OPPONENT_ENDPOINT,
}


def env(**overrides: str | None) -> dict[str, str]:
    base = {
        ROLE: ActorRole.POLICE.value,
        BIND_HOST: "127.0.0.1",
        BIND_PORT: "8801",
        KEY_IDENTIFIER: "mars777-k1",
        AUTH_SECRET: SECRET_PLACEHOLDER,
    }
    for name, value in overrides.items():
        key = NAMES[name]
        if value is None:
            base.pop(key, None)
        else:
            base[key] = value
    return base


def load(role: ActorRole = ActorRole.POLICE, **overrides: str | None) -> RuntimeSettings:
    return load_runtime_settings(env(**overrides), expected_role=role)


def test_a_minimal_valid_environment_loads_typed_values() -> None:
    settings = load()
    assert settings.role is ActorRole.POLICE
    assert settings.local == LocalPeerEndpoint("127.0.0.1", 8801)
    assert settings.key_id == KeyId("mars777-k1")
    assert settings.opponent is None
    assert settings.secret.reveal() == SECRET_PLACEHOLDER.encode()


def test_an_opponent_endpoint_is_adopted_when_supplied() -> None:
    settings = load(OPPONENT_ENDPOINT=OPPONENT)
    assert settings.opponent == OpponentPublicPeerEndpoint(OPPONENT)


@pytest.mark.parametrize("name", ["ROLE", "BIND_HOST", "BIND_PORT", "KEY_IDENTIFIER"])
def test_every_required_non_secret_refuses_when_absent_or_blank(name: str) -> None:
    for value in (None, "   "):
        with pytest.raises(SettingsError, match=NAMES[name]):
            load(**{name: value})


def test_a_missing_secret_refuses_the_process() -> None:
    with pytest.raises(SettingsError, match=AUTH_SECRET):
        load(AUTH_SECRET=None)


def test_an_empty_secret_refuses_the_process() -> None:
    with pytest.raises(SettingsError, match=AUTH_SECRET):
        load(AUTH_SECRET="   ")
    with pytest.raises(SettingsError, match=AUTH_SECRET):
        AuthSecret(b"")


@pytest.mark.parametrize("port", ["0", "70000", "eight", "88.1", "-1"])
def test_a_malformed_bind_port_refuses(port: str) -> None:
    with pytest.raises(SettingsError):
        load(BIND_PORT=port)


def test_an_unknown_role_refuses() -> None:
    with pytest.raises(SettingsError, match=ROLE):
        load(ROLE="referee")


def test_a_role_contradicting_this_repository_refuses() -> None:
    """The Police package can never boot as a Thief, whatever the operator says."""
    with pytest.raises(SettingsError, match="contradicts"):
        load_runtime_settings(env(ROLE=ActorRole.THIEF.value), expected_role=ActorRole.POLICE)


def test_unrelated_environment_variables_are_ignored_and_never_copied() -> None:
    noisy = env()
    noisy["PATH"] = "/usr/bin"
    noisy["MARS777_SOMETHING_ELSE"] = "ignored"
    settings = load_runtime_settings(noisy, expected_role=ActorRole.POLICE)
    rendered = repr(settings)
    assert "PATH" not in rendered and "ignored" not in rendered


def test_the_result_is_immutable() -> None:
    settings = load()
    with pytest.raises(Exception):  # noqa: B017
        settings.role = ActorRole.THIEF  # type: ignore[misc]


def test_the_secret_never_appears_in_a_repr() -> None:
    settings = load()
    for rendered in (repr(settings), str(settings), repr(settings.secret), str(settings.secret)):
        assert SECRET_PLACEHOLDER not in rendered
    assert "withheld" in repr(settings.secret)


def test_the_secret_never_appears_in_a_refusal_message() -> None:
    """A malformed environment must not reconstruct the key from a stack trace."""
    with pytest.raises(SettingsError) as raised:
        load(BIND_PORT="not-a-port")
    assert SECRET_PLACEHOLDER not in str(raised.value)
    with pytest.raises(SettingsError) as blank:
        load(AUTH_SECRET="")
    assert blank.value.args[0] == f"{AUTH_SECRET} is required and must not be empty"
