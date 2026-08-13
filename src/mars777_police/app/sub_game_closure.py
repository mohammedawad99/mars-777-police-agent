"""Everything that must happen, in order, when one sub-game ends.

Three facts settle at that moment and they settle in a fixed order: the replay
reviews the disclosed game, the review decides whether the end event is the one
that was played or a sanction, and only then is the log rendered - so the file
on disk carries the finding rather than a verdict that was still being decided
while it was written.

Kept out of `SeriesRuntime` because the order *is* the contract. A caller that
stored the log first and reviewed afterwards would produce an official artifact
that disagrees with the gate the same series later applies.
"""

from dataclasses import dataclass

from ..domain.negotiated_config import NegotiatedConfig
from ..domain.terminal import Outcome
from .audit_disclosure_writer import AuditDocument
from .audit_runtime import AuditRuntime
from .log_document import finalized_log
from .outbound_evidence_runtime import OutboundEvidenceRuntime
from .protocol_errors import LocalDefectError
from .semantic_review import review_sub_game, rules_for, sanctioned
from .semantic_values import SemanticFinding


@dataclass(frozen=True, slots=True)
class ClosedSubGame:
    """What a finished sub-game leaves behind: a log, an end event, a finding."""

    document: AuditDocument
    outcome: Outcome
    finding: SemanticFinding


def closed_sub_game(
    evidence: OutboundEvidenceRuntime,
    audit: AuditRuntime,
    config: NegotiatedConfig | None,
    outcome: Outcome,
) -> ClosedSubGame:
    """Review the finished sub-game, sanction it if it needs one, and log it.

    The locked config is the only outside fact required: the replay starts from
    the two start cells and the barrier quota both sides agreed to, so a sub-game
    that somehow reached its end without a locked config cannot be reviewed at
    all - and an unreviewable sub-game is refused rather than recorded as clean.
    """
    if config is None:
        raise LocalDefectError("a sub-game is closed against the config this series locked")
    finding = review_sub_game(evidence, audit, rules_for(config))
    audit.adopt_semantic(finding)
    return ClosedSubGame(finalized_log(evidence, audit), sanctioned(outcome, finding), finding)
