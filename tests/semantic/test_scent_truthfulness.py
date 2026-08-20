"""That an emission came from the cell the move actually reached.

Scent is physical evidence, so the only honest emitter is the position the move
produced - after a step, after a stay, clipped by the real board at a corner, and
for the police, the cell it never left because it spent its move on a barrier.
The board and the cell both come from the one replay authority, never from a
second opinion written for checking.
"""

from scent_truth_builders import MODEL, RULES, emission_at, record, reviewed
from semantic_builders import COP, THIEF

from mars777_police.app.sealed_record_values import ActorRole
from mars777_police.app.semantic_replay import PlayedTurn, Replay
from mars777_police.app.semantic_review import review_sub_game
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


def finding(
    own_turns: list, peer_turns: list, own_scent: tuple = (), peer_scent: tuple = ()
) -> object:
    """Review one real sub-game and return the single finding it reached."""
    evidence, audit = reviewed(POLICE, own_turns, peer_turns, own_scent, peer_scent)
    return review_sub_game(evidence, audit, RULES, MODEL)


def one_step(own_action=SOUTH, peer_action=NORTH) -> tuple[list, list]:
    """Step 1 for each side from its own locked start cell."""
    return [(1, COP, own_action)], [(1, THIEF, peer_action)]


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
