"""The turn material a play test needs, built once for everyone who needs it.

A maker that seals our own half-turn, the strategy it asks for a decision, and a
peer turn arriving from the other side. They live together because they are the
two halves of one exchange, and apart from the tests because more than one file
needs both.
"""

from kit_wire_vectors import COMMIT
from r16_builders import config

from mars777_police.__main__ import ROLE
from mars777_police.app.config_rules import hints_of, limits_of, rules_of
from mars777_police.app.kit_half_turn import KitHalfTurnMaker
from mars777_police.app.kit_messages import KitRole, KitTurn
from mars777_police.app.kit_records import KitRecordChain
from mars777_police.app.protocol_values import Sha256Digest
from mars777_police.app.turn_service import LocalTurnService
from mars777_police.domain.scent_model_default import default_scent_model
from mars777_police.infra.clock import SystemClock

OURS = KitRole(ROLE.value)
THEIRS = KitRole.THIEF if OURS is KitRole.POLICE else KitRole.POLICE


def maker(chain: KitRecordChain) -> KitHalfTurnMaker:
    limits = limits_of(config())
    return KitHalfTurnMaker(
        role=OURS,
        actor=ROLE,
        sub_game=1,
        strategy=_Strategy(),
        turns=LocalTurnService(limits, rules_of(config()).quota),
        hints=hints_of(config(), ROLE),
        model=default_scent_model(),
        chain=chain,
        clock=SystemClock(),
        survival_threshold=limits.survival_threshold,
    )


class _Strategy:
    """`STAY`, which every role may always play - so the loop is what is tested."""

    def choose_action(self, observation: object) -> object:
        from mars777_police.domain.actions import MoveAction
        from mars777_police.domain.rules import Move

        return MoveAction(Move.STAY)


def peer_turn(step: int, **changes: object) -> KitTurn:
    fields: dict[str, object] = {
        "step": step,
        "sender": THEIRS,
        "hint": "over here",
        "smell_grid": (("0,0", 0.5),),
        "commit": Sha256Digest(COMMIT),
        "timestamp": "2026-08-18T00:00:00Z",
    }
    fields.update(changes)
    return KitTurn(**fields)  # type: ignore[arg-type]
