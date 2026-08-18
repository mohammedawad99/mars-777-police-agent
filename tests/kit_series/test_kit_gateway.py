"""One group URL, two private backends, and exactly one destination per message.

`teams.<group>.mcp_endpoint` is group-level. The opponent sees one MaRs-777 URL
for the whole series and never learns that two role backends sit behind it - the
private endpoints are an implementation detail and are never advertised.

Routing comes from the **contract**: the frozen convention, the sub-game number
and the agreed first assignment. Never from a source port, a process id, an
arrival time or a strategy output, and never by asking both backends.
"""

import asyncio

import pytest
from kit_wire_vectors import NEGOTIATION, TURN

from mars777_police.app.kit_handoff import SeriesHandoff
from mars777_police.app.kit_messages import KitRole
from mars777_police.app.protocol_errors import StaleMessageError
from mars777_police.protocol.kit_identity import kit_terms_digest
from mars777_police.transport.kit_gateway import KitGroupGateway

TERMS = NEGOTIATION["terms"]
NONCE = str(NEGOTIATION["nonce"])


def greeting(**changes: object) -> dict[str, object]:
    body = dict(NEGOTIATION) | {"signature": kit_terms_digest(TERMS, NONCE)}
    body.update(changes)
    return body


def gateway(first: KitRole = KitRole.POLICE) -> tuple[KitGroupGateway, dict[str, list[str]]]:
    seen: dict[str, list[str]] = {"police": [], "thief": []}

    def route(side: str):
        async def forward(tool: str, arguments: dict[str, object]) -> None:
            seen[side].append(tool)

        return forward

    held = KitGroupGateway(
        handoff=SeriesHandoff(first),
        routes={KitRole.POLICE: route("police"), KitRole.THIEF: route("thief")},
        deadline=1.0,
    )
    return held, seen


def test_the_first_sub_game_routes_to_the_backend_the_schedule_names() -> None:
    held, seen = gateway()

    asyncio.run(held.negotiate(greeting(role="thief", sub_game_number=1)))

    assert seen["police"] == ["negotiate"]
    assert seen["thief"] == []


def test_the_second_sub_game_routes_to_the_opposite_backend() -> None:
    held, seen = gateway()
    asyncio.run(held.negotiate(greeting(role="thief", sub_game_number=1)))
    held.settle(1)

    asyncio.run(held.negotiate(greeting(role="police", sub_game_number=2)))

    assert seen["thief"] == ["negotiate"]


def test_all_six_rows_alternate_between_the_two_backends() -> None:
    held, seen = gateway()
    for number in range(1, 7):
        peer = "thief" if number % 2 == 1 else "police"
        asyncio.run(held.negotiate(greeting(role=peer, sub_game_number=number)))
        held.settle(number)

    assert seen["police"] == ["negotiate"] * 3
    assert seen["thief"] == ["negotiate"] * 3


def test_gameplay_routes_to_exactly_one_backend_and_never_to_both() -> None:
    held, seen = gateway()
    asyncio.run(held.negotiate(greeting(role="thief", sub_game_number=1)))

    asyncio.run(held.receive_turn(TURN))
    asyncio.run(held.submit_audit({"sender": "thief", "records": [], "result_claim": "survival"}))

    assert seen["police"] == ["negotiate", "receive_turn", "submit_audit"]
    assert seen["thief"] == []


def test_a_peer_declaring_our_own_scheduled_role_is_refused() -> None:
    """Two of the same side can only deadlock; the pairing check says so."""
    held, _ = gateway()

    with pytest.raises(StaleMessageError):
        asyncio.run(held.negotiate(greeting(role="police", sub_game_number=1)))


def test_a_next_game_greeting_is_not_acknowledged_before_the_previous_settled() -> None:
    """Acknowledging into a queue nobody drains burns the opponent's budget."""
    held, seen = gateway()
    asyncio.run(held.negotiate(greeting(role="thief", sub_game_number=1)))

    with pytest.raises(TimeoutError):
        asyncio.run(held.negotiate(greeting(role="police", sub_game_number=2)))
    assert seen["thief"] == []


def test_a_duplicate_greeting_for_the_live_game_opens_no_second_series() -> None:
    held, seen = gateway()
    asyncio.run(held.negotiate(greeting(role="thief", sub_game_number=1)))
    asyncio.run(held.negotiate(greeting(role="thief", sub_game_number=1)))

    assert held.handoff.sub_game == 1
    assert seen["police"] == ["negotiate", "negotiate"]


def test_settlement_is_signalled_and_a_wrong_sub_game_is_refused() -> None:
    held, _ = gateway()

    with pytest.raises(StaleMessageError):
        held.settle(2)


def test_a_series_with_no_backend_for_a_role_refuses_rather_than_guessing() -> None:
    held = KitGroupGateway(handoff=SeriesHandoff(KitRole.POLICE), routes={}, deadline=1.0)

    with pytest.raises(StaleMessageError):
        asyncio.run(held.receive_turn(TURN))


def test_the_gateway_owns_no_game_semantics() -> None:
    """It routes. Board, legality, strategy, scent, digests and score are elsewhere."""
    source = __import__("inspect").getsource(KitGroupGateway)

    for forbidden in ("Board", "strategy", "commitment_for", "ScentField", "score"):
        assert forbidden not in source
