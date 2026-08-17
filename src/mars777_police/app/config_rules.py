"""What a locked config *means*, for the live game and the audit alike.

One authority, because two would be worse than none. A replay that derived the
board differently from the game that was played would report a violation nobody
committed - and the live side asking the final-audit module for its own rules
would make gameplay depend on the layer that judges it. So the projection lives
here, `semantic_review` consumes it, and the series driver consumes the same
function.

Nothing here decides anything. Every value is already validated: `GridConfig`
refuses a grid below the App-F floor, `MovementAndBarrierTerms` refuses a quota
or ceiling below its minimum and refuses `survival_threshold > max_moves`
(JDEC-015), and `BoardAndAgentsTerms` refuses two identical start cells. This
reads those facts into the domain types that need them.

**The opening truth is per sub-game, never carried.** A series may negotiate a
different board or different start cells for `g02` (App F T13 #1/#5/#6 are
MINIMUM and NEGOTIABLE), and the final audit replays each sub-game from *its*
locked start cells - so a sub-game that began where the previous one ended would
be disclosing a game that never happened.
"""

from ..domain.barriers import BarrierQuota
from ..domain.config_model import GridConfig
from ..domain.negotiated_config import NegotiatedConfig
from ..domain.terminal import TurnLimits
from ..domain.truth import LocalTruth
from .hint_policy import TemplateHintPolicy
from .sealed_record_values import ActorRole
from .semantic_values import SemanticRules


def rules_of(config: NegotiatedConfig) -> SemanticRules:
    """The locked geometry, quota and start cells this sub-game agreed on."""
    board, barriers = config.board_and_agents, config.movement_and_barriers
    grid = GridConfig.from_grid_size(board.grid_size, board.axis_start_index)
    return SemanticRules(
        grid.to_board(), BarrierQuota(barriers.max_barriers), board.cop_start, board.thief_start
    )


def limits_of(config: NegotiatedConfig) -> TurnLimits:
    """The step ceiling and survival threshold this sub-game locked.

    The audit never needed these - a replay is bounded by the turns that were
    disclosed - but a game being *played* does, because they are what decides
    when it ends.
    """
    terms = config.movement_and_barriers
    return TurnLimits(max_moves=terms.max_moves, survival_threshold=terms.survival_threshold)


def hints_of(config: NegotiatedConfig, role: ActorRole) -> TemplateHintPolicy:
    """The language policy this sub-game's locked word budget allows *role*.

    `hint_max_words` is NEGOTIABLE (App F T14 #2) and lives in the same locked
    config every other projection here reads, so the cap reaches the policy the
    way the board and the quota already reach theirs - never as a constant.
    """
    return TemplateHintPolicy(role=role, hint_max_words=config.world.hint_max_words)


def opening_truth(config: NegotiatedConfig, role: ActorRole) -> LocalTruth:
    """Where *role* stands before this sub-game's first turn, on an empty board.

    `completed_steps` is 0 and the board carries no barrier: a sub-game starts
    where its own config says, with nothing inherited from the last one.
    """
    rules = rules_of(config)
    return LocalTruth(board=rules.board, own_position=rules.start_for(role))
