"""The lawful scent each side may fold, produced by the locked model.

Chapter 4's model is Appendix F **FIXED** in all three of its numbers - source
strength `0.9`, decay `0.10`, field `5x5` - so the benchmark uses the shipped
default and never varies it. What a side may fold is what the *other* side
emitted, one emission per completed round, exactly as `observed_field` requires
and `interpret_scent` folds.

**Each role keeps its own history of the opponent's emissions**, so neither can
read its own trail as if it were evidence about the other, and neither sees an
emission before the round that produced it is complete.
"""

from dataclasses import dataclass, field

from mars777_police.app.sealed_record_values import ActorRole
from mars777_police.app.semantic_replay import PlayedTurn
from mars777_police.domain.board import Board
from mars777_police.domain.scent_belief import NO_SCENT, ScentBelief
from mars777_police.domain.scent_emission import ScentEmission
from mars777_police.domain.scent_model_default import default_scent_model
from mars777_police.domain.scent_observation import emission_of, observed_field

from .configs import BenchConfig


@dataclass(frozen=True, slots=True)
class TrailSource:
    """One role's answer to "what has the opponent's scent shown me?"."""

    emissions: tuple[ScentEmission, ...]
    config: BenchConfig

    def for_board(self, board: Board) -> ScentBelief:
        """Fold the opponent's emissions into the belief they imply on *board*."""
        if not self.emissions:
            return NO_SCENT
        params = default_scent_model().params
        return ScentBelief(observed_field(board, self.emissions, params), len(self.emissions))


@dataclass(slots=True)
class ScentTrail:
    """Both roles' histories of what the other side emitted, round by round."""

    config: BenchConfig
    heard: dict[ActorRole, list[ScentEmission]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.heard = {role: [] for role in ActorRole}

    def source_for(self, role: ActorRole) -> TrailSource:
        """What *role* has lawfully heard so far. Never its own emissions."""
        return TrailSource(tuple(self.heard[role]), self.config)

    def record(self, turns: tuple[PlayedTurn, ...]) -> None:
        """Register one completed round's emissions, each heard by the other side.

        The emission is projected from the cell the actor **started** the round
        on, which is the cell its sealed state named - the same rule
        `scent_truth` applies, so an emitter cannot be judged against a board it
        never had.
        """
        model = default_scent_model()
        for turn in turns:
            emission = emission_of(self.config.board(), model.kernel, turn.cell, model.params)
            for role in ActorRole:
                if role is not turn.role:
                    self.heard[role].append(emission)
