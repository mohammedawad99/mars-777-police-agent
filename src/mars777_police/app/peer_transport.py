"""The outbound peer-call port: what the application asks of a transport.

`API_BOUNDARIES.md` freezes **`PeerTransportPort`** as an application-facing
port whose adapter is the FastMCP client. This module is that port, and it lives
in `app` for the reason every port does: the application must be able to depend
on it, and to be tested against a fake, without the framework existing.

**It is the mirror of `PeerOperations`, not an alias.** `PeerOperations` is what
a peer asks *of us* - inbound, server-side. This is what we ask *of a peer* -
outbound, client-side. Opposite directions, same nine frozen operations, and
conflating them would hide which side of the wire a failure came from.

Every parameter and result is a **project semantic value**: no wire DTO, no
`fastmcp` type, no `pydantic` model and no URL handling crosses this line.
Encoding is the adapter's job. The methods are `async` because peer I/O is,
while the Stage-4E-R16 runtime behind `PeerOperations` stays synchronous.
"""

from typing import Protocol

from .capture_values import TurnOutcome
from .peer_final_messages import FinalNonceReveal, ResultAgreement
from .peer_pregame_messages import (
    ConfigLockEvidence,
    ConfigProposal,
    Step0DeclarationExchange,
)
from .peer_turn_messages import Acknowledgement, Commitment, Reveal
from .protocol_values import Sha256Digest

AuditDocument = dict[str, object]
"""The frozen JSON-native audit-disclosure document (O6)."""


class PeerTransportPort(Protocol):
    """Every call this peer may make to the other, by semantic value.

    Ordinary completion returns `None` - no semantic result, never an `accepted`
    flag. Exactly two operations carry one: `send_reveal` returns the peer's
    turn `TurnOutcome`, and `send_result_agreement` returns the peer's locally
    computed `Sha256Digest`.

    Failures arrive as the project's own typed failures - the peer's error
    identity for a protocol outcome, `E-TRANSPORT` for a delivery failure -
    never as a `False` and never as a framework exception.
    """

    async def send_step0(self, exchange: Step0DeclarationExchange) -> None:
        """Send our Step-0 declaration and its keyed proof."""
        ...

    async def send_config_proposal(self, proposal: ConfigProposal) -> None:
        """Send a complete config proposal for the current sub-game."""
        ...

    async def send_config_lock(self, evidence: ConfigLockEvidence) -> None:
        """Send our authenticated config-lock evidence."""
        ...

    async def send_commitment(self, commitment: Commitment) -> None:
        """Send this turn's sealed commitment."""
        ...

    async def send_acknowledgement(self, acknowledgement: Acknowledgement) -> None:
        """Acknowledge the peer's commitment."""
        ...

    async def send_reveal(self, reveal: Reveal) -> TurnOutcome:
        """Send our reveal and return the peer's outcome for this turn."""
        ...

    async def send_final_nonce_reveal(self, disclosure: FinalNonceReveal) -> None:
        """Send the batched end-of-sub-game nonce disclosure."""
        ...

    async def send_audit_disclosure(self, document: AuditDocument) -> None:
        """Send our JSON-native audit-disclosure document."""
        ...

    async def send_result_agreement(self, agreement: ResultAgreement) -> Sha256Digest:
        """Send our single result agreement and return the peer's digest."""
        ...
