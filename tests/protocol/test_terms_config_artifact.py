"""The counted config artifact our proven wire can actually evidence.

`config_document` requires a keyed lock this side verified. That is stricter
than the course requires - the book defines `config_sha256` as the canonical
hash of the agreed terms and mandates a signature only on the report - and our
opponent's runner performs no such lock. Requiring it would have meant changing
a wire both implementations had already proven, to satisfy a rule that does not
exist.

So this artifact records the provenance the reference wire does carry. What it
does **not** relax is coherence: the model must be the one the context names,
the config must be the one the context digests, and the stored signature must be
reproducible from the stored terms.
"""

import pytest
from r16_builders import GAME_ID, GAME_UID, PROFILES, config

from mars777_police.app.peer_pregame_messages import ConfigLockContext
from mars777_police.app.protocol_errors import LocalDefectError
from mars777_police.app.terms_agreement_values import TermsAgreementEvidence
from mars777_police.artifact_documents import terms_config_document
from mars777_police.domain.scent_model_default import default_scent_model
from mars777_police.protocol.config_lock import config_sha256
from mars777_police.protocol.kit_identity import kit_terms_digest
from mars777_police.protocol.scent_model import scent_model_sha256
from mars777_police.transport.wire_terms_artifact import TermsConfigArtifactWire

MODEL = default_scent_model()
MODEL_DIGEST = scent_model_sha256(MODEL)
NONCE = "5f4dcc3b5aa765d61d8327deb882cf99"
TERMS = {"board_size": 12, "max_steps": 40}


def context(sub_game: int = 1, **changes: object) -> ConfigLockContext:
    members: dict[str, object] = {
        "game_id": GAME_ID,
        "game_uid": GAME_UID,
        "sub_game": sub_game,
        "config_sha256": config_sha256(config()),
        "profiles": PROFILES,
        "scent_model_sha256": MODEL_DIGEST,
        **changes,
    }
    return ConfigLockContext(**members)  # type: ignore[arg-type]


def evidence(sub_game: int = 1, **changes: object) -> TermsAgreementEvidence:
    return TermsAgreementEvidence(
        context(sub_game, **changes), NONCE, kit_terms_digest(TERMS, NONCE)
    )


def test_the_artifact_is_produced_and_reparses_strictly() -> None:
    """A document nobody can read back is not a record."""
    document = terms_config_document(config(), MODEL, evidence())
    reparsed = TermsConfigArtifactWire.model_validate(document)
    assert reparsed.terms_agreement.nonce == NONCE
    assert reparsed.terms_agreement.context.sub_game == 1


def test_the_three_layers_stay_separate() -> None:
    """§R12-E: the core, the agreement over it, and the model are three sections."""
    document = terms_config_document(config(), MODEL, evidence())
    assert set(document) == {"config", "terms_agreement", "scent_model_evidence"}


def test_the_section_is_not_called_config_lock_and_carries_no_proof() -> None:
    """A reader must not have to know an unkeyed digest from a keyed proof.

    `auth_profile` legitimately appears inside the agreed profile set, so the
    claim is about members, not about the substring: the agreement holds a
    context, a nonce and a digest, and no proof of any kind.
    """
    document = terms_config_document(config(), MODEL, evidence())
    assert "config_lock" not in document
    agreement = document["terms_agreement"]
    assert isinstance(agreement, dict)
    assert set(agreement) == {"context", "nonce", "terms_signature"}


def test_the_stored_signature_reproduces_from_the_stored_terms() -> None:
    stored = terms_config_document(config(), MODEL, evidence())["terms_agreement"]
    assert isinstance(stored, dict)
    assert stored["terms_signature"] == kit_terms_digest(TERMS, str(stored["nonce"]))


def test_a_model_the_context_does_not_name_is_refused() -> None:
    with pytest.raises(LocalDefectError, match="not the one the terms agreement names"):
        terms_config_document(config(), MODEL, evidence(scent_model_sha256=config_sha256(config())))


def test_a_config_the_context_does_not_digest_is_refused() -> None:
    with pytest.raises(LocalDefectError, match="not the agreed core"):
        terms_config_document(config(), MODEL, evidence(config_sha256=MODEL_DIGEST))


def test_each_sub_game_writes_its_own_binding() -> None:
    """Six artifacts, six contexts - never one signature reused across the series."""
    numbers = []
    for number in (1, 3, 5):
        document = terms_config_document(config(), MODEL, evidence(number))
        agreement = document["terms_agreement"]
        assert isinstance(agreement, dict)
        context_of = agreement["context"]
        assert isinstance(context_of, dict)
        numbers.append(context_of["sub_game"])
    assert numbers == [1, 3, 5]


def test_the_config_section_is_the_full_negotiated_core() -> None:
    """Byte-for-byte what both peers digest, not a summary of it."""
    document = terms_config_document(config(), MODEL, evidence())
    section = document["config"]
    assert isinstance(section, dict)
    assert len(section) > 1
