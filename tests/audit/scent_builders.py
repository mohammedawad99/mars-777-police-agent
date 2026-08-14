"""Real scent fixtures for the audit: real model, real emissions, no hand-made maps.

Every emission here comes from `emission_of` under the agreed model, so a test
that says "two emissions differ" is asserting the physics disagreed rather than
that a literal was typed differently. The documents are rendered by the real
`audit_disclosure_writer`, so what a test parses is what a peer would actually
have to send.
"""

import dataclasses

import audit_builders as build
from audit_builders import PEER_GROUP, SUB_GAME

from mars777_police.app.audit_disclosure_writer import scent_value
from mars777_police.app.audit_runtime import AuditRuntime
from mars777_police.app.scent_records import ScentRecord
from mars777_police.app.turn_cursor import TurnCursor
from mars777_police.app.turn_protocol_state import TurnEvidence
from mars777_police.domain.board import Position
from mars777_police.domain.config_model import GridConfig
from mars777_police.domain.scent_emission import ScentEmission
from mars777_police.domain.scent_model_default import default_scent_model
from mars777_police.domain.scent_observation import emission_of
from mars777_police.protocol.audit_commitment import CommitmentRecomputer

BOARD = GridConfig.from_grid_size(7, 0).to_board()
MODEL = default_scent_model()
CELLS = {1: Position(3, 3), 2: Position(3, 4)}


def emission(step: int) -> ScentEmission:
    """What the agreed model really deposits for that turn - never a fixture."""
    return emission_of(BOARD, MODEL.kernel, CELLS[step], MODEL.params)


def rows(steps: tuple[int, ...] = (1, 2)) -> tuple[ScentRecord, ...]:
    """The scent history a V2 session observed for those turns."""
    return tuple(ScentRecord(TurnCursor(SUB_GAME, s), emission(s)) for s in steps)


def scent_json(records: tuple[ScentRecord, ...]) -> list[dict[str, object]]:
    """That history as the peer would disclose it, through the real writer."""
    return [scent_value(record) for record in records]


def v2_evidence(steps: tuple[int, ...] = (1, 2)) -> tuple[TurnEvidence, ...]:
    """The live inbound evidence of a V2 session: every turn carried an emission."""
    return tuple(
        dataclasses.replace(one, scent=emission(one.cursor.step)) for one in build.evidence(steps)
    )


def v2_runtime(steps: tuple[int, ...] = (1, 2)) -> AuditRuntime:
    return AuditRuntime(
        build.context(), v2_evidence(steps), CommitmentRecomputer(), capture=build.capture(steps)
    )


def audited(runtime: AuditRuntime, document: dict[str, object]) -> AuditRuntime:
    """Drive the frozen cadence to the disclosure this test is about."""
    runtime.accept_final_nonce_reveal(build.nonce_batch(), PEER_GROUP)
    runtime.accept_audit_disclosure(document)
    return runtime


def v2_document(
    records: tuple[ScentRecord, ...] | None = None, **overrides: object
) -> dict[str, object]:
    """A well-formed V2 disclosure carrying the scent a test wants disclosed."""
    return build.document(scent=scent_json(rows() if records is None else records), **overrides)
