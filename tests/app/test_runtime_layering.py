"""Stage-4E-R16 layering guards: what the application runtime may reach.

`MODULE_BOUNDARIES.md` forbids `app` from importing `protocol` at all, so every
byte, digest and proof R16 needs arrives through an injected port. That is the
rule these guards make executable - and it is the reason the runtimes are
testable with plain fakes and no crypto at all.

The guards read **code**, never prose: a docstring that explains why a module
never opens a socket is not a socket.
"""

import inspect

import pytest
from r16_source import imports_of, tokens_of

from mars777_police.app import (
    config_lock_runtime,
    config_negotiation_runtime,
    ports,
    result_agreement_runtime,
    result_core_runtime,
    step0_runtime,
)

RUNTIMES = (
    step0_runtime,
    config_negotiation_runtime,
    config_lock_runtime,
    result_core_runtime,
    result_agreement_runtime,
)

NO_TRANSPORT = (
    "fastmcp",
    "socket",
    "httpx",
    "requests",
    "urllib",
    "aiohttp",
    "websocket",
    "ngrok",
    "cloudflared",
    "smtplib",
    "gmail",
    "oauth",
)

NO_IO = ("open", "pathlib", "environ", "getenv", "subprocess", "datetime", "sleep")

NO_CRYPTO = ("hashlib", "hmac", "sha256", "canonical_json_bytes", "secrets", "hexdigest")

IDS = [module.__name__.rsplit(".", 1)[-1] for module in RUNTIMES]


@pytest.mark.parametrize("module", RUNTIMES, ids=IDS)
def test_no_application_runtime_imports_the_protocol_package(module: object) -> None:
    for imported in imports_of(module):  # type: ignore[arg-type]
        assert "protocol." not in imported, imported


@pytest.mark.parametrize("module", RUNTIMES, ids=IDS)
def test_no_application_runtime_touches_transport(module: object) -> None:
    code = {token.lower() for token in tokens_of(module)}  # type: ignore[arg-type]
    assert code.isdisjoint(NO_TRANSPORT)


@pytest.mark.parametrize("module", RUNTIMES, ids=IDS)
def test_no_application_runtime_performs_io_or_reads_a_clock(module: object) -> None:
    assert tokens_of(module).isdisjoint(NO_IO)  # type: ignore[arg-type]


@pytest.mark.parametrize("module", RUNTIMES, ids=IDS)
def test_no_application_runtime_computes_a_digest_itself(module: object) -> None:
    """Bytes and hashing stay behind the ports, in the protocol adapters."""
    assert tokens_of(module).isdisjoint(NO_CRYPTO)  # type: ignore[arg-type]


def test_the_only_injected_non_determinism_is_the_timestamp_port() -> None:
    assert "TimestampPort" in tokens_of(result_agreement_runtime)
    for module in RUNTIMES:
        assert "random" not in tokens_of(module)


def test_no_runtime_method_is_async() -> None:
    for module in (*RUNTIMES, ports):
        for value in vars(module).values():
            if inspect.isclass(value):
                for member in vars(value).values():
                    assert not inspect.iscoroutinefunction(member)
            else:
                assert not inspect.iscoroutinefunction(value)


def test_every_runtime_module_stays_within_the_line_budget() -> None:
    for module in (*RUNTIMES, ports):
        assert len(inspect.getsource(module).splitlines()) <= 150
