"""How a sub-game settles, from either side of the board.

Settlement is **signalled**, never inferred, and the same evidence has to settle
the same way whichever role is holding it - which is why these are parametrized
over both roles rather than written twice from one side's point of view.
"""

import pytest
from kit_wire_vectors import COMMIT

from mars777_police.app.capture_values import CaptureAnswer
from mars777_police.app.kit_adjudicate import adjudicate
from mars777_police.app.kit_messages import KitRole
from mars777_police.domain.terminal import Outcome


@pytest.mark.parametrize("role", [KitRole.POLICE, KitRole.THIEF])
def test_a_caught_answer_settles_a_capture_for_either_side(role: KitRole) -> None:
    """`adjudicate` is a pure function of the role, so both sides are pinned here."""
    from mars777_police.app.kit_messages import KitClaimResponse, KitTurn
    from mars777_police.app.protocol_values import Sha256Digest
    from mars777_police.domain.board import Position

    incoming = KitTurn(
        1,
        KitRole.THIEF if role is KitRole.POLICE else KitRole.POLICE,
        "",
        (),
        Sha256Digest(COMMIT),
        "2026-08-18T00:00:00Z",
        claim_response=KitClaimResponse(Position(1, 1), True),
    )

    verdict = adjudicate(
        role=role,
        incoming=incoming,
        answer=CaptureAnswer.NO_QUESTION,
        trapped=False,
        step=2,
        max_steps=35,
        survival_threshold=35,
    )

    assert verdict.outcome is Outcome.CAPTURE


@pytest.mark.parametrize("role", [KitRole.POLICE, KitRole.THIEF])
def test_a_survival_claim_settles_survival_for_either_side(role: KitRole) -> None:
    from mars777_police.app.kit_messages import KitTurn
    from mars777_police.app.protocol_values import Sha256Digest

    incoming = KitTurn(
        1,
        KitRole.THIEF if role is KitRole.POLICE else KitRole.POLICE,
        "",
        (),
        Sha256Digest(COMMIT),
        "2026-08-18T00:00:00Z",
        survival_claimed=True,
    )

    verdict = adjudicate(
        role=role,
        incoming=incoming,
        answer=CaptureAnswer.NO_QUESTION,
        trapped=False,
        step=2,
        max_steps=35,
        survival_threshold=35,
    )

    assert verdict.outcome is Outcome.SURVIVAL


def test_a_thief_at_its_own_threshold_settles_survival_without_being_told() -> None:
    """Its own count, on its own turn - the one terminal the thief owns outright."""
    verdict = adjudicate(
        role=KitRole.THIEF,
        incoming=None,
        answer=CaptureAnswer.NO_QUESTION,
        trapped=False,
        step=35,
        max_steps=35,
        survival_threshold=35,
    )

    assert verdict.outcome is Outcome.SURVIVAL
