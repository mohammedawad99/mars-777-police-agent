"""Known-answer commitment digests and recomputation (Stage 4E-R9-RESUME).

The three canonical strings and digests below are **supervisor-supplied external
oracles**, verified independently with stdlib `json`/`hashlib` before any of this
production code existed. They are hard-coded literals on purpose: a digest test
that calls the implementation to learn what to expect proves only that the code
agrees with itself, which is exactly the failure mode a commit-reveal scheme
cannot afford.

Recomputation and sensitivity live in `test_commitment_recompute.py`.
"""

import pytest

from mars777_police.app.protocol_values import NonceValue, Sha256Digest
from mars777_police.app.sealed_record_values import ActorRole, Intent, SealedState
from mars777_police.app.turn_cursor import TurnCursor
from mars777_police.domain.actions import BarrierAction, MoveAction
from mars777_police.domain.board import Position
from mars777_police.domain.rules import Move
from mars777_police.protocol.canonical import canonical_json_bytes
from mars777_police.protocol.commitment import build_sealed_record, compute_commitment

A = {
    "state": SealedState(
        Sha256Digest("0" * 64),
        Position(2, 3),
        (Position(0, 1), Position(4, 5)),
        7,
        ActorRole.POLICE,
    ),
    "action": MoveAction(Move.N),
    "intent": Intent.TRUTH,
    "hint": "é",
    "cursor": TurnCursor(2, 7),
    "role": ActorRole.POLICE,
    "nonce": NonceValue("0123456789abcdef0123456789abcdef"),
}
A_JSON = '{"hint":"é","intent":"truth","move":{"kind":"MOVE","value":"N"},"nonce":"0123456789abcdef0123456789abcdef","role":"police","state":{"barriers":[[0,1],[4,5]],"config_sha256":"0000000000000000000000000000000000000000000000000000000000000000","role":"police","self_pos":[2,3],"step":7},"step":7,"sub_game":2}'  # noqa: E501
A_SHA = "6f82737e6c3031307c5b537484640a9528a34c125295739434690fde110a0dd2"

B = {
    "state": SealedState(
        Sha256Digest("f" * 64),
        Position(6, 4),
        (Position(1, 0), Position(1, 2), Position(3, 3)),
        12,
        ActorRole.THIEF,
    ),
    "action": MoveAction(Move.STAY),
    "intent": Intent.LIE,
    "hint": "שלום",
    "cursor": TurnCursor(6, 12),
    "role": ActorRole.THIEF,
    "nonce": NonceValue("f" * 32),
}
B_JSON = '{"hint":"שלום","intent":"lie","move":{"kind":"MOVE","value":"STAY"},"nonce":"ffffffffffffffffffffffffffffffff","role":"thief","state":{"barriers":[[1,0],[1,2],[3,3]],"config_sha256":"ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff","role":"thief","self_pos":[6,4],"step":12},"step":12,"sub_game":6}'  # noqa: E501
B_SHA = "7685380fe575ce5a726e4b2b895bf27d0cb1a82f70c1eaf1c0112541d02842cb"

C = {
    "state": SealedState(
        Sha256Digest("1" * 64),
        Position(3, 4),
        (Position(0, 0), Position(2, 2)),
        3,
        ActorRole.POLICE,
    ),
    "action": BarrierAction(Position(5, 6)),
    "intent": Intent.LIE,
    "hint": "barrier",
    "cursor": TurnCursor(1, 3),
    "role": ActorRole.POLICE,
    "nonce": NonceValue("a" * 32),
}
C_JSON = '{"hint":"barrier","intent":"lie","move":{"kind":"BARRIER","value":[5,6]},"nonce":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","role":"police","state":{"barriers":[[0,0],[2,2]],"config_sha256":"1111111111111111111111111111111111111111111111111111111111111111","role":"police","self_pos":[3,4],"step":3},"step":3,"sub_game":1}'  # noqa: E501
C_SHA = "8935e5e2b8f5cd46205c5a24323027ef79d1f4353f7c7f0eae29709ad64d6d34"

VECTORS = [("A", A, A_JSON, A_SHA), ("B", B, B_JSON, B_SHA), ("C", C, C_JSON, C_SHA)]


@pytest.mark.parametrize(("name", "inputs", "text", "sha"), VECTORS)
def test_the_canonical_bytes_equal_the_expected_literal(
    name: str, inputs: dict[str, object], text: str, sha: str
) -> None:
    assert canonical_json_bytes(build_sealed_record(**inputs)) == text.encode("utf-8")  # type: ignore[arg-type]


@pytest.mark.parametrize(("name", "inputs", "text", "sha"), VECTORS)
def test_the_digest_equals_the_independently_derived_expected_value(
    name: str, inputs: dict[str, object], text: str, sha: str
) -> None:
    assert compute_commitment(**inputs).value == sha  # type: ignore[arg-type]
    assert type(compute_commitment(**inputs)) is Sha256Digest  # type: ignore[arg-type]


def test_the_hebrew_vector_carries_literal_utf8_not_escapes() -> None:
    raw = canonical_json_bytes(build_sealed_record(**B))  # type: ignore[arg-type]
    assert "שלום".encode() in raw
    assert b"\\u05" not in raw


def test_the_decomposed_and_composed_hint_produce_identical_bytes_and_digest() -> None:
    """NFC is the only equivalence claimed - nothing wider."""
    decomposed = canonical_json_bytes(build_sealed_record(**{**A, "hint": "é"}))  # type: ignore[arg-type]
    composed = canonical_json_bytes(build_sealed_record(**{**A, "hint": "é"}))  # type: ignore[arg-type]
    assert decomposed == composed == A_JSON.encode("utf-8")
    assert compute_commitment(**{**A, "hint": "é"}).value == A_SHA  # type: ignore[arg-type]
