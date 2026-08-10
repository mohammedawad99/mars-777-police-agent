"""The frozen `ERROR_MODEL.md` identities, as raisable application types.

Every class below carries an **existing** error id as a class attribute; Stage
4E-R16 created no identity, renamed none and re-classified none. The module is a
naming layer over the frozen taxonomy, not a second taxonomy: `domain.errors`
still owns deterministic game-domain failures and `app.turn_service` its local
action errors, and neither is duplicated or subclassed here.

Two boundaries the ids themselves encode, restated because collapsing them is
the exact defect `API_BOUNDARIES.md` O2 forbids:

* a **malformed representation** (`E-PROTO-MALFORMED`) is not a well-formed
  value that fails to verify (`E-AUTH-FAILURE`), and neither is a value that
  arrives in the wrong phase or twice (`E-PROTO-STALE`);
* none of them is ever encoded as a returned `accepted=False`, and a local
  fault (`E-LOCAL-DEFECT`) is never reported as an accusation against the peer.

Messages carry local diagnostics only - never key bytes, a nonce, a secret or
opponent truth (SEC-003/004).
"""

from typing import ClassVar


class PeerProtocolError(Exception):
    """Base of the frozen protocol error identities.

    Deliberately **not** a `ValueError`: a structurally malformed *construction*
    of a semantic value raises `ValueError` under the existing value policy,
    while these are runtime protocol outcomes decided by a boundary that knows
    the phase, the provisioned expectation and the peer.
    """

    error_id: ClassVar[str] = ""


class MalformedMessageError(PeerProtocolError):
    """A representation that is not well formed for its declared profile/shape."""

    error_id: ClassVar[str] = "E-PROTO-MALFORMED"


class StaleMessageError(PeerProtocolError):
    """A duplicate, out-of-order, wrong-phase or wrong-sub-game message."""

    error_id: ClassVar[str] = "E-PROTO-STALE"


class AuthFailureError(PeerProtocolError):
    """A well-formed proof that fails verification, or a profile/key mismatch.

    Also the identity for *no compatible mechanism* - a configured profile with
    no provisioned provider fails closed here rather than falling back.
    """

    error_id: ClassVar[str] = "E-AUTH-FAILURE"


class ConfigMismatchError(PeerProtocolError):
    """Digest inequality, or a value outside its Appendix-F status."""

    error_id: ClassVar[str] = "E-CONFIG-MISMATCH"


class ConventionMismatchError(PeerProtocolError):
    """Each peer echoing a different series convention (`PRD05-FR-033`)."""

    error_id: ClassVar[str] = "E-NET-CONVENTION-MISMATCH"


class ReportDisagreeError(PeerProtocolError):
    """Contradictory result evidence: identity, commit, timestamp or digest."""

    error_id: ClassVar[str] = "E-REPORT-DISAGREE"


class LocalDefectError(PeerProtocolError):
    """Our own invariant violation - never a protocol accusation against a peer."""

    error_id: ClassVar[str] = "E-LOCAL-DEFECT"
