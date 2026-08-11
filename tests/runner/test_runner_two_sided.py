"""Two production peers, two persistent sessions, one real callback turn.

Nothing here is a double: both sides run the real FastMCP server, the real
`InboundPeerOperations`, the real application owners and the real `PeerRunner`
over a real held `PeerClient`. The test plays only the part Stage 5-R5 will own -
deciding when each side acts.
"""

import asyncio
from collections.abc import Iterator

import pytest
import runner_builders as build
import turn_builders
from r16_builders import GROUP_A, GROUP_B

from mars777_police.app.protocol_errors import AuthFailureError, StaleMessageError
from mars777_police.app.sealed_record_values import ActorRole, Intent, SealedState
from mars777_police.app.turn_cursor import TurnCursor
from mars777_police.transport.client import PeerClient
from mars777_police.transport.peer_transport import FastMcpPeerTransport

TIMEOUT = 20.0
CURSOR = TurnCursor(build.SUB_GAME, 1)


@pytest.fixture
def pair() -> Iterator[tuple[object, object]]:
    """Side A and side B, each behind its own real inbound server."""
    a = build.side(GROUP_A, "group_a", ActorRole.POLICE)
    b = build.side(GROUP_B, "group_b", ActorRole.THIEF)
    with build.server_for(a) as server_a, build.server_for(b) as server_b:
        a.url, b.url = server_a.url, server_b.url
        yield a, b


def sealed(role: ActorRole) -> SealedState:
    """The own-known snapshot the acting side seals."""
    from evidence_builders import CONFIG, POS

    return SealedState(CONFIG, POS[1], (), 1, role)


async def step0_on(peer: object, url: str) -> FastMcpPeerTransport:
    """Authenticate a held session and return the transport bound to it."""
    client = await PeerClient(url, timeout=TIMEOUT).__aenter__()
    transport = FastMcpPeerTransport(client)
    await peer.runner(transport).send_step0(peer.own)
    return transport


def test_a_full_callback_turn_completes_across_two_real_sessions(pair: tuple) -> None:
    """Commit → Ack → Reveal, each a separate operation on the real wire."""
    a, b = pair

    async def run() -> bool:
        a_to_b = await step0_on(a, b.url)
        b_to_a = await step0_on(b, a.url)
        prepared = await a.runner(a_to_b).open_turn(
            state=sealed(ActorRole.POLICE),
            action=turn_builders.legal_reveal().action,
            intent=Intent.TRUTH,
            hint="heading north",
            cursor=CURSOR,
        )
        assert b.turn.peer_commitment is not None
        await b.runner(b_to_a).acknowledge_peer_turn()
        assert a.turn.local_acknowledged
        return await a.runner(a_to_b).reveal_turn(prepared)

    assert asyncio.run(run()) is True
    assert b.turn.evidence and b.turn.evidence[0].legal is True


def test_a_game_illegal_reveal_returns_false_over_the_real_path(pair: tuple) -> None:
    """Protocol fine, move illegal: `False`, never an exception."""
    a, b = pair

    async def run() -> bool:
        a_to_b = await step0_on(a, b.url)
        b_to_a = await step0_on(b, a.url)
        prepared = await a.runner(a_to_b).open_turn(
            state=sealed(ActorRole.POLICE),
            action=turn_builders.illegal_reveal().action,
            intent=Intent.TRUTH,
            hint="heading south",
            cursor=CURSOR,
        )
        await b.runner(b_to_a).acknowledge_peer_turn()
        return await a.runner(a_to_b).reveal_turn(prepared)

    assert asyncio.run(run()) is False


def test_a_reveal_before_the_peer_acknowledged_is_refused(pair: tuple) -> None:
    """The gate is the turn runtime's own record, not a flag in the runner."""
    a, b = pair

    async def run() -> None:
        a_to_b = await step0_on(a, b.url)
        prepared = await a.runner(a_to_b).open_turn(
            state=sealed(ActorRole.POLICE),
            action=turn_builders.legal_reveal().action,
            intent=Intent.TRUTH,
            hint="heading north",
            cursor=CURSOR,
        )
        assert not a.turn.local_acknowledged
        with pytest.raises(StaleMessageError, match="not acknowledged"):
            await a.runner(a_to_b).reveal_turn(prepared)

    asyncio.run(run())


def test_a_fresh_session_cannot_continue_an_authenticated_conversation(pair: tuple) -> None:
    """Session loss is not recoverable: no reconnect policy exists, by design."""
    a, b = pair

    async def run() -> None:
        client = PeerClient(b.url, timeout=TIMEOUT)
        async with client:
            await a.runner(FastMcpPeerTransport(client)).send_step0(a.own)
        async with PeerClient(b.url, timeout=TIMEOUT) as fresh:
            with pytest.raises(AuthFailureError):
                await FastMcpPeerTransport(fresh).send_commitment(turn_builders.commitment())

    asyncio.run(run())
