"""The application-facing contract the transport calls, and nothing more.

This is the seam that keeps the adapter an adapter. Every method takes an
**already-decoded semantic value** and returns the exact operation-specific
result the frozen contract names; the transport never decides Step-0 policy,
negotiation cadence, lock gating, turn legality or the result cadence, and it
never assembles an approval core.

The signatures are synchronous because the Stage-4E-R16 runtime is: `async` is an
I/O property (**O1**), owned by the adapter, and the application layer stays
deterministic and testable without a framework.
"""

from typing import Protocol

from ..app.peer_final_messages import FinalNonceReveal, ResultAgreement
from ..app.peer_pregame_messages import (
    ConfigLockEvidence,
    ConfigProposal,
    Step0DeclarationExchange,
)
from ..app.peer_turn_messages import Acknowledgement, Commitment, Reveal
from ..app.protocol_values import Sha256Digest

AuditDocument = dict[str, object]
"""The frozen JSON-native audit-disclosure document (O6)."""


class PeerOperations(Protocol):
    """Everything a peer may ask this process to do, by semantic value.

    Ordinary completion returns `None` - **no semantic result**, never an
    `accepted` flag. Exactly two operations carry a result: `reveal` returns the
    game-legality `bool`, and `result_agreement` returns the locally computed
    `Sha256Digest`.
    """

    def on_step0(self, exchange: Step0DeclarationExchange) -> None:
        """Accept the peer's Step-0 declaration and its keyed proof."""
        ...

    def on_config_proposal(self, proposal: ConfigProposal) -> None:
        """Accept a complete config proposal for the expected sub-game."""
        ...

    def on_config_lock(self, evidence: ConfigLockEvidence) -> None:
        """Verify the peer's lock evidence against our own recomputation."""
        ...

    def on_commitment(self, commitment: Commitment) -> None:
        """Accept the peer's sealed commitment for this turn."""
        ...

    def on_acknowledgement(self, acknowledgement: Acknowledgement) -> None:
        """Accept the peer's acknowledgement of our commitment."""
        ...

    def on_reveal(self, reveal: Reveal) -> bool:
        """Return whether the revealed action is **game-legal**.

        `False` means the transport, parsing, authentication and protocol layers
        all succeeded and the action is illegal. It never encodes any of those
        failures - each raises its own typed error instead.
        """
        ...

    def on_final_nonce_reveal(self, disclosure: FinalNonceReveal) -> None:
        """Accept the batched end-of-sub-game nonce disclosure."""
        ...

    def on_audit_disclosure(self, document: AuditDocument) -> None:
        """Accept the peer's JSON-native audit-disclosure document."""
        ...

    def on_result_agreement(self, agreement: ResultAgreement) -> Sha256Digest:
        """Return this peer's locally computed `result_sha256`."""
        ...
