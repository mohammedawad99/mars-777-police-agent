"""One real played sub-game, written to disk by production, for a viewer to read.

Nothing is hand-built: two composed agents play a scripted sub-game through the
production runners, and what the tests read back is the official log and config
those runners wrote.
"""

import json
from pathlib import Path

import semantic_disk_harness as harness
from r16_builders import GAME_ID

from mars777_police.app.artifact_store import log_name
from mars777_police.domain.actions import MoveAction
from mars777_police.domain.rules import Move

STEPS = harness.steps_of((MoveAction(Move.S), None), (MoveAction(Move.S), None))
"""Two ordinary police moves: a sub-game with nothing to find."""


def played(root: Path) -> tuple[Path, Path]:
    """Play the sub-game and return the police log and config artifact paths."""
    harness.run(root, STEPS)
    return root / "police" / log_name(GAME_ID, 1), root / "police" / f"config_{GAME_ID}_g01.json"


def rewritten(path: Path, change: object) -> Path:
    """Write *change* over *path*, so a test can hand the viewer a doctored file."""
    path.write_text(json.dumps(change), encoding="utf-8")
    return path


def document(path: Path) -> dict[str, object]:
    """Read one artifact back as plain JSON."""
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return loaded
