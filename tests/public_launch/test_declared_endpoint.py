"""The declaration must name the ingress this run actually opened.

The opponent found this in a rehearsal: our launch document carried a
placeholder `mcp_endpoint`, and the rehearsal transport still worked because the
peer URL was configured separately. Nothing failed, and nothing would have -
until a counted Step-0 authenticated bytes naming an address no opponent could
reach, which is the mismatch `FR-015b` exists to prevent.

The counted discovery path already refuses a loopback URL. What it could not see
is a declaration written by hand into a launch document, because those bytes
never pass through discovery. These tests pin the comparison that closes it.
"""

import asyncio

import pytest
from network_fixtures import launcher, service, tracking_ingress

from mars777_police.app.protocol_errors import LocalDefectError
from mars777_police.app.public_endpoint_policy import SystemHostResolver
from mars777_police.app.public_endpoint_values import OwnPublicPeerEndpoint

PUBLIC = "https://real-ingress.example.com/mcp"
PLACEHOLDER = "http://127.0.0.1:1/mcp"


def opened(declared: str | None, url: str = PUBLIC):
    ingress = tracking_ingress(url)
    return launcher(service(ingress), declared=declared), ingress


def test_a_declaration_naming_this_run_ingress_is_accepted() -> None:
    live, _ = opened(PUBLIC)

    async def drive() -> str:
        endpoint = await live.open()
        await live.close()
        return endpoint.url

    assert asyncio.run(drive()) == PUBLIC


def test_the_placeholder_the_opponent_found_is_refused() -> None:
    """The exact value that reached a peer, and the exact reason it must not."""
    live, _ = opened(PLACEHOLDER)

    with pytest.raises(LocalDefectError, match="cannot reach"):
        asyncio.run(live.open())


def test_any_other_endpoint_is_refused_too_not_just_a_loopback_one() -> None:
    """A public URL that is simply the wrong one is the same defect."""
    live, _ = opened("https://someone-elses-tunnel.example.com/mcp")

    with pytest.raises(LocalDefectError, match="but this run's ingress is"):
        asyncio.run(live.open())


def test_a_refused_route_is_released_not_left_half_open() -> None:
    """Failing closed means holding nothing: no tunnel, no served surface."""
    live, ingress = opened(PLACEHOLDER)

    with pytest.raises(LocalDefectError):
        asyncio.run(live.open())
    assert not live.is_live
    assert ingress.closed and not ingress.is_live()


def test_a_route_carrying_no_declaration_promises_nothing_and_is_unaffected() -> None:
    """No Step-0 means no claim to contradict, so nothing is compared."""
    live, _ = opened(None)

    async def drive() -> str:
        endpoint = await live.open()
        await live.close()
        return endpoint.url

    assert asyncio.run(drive()) == PUBLIC


def test_the_placeholder_would_also_fail_the_counted_publicity_gate() -> None:
    """Two independent guards, and the rehearsal path only bypassed one of them."""
    resolver = SystemHostResolver()
    from mars777_police.app.public_endpoint_policy import is_public_endpoint

    assert not is_public_endpoint(OwnPublicPeerEndpoint(PLACEHOLDER), resolver)
