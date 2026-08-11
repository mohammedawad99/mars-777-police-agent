"""What the runner must not hold, reach for, or resolve twice."""

import asyncio
import dataclasses

import pytest
import runner_builders as build
import turn_builders
from r16_builders import GROUP_A
from r16_source import imports_of, tokens_of
from spy_transport import SpyTransport
from test_runner_delegation import CURSOR, sealed

from mars777_police.app import peer_runner as module
from mars777_police.app.peer_runner import PeerRunner
from mars777_police.app.protocol_errors import StaleMessageError
from mars777_police.app.sealed_record_values import ActorRole, Intent


def test_the_runner_holds_only_injected_dependencies() -> None:
    """No cursor, phase, sub-game, prepared turn, digest, verdict or sender."""
    assert {f.name for f in dataclasses.fields(PeerRunner)} == {
        "transport",
        "step0",
        "pregame",
        "turns",
        "evidence",
        "results",
        "series",
    }
    assert PeerRunner.__dataclass_params__.frozen


def test_the_runner_never_reaches_for_transport_concrete_or_a_framework() -> None:
    imported = imports_of(module)
    assert all("transport" not in name or name.endswith("peer_transport") for name in imported)
    for forbidden in ("fastmcp", "httpx", "ngrok", "PeerClient", "environ", "getenv", "socket"):
        assert forbidden not in tokens_of(module)


def test_the_runner_implements_no_crypto_rules_or_persistence() -> None:
    for forbidden in ("hashlib", "sha256", "secrets", "dumps", "canonical", "open", "Path"):
        assert forbidden not in tokens_of(module)


def test_the_runner_never_sleeps_polls_or_counts_retries() -> None:
    for forbidden in ("sleep", "retry", "attempts", "timeout", "Clock", "monotonic"):
        assert forbidden not in tokens_of(module)


def test_the_turn_provider_is_resolved_per_operation() -> None:
    """A consumed turn runtime must not be reused for the next turn."""
    peer = build.side(GROUP_A, "group_a", ActorRole.POLICE)
    first, second = turn_builders.runtime(), turn_builders.runtime()
    resolved = iter([first, second, second])
    spy = SpyTransport()
    runner = PeerRunner(
        spy,
        peer.pregame.step0,
        peer.pregame,
        lambda: next(resolved),
        lambda: peer.producer,
        peer.results,
        peer.gate,
    )
    asyncio.run(
        runner.open_turn(
            state=sealed(),
            action=turn_builders.legal_reveal().action,
            intent=Intent.TRUTH,
            hint="north",
            cursor=CURSOR,
        )
    )
    assert first.local_commitment is not None and second.local_commitment is None
    second.accept_commitment(turn_builders.commitment())
    asyncio.run(runner.acknowledge_peer_turn())
    assert spy.names() == ["commitment", "acknowledgement"]


def test_the_evidence_provider_is_resolved_per_operation() -> None:
    """A completed sub-game producer must not serve the next sub-game."""
    peer = build.side(GROUP_A, "group_a", ActorRole.POLICE)
    other = build.side(GROUP_A, "group_a", ActorRole.POLICE).producer
    resolved = iter([peer.producer, other])
    spy = SpyTransport()
    runner = PeerRunner(
        spy,
        peer.pregame.step0,
        peer.pregame,
        lambda: peer.turn,
        lambda: next(resolved),
        peer.results,
        peer.gate,
    )
    asyncio.run(
        runner.open_turn(
            state=sealed(),
            action=turn_builders.legal_reveal().action,
            intent=Intent.TRUTH,
            hint="north",
            cursor=CURSOR,
        )
    )
    asyncio.run(runner.send_final_nonce_reveal())
    assert len(peer.producer.records) == 1
    assert spy.sent[1][1].entries == ()


def test_revealing_a_turn_we_did_not_register_is_refused() -> None:
    """The prepared turn must be the commitment the runtime actually holds."""
    peer = build.side(GROUP_A, "group_a", ActorRole.POLICE)
    spy = SpyTransport()
    runner = peer.runner(spy)
    prepared = asyncio.run(
        runner.open_turn(
            state=sealed(),
            action=turn_builders.legal_reveal().action,
            intent=Intent.TRUTH,
            hint="north",
            cursor=CURSOR,
        )
    )
    peer.turn.local_acknowledged = True
    peer.turn.local_commitment = turn_builders.commitment(digest=turn_builders.OTHER_DIGEST)
    with pytest.raises(StaleMessageError, match="not the commitment we registered"):
        asyncio.run(runner.reveal_turn(prepared))
