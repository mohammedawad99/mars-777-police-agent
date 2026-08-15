"""What the two agreement cadences refuse to do on their own.

`agree_config` and `agree_result` order sends and waits and decide nothing, so
the only behaviour of their own they have is what they refuse. The non-proposer
branch of `agree_result` echoes the timestamp the proposer chose; it reads that
timestamp from `ResultExchange`, which owns it. If the milestone were ever set
without the state behind it, echoing `None` would send a request the peer could
not match - so the branch refuses instead, and this pins that refusal.

The state below is impossible through the protocol, which is the point: it is
reached by setting the milestone directly, exactly the mistake the "state
first, signal second" rule exists to prevent.
"""

import asyncio
from pathlib import Path
from typing import cast

import composed_builders as compose
import pytest
import r7_builders as r7
import r7_fixtures as fixtures

from mars777_police.app.peer_runner import PeerRunner
from mars777_police.app.series_agreements import agree_result
from mars777_police.infra.artifacts import JsonArtifactStore


def _unagreed() -> object:
    """A real, complete-but-unagreed `ResultExchange` - no timestamp yet."""
    import boot_builders as build

    from mars777_police.agent_runtime import AgentRuntime
    from mars777_police.app.series_record import outcome_line
    from mars777_police.domain.terminal import Outcome

    composition = compose.after_step0(compose.compose())
    agent = AgentRuntime(composition, build.HOST, build.free_port())
    series = r7.series_for(agent, JsonArtifactStore(Path(".")))
    series.lines = tuple(outcome_line(one, Outcome.CAPTURE) for one in range(1, 7))
    return fixtures.unagreed_result(series)


async def _wait(arrived: object) -> None:
    """Wait the way the driver does, without its deadline."""
    assert isinstance(arrived, asyncio.Event)
    await arrived.wait()


def test_a_non_proposer_never_echoes_a_timestamp_that_never_arrived() -> None:
    exchange = _unagreed()
    assert exchange.timestamp is None  # type: ignore[attr-defined]
    assert exchange.runtime.is_proposer is False  # type: ignore[attr-defined]
    exchange.milestones.requested.set()  # type: ignore[attr-defined]

    with pytest.raises(AssertionError, match="carries the adopted timestamp"):
        asyncio.run(agree_result(exchange, cast(PeerRunner, None), _wait))  # type: ignore[arg-type]
