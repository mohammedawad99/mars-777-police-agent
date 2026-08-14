"""The reveal peer message: the turn cursor, the chosen action and the hint.

Ch 5 §5.3.2 (p.51) sends *the action (Move) and the verbal sentence* while the
nonce stays hidden, so Reveal is deliberately incomplete beside audit material:
no nonce, state, intent, role, sealed record or `H_commit`.
The member is `action` because it holds the domain's `PhysicalAction`; the
sealed key stays `move`, mapped later by the canonical layer. `PhysicalAction`
is a *union alias*, so the rule is exact membership of `(MoveAction,
BarrierAction)`, and a wrong component is a message fault, not a domain fault.
"""

import dataclasses

import pytest

from mars777_police.app.peer_messages import (
    Acknowledgement,
    Commitment,
    Reveal,
    TurnCursor,
)
from mars777_police.app.protocol_values import Sha256Digest
from mars777_police.domain.actions import BarrierAction, MoveAction
from mars777_police.domain.board import Position
from mars777_police.domain.config_model import FIRST_SUB_GAME
from mars777_police.domain.rules import Move

CURSOR = TurnCursor(FIRST_SUB_GAME, 1)
ACTION = MoveAction(Move.N)
HINT = "circling near the north gate"


def test_the_reveal_carries_the_core_three_plus_two_unsealed_adjuncts() -> None:
    """R8 added one nullable adjunct and V2 a second; the sealed core is untouched."""
    assert tuple(f.name for f in dataclasses.fields(Reveal)) == (
        "cursor",
        "action",
        "hint",
        "capture_claim",
        "scent_emission",
    )
    assert Reveal(CURSOR, ACTION, HINT).capture_claim is None
    assert Reveal(CURSOR, ACTION, HINT).scent_emission is None, "V1 still constructs"
    with pytest.raises(ValueError, match="capture_claim must be a CaptureClaim"):
        Reveal(CURSOR, ACTION, HINT, (1, 1))  # type: ignore[arg-type]


ABSENT = ["move", "nonce", "state", "intent", "role", "by_role", "sealed_record", "phase"]
ABSENT += ["h_commit", "accepted", "ok", "valid", "verified", "success", "message_id"]
ABSENT += ["timestamp", "game_id", "game_uid", "action_kind", "kind", "barrier_target"]


@pytest.mark.parametrize("absent", ABSENT)
def test_the_reveal_carries_no_further_field(absent: str) -> None:
    """The internal member is `action`; the *sealed* key `move` is not renamed."""
    assert not hasattr(Reveal(CURSOR, ACTION, HINT), absent)


def test_the_reveal_is_frozen_slotted_and_value_equal() -> None:
    reveal = Reveal(CURSOR, ACTION, HINT)
    with pytest.raises(dataclasses.FrozenInstanceError):
        reveal.hint = "other"  # type: ignore[misc]
    assert Reveal.__slots__ == ("cursor", "action", "hint", "capture_claim", "scent_emission")
    assert reveal == Reveal(CURSOR, ACTION, HINT)
    assert reveal != Reveal(TurnCursor(2, 1), ACTION, HINT)
    assert reveal != Reveal(CURSOR, MoveAction(Move.S), HINT)
    assert reveal != Reveal(CURSOR, ACTION, "a different sentence")


@pytest.mark.parametrize("move", list(Move))
def test_every_movement_including_stay_is_revealable(move: Move) -> None:
    """A barrier turn forgoes movement; STAY is a movement, not a non-action."""
    reveal = Reveal(CURSOR, MoveAction(move), HINT)
    assert reveal.action == MoveAction(move)
    assert type(reveal.action) is MoveAction


def test_a_barrier_reveal_keeps_the_exact_action_object_it_was_given() -> None:
    """Ch 3 p.37/38: the exact cell is declared; nothing here extracts or checks it."""
    placement = BarrierAction(Position(2, 3))
    reveal = Reveal(CURSOR, placement, HINT)
    assert reveal.action is placement
    assert reveal.action.target == Position(2, 3)
    assert Reveal(CURSOR, BarrierAction(Position(-9, 99)), HINT).action.target.col == 99


@pytest.mark.parametrize("value", [(1, 1), {"sub_game": 1, "step": 1}, [1, 1], None, True, 1])
def test_a_cursor_of_the_wrong_type_is_refused_never_coerced(value: object) -> None:
    with pytest.raises(ValueError):
        Reveal(value, ACTION, HINT)  # type: ignore[arg-type]


WRONG_ACTIONS = [Move.N, Position(2, 3), "N", {"kind": "MOVE", "value": "N"}]
WRONG_ACTIONS += [{"kind": "BARRIER", "value": [2, 3]}, (Move.N,), [Move.N], None, True, 0]


@pytest.mark.parametrize("value", WRONG_ACTIONS)
def test_an_action_that_is_not_an_authoritative_action_value_is_refused(value: object) -> None:
    """A bare `Move`, a `Position`, a token or canonical JSON is never wrapped."""
    with pytest.raises(ValueError):
        Reveal(CURSOR, value, HINT)  # type: ignore[arg-type]


def test_subclasses_of_the_action_values_are_refused() -> None:
    """Exact membership of `(MoveAction, BarrierAction)`, not `isinstance`."""

    class LooseMove(MoveAction):
        pass

    class LooseBarrier(BarrierAction):
        pass

    with pytest.raises(ValueError):
        Reveal(CURSOR, LooseMove(Move.N), HINT)
    with pytest.raises(ValueError):
        Reveal(CURSOR, LooseBarrier(Position(2, 3)), HINT)


@pytest.mark.parametrize("value", [b"hint", 1, True, None, ["hint"], object()])
def test_a_hint_of_the_wrong_type_is_refused_never_coerced(value: object) -> None:
    with pytest.raises(ValueError):
        Reveal(CURSOR, ACTION, value)  # type: ignore[arg-type]


def test_a_str_subclass_hint_is_refused() -> None:
    class LoudHint(str):
        pass

    with pytest.raises(ValueError):
        Reveal(CURSOR, ACTION, LoudHint("loud"))


@pytest.mark.parametrize("hint", ["", "   ", "a " * 400])
def test_any_string_hint_is_structurally_accepted(hint: str) -> None:
    """`hint_max_words` is locked config and stays LIVE; emptiness is not a rule."""
    assert Reveal(CURSOR, ACTION, hint).hint == hint


def test_the_reveal_is_a_distinct_family_and_checks_no_live_state() -> None:
    reveal = Reveal(CURSOR, ACTION, HINT)
    assert type(reveal) is Reveal
    assert not issubclass(Reveal, Commitment | Acknowledgement)
    assert reveal != Commitment(CURSOR, Sha256Digest("0" * 64))
    for name in ("to_json", "to_dict", "canonical_value", "serialize", "encode", "verify"):
        assert not hasattr(Reveal, name)


def test_the_reveal_is_on_the_exhaustive_app_surface() -> None:
    from mars777_police import app

    assert app.Reveal is Reveal and "Reveal" in app.__all__
    assert len(app.__all__) == len(set(app.__all__))
