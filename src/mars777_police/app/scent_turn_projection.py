"""What this turn's action deposits, projected without playing the turn.

Ch 4 has both agents emit scent around themselves, and `SCENT-002` fixes the
physics. What was missing was the moment: an emission belongs to the cell the
actor occupies **after** its action, and that cell is only known once the action
has been applied. This projects it and nothing else.

**Preview, never advance.** `LocalTurnService.apply` returns a new
`LocalTruth`; the one we were given is frozen and is handed back untouched, so
the authoritative truth still describes a turn nobody has completed. Adopting a
turn's result belongs to the owner that knows the peer accepted it, and that
owner does not exist yet - projecting here must not pretend otherwise.

**Illegal means nothing is sent.** An action our own rules refuse raises the
existing domain/application error before any emission exists, so the caller
never gets an emission for a turn it may not play.

No board arithmetic, no role branch, no networking, no hashing, no belief: the
service decides where the action leads, `emission_of` decides what that cell
deposits under the agreed model, and both are existing owners.
"""

from dataclasses import dataclass

from ..domain.actions import PhysicalAction
from ..domain.scent_emission import ScentEmission
from ..domain.scent_model import ScentModelAgreement
from ..domain.scent_observation import emission_of
from ..domain.truth import LocalTruth
from .turn_protocol_runtime import TurnProtocolRuntime
from .turn_service import LocalTurnService


@dataclass(frozen=True, slots=True)
class ScentTurnProjector:
    """Projects one action's emission under this series' agreed model."""

    turns: LocalTurnService
    model: ScentModelAgreement
    """The model the series froze; never rebuilt and never defaulted here."""

    def project(self, truth: LocalTruth, action: PhysicalAction) -> ScentEmission:
        """Return what *action* would deposit, leaving *truth* exactly as it was."""
        preview = self.turns.apply(truth, action)
        return emission_of(
            preview.truth.board, self.model.kernel, preview.truth.own_position, self.model.params
        )


def emission_for(
    turn: "TurnProtocolRuntime", model: ScentModelAgreement, action: PhysicalAction
) -> ScentEmission:
    """What *action* deposits for the role whose live turn runtime this is."""
    return ScentTurnProjector(turn.turns, model).project(turn.truth, action)
