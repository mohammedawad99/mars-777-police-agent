"""The own-known state snapshot sealed into a commitment (Stage 4E-R9-R2).

`state` is the one sealed member the book names but never specifies (Ch 5 p.51:
the board snapshot the move is based on); its shape is PROJECT-LOCKED by
JDEC-012 / NDEC-002 / PRD06-FR-068. Nothing about the *board* is checked here,
because deciding a cell is illegal needs game state a value must never reach for
- and the two builder invariants Stage 4E-R9-R1 froze, `state.step ==
cursor.step` and `state.role == role`, are absent because a cursor is not in
scope. Shape, composition and immutability live here; the barrier ordering
contract is large enough to own `test_sealed_state_barriers.py`.
"""

import dataclasses

import pytest

from mars777_police.app.protocol_values import Sha256Digest
from mars777_police.app.sealed_record_values import ActorRole, SealedState
from mars777_police.domain.board import Position

DIGEST = Sha256Digest("0" * 64)
FIELDS = ("config_sha256", "self_pos", "barriers", "step", "role")


def state(**over: object) -> SealedState:
    kwargs: dict[str, object] = {
        "config_sha256": DIGEST,
        "self_pos": Position(2, 3),
        "barriers": (),
        "step": 1,
        "role": ActorRole.POLICE,
    }
    return SealedState(**(kwargs | over))  # type: ignore[arg-type]


def test_the_snapshot_carries_exactly_the_five_locked_members_in_order() -> None:
    assert tuple(f.name for f in dataclasses.fields(SealedState)) == FIELDS


OPPONENT = ["opponent_position", "opponent_pos", "thief_position", "police_position"]
OPPONENT += ["enemy_position", "other_position", "public_board", "board", "local_truth"]
OPPONENT += ["opponent_truth", "opponent_state", "extra", "metadata", "hint", "move", "nonce"]

NO_CODEC = ["to_dict", "to_json", "canonical", "serialize", "encode", "digest"]
NO_CODEC += ["commit", "recompute", "verify", "sealed_record", "h_commit"]


@pytest.mark.parametrize("absent", OPPONENT)
def test_no_opponent_truth_or_spare_slot_is_representable(absent: str) -> None:
    """Partial observation is structural here: there is nowhere to put the opponent."""
    assert not hasattr(state(), absent)


@pytest.mark.parametrize(
    "bad", ["0" * 64, b"0" * 64, None, True, 0, Position(0, 0), ("0" * 64,), DIGEST.value]
)
def test_a_config_digest_of_the_wrong_type_is_refused_never_rebuilt(bad: object) -> None:
    """A raw 64-hex string raises: `Sha256Digest` has one authoritative constructor."""
    with pytest.raises(ValueError):
        state(config_sha256=bad)


@pytest.mark.parametrize("bad", [(2, 3), [2, 3], {"row": 2, "col": 3}, None, True, 2, DIGEST])
def test_a_self_position_of_the_wrong_type_is_refused(bad: object) -> None:
    with pytest.raises(ValueError):
        state(self_pos=bad)


def test_subclasses_of_the_composed_values_are_refused() -> None:
    """An `Enum` with members cannot be subclassed at all, so only these two apply."""

    class LooseDigest(Sha256Digest): ...

    class LoosePosition(Position): ...

    with pytest.raises(ValueError):
        state(config_sha256=LooseDigest("0" * 64))
    with pytest.raises(ValueError):
        state(self_pos=LoosePosition(2, 3))
    with pytest.raises(TypeError, match="cannot extend"):

        class LooseRole(ActorRole): ...


def test_the_role_must_be_the_vocabulary_not_its_spelling() -> None:
    """`ActorRole` is a `StrEnum`, so a bare `"police"` compares equal - and is refused."""
    assert state(role=ActorRole.THIEF).role is ActorRole.THIEF
    for bad in ("police", "POLICE", "thief", None, True, 0):
        with pytest.raises(ValueError):
            state(role=bad)


@pytest.mark.parametrize("good", [1, 2, 7, 10_000])
def test_a_structurally_valid_step_is_any_positive_int(good: int) -> None:
    assert state(step=good).step == good


@pytest.mark.parametrize("bad", [0, -1, -10, True, False, 1.0, "1", None, complex(1)])
def test_a_step_that_is_not_a_positive_int_is_refused(bad: object) -> None:
    """`True` is an `int` in Python, so bools are rejected by exact type, not by value."""
    with pytest.raises(ValueError):
        state(step=bad)


def test_no_board_bound_is_applied_to_a_structurally_valid_position() -> None:
    """`Position` itself admits any int, and this value adds no geometry of its own."""
    far = Position(9_999, 9_999)
    assert state(self_pos=far, barriers=(far,)).self_pos == far


def test_the_snapshot_is_frozen_slotted_and_value_equal() -> None:
    snapshot = state()
    with pytest.raises(dataclasses.FrozenInstanceError):
        snapshot.step = 2  # type: ignore[misc]
    assert not hasattr(snapshot, "__dict__")
    assert SealedState.__slots__ == FIELDS
    assert snapshot == state()


@pytest.mark.parametrize(
    "differs",
    [
        {"config_sha256": Sha256Digest("f" * 64)},
        {"self_pos": Position(3, 2)},
        {"barriers": (Position(1, 1),)},
        {"step": 2},
        {"role": ActorRole.THIEF},
    ],
)
def test_a_snapshot_differing_in_any_single_member_is_unequal(differs: dict[str, object]) -> None:
    """Guards against a member being silently dropped from the sealed material."""
    assert state(**differs) != state()


def test_the_snapshot_neither_serializes_nor_hashes_nor_commits() -> None:
    from mars777_police.app import sealed_record_values

    for absent in NO_CODEC:
        assert not hasattr(SealedState, absent)
    for forbidden in ("json", "hashlib", "hmac", "Board", "LocalTruth", "LocalTurnService"):
        assert not hasattr(sealed_record_values, forbidden)


def test_the_snapshot_is_on_the_app_surface_but_not_the_peer_facade() -> None:
    from mars777_police import app
    from mars777_police.app import peer_messages, sealed_record_values

    assert app.SealedState is sealed_record_values.SealedState
    assert "SealedState" in app.__all__
    assert not hasattr(peer_messages, "SealedState")
