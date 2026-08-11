"""The credential never enters the project, and provider text never leaves it.

`PRD05-FR-050`/`FR-051` make the authtoken operator-only. These tests use
obviously fake dangerous text - never a real credential - and assert that
nothing resembling one can reach an argv, a diagnostic or a peer.
"""

from pathlib import Path

import pytest
from r16_source import tokens_of

from mars777_police.infra import ngrok_ingress, ngrok_process, ngrok_settings
from mars777_police.infra.ngrok_settings import NgrokSettings
from mars777_police.infra.provider_sanitize import MAX_LENGTH, REDACTED, sanitize

DANGEROUS = [
    "authtoken=<not-a-real-value>",
    "AUTH_TOKEN: <none>",
    "api_key=<none>",
    "Authorization: Bearer <none>",
    "Cookie: session=<none>",
    "password=<none>",
    "client secret <none>",
]


@pytest.mark.parametrize("line", DANGEROUS)
def test_every_credential_shaped_diagnostic_is_discarded(line: str) -> None:
    assert sanitize(line) == REDACTED
    assert "<none>" not in sanitize(line)


def test_an_ordinary_diagnostic_survives_but_is_bounded() -> None:
    assert sanitize("  failed to start tunnel  ") == "failed to start tunnel"
    assert len(sanitize("x" * 5000)) == MAX_LENGTH


def test_no_provider_module_reads_the_operator_configuration() -> None:
    """A path may be passed to the agent; its contents are never opened here."""
    for module in (ngrok_settings, ngrok_process, ngrok_ingress):
        tokens = tokens_of(module)
        for forbidden in ("read_text", "read_bytes", "environ", "getenv", "authtoken"):
            assert forbidden not in tokens
    # `open` survives only as the port's own method name, never as a file read.
    assert "open" not in tokens_of(ngrok_settings)
    assert "open" not in tokens_of(ngrok_process)


def test_no_credential_can_reach_the_command_line() -> None:
    argv = NgrokSettings(Path("/opt/ngrok"), config_paths=(Path("/x.yml"),)).argv(1)
    assert "--authtoken" not in argv
    assert all("token" not in part.lower() for part in argv)


def test_no_home_directory_is_hard_coded_into_production() -> None:
    """Operator paths are injected; the project ships nobody's home directory."""
    for module in (ngrok_settings, ngrok_process, ngrok_ingress):
        source = Path(module.__file__ or "").read_text(encoding="utf-8")
        assert "awad_moha" not in source
        assert "/home/" not in source
