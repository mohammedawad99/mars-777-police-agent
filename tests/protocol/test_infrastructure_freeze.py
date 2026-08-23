"""The infrastructure freeze, and the interop constants a peer already verified.

Stage E changes one decision function. These tests are what makes that claim
checkable rather than asserted: every byte a peer can observe - the protocol, the
wire, the artifact schema, the agreed digests - is either frozen at a recorded
value or named mutable on purpose.

They are deliberately blunt. A test that reasons about *why* a constant is right
would move with the code that produced it; these compare against numbers written
down when a real opponent confirmed them.
"""

import hashlib
import hmac
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

from check_infrastructure_freeze import MUTABLE, compare, digests, package

from mars777_police.app.kit_messages import KitRole
from mars777_police.app.report_owner import reporting_role
from mars777_police.app.scent_registration import registered_model
from mars777_police.app.series_consensus import consensus_scope, consensus_sha256
from mars777_police.domain.scent_model_default import default_scent_model
from mars777_police.first_role_source import series_first_role
from mars777_police.infra import game_contract
from mars777_police.protocol.canonical import canonical_json_bytes
from mars777_police.protocol.declaration import STEP0_CORE_MEMBERS, step0_core

ROOT = Path(__file__).resolve().parents[2]

STEP0_LEN = 732
STEP0_SHA = "f135f40bcbe5002de423d0508cba49ffef26e0d18525d5f38af00a397601a74f"
STEP0_HMAC = "07246bbe1efa3509b0891f2da78542aa15d44d05390c121ca9ab6f69a5b9731f"
CONTRACT_RAW = "2b401af481725fcf50e9143d44c50ab712b976e688b54cecd061b4546a60fbef"
CONTRACT_CANONICAL = "290b4bcefc3824868d47070eade2564b0ecdb0b78560e163db348000b4caa1fb"
SCENT_REGISTRATION = "934c220d5bf62acaa3297c6c9d723ea954c220260b02292ca17f6d5daef9f4d9"
SETTLED_SERIES = "33f1b2032e8ce87e8bd99de82aac5ebb29943571e2ae583ce4ee2d22f2eeaf1c"
"""A digest a real opponent accepted in a live settlement. Reproduced, never adjusted."""


def test_the_recorded_freeze_matches_the_tree() -> None:
    manifest = json.loads((ROOT / "config/infrastructure_freeze.json").read_text(encoding="utf-8"))
    assert compare(manifest, digests(ROOT)) == []


def test_only_the_competitive_policy_is_mutable() -> None:
    """The reference policy is not mutable: changing it rebases every comparison."""
    assert MUTABLE == ("app/competitive_strategy.py",)


def test_no_mutable_file_is_ever_recorded_as_frozen() -> None:
    """A mutable file need not exist here - one repository ships the baseline.

    What must hold either way is that it is never in the manifest: a strategy
    file recorded as frozen would fail this gate the moment anyone improved it.
    """
    manifest = json.loads((ROOT / "config/infrastructure_freeze.json").read_text(encoding="utf-8"))
    for name in MUTABLE:
        assert (package(ROOT) / name).relative_to(ROOT).as_posix() not in manifest


def test_the_frozen_tree_covers_the_protocol_and_transport_layers() -> None:
    """A freeze that quietly excluded the wire would prove nothing worth proving."""
    manifest = json.loads((ROOT / "config/infrastructure_freeze.json").read_text(encoding="utf-8"))
    for layer in ("protocol/canonical.py", "protocol/declaration.py", "app/series_consensus.py"):
        assert any(path.endswith(layer) for path in manifest), layer


def test_a_changed_frozen_file_is_reported_as_changed() -> None:
    recorded = {"src/pkg/protocol/canonical.py": "a" * 64}
    assert compare(recorded, {"src/pkg/protocol/canonical.py": "b" * 64}) == [
        "CHANGED  src/pkg/protocol/canonical.py"
    ]


def test_an_added_file_is_frozen_by_default() -> None:
    """New infrastructure is a scope change too, and is reported rather than absorbed."""
    problems = compare({}, {"src/pkg/app/new.py": "a" * 64})
    assert problems == ["ADDED    src/pkg/app/new.py (frozen by default; refresh only on purpose)"]


def test_a_removed_file_is_reported_as_removed() -> None:
    assert compare({"src/pkg/app/gone.py": "a" * 64}, {}) == ["REMOVED  src/pkg/app/gone.py"]


def test_the_shared_contract_is_still_the_agreed_bytes() -> None:
    assert game_contract.raw_digest() == CONTRACT_RAW
    assert game_contract.canonical_digest() == CONTRACT_CANONICAL
    assert game_contract.is_frozen()


def test_the_step0_interop_vector_is_still_reproduced() -> None:
    from test_step0_v2_vector import FAKE_SECRET, declaration

    core = canonical_json_bytes(step0_core(declaration(), "MaRs-777"))
    preimage = b"step0" + core
    assert len(preimage) == STEP0_LEN
    assert hashlib.sha256(preimage).hexdigest() == STEP0_SHA
    assert hmac.new(FAKE_SECRET, preimage, hashlib.sha256).hexdigest() == STEP0_HMAC
    assert STEP0_CORE_MEMBERS == 20


def test_the_scent_registration_is_still_the_agreed_one() -> None:
    registration = registered_model(default_scent_model())
    assert registration.model_id == "multiplicative_book_v1"
    assert registration.registration_sha256 == SCENT_REGISTRATION


def test_the_settlement_digest_a_real_peer_accepted_is_still_reproduced() -> None:
    ours, theirs = "MaRs-777", "sparring-s82kma9e"
    rows = [
        {
            "sub_game_number": n,
            "roles": {ours: "police", theirs: "thief"}
            if n % 2
            else {ours: "thief", theirs: "police"},
            "result": "survival" if n % 2 else "capture",
            "score": {ours: 5, theirs: 10 if n % 2 else 20},
        }
        for n in range(1, 7)
    ]
    scope = consensus_scope(f"{ours}-vs-{theirs}", rows, ours, theirs)
    assert consensus_sha256(scope) == SETTLED_SERIES


def test_the_series_arrangement_is_still_the_agreed_one() -> None:
    """Who starts as what, and which of our two processes reports. Both derived."""
    first = series_first_role("MaRs-777", None)
    assert first is KitRole.POLICE
    assert game_contract.first_role_of("s82kma9e") == "thief"
    assert reporting_role(first) is KitRole.THIEF


def test_the_agreed_settlement_window_has_not_moved() -> None:
    assert game_contract.consensus_window() == 400.0
    assert game_contract.consensus_retry() == 2.0


@pytest.mark.parametrize(
    ("member", "value"),
    [("model_id", "multiplicative_book_v1"), ("registration_sha256", SCENT_REGISTRATION)],
)
def test_the_contract_pheromone_identity_is_unchanged(member: str, value: str) -> None:
    assert json.loads(game_contract.contract_bytes())["pheromones"][member] == value
