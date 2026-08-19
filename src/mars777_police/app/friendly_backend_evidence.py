"""What one role backend witnessed, turned into rows a collector can merge.

The backend already holds every fact this needs - which sub-games it played, how
they settled, how far they ran, the chain it sealed and whether the opponent's
chain reproduced. This is the projection, and it invents nothing: a fact the
backend does not hold is absent here rather than defaulted.

The semantic statuses stay exactly as the evidence-layered audit answered them.
`NOT_CHECKABLE` is carried through unchanged, because a KIT peer's leaner
schema leaves real questions open and recording them as `VERIFIED` would score
an opponent as if it had proved something it never claimed to.
"""

from dataclasses import dataclass, field

from ..domain.terminal import Outcome
from .friendly_evidence_values import FriendlySubGameEvidence
from .kit_messages import KitAuditReveal, KitRole
from .kit_records import KitRecordChain

SCENT_TRUTHFULNESS = ("scent_truthfulness", "NOT_CHECKABLE")
"""JDEC-018 needs a disclosed trajectory the pinned wire never promised."""


@dataclass(slots=True)
class BackendWitness:
    """The per-sub-game facts a backend observes while playing, and nothing else."""

    steps: dict[int, int] = field(default_factory=dict)
    peer_records: dict[int, int] = field(default_factory=dict)
    peer_claims: dict[int, str] = field(default_factory=dict)

    def record(self, sub_game: int, reveal: KitAuditReveal) -> None:
        """Note what the opponent disclosed for *sub_game*, exactly as it came."""
        self.peer_records[sub_game] = len(reveal.records)
        self.peer_claims[sub_game] = reveal.result_claim.value


def backend_rows(
    *,
    role: KitRole,
    outcomes: dict[int, Outcome],
    chains: dict[int, KitRecordChain],
    verified: dict[int, bool],
    witnessed: BackendWitness,
) -> tuple[FriendlySubGameEvidence, ...]:
    """One row per sub-game this backend actually played, in sub-game order."""
    return tuple(
        FriendlySubGameEvidence(
            sub_game=number,
            role=role,
            outcome=outcome,
            steps=witnessed.steps[number],
            our_commits=tuple(record.commit.value for record in chains[number].records),
            peer_chain_verified=verified[number],
            peer_result_claim=witnessed.peer_claims.get(number),
            peer_records=witnessed.peer_records.get(number, 0),
            semantic_statuses=(SCENT_TRUTHFULNESS,),
        )
        for number, outcome in sorted(outcomes.items())
    )
