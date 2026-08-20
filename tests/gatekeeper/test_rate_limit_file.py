"""Reading the local rate-limit configuration, and what it refuses to read.

Guideline §5.2: the limits come from a file, never from code. So the file is the
authority, and every way it can be wrong has to end in a typed refusal rather
than a default quietly taking its place - a gate running limits nobody wrote is
worse than no gate.
"""

import json
from pathlib import Path

import pytest

from mars777_police.infra.rate_limit_file import RATE_LIMITS_PATH, load_rate_limits
from mars777_police.shared.rate_limits import RateLimitConfigError


def body(**changes: object) -> dict[str, object]:
    services: dict[str, object] = {
        "default": {
            "requests_per_minute": 30,
            "requests_per_hour": 500,
            "concurrent_max": 2,
            "queue_depth": 100,
            "max_retries": 3,
            "retry_after_seconds": 5,
            "max_backoff_seconds": 60,
            "retryable_statuses": [429],
        }
    }
    limits: dict[str, object] = {"version": "1.00", "services": services}
    limits.update(changes)
    return {"rate_limits": limits}


def written(root: Path, document: object) -> Path:
    path = root / "rate_limits.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    return path


def test_the_shipped_configuration_loads(tmp_path: Path) -> None:
    """The file this repository actually commits is the one the gate runs."""
    config = load_rate_limits()

    assert config.version == "1.00"
    assert config.policy_for("ngrok.discover_tunnels").concurrent_max == 1


def test_the_shipped_configuration_is_where_the_guideline_puts_it() -> None:
    assert RATE_LIMITS_PATH.name == "rate_limits.json"
    assert RATE_LIMITS_PATH.parent.name == "config"
    assert RATE_LIMITS_PATH.is_file()


def test_a_named_service_overrides_the_default(tmp_path: Path) -> None:
    document = body()
    services = document["rate_limits"]["services"]  # type: ignore[index]
    services["reporting.send_report"] = {**services["default"], "requests_per_minute": 6}

    config = load_rate_limits(written(tmp_path, document))

    assert config.policy_for("reporting.send_report").requests_per_minute == 6
    assert config.policy_for("anything.else").requests_per_minute == 30


def test_a_missing_file_is_refused_rather_than_defaulted(tmp_path: Path) -> None:
    with pytest.raises(RateLimitConfigError, match="no-such"):
        load_rate_limits(tmp_path / "no-such.json")


def test_bytes_that_are_not_json_are_refused(tmp_path: Path) -> None:
    path = tmp_path / "rate_limits.json"
    path.write_text("{not json", encoding="utf-8")

    with pytest.raises(RateLimitConfigError, match="not valid JSON"):
        load_rate_limits(path)


def test_a_document_without_the_rate_limits_object_is_refused(tmp_path: Path) -> None:
    with pytest.raises(RateLimitConfigError, match="rate_limits"):
        load_rate_limits(written(tmp_path, {"limits": {}}))


def test_a_missing_version_is_refused(tmp_path: Path) -> None:
    document = body()
    del document["rate_limits"]["version"]  # type: ignore[union-attr]

    with pytest.raises(RateLimitConfigError, match="version"):
        load_rate_limits(written(tmp_path, document))


def test_a_numeric_version_is_refused_because_it_cannot_round_trip(tmp_path: Path) -> None:
    """`1.00` as a JSON number reads back as `1.0` - two truths, one value."""
    with pytest.raises(RateLimitConfigError, match="version"):
        load_rate_limits(written(tmp_path, body(version=1.00)))


def test_an_unsupported_version_is_refused(tmp_path: Path) -> None:
    with pytest.raises(RateLimitConfigError, match=r"1\.99"):
        load_rate_limits(written(tmp_path, body(version="1.99")))


def test_services_without_a_default_are_refused(tmp_path: Path) -> None:
    with pytest.raises(RateLimitConfigError, match="default"):
        load_rate_limits(written(tmp_path, body(services={})))


def test_an_unknown_policy_key_is_refused_rather_than_ignored(tmp_path: Path) -> None:
    document = body()
    document["rate_limits"]["services"]["default"]["burst"] = 5  # type: ignore[index]

    with pytest.raises(RateLimitConfigError, match="burst"):
        load_rate_limits(written(tmp_path, document))


def test_a_missing_policy_key_is_refused(tmp_path: Path) -> None:
    document = body()
    del document["rate_limits"]["services"]["default"]["queue_depth"]  # type: ignore[index]

    with pytest.raises(RateLimitConfigError, match="queue_depth"):
        load_rate_limits(written(tmp_path, document))


def test_a_malformed_value_is_refused_by_the_value_object(tmp_path: Path) -> None:
    document = body()
    document["rate_limits"]["services"]["default"]["concurrent_max"] = -2  # type: ignore[index]

    with pytest.raises(RateLimitConfigError, match="concurrent_max"):
        load_rate_limits(written(tmp_path, document))


CREDENTIAL_NAMES = (
    "authtoken",
    "auth_token",
    "access_token",
    "refresh_token",
    "client_secret",
    "api_key",
    "private_key",
    "password",
    "bearer",
    "credential",
)
"""What a credential is actually called. Checked instead of the bare word "token",
which is also the first half of `token_bucket` - the algorithm Appendix E rule 28
requires by name. A guard that failed on its own requirement would teach the next
author to rename the requirement."""

ALLOWED_TEXT = frozenset({"1.00", "rolling_window", "token_bucket"})
"""Every string a limits file may legitimately hold. Anything else is refused
whether or not it looks like a secret, which is stronger than a word list."""


def test_the_file_names_no_credential() -> None:
    text = RATE_LIMITS_PATH.read_text(encoding="utf-8").lower()

    for forbidden in CREDENTIAL_NAMES:
        assert forbidden not in text


def test_every_value_in_the_file_is_a_number_or_a_known_word() -> None:
    """A secret cannot hide in a file whose only strings are enumerated."""
    document = json.loads(RATE_LIMITS_PATH.read_text(encoding="utf-8"))
    strings: list[str] = []
    numbers: list[object] = []
    _collect(document, strings, numbers)

    assert set(strings) <= ALLOWED_TEXT, sorted(set(strings) - ALLOWED_TEXT)
    assert all(type(one) is int for one in numbers)


def _collect(value: object, strings: list[str], numbers: list[object]) -> None:
    """Walk the document, gathering every leaf so none escapes the check."""
    if isinstance(value, dict):
        for item in value.values():
            _collect(item, strings, numbers)
    elif isinstance(value, list):
        for item in value:
            _collect(item, strings, numbers)
    elif isinstance(value, str):
        strings.append(value)
    else:
        numbers.append(value)


def test_a_service_that_is_not_an_object_is_refused(tmp_path: Path) -> None:
    document = body()
    document["rate_limits"]["services"]["broken"] = 7  # type: ignore[index]

    with pytest.raises(RateLimitConfigError, match="broken"):
        load_rate_limits(written(tmp_path, document))


def test_retryable_statuses_that_are_not_a_list_are_refused(tmp_path: Path) -> None:
    document = body()
    document["rate_limits"]["services"]["default"]["retryable_statuses"] = 429  # type: ignore[index]

    with pytest.raises(RateLimitConfigError, match="retryable_statuses"):
        load_rate_limits(written(tmp_path, document))
