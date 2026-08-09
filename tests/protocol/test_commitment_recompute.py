"""Recomputation, comparison and eight-field sensitivity (Stage 4E-R9-RESUME).

Recomputation is not a second function. `compute_commitment` is one pure
primitive, used once at commit time and again after the nonce is revealed. Two
code paths could drift, and a drifting verifier reports tampering that never
happened - which under Ch 5 §5.4 voids a match with no appeal.

The sensitivity block is the guard against the quiet failure this codec could
have: a sealed member that is accepted, validated and then never actually
written into the hashed bytes. Each member is varied alone and must move the
digest. `step` and `role` are duplicated by contract, so they can only be varied
in both locations at once without breaking the builder invariants.
"""

import pytest

from mars777_police.app.protocol_values import NonceValue, Sha256Digest
from mars777_police.app.sealed_record_values import ActorRole, Intent, SealedState
from mars777_police.app.turn_cursor import TurnCursor
from mars777_police.domain.actions import MoveAction
from mars777_police.domain.board import Position
from mars777_police.domain.rules import Move
from mars777_police.protocol.canonical import canonical_json_bytes
from mars777_police.protocol.commitment import (
    build_sealed_record,
    commitment_matches,
    compute_commitment,
)

BARRIERS = (Position(0, 1), Position(4, 5))
A: dict[str, object] = {
    "state": SealedState(Sha256Digest("0" * 64), Position(2, 3), BARRIERS, 7, ActorRole.POLICE),
    "action": MoveAction(Move.N),
    "intent": Intent.TRUTH,
    "hint": "\u00e9",
    "cursor": TurnCursor(2, 7),
    "role": ActorRole.POLICE,
    "nonce": NonceValue("0123456789abcdef0123456789abcdef"),
}
A_SHA = "6f82737e6c3031307c5b537484640a9528a34c125295739434690fde110a0dd2"


def test_the_same_primitive_recomputes_the_digest_from_the_revealed_nonce() -> None:
    """One deterministic function, used at commit time and again at audit time."""
    initial = compute_commitment(**A)  # type: ignore[arg-type]
    revealed = NonceValue("0123456789abcdef0123456789abcdef")
    recomputed = compute_commitment(**{**A, "nonce": revealed})  # type: ignore[arg-type]
    assert initial == recomputed and initial.value == recomputed.value == A_SHA
    assert commitment_matches(initial, recomputed) is True


def test_a_recomputation_with_a_different_nonce_simply_does_not_match() -> None:
    initial = compute_commitment(**A)  # type: ignore[arg-type]
    other = compute_commitment(**{**A, "nonce": NonceValue("b" * 32)})  # type: ignore[arg-type]
    assert other.value != A_SHA
    assert commitment_matches(initial, other) is False


def test_the_computation_is_deterministic_across_repeated_calls() -> None:
    assert len({compute_commitment(**A).value for _ in range(5)}) == 1  # type: ignore[arg-type]


def test_comparison_returns_a_plain_bool_and_never_raises_or_judges() -> None:
    """Inequality is comparison material; TAMPERED lives above this layer."""
    from mars777_police.protocol import commitment

    result = commitment_matches(Sha256Digest("0" * 64), Sha256Digest("1" * 64))
    assert result is False and type(result) is bool
    assert commitment_matches(Sha256Digest("0" * 64), Sha256Digest("0" * 64)) is True
    for absent in ("FinalAuditVerdict", "TAMPERED", "hmac", "secrets", "E_HASH_MISMATCH"):
        assert not hasattr(commitment, absent)


@pytest.mark.parametrize("bad", ["0" * 64, None, True, 0, NonceValue("a" * 32)])
def test_comparison_refuses_anything_that_is_not_an_exact_digest(bad: object) -> None:
    with pytest.raises(ValueError):
        commitment_matches(Sha256Digest("0" * 64), bad)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        commitment_matches(bad, Sha256Digest("0" * 64))  # type: ignore[arg-type]


SENSITIVE: list[tuple[str, dict[str, object]]] = [
    (
        "state.config_sha256",
        {
            "state": SealedState(
                Sha256Digest("2" * 64), Position(2, 3), BARRIERS, 7, ActorRole.POLICE
            )
        },
    ),
    (
        "state.self_pos",
        {
            "state": SealedState(
                Sha256Digest("0" * 64), Position(3, 2), BARRIERS, 7, ActorRole.POLICE
            )
        },
    ),
    (
        "state.barriers",
        {
            "state": SealedState(
                Sha256Digest("0" * 64), Position(2, 3), (Position(0, 1),), 7, ActorRole.POLICE
            )
        },
    ),
    ("move", {"action": MoveAction(Move.STAY)}),
    ("intent", {"intent": Intent.LIE}),
    ("hint", {"hint": "different"}),
    ("sub_game", {"cursor": TurnCursor(3, 7)}),
    ("nonce", {"nonce": NonceValue("c" * 32)}),
]


@pytest.mark.parametrize(("member", "change"), SENSITIVE)
def test_changing_any_single_sealed_member_changes_the_bytes_and_the_digest(
    member: str, change: dict[str, object]
) -> None:
    """Guards against a member being accepted but never written into the bytes."""
    altered = {**A, **change}
    baseline = canonical_json_bytes(build_sealed_record(**A))  # type: ignore[arg-type]
    assert canonical_json_bytes(build_sealed_record(**altered)) != baseline  # type: ignore[arg-type]
    assert compute_commitment(**altered).value != A_SHA  # type: ignore[arg-type]


def test_a_synchronised_step_change_moves_both_locations_and_the_digest() -> None:
    """`step` is duplicated by contract, so it can only be varied in both places."""
    altered = {
        **A,
        "state": SealedState(Sha256Digest("0" * 64), Position(2, 3), BARRIERS, 8, ActorRole.POLICE),
        "cursor": TurnCursor(2, 8),
    }
    built = build_sealed_record(**altered)  # type: ignore[arg-type]
    assert built["step"] == 8
    assert built["state"]["step"] == 8  # type: ignore[index]
    assert compute_commitment(**altered).value != A_SHA  # type: ignore[arg-type]


def test_a_synchronised_role_change_moves_both_locations_and_the_digest() -> None:
    altered = {
        **A,
        "state": SealedState(Sha256Digest("0" * 64), Position(2, 3), BARRIERS, 7, ActorRole.THIEF),
        "role": ActorRole.THIEF,
    }
    built = build_sealed_record(**altered)  # type: ignore[arg-type]
    assert built["role"] == "thief"
    assert built["state"]["role"] == "thief"  # type: ignore[index]
    assert compute_commitment(**altered).value != A_SHA  # type: ignore[arg-type]
