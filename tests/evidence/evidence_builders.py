"""Real producer and real receiver, wired to the same production crypto.

Nothing here fakes a hash or invents a document: the producer uses the real
`CommitmentRecomputer` and the receiver is the real `AuditRuntime`, so a
round-trip that verifies proves the writer is the exact inverse of the reader.
"""

from mars777_police.app.audit_runtime import AuditRuntime
from mars777_police.app.audit_values import SubGameContext
from mars777_police.app.outbound_evidence_runtime import OutboundEvidenceRuntime
from mars777_police.app.outbound_evidence_values import LocalEvidenceContext
from mars777_police.app.protocol_values import NonceValue, Sha256Digest
from mars777_police.app.sealed_record_values import ActorRole, Intent, SealedState
from mars777_police.app.turn_cursor import TurnCursor
from mars777_police.app.turn_protocol_state import TurnEvidence
from mars777_police.domain.actions import MoveAction
from mars777_police.domain.board import Position
from mars777_police.domain.rules import Move
from mars777_police.protocol.audit_commitment import CommitmentRecomputer
from mars777_police.protocol.secure_nonce import SecretsNonceSource

GAME_ID = "mars777-vs-groupx-2026w1-uid0001"
GAME_UID = "uid0001"
SUB_GAME = 1
CONFIG = Sha256Digest("d" * 64)
OURS = ActorRole.THIEF
PEER_GROUP = "GROUP-XY"
POS = {1: Position(2, 3), 2: Position(2, 4), 3: Position(3, 4)}
HINTS = {1: "moving north", 2: "moving north again", 3: "still north"}


class ScriptedNonces:
    """A nonce source with a known sequence, for deterministic assertions."""

    def __init__(self, values: list[str]) -> None:
        self.values = list(values)
        self.calls = 0

    def fresh(self) -> NonceValue:
        """Return the next scripted nonce, repeating the last when exhausted."""
        self.calls += 1
        return NonceValue(self.values[min(self.calls - 1, len(self.values) - 1)])


def context() -> LocalEvidenceContext:
    """Our own identity for this sub-game."""
    return LocalEvidenceContext(GAME_ID, GAME_UID, SUB_GAME, CONFIG, OURS)


def producer(source: object | None = None) -> OutboundEvidenceRuntime:
    """The real producer over real production crypto."""
    return OutboundEvidenceRuntime(
        context(), source or SecretsNonceSource(), CommitmentRecomputer()
    )


def sealed(step: int) -> SealedState:
    """The own-known snapshot we seal for *step*."""
    return SealedState(CONFIG, POS[step], (), step, OURS)


def prepare(runtime: OutboundEvidenceRuntime, step: int) -> object:
    """Seal one ordinary northward turn."""
    return runtime.prepare_turn(
        state=sealed(step),
        action=MoveAction(Move.N),
        intent=Intent.TRUTH,
        hint=HINTS[step],
        cursor=TurnCursor(SUB_GAME, step),
    )


def receiver(prepared: list[object], steps: tuple[int, ...]) -> AuditRuntime:
    """The real `AuditRuntime`, holding what a peer would have witnessed live."""
    evidence = tuple(
        TurnEvidence(
            TurnCursor(SUB_GAME, step),
            turn.commitment.h_commit,
            turn.reveal.action,
            turn.reveal.hint,
            True,
        )
        for step, turn in zip(steps, prepared, strict=True)
    )
    peer_context = SubGameContext(GAME_ID, GAME_UID, SUB_GAME, CONFIG, OURS, PEER_GROUP)
    return AuditRuntime(peer_context, evidence, CommitmentRecomputer())
