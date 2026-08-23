"""`run` ends in a settlement rather than in an exit, for the side that owns g06.

The defect this closes was measured, not imagined: both role backends returned
the moment their own last sub-game was disclosed, the port the gateway forwards
`submit_audit` to was gone, and the peer's retries had nowhere to land.

Whichever repository this is, exactly one of its two role backends owns sub-game
6 - so the test asserts the settlement in that repository and asserts its
*absence* in the other, rather than being written twice with a role hard-coded.
"""

import asyncio

import pytest
from kit_backend_builders import backend
from kit_backend_doubles import _pairing

from mars777_police.app.kit_backend_settlement import row_of
from mars777_police.app.kit_messages import KitAuditReveal, KitResultClaim, KitRole
from mars777_police.app.series_consensus import consensus_scope, consensus_sha256
from mars777_police.domain.terminal import Outcome


@pytest.mark.parametrize("first", list(KitRole), ids=[one.value for one in KitRole])
def test_only_the_backend_that_owns_the_last_sub_game_settles(first: KitRole) -> None:
    """The whole point of staying alive: `run` ends in a settlement, not an exit.

    Parametrised over the agreed first role so that **both** branches run in both
    repositories: whichever role this repository implements, one first role gives
    it sub-game 6 and the other gives it to the opposite backend.
    """
    held = backend(first)
    held.friendly.record_pairing(_pairing())
    pairing = _pairing()
    rows = tuple(
        row_of(
            pairing,
            n,
            KitRole.POLICE if n % 2 else KitRole.THIEF,
            Outcome.SURVIVAL if n % 2 else Outcome.CAPTURE,
        )
        for n in range(1, 7)
    )
    digest = consensus_sha256(
        consensus_scope(pairing.game_id, rows, pairing.our_group, pairing.peer_group)
    )
    sent: list[dict[str, object]] = []

    async def series() -> tuple[dict[str, object], ...]:
        return rows

    async def send(envelope: dict[str, object]) -> None:
        sent.append(envelope)

    class Transport:
        async def send_settlement(self, envelope: dict[str, object]) -> None:
            await send(envelope)

    held.transport = Transport()  # type: ignore[assignment]
    held.settlement.series_rows = series
    held.friendly.deliver_audit(
        KitAuditReveal(
            KitRole.THIEF if held.kit_role is KitRole.POLICE else KitRole.POLICE,
            (),
            KitResultClaim.SERIES_CONSENSUS,
            digest,
        )
    )

    class Instant(type(held)):  # type: ignore[misc]
        """Every row already played, so the test is about what happens after."""

        async def play_sub_game(self, number: int) -> Outcome:
            return Outcome.SURVIVAL

    import dataclasses

    held = Instant(**{f.name: getattr(held, f.name) for f in dataclasses.fields(held)})
    asyncio.run(held.run())

    if held.ours[-1] == 6:
        assert held.settlement.agreed == digest
        assert sent and sent[0]["consensus_sha"] == digest
    else:
        assert held.settlement.agreed is None
        assert not sent
