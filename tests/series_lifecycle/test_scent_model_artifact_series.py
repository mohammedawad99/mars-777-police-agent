"""Six real sub-games, six config artifacts, one scent-model identity.

The series-freeze invariant is a runtime fact until the files are on disk; this
is where it becomes evidence. Every one of `g01`…`g06` is played by two real
agents over the real transport, and each config artifact is then read back and
verified through the production verifier - the model, its digest, and the
authenticated context that names both.
"""

import asyncio
import json
from collections.abc import Iterator
from pathlib import Path

import artifact_evidence_builders as evidence
import pytest
import r7_builders as r7
import test_two_agent_series as live
from r16_builders import GAME_ID

from mars777_police.app.config_artifact_values import ConfigArtifactContent
from mars777_police.artifact_verification import verify_config_artifact
from mars777_police.domain.scent_model_default import default_scent_model
from mars777_police.domain.terminal import Outcome
from mars777_police.protocol.config_lock import config_sha256
from mars777_police.protocol.scent_model import scent_model_sha256

SUB_GAMES = range(1, 7)


@pytest.fixture(scope="module")
def played(tmp_path_factory: pytest.TempPathFactory) -> Iterator[Path]:
    """One real completed six-sub-game series, played once and read many times."""
    root = tmp_path_factory.mktemp("artifact-series")
    a, b = live.pair_for(root)
    asyncio.run(live.run_series(a, b, (Outcome.CAPTURE,) * 5 + (Outcome.SURVIVAL,)))
    for series in (a, b):
        series.persist_result()
    yield root / "police"


def artifact(root: Path, sub_game: int) -> dict[str, object]:
    """One config artifact, read back from disk as an independent reader would."""
    name = f"config_{GAME_ID}_g0{sub_game}.json"
    document = json.loads((root / name).read_text(encoding="utf-8"))
    assert isinstance(document, dict)
    return document


def proved(root: Path, sub_game: int, auth: object) -> ConfigArtifactContent:
    """What that artifact proves, through the production verifier."""
    return verify_config_artifact(artifact(root, sub_game), auth)  # type: ignore[arg-type]


def test_the_series_still_wrote_exactly_the_fourteen_official_files(played: Path) -> None:
    """No fifth family, no sidecar, no partial: the frozen Table-20 set."""
    names = sorted(path.name for path in played.iterdir())
    assert len(names) == 14 and not list(played.glob("*.partial"))
    assert sum(name.startswith("config_") for name in names) == 6
    assert names[:2] == [f"config_{GAME_ID}_g01.json", f"config_{GAME_ID}_g02.json"]


def test_every_sub_game_wrote_its_own_config_artifact(played: Path) -> None:
    for sub_game in SUB_GAMES:
        assert set(artifact(played, sub_game)) == {
            "config",
            "config_lock",
            "scent_model_evidence",
        }


def test_all_six_artifacts_carry_the_frozen_series_model_identity(played: Path) -> None:
    """The invariant, proven from bytes: one model identity for the whole series."""
    stored = set()
    for sub_game in SUB_GAMES:
        section = artifact(played, sub_game)["scent_model_evidence"]
        assert isinstance(section, dict)
        stored.add(section["scent_model_sha256"])
    assert stored == {scent_model_sha256(default_scent_model()).value}


def test_every_artifact_verifies_and_names_its_own_sub_game(played: Path) -> None:
    auth = evidence.authority(live.pair_for(played.parent / "unused")[0])
    for sub_game in SUB_GAMES:
        verified = proved(played, sub_game, auth)
        context = verified.evidence.context
        assert context.sub_game == sub_game
        assert (context.game_id, context.game_uid) == (GAME_ID, r7.GAME_UID)
        assert verified.scent_model == default_scent_model()
        assert context.scent_model_sha256 == scent_model_sha256(verified.scent_model)
        assert context.config_sha256 == config_sha256(verified.config)


def test_the_six_artifacts_share_one_model_and_one_config_core(played: Path) -> None:
    """`r7`'s series relocks one core, so only the sub-game distinguishes them."""
    models = {json.dumps(artifact(played, n)["scent_model_evidence"]) for n in SUB_GAMES}
    cores = {json.dumps(artifact(played, n)["config"]) for n in SUB_GAMES}
    assert len(models) == 1 and len(cores) == 1
    contexts = {json.dumps(artifact(played, n)["config_lock"]) for n in SUB_GAMES}
    assert len(contexts) == 6, "each lock names its own sub-game"
