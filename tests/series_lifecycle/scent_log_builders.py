"""A real disclosed sub-game whose turns actually carried scent.

`evidence_builders` builds the pre-V2 shape - sealed turns with no emission at
all - which is exactly what keeps the legacy log fixtures honest. This adds the
counted-contract half, over the same two real halves `test_log_contract` uses:
our own police evidence owner, and the thief half whose disclosure a real
`AuditRuntime` audited. Both keep the emissions they retained live, so a log
rendered from them is the log a current sub-game would leave.

Nothing here invents an emission. Each one comes from `emission_of` under the
agreed model, and the two sides emit from **different** cells, so a test can tell
our own retained history apart from the peer's.
"""

import evidence_builders as ev
from evidence_builders import CONFIG, GAME_ID, GAME_UID, PEER_GROUP, SUB_GAME

from mars777_police.app.audit_runtime import AuditRuntime
from mars777_police.app.audit_values import SubGameContext
from mars777_police.app.capture_transcript import CaptureRecord
from mars777_police.app.capture_values import CaptureAnswer
from mars777_police.app.outbound_evidence_runtime import OutboundEvidenceRuntime
from mars777_police.app.outbound_evidence_values import LocalEvidenceContext
from mars777_police.app.scent_records import ScentRecord
from mars777_police.app.sealed_record_values import ActorRole, Intent, SealedState
from mars777_police.app.turn_cursor import TurnCursor
from mars777_police.app.turn_protocol_state import TurnEvidence
from mars777_police.domain.actions import MoveAction
from mars777_police.domain.board import Position
from mars777_police.domain.config_model import GridConfig
from mars777_police.domain.rules import Move
from mars777_police.domain.scent_emission import ScentEmission
from mars777_police.domain.scent_model_default import default_scent_model
from mars777_police.domain.scent_observation import emission_of
from mars777_police.protocol.audit_commitment import CommitmentRecomputer
from mars777_police.protocol.secure_nonce import SecretsNonceSource

BOARD = GridConfig.from_grid_size(7, 0).to_board()
MODEL = default_scent_model()
STEPS = (1, 2)
OWN_ROLE, PEER_ROLE = ActorRole.POLICE, ActorRole.THIEF
OWN, PEER = "police", "thief"
OWN_CELLS = {1: Position(2, 2), 2: Position(2, 3)}
PEER_CELLS = {1: Position(4, 4), 2: Position(4, 5)}


def emission(step: int, own: bool = True) -> ScentEmission:
    """What the agreed model really deposits for that side's turn."""
    cells = OWN_CELLS if own else PEER_CELLS
    return emission_of(BOARD, MODEL.kernel, cells[step], MODEL.params)


def records(steps: tuple[int, ...] = STEPS, own: bool = True) -> tuple[ScentRecord, ...]:
    """The scent history one side retained for those turns."""
    return tuple(ScentRecord(TurnCursor(SUB_GAME, s), emission(s, own)) for s in steps)


def capture(steps: tuple[int, ...] = STEPS) -> tuple[CaptureRecord, ...]:
    """What these ordinary turns asked about capture: nothing at all."""
    return tuple(
        CaptureRecord(TurnCursor(SUB_GAME, s), None, CaptureAnswer.NO_QUESTION) for s in steps
    )


def own_producer(scented: bool) -> OutboundEvidenceRuntime:
    """Our own police half of the same sub-game, with what it retained."""
    context = LocalEvidenceContext(GAME_ID, GAME_UID, SUB_GAME, CONFIG, OWN_ROLE)
    runtime = OutboundEvidenceRuntime(context, SecretsNonceSource(), CommitmentRecomputer())
    for step in STEPS:
        runtime.prepare_turn(
            state=SealedState(CONFIG, ev.POS[step], (), step, OWN_ROLE),
            action=MoveAction(Move.N),
            intent=Intent.TRUTH,
            hint=ev.HINTS[step],
            cursor=TurnCursor(SUB_GAME, step),
        )
    runtime.observe_capture(capture(), records() if scented else ())
    return runtime


def _receiver(prepared: list[object], scented: bool) -> AuditRuntime:
    """The peer's real audit over what this side would have witnessed live."""
    evidence = tuple(
        TurnEvidence(
            TurnCursor(SUB_GAME, step),
            turn.commitment.h_commit,  # type: ignore[attr-defined]
            turn.reveal.action,  # type: ignore[attr-defined]
            turn.reveal.hint,  # type: ignore[attr-defined]
            True,
            emission(step, own=False) if scented else None,
        )
        for step, turn in zip(STEPS, prepared, strict=True)
    )
    context = SubGameContext(GAME_ID, GAME_UID, SUB_GAME, CONFIG, PEER_ROLE, PEER_GROUP)
    return AuditRuntime(context, evidence, CommitmentRecomputer(), capture=capture())


def _played(scented: bool) -> tuple[OutboundEvidenceRuntime, AuditRuntime]:
    """One whole real sub-game, disclosed and audited, with or without scent."""
    peer = ev.producer()
    prepared = [ev.prepare(peer, step) for step in STEPS]
    peer.observe_capture(capture(), records(own=False) if scented else ())
    receiver = _receiver(prepared, scented)
    receiver.accept_final_nonce_reveal(peer.final_nonce_reveal(), PEER_GROUP)
    receiver.accept_audit_disclosure(peer.audit_disclosure())
    return own_producer(scented), receiver


def counted() -> tuple[OutboundEvidenceRuntime, AuditRuntime]:
    """A real audited sub-game where both sides retained their scent history."""
    return _played(True)


def legacy() -> tuple[OutboundEvidenceRuntime, AuditRuntime]:
    """The same real sub-game under the pre-V2 contract: no scent anywhere."""
    return _played(False)


def reveals(log: dict[str, object], role: str) -> list[dict[str, object]]:
    """Every reveal event one side wrote, in the order the log wrote them."""
    entries = log["entries"]
    assert isinstance(entries, list)
    return [one for one in entries if one["phase"] == "reveal" and one["role"] == role]
