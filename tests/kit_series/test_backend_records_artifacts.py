"""The production play path itself creating and contributing official documents.

Standalone writer tests prove the documents can be built. They do not prove the
backend builds them, and a writer nothing calls is not a record - the same
lesson a rehearsal already taught this project about a guard nothing calls.

The other half is the deliberate silence: a development friendly given no
profile set contributes nothing rather than guessing one, so every existing
friendly keeps behaving exactly as it did.
"""

import asyncio

import pytest
from artifact_recording_doubles import (
    CONTRIBUTED,
    NONCE,
    artifacts,
    disclosure,
    greeting,
    record,
)
from kit_backend_builders import backend
from kit_backend_doubles import _pairing

from mars777_police.app.kit_backend_artifacts import BackendArtifacts
from mars777_police.app.kit_messages import KitRole
from mars777_police.app.official_artifacts import CONFIG, LOG
from mars777_police.app.sealed_record_values import ActorRole


@pytest.fixture(autouse=True)
def _clear() -> None:
    CONTRIBUTED.clear()


def drive(held: BackendArtifacts, sub_game: int = 1) -> bool:
    """Call the collaborator exactly as `play_sub_game` calls it."""
    kept: bool = asyncio.run(
        held.record(
            pairing=_pairing(),
            sub_game=sub_game,
            greeting=greeting(),
            ours=(record(1, ActorRole.POLICE),),
            disclosure=disclosure(),
            peer_verified=True,
            result="survival",
        )
    )
    return kept


def test_a_wired_backend_contributes_both_documents_for_a_sub_game() -> None:
    drive(artifacts())
    assert [(kind, number) for kind, number, _ in CONTRIBUTED] == [(CONFIG, 1), (LOG, 1)]


def test_the_config_precedes_the_log_for_each_sub_game() -> None:
    """The order the sub-game produced them, so a reader follows the same story."""
    held = artifacts()
    for number in (1, 3):
        drive(held, number)
    assert [(kind, number) for kind, number, _ in CONTRIBUTED] == [
        (CONFIG, 1),
        (LOG, 1),
        (CONFIG, 3),
        (LOG, 3),
    ]


def test_the_contributed_documents_are_the_real_ones() -> None:
    """Not placeholders: the config carries the agreement, the log both chains."""
    drive(artifacts())
    kinds = {kind: document for kind, _, document in CONTRIBUTED}
    assert set(kinds[CONFIG]) == {"config", "terms_agreement", "scent_model_evidence"}
    assert kinds[CONFIG]["terms_agreement"]["nonce"] == NONCE
    assert {entry["role"] for entry in kinds[LOG]["entries"]} == {"police", "thief"}


def test_the_record_never_states_a_profile_set_nobody_agreed() -> None:
    """Our commitment codec has no representation in the frozen profile wire.

    That is not an omission to work around: the reference wire never negotiated
    a profile set, so recording our own local selection would assert an
    agreement neither side made.
    """
    drive(artifacts())
    agreement = {kind: document for kind, _, document in CONTRIBUTED}[CONFIG]["terms_agreement"]
    assert "profiles" not in agreement["context"]
    assert set(agreement["context"]) == {
        "game_id",
        "game_uid",
        "sub_game",
        "config_sha256",
        "scent_model_sha256",
    }


def test_a_friendly_with_no_profile_set_contributes_nothing() -> None:
    """Existing development friendlies keep behaving exactly as they did."""
    assert drive(artifacts(silent=True)) is False
    assert CONTRIBUTED == []


def test_a_backend_wired_to_no_group_refuses_rather_than_dropping_documents() -> None:
    """The refusal default: silence about a missing sink would lose the record."""
    with pytest.raises(Exception, match="never given a group"):
        drive(artifacts(wired=False))


def test_the_production_backend_carries_an_artifact_collaborator() -> None:
    """The field exists on the real backend, defaulted to silence."""
    held = backend(KitRole.POLICE)
    assert isinstance(held.artifacts, BackendArtifacts)
    assert held.artifacts.profiles is None
