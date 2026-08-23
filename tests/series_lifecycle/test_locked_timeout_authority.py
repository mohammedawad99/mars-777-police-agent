"""Who owns the outbound deadline once the configuration is locked.

`response_timeout_sec` is NEGOTIABLE, both peers agree one, and it is written
into the official config artifact - and until this file existed the runtime
ignored it. The composition root built one `PeerClient` with a module constant
and nothing rebound it, so every gameplay request used that constant for the
whole series whatever the peers had agreed.

The reason it escaped is worth stating, because it shapes these tests.
`PeerClient.for_locked_config` and `TimeoutPolicy.for_config` were both correct
and both tested, and both had zero production call sites. Testing the pieces
proved the pieces; nothing crossed the seam where the pieces were supposed to
be joined. So these tests drive the **real** composed agent through the **real**
lock and then ask the client what deadline it would actually use.
"""

import dataclasses

import composed_builders as compose
import pytest
import r7_builders as r7
from r16_builders import GROUP_A, GROUP_B

from mars777_police.app.protocol_errors import ConfigMismatchError
from mars777_police.app.round_opening import open_round_for
from mars777_police.app.sealed_record_values import ActorRole
from mars777_police.composition import PEER_TIMEOUT_SECONDS
from mars777_police.composition_values import AgentComposition
from mars777_police.domain.config_league_sections import NetworkAndLeagueTerms
from mars777_police.domain.negotiated_config import NegotiatedConfig

PORTS = ("http://127.0.0.1:9101/mcp", "http://127.0.0.1:9102/mcp")


def config_with(response: int, watchdog: int = 60) -> NegotiatedConfig:
    """The lifecycle config, differing only in the deadline under test."""
    terms = r7.CONFIG.network_and_league
    return dataclasses.replace(
        r7.CONFIG,
        network_and_league=NetworkAndLeagueTerms(
            response,
            watchdog,
            terms.num_games,
            terms.diversity_reward,
            terms.min_games_to_pass,
            terms.max_games_per_team,
            terms.token_budget_per_series,
        ),
    )


def paired() -> tuple[AgentComposition, AgentComposition]:
    """Two really composed agents, pointed at each other. Nothing is running."""
    return (
        compose.compose(GROUP_A, ActorRole.POLICE, PORTS[1]),
        compose.compose(GROUP_B, ActorRole.THIEF, PORTS[0]),
    )


def locked_pair(config: NegotiatedConfig, sub_game: int = 1) -> tuple[AgentComposition, ...]:
    """Drive both sides through the production round-open and mutual lock.

    Each side verifies the other's evidence through its own real
    `ConfigLockRuntime`, which is what makes this a lock rather than an
    assignment: a candidate nobody verified must not move the deadline.
    """
    sides = paired()
    for side, group in zip(sides, (GROUP_A, GROUP_B), strict=True):
        side.pregame.open_round(*r7._round(group, sub_game))
        open_round_for(side.pregame, sub_game, config)
    ours, theirs = (side.pregame for side in sides)
    ours.accept_lock(theirs.prepare_lock())
    theirs.accept_lock(ours.prepare_lock())
    return sides


def test_the_composed_client_starts_on_the_pre_lock_deadline() -> None:
    """Negotiation has to be possible before there is anything to negotiate.

    A client that demanded a locked config would deadlock the very exchange
    that produces one, so the pre-lock bound stays and is bounded.
    """
    ours, _ = paired()

    assert ours.peer_client.timeout == PEER_TIMEOUT_SECONDS
    assert ours.peer_client.timeout > 0


@pytest.mark.parametrize("response", [17, 30, 45, 120])
def test_the_locked_config_governs_the_outbound_deadline(response: int) -> None:
    """The negotiated value, whatever it is - not a constant that resembles it.

    Thirty is included on purpose: the ordinary default must keep behaving as
    it always did, so a passing suite cannot be explained by the fix having
    quietly changed what a normal series does.
    """
    ours, theirs = locked_pair(config_with(response))

    assert ours.peer_client.timeout == float(response)
    assert theirs.peer_client.timeout == float(response)


def test_a_candidate_nobody_locked_does_not_move_the_deadline() -> None:
    """Adopting is not agreeing: only verified mutual evidence may rebind."""
    ours, _ = paired()
    ours.pregame.open_round(*r7._round(GROUP_A, 1))
    open_round_for(ours.pregame, 1, config_with(45))

    assert ours.peer_client.timeout == PEER_TIMEOUT_SECONDS


def test_every_post_lock_request_family_shares_the_bound_deadline() -> None:
    """One authority and one client, not six paths that must agree by luck.

    Commitment, acknowledgement, reveal, the final nonce disclosure, the audit
    disclosure and the result agreement all travel through the transport this
    composition holds, so binding it once is what binds all of them.
    """
    ours, _ = locked_pair(config_with(45))
    transport = ours.peer_transport

    assert transport._client is ours.peer_client  # type: ignore[attr-defined]
    assert ours.peer_runner.transport is transport
    assert ours.peer_client.timeout == 45.0


def test_a_second_conflicting_lock_cannot_silently_change_the_deadline() -> None:
    """A series holds one model; a later disagreeing lock is refused, not applied."""
    ours, theirs = locked_pair(config_with(45))
    other = config_with(120)

    with pytest.raises(ConfigMismatchError):
        ours.pregame.accept_lock(theirs.pregame.lock.outbound(other))

    assert ours.peer_client.timeout == 45.0
