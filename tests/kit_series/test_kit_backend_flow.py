"""One role backend playing the sub-game it was handed, and reporting it settled.

The backend plays only its own rows. Settlement is signalled to the gateway when
they end, never inferred by anyone from the absence of further turns.
"""

import asyncio

from kit_backend_doubles import _pairing, _peer_reveal, _settle, backend_pair
from kit_wire_vectors import COMMIT

from mars777_police.__main__ import ROLE
from mars777_police.app.capture_values import CaptureClaim
from mars777_police.app.kit_messages import (
    KitAuditReveal,
    KitRole,
    KitTurn,
)
from mars777_police.app.protocol_values import Sha256Digest
from mars777_police.domain.terminal import Outcome

OURS = KitRole(ROLE.value)
THEIRS = KitRole.THIEF if OURS is KitRole.POLICE else KitRole.POLICE


def test_a_backend_plays_the_sub_game_it_is_handed_and_reports_it_settled() -> None:
    backend, sent, friendly = backend_pair()
    pairing = _pairing()
    opening = friendly.inbox

    async def opponent() -> None:
        await _settle(lambda: friendly.inbox is not opening)
        friendly.record_pairing(pairing)
        await _settle(lambda: bool(sent))
        claim = CaptureClaim(backend.config.board_and_agents.thief_start)
        friendly.deliver_turn(
            KitTurn(
                1,
                THEIRS,
                "over here",
                (("0,0", 0.5),),
                Sha256Digest(COMMIT),
                "2026-08-18T00:00:00Z",
                capture_claim=claim if OURS is KitRole.THIEF else None,
                survival_claimed=OURS is KitRole.POLICE,
            )
        )
        await _settle(lambda: any(isinstance(one, KitAuditReveal) for one in sent))
        friendly.deliver_audit(_peer_reveal())

    async def run() -> Outcome:
        played = asyncio.ensure_future(backend.play_sub_game(1))
        await opponent()
        return await played

    outcome = asyncio.run(run())

    assert outcome in (Outcome.CAPTURE, Outcome.SURVIVAL)
    assert ("settled", 1) in sent
    assert backend.verified[1] is True
    assert backend.chains[1].disclosed is True
    assert any(isinstance(one, KitAuditReveal) for one in sent)
