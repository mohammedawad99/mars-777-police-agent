"""The two-request result-agreement cadence and its two completion gates.

Exactly **two** semantic requests per series, in a deterministic order:

1. the **proposer** - the participant whose `group_id` is byte-wise lower, never
   the `group_a` slot - obtains the timestamp once and sends its one request;
2. the **non-proposer** adopts that timestamp verbatim, assembles the core,
   computes its digest and returns it as the operation's response;
3. the non-proposer sends its own single request, echoing the identical
   timestamp;
4. the proposer verifies the echo, assembles the identical core and returns its
   digest.

The proposer **cannot** build a digest before step 3 - it has no opponent
contribution - so it retains the digest it was handed at step 2 and compares it
once its own core becomes derivable. Requiring both sides to hold a digest before
the first response would deadlock the exchange, which is why it is not required.

The response is a `Sha256Digest` and nothing else: no `accepted` bool, no ack
family, no ninth family. Regenerating a request never regenerates the timestamp,
so a transport retry re-sends an identical semantic value; there are no transport
retries here at all, and the immutability holds regardless.

Everything starts only after the **local** `FINAL_AUDIT` passes. A peer's claim
never substitutes for our own verification, and no audit verdict is transmitted.

`declaration_ref` is deliberately **not** re-checked here. `ResultAgreement`
already refuses at construction any reference that is not
`declaration_<game_id>.json`, so once the request's `game_id` equals ours its
reference equals ours too - and a second check would only add a branch that no
well-formed value can ever take.
"""

from dataclasses import dataclass

from .artifact_values import UtcTimestamp
from .peer_final_messages import DECLARATION_FILENAME, ResultAgreement
from .ports import TimestampPort
from .protocol_errors import ReportDisagreeError, StaleMessageError
from .protocol_values import FinalAuditVerdict
from .result_identity_values import ResultParticipants
from .result_values import ResultContribution


def timestamp_proposer(participants: ResultParticipants) -> str:
    """Return the `group_id` that proposes the agreement timestamp.

    The byte-wise lower **value**, compared exactly. It is emphatically not
    `participants.group_a`: the live example places the lower id in the
    `group_b` slot, so keying the rule on the slot would silently swap the roles
    in real matches.
    """
    return min(participants.group_a, participants.group_b)


@dataclass(frozen=True, slots=True)
class ResultAgreementRuntime:
    """The local result-agreement service for one series."""

    group_id: str
    game_id: str
    game_uid: str
    participants: ResultParticipants
    clock: TimestampPort

    @property
    def is_proposer(self) -> bool:
        """True when this peer owns the timestamp for the agreement attempt."""
        return timestamp_proposer(self.participants) == self.group_id

    @property
    def declaration_ref(self) -> str:
        """The frozen Table-20 filename this result joins against."""
        return DECLARATION_FILENAME.format(game_id=self.game_id)

    def require_audit(self, verdict: FinalAuditVerdict | None) -> None:
        """Refuse to start unless our own final audit has passed."""
        if verdict is not FinalAuditVerdict.VERIFIED_OK:
            raise StaleMessageError(
                "result agreement may begin only after the local FINAL_AUDIT passes",
            )

    def open_agreement(self, contribution: ResultContribution) -> ResultAgreement:
        """Return the proposer's single first request, choosing the timestamp once."""
        if not self.is_proposer:
            raise StaleMessageError(
                f"only {timestamp_proposer(self.participants)!r} opens the agreement",
            )
        return self.request(self.clock.now(), contribution)

    def request(
        self,
        timestamp: UtcTimestamp,
        contribution: ResultContribution,
    ) -> ResultAgreement:
        """Return our single request carrying *timestamp* verbatim."""
        if contribution.group_id != self.group_id:
            raise ReportDisagreeError("we may contribute only our own participant data")
        return ResultAgreement(
            self.game_id,
            self.game_uid,
            self.declaration_ref,
            timestamp,
            contribution,
        )

    def accept(
        self,
        request: ResultAgreement,
        sender_id: str,
        *,
        proposed: UtcTimestamp | None = None,
        seen: bool = False,
    ) -> UtcTimestamp:
        """Validate an inbound request and return the agreed timestamp."""
        if seen:
            raise StaleMessageError(f"{sender_id!r} already sent its single request")
        if sender_id == self.group_id:
            raise StaleMessageError("a result request cannot arrive from ourselves")
        if sender_id != request.contribution.group_id:
            raise ReportDisagreeError(
                "the authenticated sender does not own the contributed group_id",
            )
        expected_proposer = timestamp_proposer(self.participants)
        if proposed is None and sender_id != expected_proposer:
            raise StaleMessageError(f"only {expected_proposer!r} may send the first request")
        if request.game_id != self.game_id or request.game_uid != self.game_uid:
            raise ReportDisagreeError("the request does not name this game")
        if proposed is not None and request.timestamp != proposed:
            raise ReportDisagreeError(
                "the echoed timestamp differs from the one proposed; it is adopted"
                " verbatim, never reformatted, re-precisioned or regenerated",
            )
        return request.timestamp
