"""Real audit fixtures: real sealed records, real production crypto, no fakes.

Every digest here comes from `CommitmentRecomputer`, the same adapter the runtime
uses, so a tampering test proves the real comparison failed rather than that a
stand-in disagreed.
"""

from mars777_police.app.audit_runtime import AuditRuntime
from mars777_police.app.audit_values import SubGameContext
from mars777_police.app.peer_final_messages import FinalNonceReveal, NonceRevealEntry
from mars777_police.app.protocol_values import NonceValue, Sha256Digest
from mars777_police.app.sealed_record_values import ActorRole, Intent, SealedState
from mars777_police.app.turn_cursor import TurnCursor
from mars777_police.app.turn_protocol_state import TurnEvidence
from mars777_police.domain.actions import MoveAction
from mars777_police.domain.board import Position
from mars777_police.domain.rules import Move
from mars777_police.protocol.audit_commitment import CommitmentRecomputer

GAME_ID = "mars777-vs-groupx-2026w1-uid0001"
GAME_UID = "uid0001"
SUB_GAME = 1
CONFIG = Sha256Digest("d" * 64)
PEER = ActorRole.THIEF
PEER_GROUP = "GROUP-XY"
NONCES = {1: NonceValue("0" * 32), 2: NonceValue("1" * 32)}
POS = {1: Position(2, 3), 2: Position(2, 4)}
HINTS = {1: "moving north", 2: "moving north again"}
LIVE_ACTION = MoveAction(Move.N)
"""The action the live turn runtime actually observed, as a domain value."""


def context() -> SubGameContext:
    return SubGameContext(GAME_ID, GAME_UID, SUB_GAME, CONFIG, PEER, PEER_GROUP)


def sealed(step: int) -> SealedState:
    return SealedState(CONFIG, POS[step], (), step, PEER)


def digest(step: int) -> Sha256Digest:
    """The real production digest for this turn's sealed record."""
    return CommitmentRecomputer().recompute(
        state=sealed(step),
        action=LIVE_ACTION,
        intent=Intent.TRUTH,
        hint=HINTS[step],
        cursor=TurnCursor(SUB_GAME, step),
        role=PEER,
        nonce=NONCES[step],
    )


def evidence(steps: tuple[int, ...] = (1, 2)) -> tuple[TurnEvidence, ...]:
    """What the live turn runtimes observed for those steps."""
    return tuple(
        TurnEvidence(TurnCursor(SUB_GAME, s), digest(s), LIVE_ACTION, HINTS[s], True) for s in steps
    )


def runtime(steps: tuple[int, ...] = (1, 2)) -> AuditRuntime:
    return AuditRuntime(context(), evidence(steps), CommitmentRecomputer())


def nonce_batch(steps: tuple[int, ...] = (1, 2)) -> FinalNonceReveal:
    return FinalNonceReveal(
        tuple(NonceRevealEntry(TurnCursor(SUB_GAME, s), NONCES[s]) for s in steps)
    )


def entry(step: int) -> dict[str, object]:
    """One SHARED-AUDIT-INPUT entry as the peer would disclose it."""
    return {
        "step": step,
        "sub_game": SUB_GAME,
        "role": PEER.value,
        "move": {"kind": "MOVE", "value": "N"},
        "intent": Intent.TRUTH.value,
        "hint": HINTS[step],
        "commit": digest(step).value,
        "state": {
            "config_sha256": CONFIG.value,
            "self_pos": [POS[step].row, POS[step].col],
            "barriers": [],
            "step": step,
            "role": PEER.value,
        },
    }


def document(steps: tuple[int, ...] = (1, 2), **overrides: object) -> dict[str, object]:
    """A well-formed disclosure, plus any hostile override a test needs."""
    doc: dict[str, object] = {
        "game_id": GAME_ID,
        "game_uid": GAME_UID,
        "sub_game": SUB_GAME,
        "config_sha256": CONFIG.value,
        "entries": [entry(s) for s in steps],
    }
    doc.update(overrides)
    return doc


def audited(document_override: dict[str, object] | None = None) -> AuditRuntime:
    """Drive the frozen cadence to a completed verdict."""
    live = runtime()
    live.accept_final_nonce_reveal(nonce_batch(), PEER_GROUP)
    live.accept_audit_disclosure(document_override or document())
    return live
