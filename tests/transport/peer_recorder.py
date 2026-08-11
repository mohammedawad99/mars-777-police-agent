"""The recording `PeerOperations` the wire tests dispatch into.

Split out of `peer_ops` when the Stage-5-R3R session parameter pushed that file
over the 150-line limit. It is a **wire fixture**: it takes the inbound session
and ignores it, because the authentication gate is proved against the production
adapter rather than against a recorder.
"""

from peer_ops import ILLEGAL_HINT, RESULT_DIGEST

from mars777_police.app.peer_final_messages import FinalNonceReveal, ResultAgreement
from mars777_police.app.peer_pregame_messages import (
    ConfigLockEvidence,
    ConfigProposal,
    Step0DeclarationExchange,
)
from mars777_police.app.peer_turn_messages import Acknowledgement, Commitment, Reveal
from mars777_police.app.protocol_values import Sha256Digest
from mars777_police.transport.handlers import AuditDocument
from mars777_police.transport.inbound_session import InboundSession


class RecordingOperations:
    """Records what the application received; a wire fixture, never a gate."""

    def __init__(self) -> None:
        self.seen: list[tuple[str, object]] = []
        self.failure: BaseException | None = None

    def _record(self, name: str, value: object) -> None:
        if self.failure is not None:
            raise self.failure
        self.seen.append((name, value))

    def kinds(self) -> list[str]:
        """The operation names invoked, in order."""
        return [name for name, _ in self.seen]

    def on_step0(self, exchange: Step0DeclarationExchange, session: InboundSession) -> None:
        self._record("step0", exchange)

    def on_config_proposal(self, value: ConfigProposal, session: InboundSession) -> None:
        self._record("config_proposal", value)

    def on_config_lock(self, value: ConfigLockEvidence, session: InboundSession) -> None:
        self._record("config_lock", value)

    def on_commitment(self, value: Commitment, session: InboundSession) -> None:
        self._record("commitment", value)

    def on_acknowledgement(self, value: Acknowledgement, session: InboundSession) -> None:
        self._record("acknowledgement", value)

    def on_reveal(self, value: Reveal, session: InboundSession) -> bool:
        self._record("reveal", value)
        return value.hint != ILLEGAL_HINT

    def on_final_nonce_reveal(self, value: FinalNonceReveal, session: InboundSession) -> None:
        self._record("final_nonce_reveal", value)

    def on_audit_disclosure(self, value: AuditDocument, session: InboundSession) -> None:
        self._record("audit_disclosure", value)

    def on_result_agreement(self, value: ResultAgreement, session: InboundSession) -> Sha256Digest:
        self._record("result_agreement", value)
        return RESULT_DIGEST
