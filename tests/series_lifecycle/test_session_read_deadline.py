"""The read deadline of a session that was opened before the lock existed.

Fix1 made `call_tool` carry the agreed `response_timeout_sec`, and Windows
still failed on `httpx.ReadTimeout` at thirty seconds. The reason was one
layer down and is a matter of *when*, not *what*: the peer session is opened
during startup, necessarily before Step-0 and the lock, and the HTTP client
built at that moment captured the pre-lock window as its read timeout and kept
it for the life of the session. The MCP call said forty-five; the socket read
underneath it still gave up at thirty.

Connecting before the lock is correct and cannot change - a client that
demanded a locked configuration could never make the calls that produce one.
What must change is that the captured number becomes a consulted authority, so
a request *built* after the lock carries what the peers agreed.

These tests therefore open the client first and lock second, which is the
order the runtime actually uses, and then ask a newly built request what read
budget it carries. `httpx` stamps `build_request` with the client's `timeout`
property at construction time, so that request is the honest witness.
"""

import httpx
import pytest
from test_locked_timeout_authority import PORTS, config_with, locked_pair, paired

from mars777_police.transport.session_deadline import deadline_factory

BASE = httpx.Timeout(30.0, read=30.0)
"""What FastMCP hands a factory: its own connect/write/pool, our read."""


def read_of(client: httpx.AsyncClient) -> float | None:
    """The read budget a request built **now** would carry."""
    return client.build_request("POST", PORTS[0]).extensions["timeout"]["read"]


def other_than_read(client: httpx.AsyncClient) -> tuple[float | None, ...]:
    """Connect, write and pool - the components this fix must not touch."""
    stamped = client.build_request("POST", PORTS[0]).extensions["timeout"]
    return stamped["connect"], stamped["write"], stamped["pool"]


def test_a_client_built_before_the_lock_uses_the_negotiation_window() -> None:
    """Startup has no agreed value yet, so the bootstrap bound still applies."""
    ours, _ = paired()

    client = deadline_factory(ours.peer_client.deadline)(timeout=BASE)

    assert read_of(client) == 30.0


@pytest.mark.parametrize("response", [17, 30, 45, 120])
def test_a_request_built_after_the_lock_carries_the_agreed_deadline(response: int) -> None:
    """The regression: same client, opened first, locked afterwards.

    This is the shape the runtime has - connect during startup, agree the
    configuration later - and the deadline has to follow the agreement rather
    than the moment the socket happened to open.
    """
    ours, _ = paired()
    client = deadline_factory(ours.peer_client.deadline)(timeout=BASE)

    assert read_of(client) == 30.0

    ours.pregame.open_round(*_round_for(ours))
    _lock_at(ours, config_with(response))

    assert read_of(client) == float(response)


def test_the_other_timeout_components_are_left_alone() -> None:
    """`response_timeout_sec` owns the response, and nothing else.

    Connect, write and pool belong to the transport that already set them, so
    they must survive a lock untouched - widening them for symmetry would be
    this project taking ownership of values it never negotiated.
    """
    ours, _peer = locked_pair(config_with(120))
    client = deadline_factory(ours.peer_client.deadline)(timeout=BASE)

    assert read_of(client) == 120.0
    assert other_than_read(client) == (30.0, 30.0, 30.0)


def test_a_candidate_nobody_locked_leaves_the_read_deadline_alone() -> None:
    """Only verified mutual evidence may move it, exactly as for `call_tool`."""
    from mars777_police.app.round_opening import open_round_for

    ours, _ = paired()
    client = deadline_factory(ours.peer_client.deadline)(timeout=BASE)
    ours.pregame.open_round(*_round_for(ours))
    open_round_for(ours.pregame, 1, config_with(45))

    assert read_of(client) == 30.0


def test_the_factory_passes_every_argument_fastmcp_supplies() -> None:
    """The seam is FastMCP's documented one, so its keywords must survive."""
    ours, _ = paired()

    client = deadline_factory(ours.peer_client.deadline)(
        headers={"x-test": "1"}, auth=None, follow_redirects=True, timeout=BASE
    )

    assert client.headers["x-test"] == "1"
    assert client.follow_redirects is True
    assert read_of(client) == 30.0


def test_a_factory_called_without_a_timeout_still_answers() -> None:
    """FastMCP omits `timeout` when no read budget was configured."""
    ours, _ = paired()

    client = deadline_factory(ours.peer_client.deadline)()

    assert read_of(client) == 30.0


def _round_for(side: object) -> tuple[object, object]:
    import r7_builders as r7
    from r16_builders import GROUP_A

    return r7._round(GROUP_A, 1)


def _lock_at(side: object, config: object) -> None:
    """Drive the real mutual lock for *side* against a freshly built peer."""
    import r7_builders as r7
    from r16_builders import GROUP_B

    from mars777_police.app.round_opening import open_round_for

    _, peer = paired()
    peer.pregame.open_round(*r7._round(GROUP_B, 1))
    open_round_for(peer.pregame, 1, config)
    open_round_for(side.pregame, 1, config)  # type: ignore[attr-defined]
    side.pregame.accept_lock(peer.pregame.prepare_lock())  # type: ignore[attr-defined]


def test_reassigning_the_base_timeout_still_leaves_the_agreed_read_in_charge() -> None:
    """The authority is not a default that a later assignment can overwrite.

    Anything that sets the client's timeout - httpx itself, or a future
    transport - replaces the components this fix does not own, and must not be
    able to take back the response deadline the peers agreed.
    """
    ours, _peer = locked_pair(config_with(45))
    client = deadline_factory(ours.peer_client.deadline)(timeout=BASE)

    client.timeout = httpx.Timeout(5.0, read=1.0)

    assert read_of(client) == 45.0
    assert other_than_read(client) == (5.0, 5.0, 5.0)
