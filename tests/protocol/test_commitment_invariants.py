"""The two cross-component builder invariants (Stage 4E-R9-RESUME).

The sealed record records `step` and `role` twice - once at the top level and
once inside `state` - which Stage 4E-R9-R1 froze deliberately rather than
trimming to a single copy. The price of that duplication is that the two copies
can disagree, so the builder refuses a contradictory record **before** anything
is hashed.

These are local composition defects, not peer tampering: nothing has been hashed,
no peer has sent anything, and no verdict is involved. Hashing a
self-contradictory record would be the actual bug, because the digest would be
perfectly valid and permanently unreproducible for the right reasons.
"""

import pytest

from mars777_police.app.protocol_values import NonceValue, Sha256Digest
from mars777_police.app.sealed_record_values import ActorRole, Intent, SealedState
from mars777_police.app.turn_cursor import TurnCursor
from mars777_police.domain.actions import MoveAction
from mars777_police.domain.board import Position
from mars777_police.domain.rules import Move
from mars777_police.protocol.commitment import build_sealed_record

STATE = SealedState(
    config_sha256=Sha256Digest("1" * 64),
    self_pos=Position(3, 4),
    barriers=(Position(0, 0), Position(2, 2)),
    step=3,
    role=ActorRole.POLICE,
)
CURSOR = TurnCursor(1, 3)


def record(**over: object) -> dict[str, object]:
    kwargs: dict[str, object] = {
        "state": STATE,
        "action": MoveAction(Move.N),
        "intent": Intent.LIE,
        "hint": "barrier",
        "cursor": CURSOR,
        "role": ActorRole.POLICE,
        "nonce": NonceValue("a" * 32),
    }
    return build_sealed_record(**(kwargs | over))  # type: ignore[arg-type]


def test_a_step_that_disagrees_with_the_cursor_is_refused_before_hashing() -> None:
    """`state.step` and the top-level `step` are one fact recorded twice."""
    with pytest.raises(ValueError, match="step"):
        record(cursor=TurnCursor(1, 4))
    with pytest.raises(ValueError, match="step"):
        record(cursor=TurnCursor(2, 9))


def test_a_role_that_disagrees_with_the_state_is_refused_before_hashing() -> None:
    with pytest.raises(ValueError, match="role"):
        record(role=ActorRole.THIEF)
    thief_state = SealedState(
        config_sha256=Sha256Digest("1" * 64),
        self_pos=Position(3, 4),
        barriers=(),
        step=3,
        role=ActorRole.THIEF,
    )
    with pytest.raises(ValueError, match="role"):
        record(state=thief_state)


def test_a_contradictory_record_yields_no_digest_material_at_all() -> None:
    """The refusal happens in the builder, so nothing partial escapes to be hashed."""
    with pytest.raises(ValueError):
        record(cursor=TurnCursor(1, 4))
    assert record()["step"] == 3


def test_the_builder_constructs_no_peer_message() -> None:
    from mars777_police.protocol import commitment

    for absent in ("Commitment", "Acknowledgement", "Reveal", "FinalNonceReveal"):
        assert not hasattr(commitment, absent)
