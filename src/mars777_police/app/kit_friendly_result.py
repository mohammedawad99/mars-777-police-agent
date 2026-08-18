"""What a completed development friendly is worth, said in one place.

Operational metadata, deliberately **not** a game verdict: `FinalAuditVerdict`
answers whether a chain is sound, and overloading it with "this run may not be
counted" would put an operational fact inside a cryptographic one.

`counted_eligible` is derived from the run classification rather than stored,
so a friendly that went perfectly - exact six, both chains reproducing, results
agreed - is still not counted. That is the point: the source requires keyed
producer authentication at Step-0, the pinned peer offers an unkeyed content
agreement, and a clean game does not retroactively supply the key.
"""

from dataclasses import dataclass

from ..domain.terminal import Outcome
from .run_class import RunClassification


@dataclass(frozen=True, slots=True)
class KitFriendlyResult:
    """One finished friendly series, and every fact that decides its standing."""

    classification: RunClassification
    outcomes: tuple[Outcome, ...]
    crypto_audit_passed: bool
    semantic_audit_clean: bool
    peer_audit_received: bool
    result_agreed: bool

    @property
    def exact_six(self) -> bool:
        """Whether six sub-games actually settled. Five is not a short series."""
        return len(self.outcomes) == 6

    @property
    def keyed_auth(self) -> bool:
        """The source-required gate, reported under its own name."""
        return self.classification.keyed_auth_satisfied

    @property
    def counted_eligible(self) -> bool:
        """Never true for a friendly, however clean the game was."""
        return self.classification.counted_capable and self.exact_six

    @property
    def complete(self) -> bool:
        """`KIT_FRIENDLY_COMPLETE`: the run did everything a friendly can do."""
        return self.exact_six and self.crypto_audit_passed and self.peer_audit_received
