"""The acknowledgement peer message: a turn cursor and the acknowledged digest.

Ch 5 §5.3.2 (p.51) gives its whole content - *the opponent confirms it received
the commitment and is locked onto it* - which PRD06-FR-082 renders as binding
receipt of a **specific** `H_commit` for a **specific** `(sub_game, step)`. So
the message is that cursor plus that digest, and nothing else.

Three absences are deliberate (Stage 4E-R3). `by_role` is LOCAL-LOG-ATTRIBUTION
the writer derives from send/receive direction and the `CONFIG_LOCKED` role map,
so it is never transmitted and so never forgeable; `ack_of_step` is the persisted
name of `cursor.step` rather than a second field; and an acknowledgement is
positive by existing, so there is no `accepted` flag. `Commitment` carries the
same two component types and is still a different peer-message family - the class
identity is what says which.
"""

import dataclasses

import pytest

from mars777_police.app.peer_messages import Acknowledgement, Commitment, TurnCursor
from mars777_police.app.protocol_values import Sha256Digest
from mars777_police.domain.config_model import FIRST_SUB_GAME

ZEROES = "0" * 64
EFFS = "f" * 64
DIGEST = Sha256Digest(ZEROES)
CURSOR = TurnCursor(FIRST_SUB_GAME, 1)


def test_the_acknowledgement_carries_exactly_the_cursor_and_the_acked_digest() -> None:
    assert tuple(f.name for f in dataclasses.fields(Acknowledgement)) == ("cursor", "h_commit")


ABSENT = ["by_role", "ack_of_step", "accepted", "ok", "valid", "verified", "success"]
ABSENT += ["timestamp", "message_id", "phase", "kind", "role", "game_id", "game_uid"]
ABSENT += ["state", "move", "intent", "hint", "nonce", "sealed_record"]


@pytest.mark.parametrize("absent", ABSENT)
def test_the_acknowledgement_carries_no_further_field(absent: str) -> None:
    """`by_role` is derived locally; `ack_of_step` is `cursor.step` persisted."""
    assert not hasattr(Acknowledgement(CURSOR, DIGEST), absent)


def test_the_acknowledgement_is_frozen_slotted_and_value_equal() -> None:
    ack = Acknowledgement(CURSOR, DIGEST)
    with pytest.raises(dataclasses.FrozenInstanceError):
        ack.h_commit = Sha256Digest(EFFS)  # type: ignore[misc]
    assert not hasattr(ack, "__dict__")
    assert Acknowledgement.__slots__ == ("cursor", "h_commit")
    assert ack == Acknowledgement(CURSOR, DIGEST)
    assert ack != Acknowledgement(TurnCursor(2, 1), DIGEST)
    assert ack != Acknowledgement(CURSOR, Sha256Digest(EFFS))


def test_the_acknowledgement_reads_back_the_cursor_and_digest_it_was_given() -> None:
    ack = Acknowledgement(TurnCursor(3, 7), Sha256Digest(EFFS))
    assert ack.cursor == TurnCursor(3, 7)
    assert ack.cursor.step == 7
    assert ack.h_commit == Sha256Digest(EFFS)


@pytest.mark.parametrize("value", [(1, 1), {"sub_game": 1, "step": 1}, [1, 1], None, True, 1])
def test_a_cursor_of_the_wrong_type_is_refused_never_coerced(value: object) -> None:
    with pytest.raises(ValueError):
        Acknowledgement(value, DIGEST)  # type: ignore[arg-type]


@pytest.mark.parametrize("value", [ZEROES, ZEROES.upper(), b"0" * 64, None, True, 0])
def test_a_digest_of_the_wrong_type_is_refused_never_wrapped(value: object) -> None:
    """A valid 64-hex string is still refused: one authoritative constructor."""
    with pytest.raises(ValueError):
        Acknowledgement(CURSOR, value)  # type: ignore[arg-type]


def test_subclasses_of_the_composed_values_are_refused() -> None:
    """Exact identity, not `isinstance`: a subclass could weaken validation."""

    class LooseCursor(TurnCursor):
        pass

    class LooseDigest(Sha256Digest):
        pass

    with pytest.raises(ValueError):
        Acknowledgement(LooseCursor(FIRST_SUB_GAME, 1), DIGEST)
    with pytest.raises(ValueError):
        Acknowledgement(CURSOR, LooseDigest(ZEROES))


def test_the_acknowledgement_is_a_distinct_family_from_the_commitment() -> None:
    """Same component types, different protocol meaning; the class says which."""
    ack = Acknowledgement(CURSOR, DIGEST)
    commitment = Commitment(CURSOR, DIGEST)
    assert type(ack) is Acknowledgement
    assert type(commitment) is Commitment
    assert Acknowledgement is not Commitment
    assert not issubclass(Acknowledgement, Commitment)
    assert not issubclass(Commitment, Acknowledgement)
    assert ack != commitment
    assert commitment != ack


def test_the_acknowledgement_neither_hashes_nor_checks_live_protocol_state() -> None:
    """It stores an already-validated digest; matching it is LIVE validation."""
    for name in ("compute", "verify", "matches", "hexdigest", "is_stale", "expected_cursor"):
        assert not hasattr(Acknowledgement, name)
    outstanding = Sha256Digest(EFFS)
    assert Acknowledgement(CURSOR, DIGEST).h_commit != outstanding


def test_the_acknowledgement_is_on_the_exhaustive_app_surface() -> None:
    from mars777_police import app

    assert app.Acknowledgement is Acknowledgement
    assert "Acknowledgement" in app.__all__
    assert len(app.__all__) == len(set(app.__all__))
