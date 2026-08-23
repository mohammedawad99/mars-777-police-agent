"""Doubles for driving the backend's artifact recording exactly as play does."""

from typing import Any

from r16_builders import config

from mars777_police.app.auth_values import KeyId
from mars777_police.app.kit_backend_artifacts import BackendArtifacts
from mars777_police.app.kit_greeting import KitGreeting
from mars777_police.app.kit_messages import KitAuditReveal, KitRecord, KitResultClaim, KitRole
from mars777_police.app.kit_payload import PeerPayload, kit_payload
from mars777_police.app.kit_preset import ExternalMode, external_profiles
from mars777_police.app.protocol_values import Sha256Digest
from mars777_police.app.sealed_record_values import ActorRole, Intent
from mars777_police.app.turn_cursor import TurnCursor
from mars777_police.artifact_documents import terms_config_document
from mars777_police.domain.actions import MoveAction
from mars777_police.domain.board import Position
from mars777_police.domain.rules import Move
from mars777_police.domain.scent_model_default import default_scent_model
from mars777_police.protocol.commitment_codec import CommitmentCodec, commitment_for
from mars777_police.protocol.kit_identity import kit_terms_digest

TERMS: dict[str, object] = {"board_size": 7, "max_steps": 35}
NONCE = "5f4dcc3b5aa765d61d8327deb882cf99"
CODEC = CommitmentCodec.KIT_CORE_COMMITMENT_V1
CONTRIBUTED: list[tuple[str, int, dict[str, Any]]] = []


async def sink(kind: str, sub_game: int, document: dict[str, Any]) -> None:
    """Stand in for the gateway, keeping what a backend actually handed over."""
    CONTRIBUTED.append((kind, sub_game, document))


def artifacts(*, wired: bool = True, silent: bool = False) -> BackendArtifacts:
    """The production collaborator, in its three real configurations."""
    if silent:
        return BackendArtifacts()
    made = BackendArtifacts(
        profiles=external_profiles(ExternalMode.KIT_CORE_V1, KeyId("mars777-k1")),
        config=config(),
        model=default_scent_model(),
        write_config=terms_config_document,
    )
    if wired:
        made.contribute = sink
    return made


def greeting() -> KitGreeting:
    return KitGreeting(
        PeerPayload(TERMS), NONCE, kit_terms_digest(TERMS, NONCE), "s82kma9e", KitRole.THIEF, 1
    )


def record(step: int, role: ActorRole) -> KitRecord:
    payload = kit_payload(
        cursor=TurnCursor(1, step),
        role=role,
        action=MoveAction(Move.STAY),
        intent=Intent.TRUTH,
        hint="",
        own_position=Position(step, 0),
        barriers=(),
    )
    nonce = f"{step:032x}"
    return KitRecord(
        PeerPayload(payload), nonce, Sha256Digest(commitment_for(CODEC, payload, nonce))
    )


def disclosure() -> KitAuditReveal:
    return KitAuditReveal(KitRole.THIEF, (record(1, ActorRole.THIEF),), KitResultClaim.SURVIVAL)
