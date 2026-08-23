"""One played sub-game becoming the two official documents it owes.

The backend that played it is the only process holding what those documents are
made of. These tests pin that they are built from what actually happened - the
greeting's own terms and nonce, the chain we sealed, the chain the peer
disclosed - and that a sub-game missing any of it produces a refusal rather
than a plausible-looking file.
"""

import pytest
from r16_builders import GAME_ID, GAME_UID, PROFILES, config

from mars777_police.app.kit_artifact_build import sub_game_artifacts, terms_evidence
from mars777_police.app.kit_greeting import KitGreeting
from mars777_police.app.kit_messages import KitAuditReveal, KitRecord, KitResultClaim, KitRole
from mars777_police.app.kit_payload import PeerPayload, kit_payload
from mars777_police.app.peer_pregame_messages import ConfigLockContext
from mars777_police.app.protocol_errors import LocalDefectError
from mars777_police.app.protocol_values import Sha256Digest
from mars777_police.app.sealed_record_values import ActorRole, Intent
from mars777_police.app.turn_cursor import TurnCursor
from mars777_police.artifact_documents import terms_config_document
from mars777_police.domain.actions import MoveAction
from mars777_police.domain.board import Position
from mars777_police.domain.rules import Move
from mars777_police.domain.scent_model_default import default_scent_model
from mars777_police.protocol.commitment_codec import CommitmentCodec, commitment_for
from mars777_police.protocol.config_lock import config_sha256
from mars777_police.protocol.kit_identity import kit_terms_digest
from mars777_police.protocol.scent_model import scent_model_sha256

MODEL = default_scent_model()
MODEL_DIGEST = scent_model_sha256(MODEL)
NONCE = "5f4dcc3b5aa765d61d8327deb882cf99"
TERMS = {"board_size": 12, "max_steps": 40}
CODEC = CommitmentCodec.KIT_CORE_COMMITMENT_V1


def context(sub_game: int = 1) -> ConfigLockContext:
    return ConfigLockContext(
        GAME_ID, GAME_UID, sub_game, config_sha256(config()), PROFILES, MODEL_DIGEST
    )


def greeting(nonce: str = NONCE) -> KitGreeting:
    return KitGreeting(
        PeerPayload(TERMS), nonce, kit_terms_digest(TERMS, nonce), "s82kma9e", KitRole.THIEF, 1
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


def built(**changes: object) -> object:
    members: dict[str, object] = {
        "sub_game": 1,
        "greeting": greeting(),
        "context": context(),
        "config": config(),
        "model": MODEL,
        "ours": (record(1, ActorRole.POLICE),),
        "disclosure": KitAuditReveal(
            KitRole.THIEF, (record(1, ActorRole.THIEF),), KitResultClaim.SURVIVAL
        ),
        "peer_verified": True,
        "result": "survival",
        "build_config": terms_config_document,
        **changes,
    }
    return sub_game_artifacts(**members)  # type: ignore[arg-type]


def test_a_played_sub_game_owes_exactly_a_config_and_a_log() -> None:
    made = built()
    assert made.sub_game == 1  # type: ignore[attr-defined]
    assert set(made.config) == {"config", "terms_agreement", "scent_model_evidence"}  # type: ignore[attr-defined]
    assert set(made.log) >= {"game_id", "game_uid", "sub_game", "config_sha256", "entries"}  # type: ignore[attr-defined]


def test_the_signature_recorded_is_the_one_the_greeting_sent() -> None:
    """Recomputing it would record our own canonicalization, not the peer's claim."""
    sent = greeting()
    evidence = terms_evidence(greeting=sent, context=context())
    assert evidence.terms_signature == sent.signature
    assert evidence.nonce == sent.nonce


def test_the_recorded_agreement_still_reproduces_from_the_terms() -> None:
    assert terms_evidence(greeting=greeting(), context=context()).reproduces(TERMS)


def test_a_sub_game_with_no_greeting_is_refused() -> None:
    """No recorded agreement means the config artifact would state one nobody made."""
    with pytest.raises(LocalDefectError, match="no recorded greeting"):
        built(greeting=None)


def test_a_context_for_another_sub_game_is_refused() -> None:
    with pytest.raises(LocalDefectError, match="names sub-game 3, not 1"):
        built(context=context(3))


def test_a_sub_game_with_no_disclosure_is_refused() -> None:
    """The log builder's own refusal travels rather than being swallowed here."""
    with pytest.raises(LocalDefectError, match="only after this sub-game was audited"):
        built(disclosure=None)


def test_the_log_carries_both_chains_not_only_ours() -> None:
    entries = built().log["entries"]  # type: ignore[attr-defined]
    roles = {entry["role"] for entry in entries}
    assert roles == {"police", "thief"}
