"""Real config artifacts on disk, and the authority a reader verifies them with.

Nothing here builds a document by hand. A real pair negotiates, really locks and
lets `SeriesRuntime` write the file, so what the tests read back is exactly what
production would leave behind.
"""

import copy
import json
from pathlib import Path

import r7_builders as r7
import series_freeze_builders as freeze
from r16_builders import GAME_ID

from mars777_police.app.artifact_store import ArtifactDocument
from mars777_police.app.ports import ConfigLockAuthPort
from mars777_police.domain.scent_model import ScentModelAgreement
from mars777_police.series_runtime import SeriesRuntime

NAME = f"config_{GAME_ID}_g01.json"
"""The one artifact a single-round harness writes; six of them need six rounds."""


def locked_pair(
    root: Path, model: ScentModelAgreement | None = None
) -> tuple[SeriesRuntime, SeriesRuntime]:
    """Two real agents that negotiated and verified `g01`'s lock on *model*."""
    a, b = freeze.pair(root)
    freeze.lock(a, b, 1, model)
    return a, b


def written(root: Path, model: ScentModelAgreement | None = None) -> SeriesRuntime:
    """One real series that locked `g01` and wrote its config artifact."""
    series, _ = locked_pair(root, model)
    series.lock_config(r7.CONFIG)
    return series


def read_artifact(root: Path, name: str = NAME) -> dict[str, object]:
    """Read one artifact back from disk exactly as an independent reader would."""
    document = json.loads((root / "police" / name).read_text(encoding="utf-8"))
    assert isinstance(document, dict)
    return document


def authority(series: SeriesRuntime) -> ConfigLockAuthPort:
    """The provisioned verification authority - never carried by the artifact."""
    return series.composition.pregame.lock.auth


def tampered(document: ArtifactDocument, path: tuple[str, ...], value: object) -> ArtifactDocument:
    """A copy of *document* with one nested member replaced."""
    changed = copy.deepcopy(dict(document))
    target: dict[str, object] = changed
    for key in path[:-1]:
        section = target[key]
        assert isinstance(section, dict)
        target = section
    target[path[-1]] = value
    return changed
