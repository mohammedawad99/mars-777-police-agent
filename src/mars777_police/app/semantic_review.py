"""Driving one sub-game's semantic review from the two records that survive it.

Both sides of the game are needed and both are already held locally when a
sub-game ends: our own sealed turns in `OutboundEvidenceRuntime`, the peer's in
the disclosure `AuditRuntime` verified, and the capture transcript in the two
directions each of them retained. Nothing here asks the network for anything -
the review is a second reading of evidence that already passed the hashes.

**Step by step, both sides at once.** A step is checked as a whole, its capture
questions are recomputed against the cells and the board *before* its effects,
and only then is the step applied. The first violation ends the review: after a
peer's story has broken once, later steps are replays of a game that did not
happen.

**Who is at fault is part of the finding.** A dishonest answer belongs to the
side that gave it and a false declaration to the side that made it - including
when that side is us. One event can carry a fault on each side, and the finding
names both rather than reporting whichever was noticed first. This runs
identically in both repositories, so a peer's finding about our own play is the
one we would reach about ourselves.
"""

from ..domain.barriers import BarrierQuota
from ..domain.config_model import GridConfig
from ..domain.negotiated_config import NegotiatedConfig
from ..domain.terminal import Outcome
from .audit_disclosure import turns as disclosed_turns
from .audit_runtime import AuditRuntime
from .capture_transcript import CaptureRecord
from .outbound_evidence_runtime import OutboundEvidenceRuntime
from .protocol_errors import LocalDefectError
from .sealed_record_values import ActorRole
from .semantic_capture import AnsweredTurn, review_answer
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


Asked = dict[tuple[int, ActorRole], AnsweredTurn]
"""Every retained capture row, keyed by the step and the side that asked it."""


def _asked(
    rows: tuple[CaptureRecord, ...],
    asker: ActorRole,
    answerer: ActorRole,
    played: tuple[PlayedTurn, ...],
) -> Asked:
    """One direction's rows, each carried back to the reveal that produced it."""
    actions = {turn.step: turn.action for turn in played}
    return {
        (row.cursor.step, asker): AnsweredTurn(row, asker, answerer, actions[row.cursor.step])
        for row in rows
    }


def _grouped(turns: tuple[PlayedTurn, ...]) -> dict[int, tuple[PlayedTurn, ...]]:
    """The turns of both sides by step, the police's first inside each step."""
    grouped: dict[int, tuple[PlayedTurn, ...]] = {}
    for turn in sorted(turns, key=lambda one: (one.step, one.role is not ActorRole.POLICE)):
        grouped[turn.step] = (*grouped.get(turn.step, ()), turn)
    return grouped


def review_sub_game(
    evidence: OutboundEvidenceRuntime, audit: AuditRuntime, rules: SemanticRules
) -> SemanticFinding:
    """Replay the finished sub-game and return the first violation it shows."""
    ours, theirs = own_turns(evidence), peer_turns(audit)
    own_role, peer_role = evidence.context.role, audit.context.peer_role
    asked = _asked(evidence.capture, own_role, peer_role, ours)
    asked |= _asked(audit.capture, peer_role, own_role, theirs)
    return _walk(Replay(rules), _grouped(ours + theirs), asked)


def _walk(
    replay: Replay, by_step: dict[int, tuple[PlayedTurn, ...]], asked: Asked
) -> SemanticFinding:
    """Check, recompute and apply each step in order until something fails."""
    for step in sorted(by_step):
        played = by_step[step]
        finding = replay.check(played)
        if not finding.consistent:
            return finding
        finding = _answers(replay, played, asked)
        if not finding.consistent:
            return finding
        replay.apply(played)
    return CONSISTENT


def _answers(replay: Replay, played: tuple[PlayedTurn, ...], asked: Asked) -> SemanticFinding:
    """Recompute this step's capture questions, before the step takes effect."""
    for turn in played:
        question = asked.get((turn.step, turn.role))
        if question is None:
            continue
        finding = review_answer(question, replay.board, replay.cell_of(ActorRole.THIEF))
        if not finding.consistent:
            return finding
    return CONSISTENT


def sanctioned(outcome: Outcome, finding: SemanticFinding) -> Outcome:
    """The sub-game's end event once the review has had its say.

    A finding that the source scores rather than disqualifies replaces the end
    event with `TECHNICAL_LOSS`, which `domain.scoring` already scores 0/0: an
    illegal move (`GAME-003`), an illegal placement (`BAR-004`) and a false
    declaration (`CRYPTO-005`) all say exactly that. A purely disqualifying
    finding leaves the end event alone and goes to the audit gate instead, which
    is what stops the whole series from reaching result agreement.
    """
    if finding.verdict in SCORED_AS_TECHNICAL_LOSS:
        return Outcome.TECHNICAL_LOSS
    return outcome
