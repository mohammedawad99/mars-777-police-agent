"""The application owner of one result agreement, end to end.

Everything below it already existed and none of it was wired to anything: the
cadence lived in `ResultAgreementRuntime`, the digest in the result core runtime,
the comparison in `require_matching_digest` and the verdict in
`MutualAgreementGate` - and no production module called any of them. This is the
service that does, so a mismatched digest fails in the runtime rather than only
in a test.

**Ownership.** Verifying agreement is an application concern. The transport
sends a `ResultAgreement` and returns the peer's `Sha256Digest`; it does not
decide whether that digest agrees, and this module never learns how the digest
travelled.

**The asymmetry is the frozen one.** The non-proposer can compute its local
digest as soon as the proposer's request arrives, so it compares when its own
request returns. The proposer cannot - it has no opponent contribution yet - so
it retains the digest handed back to it and compares once its own core becomes
derivable. One `_verify` covers both: it fires the moment both digests exist.
"""

from dataclasses import dataclass, field

from .artifact_values import UtcTimestamp
from .declaration_values import Declaration
from .peer_final_messages import ResultAgreement
from .peer_transport import PeerTransportPort
from .ports import ResultDigestPort
from .protocol_errors import StaleMessageError
from .protocol_values import Sha256Digest
from .result_agreement_gates import MutualAgreementGate, require_matching_digest
from .result_agreement_runtime import ResultAgreementRuntime
from .result_core_runtime import SubGameOutcomeLine, assemble
from .result_core_values import CumulativeResult, ResultApprovalCore
from .result_identity_values import GithubLinks
from .result_values import ResultContribution
from .series_audit_gate import SeriesAuditGate
from .series_milestones import ResultMilestones


@dataclass(slots=True)
class ResultExchange:
    """One peer's half of the result agreement, from first request to verdict."""

    runtime: ResultAgreementRuntime
    transport: PeerTransportPort
    digester: ResultDigestPort
    declaration: Declaration
    lines: tuple[SubGameOutcomeLine, ...]
    links: GithubLinks
    cumulative: CumulativeResult
    own: ResultContribution
    local_digest: Sha256Digest | None = field(default=None)
    peer_digest: Sha256Digest | None = field(default=None)
    own_request_sent: bool = field(default=False)
    peer_request_handled: bool = field(default=False)
    peer_contribution: ResultContribution | None = field(default=None)
    verified: bool = field(default=False)
    timestamp: UtcTimestamp | None = field(default=None)
    milestones: ResultMilestones = field(default_factory=ResultMilestones)

    @property
    def gate(self) -> MutualAgreementGate:
        """The frozen completion verdict, from the facts actually recorded."""
        return MutualAgreementGate(
            self.runtime.is_proposer,
            self.local_digest,
            self.peer_digest,
            self.own_request_sent,
            self.peer_request_handled,
        )

    def _core(self, peer: ResultContribution, timestamp: UtcTimestamp) -> ResultApprovalCore:
        """The one assembled core; every digest and every report uses this call."""
        return assemble(
            self.declaration,
            self.runtime.declaration_ref,
            self.lines,
            (self.own, peer),
            self.links,
            self.cumulative,
            timestamp,
        )

    def _digest_with(self, peer: ResultContribution, timestamp: UtcTimestamp) -> Sha256Digest:
        """The one production digest truth: assemble the core, then hash it."""
        return self.digester.digest(self._core(peer, timestamp))

    def approval_core(self) -> ResultApprovalCore:
        """The exact core the agreed digest covers, for the official report.

        Rebuilt from the retained facts through the same `_core` the digest
        used, so a report can never present a core the hash did not cover.
        """
        if not self.is_agreed or self.peer_contribution is None or self.timestamp is None:
            raise StaleMessageError("the approval core exists only once the result is agreed")
        return self._core(self.peer_contribution, self.timestamp)

    def _verify(self) -> None:
        """Compare as soon as both digests exist; a mismatch fails closed.

        `require_matching_digest` raises `E-REPORT-DISAGREE`, so the direction
        is never recorded verified on a disagreement - the assignment below is
        unreachable in that case, which is the point.
        """
        if self.local_digest is not None and self.peer_digest is not None:
            require_matching_digest(self.local_digest, self.peer_digest)
            self.verified = True

    def require_series_audit(self, gate: SeriesAuditGate) -> None:
        """Refuse to start unless this side's whole series audit has passed.

        The runtime already owns what a passing verdict means; the gate owns
        what the series verdict *is*. This only carries one to the other, so an
        incomplete series arrives as `None` and is refused by the same check
        that refuses a tampered one.
        """
        self.runtime.require_audit(gate.verdict)

    def accept_peer_request(self, agreement: ResultAgreement, sender_id: str) -> Sha256Digest:
        """Process the peer's single request and return our own digest."""
        adopted = self.runtime.accept(agreement, sender_id, proposed=self.timestamp)
        self.timestamp, self.peer_contribution = adopted, agreement.contribution
        self.local_digest = self._digest_with(agreement.contribution, adopted)
        self.peer_request_handled = True
        self._verify()
        self.milestones.requested.set()
        return self.local_digest

    async def open_agreement(self) -> None:
        """Proposer: choose the timestamp, send, and retain the peer's digest."""
        request = self.runtime.open_agreement(self.own)
        self.timestamp = request.timestamp
        await self._send(request)

    async def send_response(self, timestamp: UtcTimestamp) -> None:
        """Non-proposer: echo the adopted timestamp and send our own request."""
        await self._send(self.runtime.request(timestamp, self.own))

    async def _send(self, request: ResultAgreement) -> None:
        self.peer_digest = await self.transport.send_result_agreement(request)
        self.own_request_sent = True
        self._verify()

    @property
    def is_agreed(self) -> bool:
        """True only when both directions completed and the digests matched."""
        return self.verified and self.gate.is_agreed
