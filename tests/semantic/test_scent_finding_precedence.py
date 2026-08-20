"""Which finding wins when more than one is true, and what is never written.

A broken trajectory or an illegal action outranks a scent mismatch, because the
reconstruction the scent check depends on has already failed. A legacy sub-game
with no scent at all is not dishonest, a mismatch is scored rather than called
tampering, and none of this persists a single fact about the opponent.
"""

import dataclasses

import semantic_builders as build
from scent_truth_builders import MODEL, RULES, record, reviewed
from semantic_builders import COP, SUB_GAME, THIEF
from test_scent_emission_refusals import _halved_kernel
from test_scent_truthfulness import finding, one_step

from mars777_police.app.sealed_record_values import ActorRole
from mars777_police.app.semantic_review import review_sub_game
from mars777_police.app.semantic_values import (
    SCORED_AS_TECHNICAL_LOSS,
    TAMPERING,
    SemanticVerdict,
)
from mars777_police.domain.actions import BarrierAction, MoveAction
from mars777_police.domain.board import Position
from mars777_police.domain.rules import Move, destination_of

POLICE, THIEF_ROLE = ActorRole.POLICE, ActorRole.THIEF
NORTH, SOUTH, EAST, STAY = (
    MoveAction(Move.N),
    MoveAction(Move.S),
    MoveAction(Move.E),
    MoveAction(Move.STAY),
)


def test_a_broken_trajectory_outranks_a_scent_mismatch() -> None:
    """The stronger, more fundamental finding must not be hidden behind scent."""
    ours = [(1, COP, SOUTH)]
    theirs = [(1, Position(THIEF.row + 2, THIEF.col), NORTH)]
    verdict = finding(
        ours,
        theirs,
        own_scent=(record(1, destination_of(COP, Move.S)),),
        peer_scent=(record(1, COP),),
    )
    assert verdict.verdict is SemanticVerdict.WRONG_START


def test_an_illegal_action_outranks_a_scent_mismatch() -> None:
    ours = [(1, COP, SOUTH)]
    theirs = [(1, THIEF, BarrierAction(Position(0, 1)))]
    verdict = finding(
        ours,
        theirs,
        own_scent=(record(1, destination_of(COP, Move.S)),),
        peer_scent=(record(1, COP),),
    )
    assert verdict.verdict is SemanticVerdict.ILLEGAL_ACTION


def test_a_legacy_sub_game_with_no_scent_is_never_dishonest() -> None:
    """Absence is V1, not a lie; Parts 1A/1B already own completeness."""
    ours, theirs = one_step()
    assert finding(ours, theirs).consistent


def test_the_finding_is_scored_and_never_tampering() -> None:
    ours, theirs = one_step()
    verdict = finding(
        ours,
        theirs,
        own_scent=(record(1, destination_of(COP, Move.S)),),
        peer_scent=(record(1, THIEF),),
    )
    assert verdict.verdict in SCORED_AS_TECHNICAL_LOSS
    assert verdict.verdict not in TAMPERING
    assert verdict.honest, "a physical lie is a truthful record of bad play, not a forgery"


def test_the_verifier_is_given_the_model_and_never_reaches_for_a_default() -> None:
    """Passing another model changes the answer - proof there is no fallback."""
    import inspect

    from mars777_police.app import scent_truth

    source = inspect.getsource(scent_truth)
    assert "default_scent_model" not in source
    evidence, audit = reviewed(
        POLICE,
        *one_step(),
        own_scent=(record(1, destination_of(COP, Move.S)),),
        peer_scent=(record(1, destination_of(THIEF, Move.N)),),
    )
    assert review_sub_game(evidence, audit, RULES, MODEL).consistent
    other = dataclasses.replace(MODEL, kernel=_halved_kernel())
    assert not review_sub_game(evidence, audit, RULES, other).consistent


def test_no_opponent_truth_is_persisted_by_the_check() -> None:
    evidence, audit = reviewed(
        POLICE,
        *one_step(),
        own_scent=(record(1, destination_of(COP, Move.S)),),
        peer_scent=(record(1, destination_of(THIEF, Move.N)),),
    )
    review_sub_game(evidence, audit, RULES, MODEL)
    for owner in (evidence, audit):
        names = {field.name for field in dataclasses.fields(owner)}
        assert not names & {"opponent_truth", "peer_truth", "world", "cells"}
    assert build.SUB_GAME == SUB_GAME
