"""Step0DeclarationExchange and ConfigProposal semantic composition."""

import dataclasses
import sys

import pytest
from pregame_builders import declaration, profiles, proof

from mars777_police.app.auth_values import AuthProfile
from mars777_police.app.peer_pregame_messages import (
    ConfigProposal,
    InvalidPregameMessageError,
    Step0DeclarationExchange,
)

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1] / "domain"))
from config_builders import config


def test_valid_step0_exchange() -> None:
    value = Step0DeclarationExchange(declaration(), proof())
    assert value.auth.profile is AuthProfile.HMAC_SHA256
    assert value.declaration.game_uid == "uid0001"


def test_step0_exchange_field_order() -> None:
    assert [f.name for f in dataclasses.fields(Step0DeclarationExchange)] == [
        "declaration",
        "auth",
    ]


def test_step0_exchange_carries_no_turn_or_phase_member() -> None:
    names = {f.name for f in dataclasses.fields(Step0DeclarationExchange)}
    assert not names & {"sub_game", "step", "phase", "cursor", "accepted", "timestamp"}


def test_step0_exchange_is_immutable() -> None:
    with pytest.raises(dataclasses.FrozenInstanceError):
        Step0DeclarationExchange(declaration(), proof()).auth = proof()  # type: ignore[misc]


def test_step0_exchange_rejects_raw_declaration() -> None:
    with pytest.raises(InvalidPregameMessageError, match="declaration must be a Declaration"):
        Step0DeclarationExchange({"game_id": "g"}, proof())  # type: ignore[arg-type]


def test_step0_exchange_rejects_raw_auth() -> None:
    with pytest.raises(InvalidPregameMessageError, match="auth must be a AuthProof"):
        Step0DeclarationExchange(declaration(), "a" * 64)  # type: ignore[arg-type]


def test_valid_config_proposal() -> None:
    value = ConfigProposal(1, config(), profiles())
    assert value.sub_game == 1
    assert value.config.schema_version == "mars777-1"


def test_config_proposal_field_order() -> None:
    """The full agreed scent model rides last, and only when there is one."""
    assert [f.name for f in dataclasses.fields(ConfigProposal)] == [
        "sub_game",
        "config",
        "profiles",
        "scent_model",
    ]
    assert ConfigProposal(1, config(), profiles()).scent_model is None


@pytest.mark.parametrize("bad", [True, "1", 1.0, None])
def test_config_proposal_sub_game_is_strict_int(bad: object) -> None:
    with pytest.raises(InvalidPregameMessageError, match="sub_game must be an int"):
        ConfigProposal(bad, config(), profiles())  # type: ignore[arg-type]


def test_config_proposal_sub_game_floor() -> None:
    assert ConfigProposal(1, config(), profiles()).sub_game == 1
    with pytest.raises(InvalidPregameMessageError, match="sub_game must be >= 1"):
        ConfigProposal(0, config(), profiles())


def test_config_proposal_rejects_raw_config() -> None:
    with pytest.raises(InvalidPregameMessageError, match="config must be a NegotiatedConfig"):
        ConfigProposal(1, {"schema_version": "x"}, profiles())  # type: ignore[arg-type]


def test_config_proposal_rejects_raw_profiles() -> None:
    with pytest.raises(InvalidPregameMessageError, match="profiles must be a InteropProfileSet"):
        ConfigProposal(1, config(), {"auth_profile": "HMAC_SHA256"})  # type: ignore[arg-type]


def test_config_proposal_is_immutable() -> None:
    with pytest.raises(dataclasses.FrozenInstanceError):
        ConfigProposal(1, config(), profiles()).sub_game = 2  # type: ignore[misc]
