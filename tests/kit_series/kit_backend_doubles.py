"""The doubles a backend test needs: a wired turn, a pair, a settlement sink.

None of these asserts anything. They stand in for the things a real friendly
supplies - a turn already on the wire, two backends facing each other, the
pairing a greeting established, and a settlement signal that only records that
it was sent.
"""

import asyncio

from kit_wire_vectors import COMMIT
from r16_builders import config

from mars777_police.__main__ import ROLE
from mars777_police.app.commitment_codecs import CommitmentCodec
from mars777_police.app.kit_backend_settlement import BackendSettlement
from mars777_police.app.kit_friendly import KitFriendlySession
from mars777_police.app.kit_messages import (
    KitAuditReveal,
    KitRecord,
    KitResultClaim,
    KitRole,
)
from mars777_police.app.kit_payload import PeerPayload
from mars777_police.app.kit_session import KitSessionContext
from mars777_police.app.protocol_values import Sha256Digest
from mars777_police.app.run_class import RunClassification
from mars777_police.domain.scent_model_default import default_scent_model
from mars777_police.infra.clock import SystemClock
from mars777_police.kit_backend import KitRoleBackend
from mars777_police.protocol.kit_commitment import kit_commitment
from mars777_police.protocol.secure_nonce import SecretsNonceSource

OURS = KitRole(ROLE.value)
THEIRS = KitRole.THIEF if OURS is KitRole.POLICE else KitRole.POLICE
TERMS: dict[str, object] = {"board_size": 7, "max_steps": 35}


def _wire_turn() -> dict[str, object]:
    return {
        "step": 1,
        "sender": THEIRS.value,
        "hint": "over here",
        "smell_grid": {"0,0": 0.5},
        "commit": COMMIT,
        "timestamp": "2026-08-18T00:00:00Z",
    }


def backend_pair() -> tuple[KitRoleBackend, list[object], KitFriendlySession]:
    friendly = KitFriendlySession(RunClassification.friendly(kit_terms_agreement=True))
    context = KitSessionContext("MaRs-777", OURS, PeerPayload(TERMS), 1, friendly=friendly)
    context.peer_group = "sparring-local"
    sent: list[object] = []

    class Transport:
        async def send_kit(self, message: object) -> None:
            sent.append(message)

    async def settled(number: int) -> None:
        sent.append(("settled", number))

    async def contribute(row: dict[str, object]) -> None:
        sent.append(("row", row))

    async def series_rows() -> tuple[dict[str, object], ...]:
        return ()

    first = KitRole.POLICE if OURS is KitRole.POLICE else KitRole.THIEF
    backend = KitRoleBackend(
        context=context,
        friendly=friendly,
        transport=Transport(),  # type: ignore[arg-type]
        settled=settled,
        config=config(),
        role=ROLE,
        strategy=_First(),
        model=default_scent_model(),
        nonces=SecretsNonceSource(),
        clock=SystemClock(),
        codec=CommitmentCodec.KIT_CORE_COMMITMENT_V1,
        deadline=5.0,
        first_role=first,
        settlement=BackendSettlement(contribute=contribute, series_rows=series_rows),
    )
    return backend, sent, friendly


class _First:
    def choose_action(self, observation: object) -> object:
        from mars777_police.domain.actions import MoveAction
        from mars777_police.domain.rules import Move

        return MoveAction(Move.STAY)


async def _settle(condition, timeout: float = 5.0) -> None:
    """Wait for the backend to reach the point the opponent is answering."""
    for _ in range(int(timeout / 0.01)):
        if condition():
            return
        await asyncio.sleep(0.01)
    raise AssertionError("the backend never reached the awaited point")


def _pairing():
    from mars777_police.app.kit_greeting import KitPairing

    return KitPairing(
        "MaRs-777-vs-sparring-local",
        "1e73c318-5b29-4a7b-1c60-ecb8286265f0",
        "MaRs-777",
        "sparring-local",
        OURS,
        THEIRS,
        1,
        terms_agreed=True,
    )


def _peer_reveal() -> KitAuditReveal:
    payload = {"step": 1, "move": "MOVE:N"}
    nonce = "0" * 32
    return KitAuditReveal(
        THEIRS,
        (KitRecord(PeerPayload(payload), nonce, Sha256Digest(kit_commitment(payload, nonce))),),
        KitResultClaim.SURVIVAL,
    )
