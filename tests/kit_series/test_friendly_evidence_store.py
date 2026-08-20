"""The names development evidence is written under, and the ones it refuses.

The store is the structural half of the honesty: a file that could be mistaken
for a counted artifact is not merely discouraged, it cannot be written. The same
identifier validator the official contract uses guards these names too, so a
path cannot escape through one of them either.
"""

import pytest
from r16_builders import GAME_ID
from test_friendly_evidence import evidence

from mars777_police.app.artifact_store import (
    config_name,
    declaration_name,
    log_name,
    result_name,
)
from mars777_police.app.friendly_evidence import (
    DevelopmentEvidenceStore,
    friendly_series_name,
    friendly_sub_game_name,
    persist_friendly_evidence,
)
from mars777_police.app.kit_messages import KitRole
from mars777_police.app.protocol_errors import LocalDefectError


class _Store:
    def __init__(self) -> None:
        self.written: dict[str, object] = {}

    def store(self, name: str, document: object) -> object:
        self.written[name] = document
        return name


def test_development_names_never_collide_with_the_official_contract() -> None:
    official = {
        declaration_name(GAME_ID),
        result_name(GAME_ID),
        *(config_name(GAME_ID, n) for n in range(1, 7)),
        *(log_name(GAME_ID, n) for n in range(1, 7)),
    }
    ours = {
        friendly_series_name(GAME_ID),
        *(friendly_sub_game_name(GAME_ID, n) for n in range(1, 7)),
    }

    assert official.isdisjoint(ours)


def test_the_development_store_refuses_an_official_filename() -> None:
    """Structural, not remembered: the wrapper cannot write a counted name."""
    store = DevelopmentEvidenceStore(_Store())

    with pytest.raises(LocalDefectError):
        store.store(result_name(GAME_ID), {})


def test_persisting_writes_one_series_document_and_six_sub_game_documents() -> None:
    inner = _Store()

    persist_friendly_evidence(DevelopmentEvidenceStore(inner), evidence())

    assert sorted(inner.written) == sorted(
        [friendly_series_name(GAME_ID), *(friendly_sub_game_name(GAME_ID, n) for n in range(1, 7))]
    )


def test_persisted_evidence_cannot_make_a_run_counted() -> None:
    inner = _Store()
    held = evidence()

    persist_friendly_evidence(DevelopmentEvidenceStore(inner), held)

    assert held.classification.counted_capable is False
    assert held.classification.step0_authenticated is False


def test_each_role_contribution_has_its_own_development_filename() -> None:
    """Two backends write two files, and neither is a counted name."""
    from mars777_police.app.friendly_merge import friendly_contribution_name

    police = friendly_contribution_name(GAME_ID, KitRole.POLICE)
    thief = friendly_contribution_name(GAME_ID, KitRole.THIEF)

    assert police != thief
    assert police.startswith("friendly_") and thief.startswith("friendly_")
    assert police.endswith("_police.json") and thief.endswith("_thief.json")


def test_the_development_bundle_shares_the_one_identifier_validator() -> None:
    """One semantic `game_id`, one lexical rule.

    Stage 8A-2F needed a separate development check because the counted namer
    was lowercase-only and could not express a kit-derived id containing our own
    `MaRs-777`. Stage 8A-2G amended that format - it is PROJECT-CONTRACT, not
    source-fixed - so the second validator has no reason to exist and is gone.
    The development *filenames* stay separate; only the id rule is shared.
    """
    from mars777_police.app.artifact_store import require_game_id
    from mars777_police.app.friendly_evidence import friendly_series_name

    kit_game_id = "MaRs-777-vs-sparring-local"

    assert require_game_id(kit_game_id) == kit_game_id
    assert friendly_series_name(kit_game_id) == f"friendly_{kit_game_id}.json"


def test_a_development_name_still_refuses_anything_a_path_could_escape_through() -> None:
    from mars777_police.app.artifact_store import InvalidArtifactNameError
    from mars777_police.app.friendly_evidence import friendly_series_name

    for unsafe in ("../escape", "with/slash", "with space", ""):
        with pytest.raises(InvalidArtifactNameError):
            friendly_series_name(unsafe)
