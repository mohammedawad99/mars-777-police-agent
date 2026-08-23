"""Reading the settlement terms out of the frozen contract, and refusing bad ones.

The window, the retry cadence and the scent registration are all *agreed*
numbers: one side shortening a window or inventing a digest is a side that fails
to settle with a peer that did neither. So every one of them is read from the
agreement, and a member the agreement cannot supply is refused rather than
defaulted.
"""

import json
from pathlib import Path

import pytest

from mars777_police.infra import game_contract


def test_the_contract_supplies_both_agreed_settlement_numbers() -> None:
    assert game_contract.consensus_window() == 400.0
    assert game_contract.consensus_retry() == 2.0


@pytest.mark.parametrize(
    ("section", "member", "value"),
    [
        ("series_protocol", "consensus_timeout_sec", 0),
        ("series_protocol", "consensus_retry_sec", -1),
        ("pheromones", "model_id", ""),
        ("pheromones", "registration_sha256", "short"),
    ],
)
def test_an_unusable_contract_member_is_refused_rather_than_guessed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, section: str, member: str, value: object
) -> None:
    document = json.loads(game_contract.contract_bytes())
    document[section][member] = value
    broken = tmp_path / "broken.json"
    broken.write_text(json.dumps(document), encoding="utf-8")
    monkeypatch.setenv(game_contract.CONTRACT_OVERRIDE, str(broken))
    reader = {
        "consensus_timeout_sec": game_contract.consensus_window,
        "consensus_retry_sec": game_contract.consensus_retry,
        "model_id": game_contract.scent_registration,
        "registration_sha256": game_contract.scent_registration,
    }[member]
    with pytest.raises(KeyError):
        reader()


def test_a_contract_missing_a_fixed_pheromone_value_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    document = json.loads(game_contract.contract_bytes())
    del document["pheromones"]["pheromone_decay"]
    broken = tmp_path / "missing.json"
    broken.write_text(json.dumps(document), encoding="utf-8")
    monkeypatch.setenv(game_contract.CONTRACT_OVERRIDE, str(broken))
    with pytest.raises(KeyError, match="omits a FIXED pheromone value"):
        game_contract.scent_parameters()
