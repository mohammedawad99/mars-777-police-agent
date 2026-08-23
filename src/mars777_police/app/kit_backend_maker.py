"""Building one sub-game's half-turn maker from the terms the pairing agreed.

Split from `kit_backend` under guideline §3.2: assembling a maker is a different
job from sequencing a series, and the two had grown into one file. Every value
here comes from the locked configuration, so a sub-game cannot be played under
terms the pairing did not agree.
"""

from ..domain.negotiated_config import NegotiatedConfig
from ..domain.scent_model import ScentModelAgreement
from .config_rules import hints_of, limits_of, rules_of
from .kit_half_turn import KitHalfTurnMaker
from .kit_messages import KitRole
from .kit_play import KitPlayState
from .kit_records import KitRecordChain
from .kit_sub_game import KitSubGame
from .ports import TimestampPort
from .sealed_record_values import ActorRole
from .strategy_api import StrategyPort
from .turn_service import LocalTurnService


def half_turn_maker(
    *,
    role: KitRole,
    actor: ActorRole,
    sub_game: int,
    strategy: StrategyPort,
    model: ScentModelAgreement,
    chain: KitRecordChain,
    clock: TimestampPort,
    config: NegotiatedConfig,
) -> KitHalfTurnMaker:
    """One sub-game's half-turn maker, from the locked configuration alone."""
    limits = limits_of(config)
    return KitHalfTurnMaker(
        role=role,
        actor=actor,
        sub_game=sub_game,
        strategy=strategy,
        turns=LocalTurnService(limits, rules_of(config).quota),
        hints=hints_of(config, actor),
        model=model,
        chain=chain,
        clock=clock,
        survival_threshold=limits.survival_threshold,
    )


def sub_game_for(
    *,
    maker: "KitHalfTurnMaker",
    inbox: object,
    send: object,
    role: "KitRole",
    config: "NegotiatedConfig",
    deadline: float,
    actor: "ActorRole",
) -> "KitSubGame":
    """One sub-game, assembled from the pieces its backend already holds.

    Built here rather than at the call site so the backend reads as the sequence
    it performs - wait, greet, play, disclose, audit, record - instead of as a
    constructor argument list interrupting that sequence.
    """
    return KitSubGame(
        maker=maker,
        inbox=inbox,  # type: ignore[arg-type]
        send=send,  # type: ignore[arg-type]
        role=role,
        limits=limits_of(config),
        deadline=deadline,
        state=KitPlayState.opening(config, actor),
    )
