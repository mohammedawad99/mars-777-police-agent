"""One turn's worth of material: a board, a move, a seal, its evidence.

The small pieces a sub-game is assembled from, each built through the same
authority production uses so a test can never seal bytes production would not.
"""

import dataclasses

import turn_builders
from r16_builders import config
from session_builders import GAME_ID, GAME_UID

from mars777_police.app.audit_runtime import AuditRuntime
from mars777_police.app.audit_values import SubGameContext
from mars777_police.app.outbound_evidence_runtime import OutboundEvidenceRuntime
from mars777_police.app.outbound_evidence_values import LocalEvidenceContext
from mars777_police.app.protocol_values import Sha256Digest
from mars777_police.app.sealed_record_values import ActorRole, SealedState
from mars777_police.app.turn_cursor import TurnCursor
from mars777_police.app.turn_protocol_runtime import TurnProtocolRuntime
from mars777_police.domain.actions import BarrierAction, MoveAction, PhysicalAction
from mars777_police.domain.board import Board, Position
from mars777_police.domain.config_model import GridConfig
from mars777_police.domain.config_sections import BoardAndAgentsTerms
from mars777_police.domain.rules import destination_of
from mars777_police.domain.truth import LocalTruth
from mars777_police.protocol.audit_commitment import CommitmentRecomputer
from mars777_police.protocol.config_lock import config_sha256

CONFIG = dataclasses.replace(
    config(),
    board_and_agents=BoardAndAgentsTerms(7, 2, Position(0, 0), Position(0, 1), "top-left", 0),
)
"""The locked config for a lifecycle run: the two start cells are neighbours.

Adjacency is what makes the capture routes reachable at all - BAR-004 lets the
police place only on its own cell or one beside it, so a thief that starts four
cells away cannot be captured by a barrier in the first turn of a sub-game."""
DIGEST = Sha256Digest(config_sha256(CONFIG).value)
POSITIONS = {
    ActorRole.POLICE: CONFIG.board_and_agents.cop_start,
    ActorRole.THIEF: CONFIG.board_and_agents.thief_start,
}
"""Where each side really starts - the cells this series' config locked.

The final audit replays the disclosed game against them, so a lifecycle fixture
that opened somewhere else would be disclosing a game that never happened."""
"""One legal opening move each, from the corner cells the config locks."""


def board() -> Board:
    """The empty geometry this series' config locked."""
    terms = CONFIG.board_and_agents
    return GridConfig.from_grid_size(terms.grid_size, terms.axis_start_index).to_board()


def moved(cell: Position, action: PhysicalAction) -> Position:
    """Where a side stands after that action - a barrier leaves it where it was."""
    if isinstance(action, MoveAction):
        return destination_of(cell, action.move)
    return cell


def placed(walls: tuple[Position, ...], action: PhysicalAction) -> tuple[Position, ...]:
    """The public barrier set after that action, in placement order."""
    if isinstance(action, BarrierAction):
        return (*walls, action.target)
    return walls


def sealed_for(role: ActorRole, step: int = 1) -> SealedState:
    """The own-known snapshot this side seals for one step."""
    return SealedState(DIGEST, POSITIONS[role], (), step, role)


def turn_for(
    role: ActorRole, cursor: TurnCursor, truth: LocalTruth | None = None
) -> TurnProtocolRuntime:
    """A real turn runtime positioned on one step of one sub-game.

    Its own truth is the locked board and this side's locked start cell, so the
    answer a live turn gives about capture is about the same game the final
    audit later replays. Pass *truth* to carry a sub-game's adopted barriers
    from one turn into the next - a role a later stage will own.
    """
    runtime = turn_builders.runtime(role)
    runtime.cursor = cursor
    runtime.truth = truth or LocalTruth(board=board(), own_position=POSITIONS[role])
    return runtime


def evidence_for(role: ActorRole, sub_game: int) -> OutboundEvidenceRuntime:
    """Our own evidence owner for one sub-game, over the production nonce source."""
    from mars777_police.protocol.secure_nonce import SecretsNonceSource

    context = LocalEvidenceContext(GAME_ID, GAME_UID, sub_game, DIGEST, role)
    return OutboundEvidenceRuntime(context, SecretsNonceSource(), CommitmentRecomputer())


def audit_for(peer_role: ActorRole, peer_group: str, sub_game: int) -> AuditRuntime:
    """The audit owner for one sub-game; its evidence arrives as turns finish."""
    context = SubGameContext(GAME_ID, GAME_UID, sub_game, DIGEST, peer_role, peer_group)
    return AuditRuntime(context, (), CommitmentRecomputer())
