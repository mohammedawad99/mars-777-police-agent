"""The two local completion gates of the result agreement.

Split from `app.result_agreement_runtime` by measured line budget and by
responsibility: that module owns the **cadence** - who speaks, in what order,
carrying what - while this one owns the **verdict** on whether the exchange is
finished. The asymmetry is the substance: the proposer and the non-proposer
finish on different evidence, and neither finishes on one direction alone.

`mutual_agreement` is local application state. It is never a peer field, never
an `accepted` flag on a message, and never something a peer can assert on our
behalf.
"""

from dataclasses import dataclass

from .protocol_values import Sha256Digest


@dataclass(frozen=True, slots=True)
class MutualAgreementGate:
    """The frozen asymmetric completion gate; neither direction alone suffices.

    The proposer reaches it only once the non-proposer's request has arrived,
    its own core has become derivable, and the digest handed to it earlier
    equals the one it then computes. The non-proposer reaches it only once it
    has processed the first request, sent its own, and had its digest returned
    equal. Both readings are the same four facts, which is why one value serves
    both sides.
    """

    is_proposer: bool
    local_digest: Sha256Digest | None
    peer_digest: Sha256Digest | None
    own_request_sent: bool
    peer_request_handled: bool

    @property
    def is_agreed(self) -> bool:
        """True only when both directions completed and the digests are equal."""
        if self.local_digest is None or self.peer_digest is None:
            return False
        if not (self.own_request_sent and self.peer_request_handled):
            return False
        return self.local_digest == self.peer_digest
