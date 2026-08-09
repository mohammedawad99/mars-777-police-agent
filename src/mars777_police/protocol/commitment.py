"""The sealed commitment record and the unkeyed SHA-256 computed over it.

`H_commit = SHA256(canonical_json(sealed_record))` over the eight members Ch 5
p.50 names — `{state, move, intent, hint, step, role, sub_game, nonce}` — with
every member mapped by hand. Nothing here reflects over an object: a generic
encoder would silently follow whatever field a value grows next, and the point of
this key set is that it cannot grow.

Two things this module deliberately does *not* do. It does not sort or repair
barriers: `SealedState` already fixed that order, and re-sorting here would hide
a producer defect behind bytes that happen to agree. And it does not judge - a
digest that differs comes back as `False`, because `E-HASH-MISMATCH` and
`FinalAuditVerdict.TAMPERED` belong to the audit consumer above this layer, not
inside a hash function.

The same `compute_commitment` serves both the initial commit and the later
recomputation once the nonce is revealed. Two code paths could drift, and a
drifting verifier reports tampering that never happened.
"""

import hashlib

from ..app.protocol_values import NonceValue, Sha256Digest
from ..app.sealed_record_values import ActorRole, Intent, SealedState
from ..app.turn_cursor import TurnCursor
from ..domain.actions import BarrierAction, MoveAction, PhysicalAction
from .canonical import canonical_json_bytes, canonical_text


def canonical_action_value(action: PhysicalAction) -> dict[str, object]:
    """Map a physical action to NDEC-001's tagged object, exactly two keys."""
    if type(action) is MoveAction:
        return {"kind": "MOVE", "value": action.move.value}
    if type(action) is BarrierAction:
        return {"kind": "BARRIER", "value": [action.target.row, action.target.col]}
    raise ValueError(f"action must be a MoveAction or BarrierAction, got {type(action).__name__}")


def canonical_state_value(state: SealedState) -> dict[str, object]:
    """Map the own-known snapshot to JDEC-012's five keys, order untouched."""
    if type(state) is not SealedState:
        raise ValueError(f"state must be a SealedState, got {type(state).__name__}")
    return {
        "config_sha256": state.config_sha256.value,
        "self_pos": [state.self_pos.row, state.self_pos.col],
        "barriers": [[barrier.row, barrier.col] for barrier in state.barriers],
        "step": state.step,
        "role": state.role.value,
    }


def _require(value: object, expected: type, name: str) -> None:
    if type(value) is not expected:
        raise ValueError(f"{name} must be a {expected.__name__}, got {type(value).__name__}")


def build_sealed_record(
    *,
    state: SealedState,
    action: PhysicalAction,
    intent: Intent,
    hint: str,
    cursor: TurnCursor,
    role: ActorRole,
    nonce: NonceValue,
) -> dict[str, object]:
    """Assemble the exact eight-member record from already-valid semantic values."""
    _require(state, SealedState, "state")
    _require(intent, Intent, "intent")
    _require(hint, str, "hint")
    _require(cursor, TurnCursor, "cursor")
    _require(role, ActorRole, "role")
    _require(nonce, NonceValue, "nonce")
    move = canonical_action_value(action)
    if state.step != cursor.step:
        raise ValueError(
            f"state.step {state.step} must equal the cursor step {cursor.step};"
            " a self-contradictory record is never hashed"
        )
    if state.role is not role:
        raise ValueError(
            f"state.role {state.role.value!r} must equal the sealed role {role.value!r};"
            " a self-contradictory record is never hashed"
        )
    return {
        "state": canonical_state_value(state),
        "move": move,
        "intent": intent.value,
        "hint": canonical_text(hint),
        "step": cursor.step,
        "role": role.value,
        "sub_game": cursor.sub_game,
        "nonce": nonce.value,
    }


def compute_commitment(
    *,
    state: SealedState,
    action: PhysicalAction,
    intent: Intent,
    hint: str,
    cursor: TurnCursor,
    role: ActorRole,
    nonce: NonceValue,
) -> Sha256Digest:
    """Unkeyed SHA-256 over the canonical sealed bytes.

    Used unchanged for the initial commitment and for the later recomputation
    once the previously-secret nonce is revealed.
    """
    record = build_sealed_record(
        state=state,
        action=action,
        intent=intent,
        hint=hint,
        cursor=cursor,
        role=role,
        nonce=nonce,
    )
    return Sha256Digest(hashlib.sha256(canonical_json_bytes(record)).hexdigest())


def commitment_matches(expected: Sha256Digest, recomputed: Sha256Digest) -> bool:
    """Compare two digests. Inequality is a result, not a failure or a verdict."""
    _require(expected, Sha256Digest, "expected")
    _require(recomputed, Sha256Digest, "recomputed")
    return expected == recomputed
