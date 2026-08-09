"""Internal peer-message semantic contracts: the turn cursor and the commitment.

`TurnCursor` is the transmitted identity of a **turn-scoped** message (PRD-02 §8,
FR-044/FR-063) - `(sub_game, step)` and nothing else, with phase admissibility
left to the receiver's own `ProtocolMachine` (FR-021/FR-062). Its sub-game bound
reads the one authoritative FIXED contract in `domain.config_model`; `max_moves`
is per-sub-game locked config and stays LIVE. `Commitment` carries exactly what
`PROTOCOL_TIMELINE.md` event 5 transmits - "`H_commit` only" - plus that
independently-required cursor. Both refuse malformed construction with the
built-in `ValueError` the sibling `FinalAuditVerdict` already raises natively.
"""

import dataclasses

import pytest

from mars777_police.app.peer_messages import Commitment, TurnCursor
from mars777_police.app.protocol_values import Sha256Digest
from mars777_police.domain.config_model import FIRST_SUB_GAME, FIXED_NUM_GAMES

ZEROES = "0" * 64
EFFS = "f" * 64
DIGEST = Sha256Digest(ZEROES)
CURSOR = TurnCursor(FIRST_SUB_GAME, 1)
NOT_INTS = [None, True, False, 1.0, "1", b"1", [1], object()]


def test_the_cursor_carries_exactly_sub_game_and_step() -> None:
    assert tuple(f.name for f in dataclasses.fields(TurnCursor)) == ("sub_game", "step")


@pytest.mark.parametrize("absent", ["phase", "game_id", "game_uid", "role", "kind", "max_moves"])
def test_the_cursor_carries_no_further_identity_or_configuration(absent: str) -> None:
    assert not hasattr(TurnCursor(FIRST_SUB_GAME, 1), absent)


def test_the_cursor_is_frozen_slotted_and_value_equal() -> None:
    cursor = TurnCursor(2, 3)
    with pytest.raises(dataclasses.FrozenInstanceError):
        cursor.step = 4  # type: ignore[misc]
    assert not hasattr(cursor, "__dict__")
    assert TurnCursor.__slots__ == ("sub_game", "step")
    assert cursor == TurnCursor(2, 3)
    assert cursor != TurnCursor(2, 4)
    assert cursor != TurnCursor(3, 3)


@pytest.mark.parametrize("sub_game", [FIRST_SUB_GAME, 2, 5, FIXED_NUM_GAMES])
def test_every_counted_sub_game_is_accepted(sub_game: int) -> None:
    assert TurnCursor(sub_game, 1).sub_game == sub_game


@pytest.mark.parametrize("step", [1, 2, 35, 36, 10_000])
def test_any_positive_step_is_structurally_valid(step: int) -> None:
    """`step <= max_moves` is LIVE: `max_moves` is per-sub-game locked config."""
    assert TurnCursor(FIRST_SUB_GAME, step).step == step


@pytest.mark.parametrize("sub_game", [FIRST_SUB_GAME - 1, 0, -1, FIXED_NUM_GAMES + 1, 99])
def test_a_sub_game_outside_the_fixed_series_is_refused(sub_game: int) -> None:
    with pytest.raises(ValueError):
        TurnCursor(sub_game, 1)


@pytest.mark.parametrize("step", [0, -1, -35])
def test_a_step_below_one_is_refused(step: int) -> None:
    with pytest.raises(ValueError):
        TurnCursor(FIRST_SUB_GAME, step)


@pytest.mark.parametrize("value", NOT_INTS)
def test_a_non_integer_sub_game_is_refused(value: object) -> None:
    with pytest.raises(ValueError):
        TurnCursor(value, 1)  # type: ignore[arg-type]


@pytest.mark.parametrize("value", NOT_INTS)
def test_a_non_integer_step_is_refused(value: object) -> None:
    with pytest.raises(ValueError):
        TurnCursor(FIRST_SUB_GAME, value)  # type: ignore[arg-type]


def test_booleans_are_refused_although_they_are_ints() -> None:
    """`True` would silently mean sub-game 1; the project never coerces."""
    for cursor in ((True, 1), (FIRST_SUB_GAME, True)):
        with pytest.raises(ValueError):
            TurnCursor(*cursor)  # type: ignore[arg-type]


def test_the_commitment_carries_exactly_the_cursor_and_one_digest() -> None:
    assert tuple(f.name for f in dataclasses.fields(Commitment)) == ("cursor", "h_commit")


LEAKS = ["game_id", "game_uid", "role", "state", "move", "intent", "hint", "nonce"]
LEAKS += ["sealed_record", "timestamp", "message_id", "phase", "kind", "accepted", "verified"]


@pytest.mark.parametrize("absent", LEAKS)
def test_the_commitment_transmits_nothing_but_the_digest(absent: str) -> None:
    """Event 5 transmits `H_commit` **only**; the cursor is separately required."""
    assert not hasattr(Commitment(CURSOR, DIGEST), absent)


def test_the_commitment_is_frozen_slotted_and_value_equal() -> None:
    commitment = Commitment(CURSOR, DIGEST)
    with pytest.raises(dataclasses.FrozenInstanceError):
        commitment.h_commit = Sha256Digest(EFFS)  # type: ignore[misc]
    assert not hasattr(commitment, "__dict__")
    assert Commitment.__slots__ == ("cursor", "h_commit")
    assert commitment == Commitment(CURSOR, DIGEST)
    assert commitment != Commitment(TurnCursor(2, 1), DIGEST)
    assert commitment != Commitment(CURSOR, Sha256Digest(EFFS))


@pytest.mark.parametrize("value", [(1, 1), {"sub_game": 1, "step": 1}, [1, 1], None, True, 1])
def test_a_cursor_of_the_wrong_type_is_refused_never_coerced(value: object) -> None:
    with pytest.raises(ValueError):
        Commitment(value, DIGEST)  # type: ignore[arg-type]


@pytest.mark.parametrize("value", [ZEROES, ZEROES.upper(), b"0" * 64, None, True, 0])
def test_a_digest_of_the_wrong_type_is_refused_never_wrapped(value: object) -> None:
    """A valid 64-hex string is still refused: one authoritative constructor."""
    with pytest.raises(ValueError):
        Commitment(CURSOR, value)  # type: ignore[arg-type]


def test_the_message_module_neither_hashes_nor_names_a_second_family() -> None:
    from mars777_police.app import peer_messages

    for forbidden in ("hashlib", "sha256", "hexdigest", "compute", "json", "enum"):
        assert not hasattr(peer_messages, forbidden)
    for family in ("Reveal", "MoveValidation", "FinalAudit", "Declaration", "ResultAgreement"):
        assert not hasattr(peer_messages, family)


def test_both_public_types_are_on_the_exhaustive_app_surface() -> None:
    from mars777_police import app

    assert app.TurnCursor is TurnCursor
    assert app.Commitment is Commitment
    assert {"TurnCursor", "Commitment"} <= set(app.__all__)
    assert not {"FIRST_SUB_GAME", "FIXED_NUM_GAMES"} & set(app.__all__)
