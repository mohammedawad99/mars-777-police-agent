"""The locked scent world these app tests interpret, built from the real model.

Duplicated per test directory on purpose, exactly as `r16_builders` is:
`tests/app` has no package, so it owns the helpers it imports rather than
reaching into another directory's module. Every value below is the production
default model's own - `default_scent_model()` is the authority, so a fixture
cannot drift from the physics it is meant to exercise.
"""

from mars777_police.app.scent_records import ScentRecord
from mars777_police.app.turn_cursor import TurnCursor
from mars777_police.domain.board import Position
from mars777_police.domain.config_model import GridConfig
from mars777_police.domain.scent_model_default import default_scent_model
from mars777_police.domain.scent_observation import emission_of

MODEL = default_scent_model()
"""The agreed model, read rather than restated - kernel and parameters both."""

PARAMS = MODEL.params
RADIAL = MODEL.kernel
GRID = 7
BOARD = GridConfig.from_grid_size(GRID, 0).to_board()
CENTRE = Position(3, 3)
FAR = Position(0, 0)


def row(step: int, source: Position = CENTRE) -> ScentRecord:
    """One turn's disclosed emission, as the live evidence retains it."""
    return ScentRecord(TurnCursor(1, step), emission_of(BOARD, RADIAL, source, PARAMS))
