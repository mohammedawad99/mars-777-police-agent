"""Composing one sub-game's driver from the config the peers locked.

`SeriesDriver` owns the *sequence* of six sub-games; what a single sub-game's
driver is made of is a different question, and it had grown into a thirteen-line
constructor call inside a file already at its size ceiling. Moving it here keeps
the series loop readable as open, play, close, and gives the per-sub-game
services one place to be assembled - which is where the scent authority now
joins the board, the quota and the word budget.

**Everything here is projected from the locked config or the live runtimes.**
`config_rules` turns the agreed terms into this sub-game's rules, limits, opening
truth and language policy; the scent parameters come from the model the peers
authenticated before the series (`SCENT-001`); and the belief source reads the
emissions the current audit runtime has actually accepted. Nothing is
constructed from a default, and nothing here decides anything.

**The history is a question, not an answer.** The source holds a callable so the
belief is folded at the moment a decision asks for it: a tuple captured here
would freeze the opening view for the whole sub-game, and every turn after the
first would decide on stale evidence.
"""

from ..domain.negotiated_config import NegotiatedConfig
from .active_runtime_context import ActiveRuntimeContext
from .config_rules import hints_of, limits_of, opening_truth, rules_of
from .peer_runner import PeerRunner
from .pregame_session_runtime import PregameSessionRuntime
from .protocol_values import Sha256Digest
from .scent_interpretation import LiveScentBelief
from .sealed_record_values import ActorRole
from .sub_game_driver import SubGameDriver
from .turn_service import LocalTurnService


def launch_sub_game(
    strategy: object,
    runner: PeerRunner,
    context: ActiveRuntimeContext,
    pregame: PregameSessionRuntime,
    config: NegotiatedConfig,
    role: ActorRole,
    config_sha256: Sha256Digest,
    sub_game: int,
    deadline: float,
) -> SubGameDriver:
    """The driver for *sub_game*, with every service this config implies."""
    return SubGameDriver(
        strategy=strategy,  # type: ignore[arg-type]
        runner=runner,
        context=context,
        role=role,
        turns=LocalTurnService(limits_of(config), rules_of(config).quota),
        config_sha256=config_sha256,
        hints=hints_of(config, role),
        scent=LiveScentBelief(
            lambda: context.current_audit().expected_scent, pregame.lock.scent_model.params
        ),
        sub_game=sub_game,
        truth=opening_truth(config, role),
        deadline=deadline,
    )
