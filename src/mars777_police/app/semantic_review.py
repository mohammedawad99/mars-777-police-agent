"""Driving one sub-game's semantic review from the two records that survive it.

Both sides are already held locally when a sub-game ends: our own sealed turns
in `OutboundEvidenceRuntime`, the peer's in the disclosure `AuditRuntime`
verified, the capture transcript each retained, and - since JDEC-018 - the scent
history both directions kept. Nothing here asks the network for anything.

**Step by step, both sides at once.** A step is checked whole, its capture
questions and emissions are recomputed against the cells and the board *before*
its effects, and only then is the step applied. The first violation ends the
review.

**Who is at fault is part of the finding.** A dishonest answer belongs to the
side that gave it and a false declaration to the side that made it - including
when that side is us. One event can carry a fault on each side and the finding
names both. This runs identically in both repositories."""

from ..domain.barriers import BarrierQuota
from ..domain.config_model import GridConfig
from ..domain.negotiated_config import NegotiatedConfig
from ..domain.scent_model import ScentModelAgreement
from ..domain.terminal import Outcome
from .audit_disclosure import turns as disclosed_turns
from .audit_runtime import AuditRuntime
from .outbound_evidence_runtime import OutboundEvidenceRuntime
from .protocol_errors import LocalDefectError
from .scent_truth import ScentHistory, history_of, require_truthful_scent
from .sealed_record_values import ActorRole
from .semantic_capture import Asked, answered_step, asked_rows
from .semantic_replay import PlayedTurn, Replay
from .semantic_values import CONSISTENT, SCORED_AS_TECHNICAL_LOSS, SemanticFinding, SemanticRules


def rules_for(config: NegotiatedConfig) -> SemanticRules:
    """The locked geometry, quota and start cells this series agreed on."""
    board, barriers = config.board_and_agents, config.movement_and_barriers
    grid = GridConfig.from_grid_size(board.grid_size, board.axis_start_index)
    return SemanticRules(
        grid.to_board(), BarrierQuota(barriers.max_barriers), board.cop_start, board.thief_start
    )


def own_turns(evidence: OutboundEvidenceRuntime) -> tuple[PlayedTurn, ...]:
    """Our own disclosed play, from the records we sealed it with."""
    role = evidence.context.role
    return tuple(
        PlayedTurn(
            record.cursor.step, role, record.state.self_pos, record.state.barriers, record.action
        )
        for record in evidence.ordered
    )


def peer_turns(audit: AuditRuntime) -> tuple[PlayedTurn, ...]:
    """The peer's play, from the disclosure its own hashes already verified."""
    document = audit.disclosure
    if document is None:
        raise LocalDefectError("a semantic review follows the peer's audit disclosure")
    role = audit.context.peer_role
    return tuple(
        PlayedTurn(turn.step, role, turn.self_pos, turn.barriers, turn.move)
        for turn in disclosed_turns(document)
    )


def _grouped(turns: tuple[PlayedTurn, ...]) -> dict[int, tuple[PlayedTurn, ...]]:
    """The turns of both sides by step, the police's first inside each step."""
    grouped: dict[int, tuple[PlayedTurn, ...]] = {}
    for turn in sorted(turns, key=lambda one: (one.step, one.role is not ActorRole.POLICE)):
        grouped[turn.step] = (*grouped.get(turn.step, ()), turn)
    return grouped


def review_sub_game(
    evidence: OutboundEvidenceRuntime,
    audit: AuditRuntime,
    rules: SemanticRules,
    model: ScentModelAgreement,
) -> SemanticFinding:
    """Replay the finished sub-game and return the first violation it shows.

    *model* is the series-locked agreement, passed in rather than looked up: a
    reviewer reaching for a local default could clear a peer running other
    physics."""
    ours, theirs = own_turns(evidence), peer_turns(audit)
    own_role, peer_role = evidence.context.role, audit.context.peer_role
    asked = asked_rows(evidence.capture, own_role, peer_role, ours)
    asked |= asked_rows(audit.capture, peer_role, own_role, theirs)
    scent = history_of(evidence.scent, own_role, audit.expected_scent, peer_role)
    return _walk(Replay(rules), _grouped(ours + theirs), asked, scent, model)


def _walk(
    replay: Replay,
    by_step: dict[int, tuple[PlayedTurn, ...]],
    asked: Asked,
    scent: ScentHistory,
    model: ScentModelAgreement,
) -> SemanticFinding:
    """Check, recompute and apply each step in order until something fails.

    Scent is judged last, and only where trajectory and answers already hold: a
    cell never legally reached cannot be asked what it should have emitted, so a
    stronger finding is never displaced."""
    for step in sorted(by_step):
        played = by_step[step]
        finding = replay.check(played)
        if not finding.consistent:
            return finding
        finding = answered_step(replay, played, asked)
        if not finding.consistent:
            return finding
        finding = require_truthful_scent(replay, played, scent, model)
        if not finding.consistent:
            return finding
        replay.apply(played)
    return CONSISTENT


def sanctioned(outcome: Outcome, finding: SemanticFinding) -> Outcome:
    """The sub-game's end event once the review has had its say.

    A finding that is scored rather than disqualifying replaces the end event
    with `TECHNICAL_LOSS`, which `domain.scoring` already scores 0/0: an illegal
    move (`GAME-003`), an illegal placement (`BAR-004`), a false declaration
    (`CRYPTO-005`) and a physically impossible emission (`JDEC-018`) all say
    that. One set membership decides it - nothing is special-cased here. A purely
    disqualifying finding goes to the audit gate instead."""
    if finding.verdict in SCORED_AS_TECHNICAL_LOSS:
        return Outcome.TECHNICAL_LOSS
    return outcome
