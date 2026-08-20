"""Every way a well-formed emission can still be a lie, and its refusal.

Shape is not truth. A validly shaped field centred on the wrong cell, one
altered intensity, a deposit removed or added, an emission taken before the
action, or one produced under a different model - each is refused, and each by
the physics rather than by a tolerance.
"""

from scent_truth_builders import MODEL, RULES, emission_at, record
from semantic_builders import COP, SUB_GAME, THIEF
from test_scent_truthfulness import finding, one_step

from mars777_police.app.sealed_record_values import ActorRole
from mars777_police.app.semantic_values import (
    SemanticVerdict,
)
from mars777_police.app.turn_cursor import TurnCursor
from mars777_police.domain.actions import MoveAction
from mars777_police.domain.board import Position
from mars777_police.domain.rules import Move, destination_of
from mars777_police.domain.scent_emission import ScentDeposit, ScentEmission

POLICE, THIEF_ROLE = ActorRole.POLICE, ActorRole.THIEF
NORTH, SOUTH, EAST, STAY = (
    MoveAction(Move.N),
    MoveAction(Move.S),
    MoveAction(Move.E),
    MoveAction(Move.STAY),
)


def test_a_validly_shaped_emission_centred_on_the_wrong_cell_is_refused() -> None:
    ours, theirs = one_step()
    elsewhere = record(1, destination_of(THIEF, Move.E))
    verdict = finding(
        ours, theirs, own_scent=(record(1, destination_of(COP, Move.S)),), peer_scent=(elsewhere,)
    )
    assert verdict.verdict is SemanticVerdict.DISHONEST_SCENT_EMISSION
    assert verdict.at_fault is THIEF_ROLE and verdict.step == 1


def test_one_altered_intensity_is_refused() -> None:
    ours, theirs = one_step()
    honest = emission_at(destination_of(THIEF, Move.N))
    first, *rest = honest.deposits
    tweaked = ScentEmission(
        (ScentDeposit(first.cell, first.intensity / 2), *rest)  # type: ignore[arg-type]
    )
    verdict = finding(
        ours,
        theirs,
        own_scent=(record(1, destination_of(COP, Move.S)),),
        peer_scent=(_row(tweaked),),
    )
    assert verdict.verdict is SemanticVerdict.DISHONEST_SCENT_EMISSION


def test_a_removed_deposit_is_refused() -> None:
    ours, theirs = one_step()
    honest = emission_at(destination_of(THIEF, Move.N))
    verdict = finding(
        ours,
        theirs,
        own_scent=(record(1, destination_of(COP, Move.S)),),
        peer_scent=(_row(ScentEmission(honest.deposits[1:])),),
    )
    assert verdict.verdict is SemanticVerdict.DISHONEST_SCENT_EMISSION


def test_an_extra_deposit_is_refused() -> None:
    ours, theirs = one_step()
    honest = emission_at(destination_of(THIEF, Move.N))
    far = ScentDeposit(Position(6, 6), honest.deposits[0].intensity)
    verdict = finding(
        ours,
        theirs,
        own_scent=(record(1, destination_of(COP, Move.S)),),
        peer_scent=(_row(ScentEmission((*honest.deposits, far))),),
    )
    assert verdict.verdict is SemanticVerdict.DISHONEST_SCENT_EMISSION


def test_the_pre_action_emission_is_refused() -> None:
    """Correct physics, wrong moment - the exact mistake §4.3 rules out."""
    ours, theirs = one_step()
    verdict = finding(
        ours,
        theirs,
        own_scent=(record(1, destination_of(COP, Move.S)),),
        peer_scent=(record(1, THIEF),),
    )
    assert verdict.verdict is SemanticVerdict.DISHONEST_SCENT_EMISSION


def test_an_emission_from_another_model_is_refused() -> None:
    """Right centre, right board, wrong physics."""
    import dataclasses as dc

    other = dc.replace(MODEL, kernel=_halved_kernel())
    ours, theirs = one_step()
    cell = destination_of(THIEF, Move.N)
    from mars777_police.domain.scent_observation import emission_of

    verdict = finding(
        ours,
        theirs,
        own_scent=(record(1, destination_of(COP, Move.S)),),
        peer_scent=(_row(emission_of(RULES.board, other.kernel, cell, other.params)),),
    )
    assert verdict.verdict is SemanticVerdict.DISHONEST_SCENT_EMISSION


def _halved_kernel():
    """A structurally valid kernel that is not the locked one."""
    from decimal import Decimal

    from mars777_police.domain.scent_kernel import ScentKernel

    rows = tuple(
        tuple((weight / Decimal(2)).quantize(Decimal("0.01")) for weight in row)
        for row in MODEL.kernel.weights
    )
    return ScentKernel(rows)


def _row(emission: ScentEmission):
    from mars777_police.app.scent_records import ScentRecord

    return ScentRecord(TurnCursor(SUB_GAME, 1), emission)
