"""The permanent boot path: serve, reach the opponent, and stop either way.

Joining is a bounded startup step, because two teams start independently and the
first one up finds nothing to reach. What is pinned here is the shape of that
bound - only a transport failure is retried, the budget really ends, and a
failure still closes the runtime it opened.
"""

import asyncio
import socket
from pathlib import Path

import boot_builders as build
import pytest
from r16_builders import GROUP_A, GROUP_B

from mars777_police import autonomous_boot as boot
from mars777_police.agent_runtime import AgentRuntime, RuntimeState
from mars777_police.app.protocol_errors import (
    AuthFailureError,
    ConfigMismatchError,
    LocalDefectError,
)
from mars777_police.app.sealed_record_values import ActorRole
from mars777_police.startup_budget import StartupBudget
from mars777_police.transport.wire_errors import TransportFailureError

HOST = build.HOST


def pair() -> tuple[AgentRuntime, AgentRuntime]:
    """Two composed agents pointed at each other, neither started."""
    port_a, port_b = build.pair_urls()
    a = build.agent(GROUP_A, ActorRole.POLICE, f"http://{HOST}:{port_b}/mcp")
    b = build.agent(GROUP_B, ActorRole.THIEF, f"http://{HOST}:{port_a}/mcp")
    return AgentRuntime(a, HOST, port_a), AgentRuntime(b, HOST, port_b)


def closed_port() -> int:
    """A port bound and released, so nothing is listening on it."""
    with socket.socket() as probe:
        probe.bind((HOST, 0))
        return int(probe.getsockname()[1])


def test_a_closed_port_raises_the_transport_failure_identity() -> None:
    """RED B: the retryable boundary is pinned to what the adapter really raises.

    Not `OSError`, not `httpx.ConnectError`: `PeerClient` translates both into
    the existing local `E-TRANSPORT` category before anything else sees them, so
    that identity - and nothing wider - is what a startup retry may catch.
    """
    composition = build.agent(
        GROUP_A,
        ActorRole.POLICE,
        f"http://{HOST}:{closed_port()}/mcp",
    )
    runtime = AgentRuntime(composition, HOST, build.free_port())

    async def attempt() -> None:
        await runtime.serve()
        try:
            await runtime.connect()
        finally:
            await runtime.stop()

    with pytest.raises(TransportFailureError):
        asyncio.run(attempt())


def test_a_failed_single_attempt_still_closes_the_runtime() -> None:
    """The historical `connect()` contract is unchanged by the new operation."""
    composition = build.agent(
        GROUP_A,
        ActorRole.POLICE,
        f"http://{HOST}:{closed_port()}/mcp",
    )
    runtime = AgentRuntime(composition, HOST, build.free_port())

    async def attempt() -> None:
        await runtime.serve()
        with pytest.raises(TransportFailureError):
            await runtime.connect()
        assert runtime.state is RuntimeState.CLOSED

    asyncio.run(attempt())


def test_the_startup_budget_is_bounded_and_stops_the_runtime() -> None:
    """A peer that never appears fails inside the budget, leaving nothing open."""
    composition = build.agent(
        GROUP_A,
        ActorRole.POLICE,
        f"http://{HOST}:{closed_port()}/mcp",
    )
    runtime = AgentRuntime(composition, HOST, build.free_port())
    budget = StartupBudget(total_seconds=0.5, pause_seconds=0.05)

    async def attempt() -> None:
        await runtime.serve()
        with pytest.raises(TransportFailureError):
            await runtime.connect_until_ready(budget)
        assert runtime.state is RuntimeState.CLOSED

    asyncio.run(attempt())


def test_only_a_transport_failure_is_retried() -> None:
    """Auth, config and protocol refusals are answers, not unavailability."""
    budget = StartupBudget(total_seconds=1.0, pause_seconds=0.01)
    assert budget.retryable(TransportFailureError("E-TRANSPORT")) is True
    for refusal in (AuthFailureError("E-AUTH-FAILURE"), ConfigMismatchError("E-CONFIG-MISMATCH")):
        assert budget.retryable(refusal) is False


def test_a_peer_that_appears_late_is_still_joined(tmp_path: Path) -> None:
    """The startup race, deterministically: the listener opens mid-budget."""
    a, b = pair()
    budget = StartupBudget(total_seconds=10.0, pause_seconds=0.05)

    async def run() -> None:
        await a.serve()

        async def open_the_peer_late() -> None:
            await asyncio.sleep(0.2)
            await b.serve()

        late = asyncio.create_task(open_the_peer_late())
        try:
            await a.connect_until_ready(budget)
            assert a.state is RuntimeState.RUNNING
        finally:
            await late
            await a.stop()
            await b.stop()

    asyncio.run(run())


def test_a_budget_must_be_positive_in_both_directions() -> None:
    """A non-positive bound or cadence is a local defect, not a fast retry."""
    for total, pause in ((0.0, 0.1), (1.0, 0.0), (-1.0, 0.1)):
        with pytest.raises(LocalDefectError, match="must be positive"):
            StartupBudget(total_seconds=total, pause_seconds=pause)


def test_the_startup_variant_refuses_a_runtime_that_is_not_serving() -> None:
    """Same precondition as `connect`: there is nothing to connect from."""
    composition = build.agent(
        GROUP_A,
        ActorRole.POLICE,
        f"http://{HOST}:{closed_port()}/mcp",
    )
    runtime = AgentRuntime(composition, HOST, build.free_port())
    budget = StartupBudget(total_seconds=1.0, pause_seconds=0.05)

    async def attempt() -> None:
        with pytest.raises(LocalDefectError, match="cannot connect while NEW"):
            await runtime.connect_until_ready(budget)

    asyncio.run(attempt())


def test_boot_owns_no_gameplay_vocabulary() -> None:
    """The coordinator sequences owners; it never decides anything they own."""
    import inspect

    source = inspect.getsource(boot)
    for forbidden in (
        "MoveAction",
        "BarrierAction",
        "Outcome.",
        "choose_action",
        "close_turn",
        "close_sub_game",
        "send_config_proposal",
        "send_config_lock",
        "adopt_config",
        "open_result_agreement",
        "respond_to_result",
        "legal_moves",
    ):
        assert forbidden not in source
