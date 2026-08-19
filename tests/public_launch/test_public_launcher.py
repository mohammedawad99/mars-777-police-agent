"""Putting the group gateway behind one public route, and taking it down again.

Two things already existed and neither had a production caller: the group
gateway, and the ngrok-backed `PublicIngressPort`. This is the seam between
them, and it is deliberately thin - the ingress decides what a public endpoint
is, the gateway decides which backend a message belongs to, and this owns only
the order those two happen in and the guarantee that both are released.

**One endpoint is advertised, and it is the group's.** The role backends stay on
private local ports that never leave this process: not in the operator banner,
not in a pairing document, not in an artifact.
"""

import asyncio

import pytest
from network_fixtures import launcher, service, tracking_ingress

from mars777_police.app.public_endpoint_values import OwnPublicPeerEndpoint
from mars777_police.app.public_ingress import PublicIngressError
from mars777_police.app.run_class import RunClass


def test_the_gateway_port_is_what_gets_exposed() -> None:
    ingress = tracking_ingress()
    held = launcher(service(ingress))

    endpoint = asyncio.run(_opened(held))

    assert ingress.opened is not None
    assert ingress.opened.port == held.public_port
    assert isinstance(endpoint, OwnPublicPeerEndpoint)


def test_the_discovered_endpoint_is_propagated_and_never_invented() -> None:
    ingress = tracking_ingress()
    held = launcher(service(ingress))

    advertised = while_live(held, lambda: held.status().public_endpoint)

    assert advertised == ingress.endpoint.url


def test_exactly_one_public_endpoint_is_advertised() -> None:
    held = launcher(service(tracking_ingress()))

    banner = while_live(held, lambda: "\n".join(held.status().operator_lines()))

    assert banner.count("https://") == 1


def test_no_private_backend_endpoint_reaches_the_operator_surface() -> None:
    held = launcher(service(tracking_ingress()))

    banner = while_live(held, lambda: "\n".join(held.status().operator_lines()))

    assert "127.0.0.1" not in banner
    assert str(held.admin_port) not in banner
    for private in held.backend_endpoints:
        assert private not in banner


def test_a_private_endpoint_is_refused_and_the_route_is_closed() -> None:
    """The existing policy decides; this only has to not swallow the refusal."""
    ingress = tracking_ingress(url="https://127.0.0.1/mcp")
    held = launcher(service(ingress))

    with pytest.raises(PublicIngressError):
        asyncio.run(_opened(held))

    assert ingress.closed is True


def test_a_failure_after_the_route_opened_still_releases_everything() -> None:
    ingress = tracking_ingress()
    held = launcher(service(ingress), admin_port=-1)

    with pytest.raises(OverflowError):
        asyncio.run(_opened(held))

    assert ingress.closed is True
    assert held.is_live is False


def test_closing_releases_the_route_and_both_servers() -> None:
    ingress = tracking_ingress()
    held = launcher(service(ingress))

    async def run() -> None:
        await held.open()
        await held.close()

    asyncio.run(run())

    assert ingress.closed is True
    assert held.is_live is False


def test_closing_twice_is_safe() -> None:
    held = launcher(service(tracking_ingress()))

    async def run() -> None:
        await held.open()
        await held.close()
        await held.close()

    asyncio.run(run())

    assert held.is_live is False


def test_no_endpoint_survives_a_closed_launcher() -> None:
    """A new run discovers again; nothing stale is reused."""
    held = launcher(service(tracking_ingress()))

    async def run() -> None:
        await held.open()
        await held.close()

    asyncio.run(run())

    assert held.status().public_endpoint is None


def test_a_public_route_does_not_make_the_run_counted() -> None:
    held = launcher(service(tracking_ingress()))

    status = while_live(held, held.status)

    assert status.run_class is RunClass.KIT_FRIENDLY_ONLY
    assert status.counted_eligible is False


async def _opened(held: object) -> object:
    """Open, and always leave the launcher closed for the next test."""
    try:
        return await held.open()  # type: ignore[attr-defined]
    finally:
        await held.close()  # type: ignore[attr-defined]


def while_live(held: object, read):
    """Open, read something from the launcher while the route is up, then close."""

    async def run():
        await held.open()  # type: ignore[attr-defined]
        try:
            return read()
        finally:
            await held.close()  # type: ignore[attr-defined]

    return asyncio.run(run())
