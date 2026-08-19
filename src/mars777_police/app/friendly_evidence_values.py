"""What one development friendly witnessed, as values that infer nothing.

Every member here is a fact this side actually observed: the side we played, the
end event the sub-game reached, the commits we sealed, whether the opponent's
disclosed chain reproduced under our own serializer, and what the evidence-layered
audit answered - `NOT_CHECKABLE` included, never promoted to `VERIFIED` because
a cleaner-looking record would be a more useful one.

Deliberately absent: any field that would state a mutual result agreement or a
keyed Step-0 proof. Neither happened on this wire, and a value type that could
hold them would be a value type somebody could fill in.
"""

from dataclasses import dataclass

from ..domain.terminal import Outcome
from .kit_messages import KitRole
from .run_class import RunClassification


@dataclass(frozen=True, slots=True)
class FriendlySubGameEvidence:
    """One sub-game as this side witnessed it. Nothing here is inferred."""

    sub_game: int
    role: KitRole
    outcome: Outcome
    steps: int
    our_commits: tuple[str, ...]
    peer_chain_verified: bool
    peer_result_claim: str | None
    peer_records: int
    semantic_statuses: tuple[tuple[str, str], ...] = ()
    """`(check, status)` exactly as the evidence-layered audit answered."""


@dataclass(frozen=True, slots=True)
class FriendlySeriesEvidence:
    """One group series, played by two role backends against one opponent."""

    classification: RunClassification
    game_id: str
    game_uid: str
    our_group: str
    peer_group: str
    schedule: tuple[KitRole, ...]
    rows: tuple[FriendlySubGameEvidence, ...]
