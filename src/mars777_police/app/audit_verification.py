"""Matching a disclosure to the sub-game it claims, and recomputing its hashes.

This is the checking half of the final audit, kept apart from the lifecycle
that decides when it may run. It holds nothing: every input is passed in, and
what comes back is an `AuditOutcome` derived only from evidence.

**Live evidence is checked before any hash.** A disclosure that already
contradicts what we saw - a different digest, hint, role or step, or an action
that is not the one revealed - fails without recomputing anything, because the
recomputation would otherwise be answering a question about a turn that never
happened. Only then are the three sealed members opened and SHA-256 run.

**A malformed member is a failed audit, not a crash.** A config digest of the
wrong shape or an intent outside the vocabulary means the peer cannot produce
the state it committed to, so `ValueError` from a domain constructor is the
audit's answer, not an exception for a caller to handle.
"""

from ..domain.actions import BarrierAction, MoveAction
from .audit_disclosure import DisclosedTurn, identity
from .audit_values import AuditOutcome, SubGameContext
from .ports import CommitmentPort
from .protocol_errors import StaleMessageError
from .protocol_values import FinalAuditVerdict, NonceValue, Sha256Digest
from .sealed_record_values import ActorRole, Intent, SealedState
from .turn_cursor import TurnCursor
from .turn_protocol_state import TurnEvidence


def require_identity(document: dict[str, object], context: SubGameContext) -> None:
    """Refuse a document that is not this sub-game's, before anything is opened."""
    expected = (
        context.game_id,
        context.game_uid,
        context.sub_game,
        context.config_sha256.value,
    )
    if identity(document) != expected:
        raise StaleMessageError("the disclosed log is not this sub-game's")


def by_cursor(
    disclosed: tuple[DisclosedTurn, ...], expected: tuple[TurnCursor, ...]
) -> dict[TurnCursor, DisclosedTurn]:
    """The disclosed turns by cursor - exactly the played ones, each once."""
    indexed: dict[TurnCursor, DisclosedTurn] = {}
    for turn in disclosed:
        cursor = TurnCursor(turn.sub_game, turn.step)
        if cursor in indexed:
            raise StaleMessageError("the disclosed log repeats a turn")
        indexed[cursor] = turn
    if tuple(sorted(indexed, key=lambda one: one.step)) != expected:
        raise StaleMessageError("the disclosed log does not match the played turns")
    return indexed


def verdict_for(
    evidence: tuple[TurnEvidence, ...],
    disclosed: dict[TurnCursor, DisclosedTurn],
    nonces: dict[TurnCursor, NonceValue],
    peer: ActorRole,
    commitments: CommitmentPort,
) -> AuditOutcome:
    """The first step that fails to verify decides the whole sub-game."""
    for record in sorted(evidence, key=lambda one: one.cursor.step):
        if not turn_verifies(record, disclosed[record.cursor], nonces, peer, commitments):
            return AuditOutcome(FinalAuditVerdict.TAMPERED, record.cursor.step)
    return AuditOutcome(FinalAuditVerdict.VERIFIED_OK)


def turn_verifies(
    live: TurnEvidence,
    turn: DisclosedTurn,
    nonces: dict[TurnCursor, NonceValue],
    peer: ActorRole,
    commitments: CommitmentPort,
) -> bool:
    """Cross-check the log against live facts, then recompute the digest."""
    action = live.action
    if not isinstance(action, MoveAction | BarrierAction):
        return False
    disclosed = (turn.commit, turn.hint, turn.role, turn.step, turn.move)
    if disclosed != (live.h_commit.value, live.hint, peer.value, live.cursor.step, action):
        return False
    try:
        state = SealedState(
            Sha256Digest(turn.config_sha256), turn.self_pos, turn.barriers, turn.step, peer
        )
        intent = Intent(turn.intent)
    except ValueError:
        return False
    recomputed = commitments.recompute(
        state=state,
        action=action,
        intent=intent,
        hint=live.hint,
        cursor=live.cursor,
        role=peer,
        nonce=nonces[live.cursor],
    )
    return commitments.matches(live.h_commit, recomputed)
