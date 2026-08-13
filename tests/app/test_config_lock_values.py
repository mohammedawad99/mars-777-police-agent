"""ConfigLockContext and the ConfigLockEvidence self-consistency invariant."""

import dataclasses

import pytest
from pregame_builders import KEY, profiles, proof

from mars777_police.app.auth_values import AuthProfile, AuthProof, KeyId
from mars777_police.app.peer_pregame_messages import (
    ConfigLockContext,
    ConfigLockEvidence,
    InvalidPregameMessageError,
)
from mars777_police.app.protocol_values import Sha256Digest

DIGEST = Sha256Digest("c" * 64)
MODEL_DIGEST = Sha256Digest("d" * 64)
"""The agreed model's identity - a different digest, bound in the same context."""


def context(**over: object) -> ConfigLockContext:
    fields: dict[str, object] = {
        "game_id": "mars777-g1",
        "game_uid": "uid0001",
        "sub_game": 1,
        "config_sha256": DIGEST,
        "profiles": profiles(),
        "scent_model_sha256": MODEL_DIGEST,
    }
    fields.update(over)
    return ConfigLockContext(**fields)  # type: ignore[arg-type]


def test_valid_context() -> None:
    assert context().config_sha256 is DIGEST


def test_context_field_order() -> None:
    """The agreed model's identity rides last, beside the config's own."""
    assert [f.name for f in dataclasses.fields(ConfigLockContext)] == [
        "game_id",
        "game_uid",
        "sub_game",
        "config_sha256",
        "profiles",
        "scent_model_sha256",
    ]


def test_the_scent_model_digest_must_be_a_real_digest() -> None:
    with pytest.raises(InvalidPregameMessageError, match="scent_model_sha256 must be a"):
        context(scent_model_sha256="d" * 64)


def test_context_carries_no_auth_or_full_config() -> None:
    names = {f.name for f in dataclasses.fields(ConfigLockContext)}
    assert not names & {"auth", "config", "config_auth", "key"}


@pytest.mark.parametrize("field", ["game_id", "game_uid"])
@pytest.mark.parametrize("bad", [None, 1])
def test_context_identity_must_be_str(field: str, bad: object) -> None:
    with pytest.raises(InvalidPregameMessageError, match=f"{field} must be a str"):
        context(**{field: bad})


@pytest.mark.parametrize("field", ["game_id", "game_uid"])
def test_context_identity_must_be_non_empty(field: str) -> None:
    with pytest.raises(InvalidPregameMessageError, match=f"{field} must be non-empty"):
        context(**{field: ""})


def test_context_sub_game_floor() -> None:
    with pytest.raises(InvalidPregameMessageError, match="sub_game must be >= 1"):
        context(sub_game=0)


def test_context_rejects_raw_digest_string() -> None:
    with pytest.raises(InvalidPregameMessageError, match="config_sha256 must be a Sha256Digest"):
        context(config_sha256="c" * 64)


def test_context_rejects_raw_profiles() -> None:
    with pytest.raises(InvalidPregameMessageError, match="profiles must be a InteropProfileSet"):
        context(profiles={"auth_profile": "HMAC_SHA256"})


def test_valid_evidence_when_profile_and_key_agree() -> None:
    value = ConfigLockEvidence(context(), proof())
    assert value.auth.profile is value.context.profiles.auth_profile
    assert value.auth.key_id == value.context.profiles.key_id


def test_evidence_field_order() -> None:
    assert [f.name for f in dataclasses.fields(ConfigLockEvidence)] == ["context", "auth"]


def test_evidence_rejects_profile_mismatch() -> None:
    with pytest.raises(InvalidPregameMessageError, match=r"auth\.profile must equal"):
        ConfigLockEvidence(context(), proof(profile=AuthProfile.ED25519))


def test_evidence_rejects_key_id_mismatch() -> None:
    with pytest.raises(InvalidPregameMessageError, match=r"auth\.key_id must equal"):
        ConfigLockEvidence(context(), proof(key=KeyId("other-key")))


def test_evidence_accepts_a_matching_ed25519_pair() -> None:
    ed_profiles = profiles(auth_profile=AuthProfile.ED25519)
    evidence = ConfigLockEvidence(
        context(profiles=ed_profiles),
        AuthProof(AuthProfile.ED25519, KEY, "d" * 128),
    )
    assert evidence.auth.profile is AuthProfile.ED25519


def test_evidence_rejects_raw_context() -> None:
    with pytest.raises(InvalidPregameMessageError, match="context must be a ConfigLockContext"):
        ConfigLockEvidence({"game_id": "g"}, proof())  # type: ignore[arg-type]


def test_evidence_rejects_raw_auth() -> None:
    with pytest.raises(InvalidPregameMessageError, match="auth must be a AuthProof"):
        ConfigLockEvidence(context(), "a" * 64)  # type: ignore[arg-type]


def test_evidence_is_immutable_and_has_no_ack_member() -> None:
    names = {f.name for f in dataclasses.fields(ConfigLockEvidence)}
    assert not names & {"accepted", "ok", "timestamp", "phase", "score"}
    with pytest.raises(dataclasses.FrozenInstanceError):
        ConfigLockEvidence(context(), proof()).auth = proof()  # type: ignore[misc]
