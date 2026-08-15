"""A real reviewed sub-game whose reveals actually carried scent.

`semantic_builders` seals turns without emissions, which is what keeps the
pre-V2 review honest. This adds the counted half: the same real producer, the
same real audit over real crypto, plus the emissions both sides retained live -
so a review driven from these owners is the review a current sub-game gets.

Every emission comes from `emission_of` under the **locked** model, on the board
the emitter itself had. Nothing here hand-writes a deposit map, so a test that
says "this is dishonest" is disagreeing with the domain's own physics rather
than with a literal someone typed.
"""

import semantic_builders as build
from semantic_builders import CONFIG, COP, SUB_GAME, THIEF, seal, witness

from mars777_police.app.audit_runtime import AuditRuntime
from mars777_police.app.config_rules import rules_of
from mars777_police.app.outbound_evidence_runtime import OutboundEvidenceRuntime
from mars777_police.app.scent_records import ScentRecord
from mars777_police.app.sealed_record_values import ActorRole
from mars777_police.app.turn_cursor import TurnCursor
from mars777_police.domain.actions import PhysicalAction
from mars777_police.domain.board import Board, Position
from mars777_police.domain.scent_emission import ScentEmission
from mars777_police.domain.scent_model_default import default_scent_model
from mars777_police.domain.scent_observation import emission_of

MODEL = default_scent_model()
"""The model a series locks in these fixtures; the verifier must be *given* it."""

RULES = rules_of(CONFIG)
BOARD: Board = RULES.board


def emission_at(cell: Position, board: Board = BOARD) -> ScentEmission:
    """What the locked model really deposits from *cell* on *board*."""
    return emission_of(board, MODEL.kernel, cell, MODEL.params)


def record(step: int, cell: Position, board: Board = BOARD) -> ScentRecord:
    """The scent history row an honest emitter would retain for that turn."""
    return ScentRecord(TurnCursor(SUB_GAME, step), emission_at(cell, board))


def played(
    producer: OutboundEvidenceRuntime, step: int, cell: Position, action: PhysicalAction
) -> object:
    """Seal one turn and return what the peer would have witnessed."""
    return seal(producer, step, cell, action)


def reviewed(
    own_role: ActorRole,
    own_turns: list[tuple[int, Position, PhysicalAction]],
    peer_turns: list[tuple[int, Position, PhysicalAction]],
    own_scent: tuple[ScentRecord, ...] = (),
    peer_scent: tuple[ScentRecord, ...] = (),
) -> tuple[OutboundEvidenceRuntime, AuditRuntime]:
    """A real audited sub-game with both sides' retained scent history.

    The peer discloses **exactly** the rows it sent, so Part 1A's correspondence
    passes even when those rows are a physical lie - which is the whole scenario
    Part 2B exists to catch.
    """
    peer_role = ActorRole.THIEF if own_role is ActorRole.POLICE else ActorRole.POLICE
    ours = build.evidence_for(own_role)
    theirs = build.evidence_for(peer_role)
    for step, cell, action in own_turns:
        played(ours, step, cell, action)
    prepared = [played(theirs, step, cell, action) for step, cell, action in peer_turns]
    ours.observe_capture((), own_scent)
    theirs.observe_capture((), peer_scent)
    audit = build.audit_for(peer_role)
    audit.evidence = tuple(
        _scented(witness(one), peer_scent)
        for one in prepared  # type: ignore[arg-type]
    )
    audit.accept_final_nonce_reveal(theirs.final_nonce_reveal(), build.PEER_GROUP)
    audit.accept_audit_disclosure(theirs.audit_disclosure())
    return ours, audit


def _scented(evidence: object, rows: tuple[ScentRecord, ...]) -> object:
    """Attach the retained emission for that step, exactly as a V2 turn would."""
    import dataclasses

    step = evidence.cursor.step  # type: ignore[attr-defined]
    found = next((row for row in rows if row.cursor.step == step), None)
    return evidence if found is None else dataclasses.replace(evidence, scent=found.emission)


START = {ActorRole.POLICE: COP, ActorRole.THIEF: THIEF}
"""Where the locked configuration puts each side before step 1."""
