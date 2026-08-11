"""Publicity is decided once, and refuses everything `FR-004`/`FR-014` refuse.

The conjunctive rule over resolved addresses is the one worth stating: a host
answering with one global and one loopback address is refused, because the peer
resolving it might reach the loopback one.
"""

import pytest
from net_fakes import PUBLIC_HOST, PUBLIC_URL, FakeResolver

from mars777_police.app.public_endpoint_policy import SystemHostResolver, is_public_endpoint
from mars777_police.app.public_endpoint_values import OwnPublicPeerEndpoint


def ok(url: str, resolver: FakeResolver | None = None) -> bool:
    return is_public_endpoint(OwnPublicPeerEndpoint(url), resolver or FakeResolver())


def test_a_genuinely_public_https_mcp_endpoint_is_accepted() -> None:
    assert ok(PUBLIC_URL)


@pytest.mark.parametrize(
    "url",
    [
        "http://host.example/mcp",
        "ftp://host.example/mcp",
        "https://user:pw@host.example/mcp",
        "https://host.example/mcp?token=x",
        "https://host.example/mcp#frag",
        "https://host.example/",
        "https://host.example/other",
        "https://host.example",
        "https://localhost/mcp",
        "https://127.0.0.1/mcp",
    ],
)
def test_every_forbidden_endpoint_form_is_refused(url: str) -> None:
    assert not ok(url)


def test_an_endpoint_resolving_to_nothing_is_refused() -> None:
    assert not ok(PUBLIC_URL, FakeResolver(default=()))


@pytest.mark.parametrize(
    "addresses",
    [
        ("127.0.0.1",),
        ("::1",),
        ("10.0.0.4",),
        ("192.168.1.9",),
        ("169.254.3.3",),
        ("3.125.102.39", "127.0.0.1"),
        ("not-an-address",),
    ],
)
def test_a_non_globally_routable_resolution_is_refused(addresses: tuple[str, ...]) -> None:
    assert not ok(PUBLIC_URL, FakeResolver(answers={PUBLIC_HOST: addresses}))


def test_a_host_with_only_global_addresses_is_accepted() -> None:
    globals_only = FakeResolver(answers={PUBLIC_HOST: ("3.125.102.39", "2a05:d014:21b::1")})
    assert ok(PUBLIC_URL, globals_only)


def test_the_system_resolver_answers_and_fails_closed() -> None:
    """The one place this layer touches the network, exercised both ways."""
    resolver = SystemHostResolver()
    assert resolver.resolve("localhost")
    assert resolver.resolve("invalid.invalid.mars777-does-not-exist.") == ()
