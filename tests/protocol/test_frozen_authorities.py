"""Every value two teams agreed, asserted against the agreement itself.

These are not internal constants. Each one is something the opponent verifies
independently, so drift here is not a failing test locally - it is a series that
cannot start, or worse, one that starts and disagrees. They are gathered in one
place because that is how an operator confirms the build is still the agreed
build without reading six modules.

The superseded Step-0 vector is asserted **absent** from the runtime rather than
merely unused: an obsolete authority that still exists somewhere reachable is an
authority that can come back.
"""

import json
from pathlib import Path

from mars777_police.infra.game_contract import (
    CANONICAL_SHA256,
    RAW_SHA256,
    canonical_digest,
    consensus_retry,
    consensus_window,
    contract_bytes,
    is_frozen,
    raw_digest,
)

SRC = Path(__file__).resolve().parents[2] / "src"
CONFIG = Path(__file__).resolve().parents[2] / "config"

SUPERSEDED = (
    "94aba7f9",
    "283cca6c",
    "PREIMAGE_LEN = 734",
)
"""The retired Step-0 vector. Absent from the runtime, not merely unreferenced."""


def contract() -> dict[str, object]:
    document = json.loads(contract_bytes())
    assert isinstance(document, dict)
    return document


def test_the_shipped_contract_is_the_agreed_bytes() -> None:
    assert (
        raw_digest()
        == RAW_SHA256
        == ("2b401af481725fcf50e9143d44c50ab712b976e688b54cecd061b4546a60fbef")
    )
    assert (
        canonical_digest()
        == CANONICAL_SHA256
        == ("290b4bcefc3824868d47070eade2564b0ecdb0b78560e163db348000b4caa1fb")
    )
    assert is_frozen()


def test_the_slot_layout_is_the_one_the_pairing_derived() -> None:
    """Unicode code-point order: `M` precedes `s`, so MaRs takes group_a."""
    step_zero = contract()["step_zero"]
    assert isinstance(step_zero, dict)
    assert step_zero["group_slots"] == {"group_a": "MaRs-777", "group_b": "s82kma9e"}


def test_the_role_convention_is_the_reference_alternation() -> None:
    series = contract()["series_protocol"]
    assert isinstance(series, dict)
    assert series["role_convention"] == "REFERENCE_ODD_EVEN_ALTERNATION"
    assert series["thief_sends_first"] is True


def test_the_agreed_timeouts_are_unchanged() -> None:
    network = contract()["network_and_league"]
    assert isinstance(network, dict)
    assert network["response_timeout_sec"] == 30
    assert network["watchdog_timeout_sec"] == 60


def test_the_settlement_window_is_four_hundred_seconds_every_two() -> None:
    """Changing either unilaterally desynchronises a settlement both sides wait on."""
    assert consensus_window() == 400.0
    assert consensus_retry() == 2.0


def test_the_scent_registration_digest_is_the_registered_one() -> None:
    pheromones = contract()["pheromones"]
    assert isinstance(pheromones, dict)
    assert pheromones["registration_sha256"] == (
        "934c220d5bf62acaa3297c6c9d723ea954c220260b02292ca17f6d5daef9f4d9"
    )


def test_the_superseded_step0_vector_is_absent_from_the_runtime() -> None:
    """An obsolete authority that still exists somewhere reachable can come back."""
    found: list[str] = []
    for root in (SRC, CONFIG):
        for path in root.rglob("*"):
            if path.suffix not in (".py", ".json") or not path.is_file():
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            found += [f"{path.name}:{token}" for token in SUPERSEDED if token in text]
    assert found == []
