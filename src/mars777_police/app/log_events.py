"""How one line of the official log is written.

Every event here is a *projection* of evidence some other owner already holds -
a sealed record, a disclosed turn, an acknowledgement, a released nonce, the
emission a reveal carried - into the frozen `LOG_CONTRACT.md` shape. Nothing is
computed, verified or decided: `log_document` decides which events exist and in
what order, and these decide only how each one is spelled.

The shared cores are reused field for field - `audit_disclosure_writer` for the
sealed entry, `scent_json` for the deposits - so an event and the disclosure the
peer receives cannot drift into two spellings of one fact."""

from .audit_disclosure import DisclosedTurn
from .audit_disclosure_writer import action_value, entry_value, state_value
from .audit_runtime import AuditRuntime
from .capture_transcript import CaptureRecord
from .outbound_evidence_values import SealedTurnRecord
from .protocol_values import Sha256Digest
from .scent_json import Emission, scent_fields
from .sealed_record_values import ActorRole, SealedState
from .turn_protocol_state import AckEvidence

COMMIT, ACK, REVEAL = "commit", "ack", "reveal"
"""The three event phases; `JDEC-007` keeps commit, ack and reveal separate."""


def own_commit(record: SealedTurnRecord, role: ActorRole) -> dict[str, object]:
    """Our own sealed turn, as the shared core plus the local annotations."""
    entry = dict(entry_value(record, role.value))
    entry["phase"], entry["verified"] = COMMIT, None
    return entry


def capture_fields(row: CaptureRecord | None) -> dict[str, object]:
    """What this reveal asked about capture and what came back.

    A turn that was sealed but never revealed produced no answer at all, and says
    so with nulls rather than borrowing `NO_QUESTION` - that token means "the
    reveal asked nothing", a different fact from "there was no reveal"."""
    if row is None:
        return {"capture_claim": None, "capture_answer": None}
    claim = row.claim
    return {
        "capture_claim": None if claim is None else [claim.cell.row, claim.cell.col],
        "capture_answer": row.answer.value,
    }


def own_reveal(
    record: SealedTurnRecord, role: ActorRole, row: CaptureRecord | None, scent: Emission
) -> dict[str, object]:
    """What we revealed for that turn: the action, the sentence and the answer."""
    return {
        "phase": REVEAL,
        "sub_game": record.cursor.sub_game,
        "step": record.cursor.step,
        "role": role.value,
        "move": action_value(record.action),
        "hint": record.hint,
        **capture_fields(row),
        **scent_fields(scent),
    }


def peer_state(turn: DisclosedTurn, role: ActorRole) -> dict[str, object]:
    """The peer's disclosed snapshot, through the one state representation."""
    state = SealedState(
        Sha256Digest(turn.config_sha256), turn.self_pos, turn.barriers, turn.step, role
    )
    return state_value(state)


def peer_commit(turn: DisclosedTurn, verified: bool | None) -> dict[str, object]:
    """One disclosed peer turn, with the verdict we actually reached for it."""
    role = ActorRole(turn.role)
    return {
        "phase": COMMIT,
        "step": turn.step,
        "sub_game": turn.sub_game,
        "role": turn.role,
        "move": action_value(turn.move),
        "intent": turn.intent,
        "hint": turn.hint,
        "commit": turn.commit,
        "state": peer_state(turn, role),
        "verified": verified,
    }


def peer_reveal(
    turn: DisclosedTurn, row: CaptureRecord | None, scent: Emission
) -> dict[str, object]:
    """The peer's revealed action and sentence, with the answer we gave it.

    *scent* is what the reveal really carried live, never what the disclosure
    says - the two were proved identical before this document exists."""
    return {
        "phase": REVEAL,
        "sub_game": turn.sub_game,
        "step": turn.step,
        "role": turn.role,
        "move": action_value(turn.move),
        "hint": turn.hint,
        **capture_fields(row),
        **scent_fields(scent),
    }


def verified_at(step: int, tampered_step: int | None) -> bool | None:
    """`True` up to the failure, `False` at it, `null` after: nothing was checked there."""
    if tampered_step is None:
        return True
    if step < tampered_step:
        return True
    return False if step == tampered_step else None


def ack_event(ack: AckEvidence, sub_game: int) -> dict[str, object]:
    """One acknowledgement event, in the three frozen §C fields.

    `ack_of_step` is both the acked step and this event's step association, so
    it is written once rather than twice: `LOG_CONTRACT.md` asks that no field
    be duplicated inside a single event.
    """
    return {
        "phase": ACK,
        "sub_game": sub_game,
        "ack_of_step": ack.cursor.step,
        "ack_commit": ack.h_commit.value,
        "by_role": ack.by_role.value,
    }


def nonce_entry(step: int, role: str, nonce: str) -> dict[str, object]:
    """One released nonce, attached by `(step, role)` as the contract requires."""
    return {"step": step, "role": role, "nonce": nonce}


def final_reveal(
    records: tuple[SealedTurnRecord, ...], role: ActorRole, audit: AuditRuntime
) -> list[dict[str, object]]:
    """Every nonce this sub-game released, ours and the peer's, by step and role."""
    peer_role = audit.context.peer_role.value
    ours = [nonce_entry(record.cursor.step, role.value, record.nonce.value) for record in records]
    return ours + [
        nonce_entry(cursor.step, peer_role, nonce.value)
        for cursor, nonce in sorted(audit.nonces.items(), key=lambda item: item[0].step)
    ]
