"""The second lawful provenance for a config artifact, and its limits.

Our own counted path proves a sub-game's configuration with a keyed lock. The
opponent's does not, and the course book does not require one: `config_sha256`
is defined there as the canonical hash of the agreed terms, and the only
mandatory signed artifact is the report. These tests pin the weaker-but-lawful
form so it can be recorded honestly - and pin, just as hard, that it is never
allowed to look like authentication.
"""

import pytest
from r16_builders import GAME_ID, GAME_UID, PROFILES, config

from mars777_police.app.peer_pregame_messages import ConfigLockContext
from mars777_police.app.protocol_errors import LocalDefectError
from mars777_police.app.terms_agreement_values import TermsAgreementEvidence
from mars777_police.domain.scent_model_default import default_scent_model
from mars777_police.protocol.config_lock import config_sha256
from mars777_police.protocol.kit_identity import kit_terms_digest
from mars777_police.protocol.scent_model import scent_model_sha256

MODEL_DIGEST = scent_model_sha256(default_scent_model())
NONCE = "5f4dcc3b5aa765d61d8327deb882cf99"
TERMS = {"board_size": 12, "max_steps": 40, "hint_max_words": 12}


def context(sub_game: int = 1) -> ConfigLockContext:
    return ConfigLockContext(
        GAME_ID, GAME_UID, sub_game, config_sha256(config()), PROFILES, MODEL_DIGEST
    )


def evidence(sub_game: int = 1, nonce: str = NONCE, terms: object = None) -> TermsAgreementEvidence:
    body = TERMS if terms is None else terms
    return TermsAgreementEvidence(context(sub_game), nonce, kit_terms_digest(body, nonce))


def test_the_stored_signature_reproduces_from_the_stored_terms() -> None:
    """The whole point of recording it: the record can be checked, not trusted."""
    assert evidence().reproduces(TERMS)


def test_terms_that_differ_by_one_value_do_not_reproduce() -> None:
    assert not evidence().reproduces({**TERMS, "max_steps": 41})


def test_a_different_nonce_does_not_reproduce_the_same_signature() -> None:
    """Nonce-bound means bound: the same terms under another nonce is another game."""
    other = TermsAgreementEvidence(context(), "0" * 32, kit_terms_digest(TERMS, "0" * 32))
    assert other.reproduces(TERMS)
    assert other.terms_signature != evidence().terms_signature


def test_each_sub_game_carries_its_own_binding() -> None:
    """A signature valid for every sub-game would prove nothing about this one."""
    assert evidence(1).context.sub_game == 1
    assert evidence(3).context.sub_game == 3


def test_the_context_still_binds_the_config_and_model_digests() -> None:
    """The weaker proof does not mean a weaker binding: the same context is kept."""
    bound = evidence().context
    assert bound.config_sha256 == config_sha256(config())
    assert bound.scent_model_sha256 == MODEL_DIGEST
    assert bound.game_id == GAME_ID and bound.game_uid == GAME_UID


def test_an_empty_nonce_is_refused() -> None:
    with pytest.raises(LocalDefectError, match="non-empty nonce"):
        TermsAgreementEvidence(context(), "", kit_terms_digest(TERMS, NONCE))


@pytest.mark.parametrize(
    "signature",
    ["", "abc", "z" * 64, kit_terms_digest(TERMS, NONCE).upper(), "0" * 63],
    ids=["empty", "too short", "not hex", "uppercase", "one short"],
)
def test_a_malformed_signature_is_refused(signature: str) -> None:
    """Sixty-four lowercase hex characters, or it is not a digest we can compare."""
    with pytest.raises(LocalDefectError):
        TermsAgreementEvidence(context(), NONCE, signature)


def test_a_signature_that_is_not_text_is_refused() -> None:
    with pytest.raises(LocalDefectError, match="is text"):
        TermsAgreementEvidence(context(), NONCE, 12345)  # type: ignore[arg-type]


def test_this_evidence_carries_no_key_and_claims_no_identity() -> None:
    """The line that must never blur: agreement is not authentication.

    Anyone holding the terms and the nonce reproduces this digest, so it says
    nothing about who spoke. Identity comes from the authenticated Step-0, once
    per series, and this must never be offered in its place.
    """
    stored = evidence()
    assert not hasattr(stored, "auth")
    assert stored.terms_signature == kit_terms_digest(TERMS, stored.nonce), (
        "a third party with only public values must be able to recompute it"
    )
