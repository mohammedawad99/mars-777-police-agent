"""Was the scent a reveal carried the scent its own disclosed action produces?

Parts 1A and 1B answered a different question. They prove the peer told the
audit and the log exactly what it told us live - which a peer that lied *live*
and then disclosed that same lie faithfully passes without difficulty. Nothing
before this recomputed the physics, so a deliberately misleading emission was
undetectable, and the book's own premise that a scent map "cannot lie" was false
in this architecture rather than true.

This closes it (`JDEC-018`). For every counted reveal the review recomputes the
emission from evidence the verifier anchors itself - the trajectory the semantic
replay already reconstructs from the config-locked start cells, the board that
emitter actually had, and the model the series cryptographically locked - and
compares it to the retained history. The centre is never taken from the scent
being judged, and the model is never the local default.

It is deliberately **not** tampering: every hash can verify and every disclosure
can be faithful while the emission is still physically impossible.
"""

import dataclasses

import semantic_builders as build
from scent_truth_builders import MODEL, RULES, emission_at, record, reviewed
from semantic_builders import COP, SUB_GAME, THIEF

from mars777_police.app.sealed_record_values import ActorRole
from mars777_police.app.semantic_replay import PlayedTurn, Replay
from mars777_police.app.semantic_review import review_sub_game
from mars777_police.app.semantic_values import (
    SCORED_AS_TECHNICAL_LOSS,
    TAMPERING,
    SemanticVerdict,
)
from mars777_police.app.turn_cursor import TurnCursor
from mars777_police.domain.actions import BarrierAction, MoveAction
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


def finding(
    own_turns: list, peer_turns: list, own_scent: tuple = (), peer_scent: tuple = ()
) -> object:
    """Review one real sub-game and return the single finding it reached."""
    evidence, audit = reviewed(POLICE, own_turns, peer_turns, own_scent, peer_scent)
    return review_sub_game(evidence, audit, RULES, MODEL)


def one_step(own_action=SOUTH, peer_action=NORTH) -> tuple[list, list]:
    """Step 1 for each side from its own locked start cell."""
    return [(1, COP, own_action)], [(1, THIEF, peer_action)]


# --------------------------------------------------------------- honest scent


def test_an_honest_move_emits_from_the_cell_the_move_reaches() -> None:
    ours, theirs = one_step()
    verdict = finding(
        ours,
        theirs,
        own_scent=(record(1, destination_of(COP, Move.S)),),
        peer_scent=(record(1, destination_of(THIEF, Move.N)),),
    )
    assert verdict.consistent


def test_an_honest_stay_emits_from_the_unchanged_cell() -> None:
    ours, theirs = one_step(own_action=STAY, peer_action=STAY)
    verdict = finding(ours, theirs, own_scent=(record(1, COP),), peer_scent=(record(1, THIEF),))
    assert verdict.consistent


def test_an_honest_corner_emission_is_clipped_by_the_real_board() -> None:
    """The cop starts in a corner, so its window is cut by the board itself."""
    ours, theirs = one_step(own_action=STAY, peer_action=STAY)
    corner = emission_at(COP)
    assert len(corner.deposits) < 25, "a corner emits fewer cells than a full window"
    verdict = finding(ours, theirs, own_scent=(record(1, COP),), peer_scent=(record(1, THIEF),))
    assert verdict.consistent


def test_two_steps_follow_the_reconstructed_trajectory() -> None:
    after_one = destination_of(COP, Move.S)
    ours = [(1, COP, SOUTH), (2, after_one, SOUTH)]
    theirs = [(1, THIEF, NORTH), (2, destination_of(THIEF, Move.N), NORTH)]
    verdict = finding(
        ours,
        theirs,
        own_scent=(record(1, after_one), record(2, destination_of(after_one, Move.S))),
        peer_scent=(
            record(1, destination_of(THIEF, Move.N)),
            record(2, destination_of(destination_of(THIEF, Move.N), Move.N)),
        ),
    )
    assert verdict.consistent


def test_a_police_barrier_emits_from_the_cell_the_police_never_left() -> None:
    target = Position(COP.row + 1, COP.col)
    ours = [(1, COP, BarrierAction(target))]
    theirs = [(1, THIEF, NORTH)]
    verdict = finding(
        ours,
        theirs,
        own_scent=(record(1, COP, _with_barrier(target)),),
        peer_scent=(record(1, destination_of(THIEF, Move.N)),),
    )
    assert verdict.consistent


def _with_barrier(target: Position):
    """The board the police itself had: start-of-step plus its own placement."""
    from mars777_police.domain.barriers import place_barrier

    return place_barrier(RULES.board, COP, target, RULES.quota)


# ------------------------------------------------- emitter-correct board timing


def test_each_emitter_is_judged_on_the_board_it_actually_had() -> None:
    """The high-risk edge: one side places a barrier in the step the other moves.

    Both step-`k` commitments are sealed before either step-`k` reveal, so the
    thief could not have seen the police's step-`k` barrier when it produced its
    scent. The board handed to the recomputation must therefore be **per
    emitter** - start-of-step plus that emitter's own effect - and must not be
    the fully-applied end-of-step board the replay holds afterwards.

    Asserted against `Replay` directly rather than through an emission, because
    of a fact worth recording: `ScentField` consults only the board's *shape*
    (`ScentField.zero` takes `rows`/`cols`/`start_index`, and `_deposits` clips
    to bounds), never `board.blocked`. A barrier therefore cannot change any
    emission today, so the distinction is currently equivalence-preserving. It is
    still implemented per JDEC-018 §5, and this test pins the contract so that if
    scent ever becomes blocked-aware the verifier is already correct.
    """
    target = Position(COP.row, COP.col + 1)
    police = PlayedTurn(1, POLICE, COP, (), BarrierAction(target))
    thief = PlayedTurn(1, THIEF_ROLE, THIEF, (), NORTH)
    replay = Replay(RULES)

    assert target in replay.board_after(police).blocked, "the placer's own board has it"
    assert target not in replay.board_after(thief).blocked, "the opponent's board does not"
    assert target not in replay.board.blocked, "start-of-step board is untouched"

    replay.apply((police, thief))
    assert target in replay.board.blocked, "only after the step is applied"
    assert replay.board_after(thief).blocked == replay.board.blocked, (
        "a mover's board is whatever the replay currently holds"
    )


def test_the_emitter_board_and_cell_come_from_the_one_replay_authority() -> None:
    """No second movement or placement implementation exists for the check."""
    import inspect

    from mars777_police.app import scent_truth

    source = inspect.getsource(scent_truth)
    for forbidden in ("destination_of", "place_barrier", "is_legal_move", "delta_of"):
        assert forbidden not in source
    assert "replay.board_after(turn)" in source and "replay.cell_after(turn)" in source


# ---------------------------------------------------------------- physical lies


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


# -------------------------------------------------------------------- precedence


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


# ------------------------------------------------------------ V1 / classification


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
