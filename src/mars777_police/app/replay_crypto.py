"""Per-step commitment correspondence, asked of the authority that owns it.

`REPLAY-002` requires the viewer to recompute SHA-256 over the revealed data and
compare it with the stored commitment, showing `Verified OK` or `TAMPERED`. It
does **not** require the viewer to own that computation, and it must not: this
module builds the eight-member sealed record from what the log disclosed and
hands it to the same `CommitmentPort` the live audit uses. There is no hashing
here, and no second opinion about what a commitment is.

**Missing evidence is not a verdict.** A commitment whose nonce this side never
received is `NOT_CHECKABLE`, never `Verified OK` and never `TAMPERED`.
"""

from collections.abc import Mapping

from ..domain.actions import PhysicalAction
from ..domain.board import Position
from .ports import CommitmentPort
from .protocol_values import NonceValue, Sha256Digest
from .replay_values import ReplayCheck, ReplayError
from .sealed_record_values import ActorRole, Intent, SealedState
from .turn_cursor import TurnCursor


def _position(raw: object) -> Position:
    if not isinstance(raw, list | tuple) or len(raw) != 2:
        raise ReplayError("a disclosed cell is not a two-member position")
    row, col = raw
    if type(row) is not int or type(col) is not int:
        raise ReplayError("a disclosed cell is not a pair of whole numbers")
    return Position(row, col)


def barriers_of(state: Mapping[str, object]) -> tuple[Position, ...]:
    """Every barrier the disclosed snapshot says stood at that moment."""
    raw = state.get("barriers", ())
    if not isinstance(raw, list | tuple):
        raise ReplayError("a disclosed barrier set is not a list")
    return tuple(_position(one) for one in raw)


def sealed_state(entry: Mapping[str, object], sub_game: int) -> SealedState:
    """Rebuild the disclosed snapshot exactly as the sealed record held it."""
    state = entry["state"]
    if not isinstance(state, Mapping):
        raise ReplayError("a commit entry has no sealed state")
    try:
        return SealedState(
            Sha256Digest(str(state["config_sha256"])),
            _position(state["self_pos"]),
            barriers_of(state),
            int(state["step"]),
            ActorRole(str(state["role"])),
        )
    except (KeyError, ValueError) as failure:
        raise ReplayError(f"a sealed state could not be rebuilt: {failure}") from failure


def check_commit(
    entry: Mapping[str, object],
    action: PhysicalAction,
    nonces: Mapping[int, str],
    commitments: CommitmentPort,
    sub_game: int,
) -> ReplayCheck:
    """The status of one commit entry, decided by the commitment authority.

    *action* arrives already decoded: the wire shape belongs to `transport`, and
    a viewer in the application layer has no business owning a second decoder.
    """
    stored = entry.get("commit")
    if type(stored) is not str:
        return ReplayCheck.NOT_APPLICABLE
    step = entry.get("step")
    if type(step) is not int or step not in nonces:
        return ReplayCheck.NOT_CHECKABLE
    state = sealed_state(entry, sub_game)
    try:
        intent = Intent(str(entry["intent"]))
    except (KeyError, ValueError) as failure:
        raise ReplayError(f"a disclosed turn could not be rebuilt: {failure}") from failure
    recomputed = commitments.recompute(
        state=state,
        action=action,
        intent=intent,
        hint=str(entry.get("hint", "")),
        cursor=TurnCursor(sub_game, step),
        role=state.role,
        nonce=NonceValue(nonces[step]),
    )
    matched = commitments.matches(Sha256Digest(stored), recomputed)
    return ReplayCheck.VERIFIED_OK if matched else ReplayCheck.TAMPERED
