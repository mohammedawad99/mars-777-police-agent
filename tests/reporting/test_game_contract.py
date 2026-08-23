"""The frozen shared game contract, and the drift it must never tolerate.

Both peers agreed these exact bytes, and the pre-game exchange refuses to play on
any mismatch - so a reformat, a reordered key or a tidied sentence is a breaking
change even though no value moved. These tests exist to make that failure loud
here rather than at the opponent's handshake.
"""

import json
from pathlib import Path

import pytest

from mars777_police.infra import game_contract


def test_the_shipped_contract_still_has_the_agreed_raw_digest() -> None:
    assert game_contract.raw_digest() == game_contract.RAW_SHA256


def test_the_shipped_contract_still_has_the_agreed_canonical_digest() -> None:
    assert game_contract.canonical_digest() == game_contract.CANONICAL_SHA256


def test_the_two_digests_are_different_domains() -> None:
    """Neither digest is derived from the other, so they must not coincide."""
    assert game_contract.RAW_SHA256 != game_contract.CANONICAL_SHA256


def test_reformatting_the_file_breaks_the_raw_digest(tmp_path: Path) -> None:
    """The raw digest covers the bytes, so pretty-printing is a real change."""
    document = json.loads(game_contract.contract_bytes())
    reformatted = tmp_path / "reformatted.json"
    reformatted.write_text(json.dumps(document, indent=4), encoding="utf-8")
    assert game_contract.raw_digest(reformatted) != game_contract.RAW_SHA256
    assert game_contract.canonical_digest(reformatted) == game_contract.CANONICAL_SHA256


def test_changing_one_value_breaks_both_digests(tmp_path: Path) -> None:
    document = json.loads(game_contract.contract_bytes())
    document["world"]["hint_max_words"] = 16
    altered = tmp_path / "altered.json"
    altered.write_text(json.dumps(document), encoding="utf-8")
    assert game_contract.raw_digest(altered) != game_contract.RAW_SHA256
    assert game_contract.canonical_digest(altered) != game_contract.CANONICAL_SHA256


def test_the_contract_carries_the_agreed_pairing_terms() -> None:
    """A digest proves bytes; these are the values the pairing actually froze."""
    document = json.loads(game_contract.contract_bytes())
    assert document["agreed_between"] == ["MaRs-777", "s82kma9e"]
    assert document["series_protocol"]["role_convention"] == "REFERENCE_ODD_EVEN_ALTERNATION"
    assert document["step_zero"]["group_slots"] == {"group_a": "MaRs-777", "group_b": "s82kma9e"}
    assert document["network_and_league"]["token_budget_per_series"] == 200000
    assert document["pheromones"]["registration_sha256"] == (
        "934c220d5bf62acaa3297c6c9d723ea954c220260b02292ca17f6d5daef9f4d9"
    )


def test_the_vestigial_pheromone_minimum_is_absent() -> None:
    """Removed in the final round: nothing on either side consumes it."""
    document = json.loads(game_contract.contract_bytes())
    assert "pheromone_min_center_intensity" not in document["pheromones"]


def test_the_shipped_contract_is_the_frozen_one() -> None:
    assert game_contract.is_frozen()
    assert game_contract.contract_path() == game_contract.SHIPPED_PATH


def test_an_override_is_detectable_and_never_silent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The override exists for synthetic pairings and cannot pass as the agreement.

    A counted entrypoint asks `is_frozen()`; a substituted contract answers no,
    so it can be refused rather than played.
    """
    document = json.loads(game_contract.contract_bytes())
    document["series_protocol"]["sub_game_1_roles"] = {"a": "police", "b": "thief"}
    other = tmp_path / "synthetic.json"
    other.write_text(json.dumps(document), encoding="utf-8")

    monkeypatch.setenv(game_contract.CONTRACT_OVERRIDE, str(other))
    assert game_contract.contract_path() == other
    assert not game_contract.is_frozen()
    assert game_contract.first_role_of("a") == "police"


def test_the_frozen_agreement_names_only_the_real_pairing() -> None:
    """Fail-closed proof: an unknown group has no role, and none is invented."""
    assert game_contract.first_role_of("MaRs-777") == "police"
    assert game_contract.first_role_of("s82kma9e") == "thief"
    with pytest.raises(KeyError):
        game_contract.first_role_of("GROUP-XY")
