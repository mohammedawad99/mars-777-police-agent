"""Translating project failures onto the framework error channel, both ways.

Two rules do all the work. A **known** application failure crosses carrying
**exactly its existing error identity** and nothing else, so the caller rebuilds
the same typed failure it would have raised locally. An **unknown** failure -
a genuine defect on our side - crosses as `E-LOCAL-DEFECT` with **no message at
all**, because a traceback, an exception string or a repr is precisely the
material that leaks internals and secrets to an untrusted peer.

Neither path ever uses `False`. That value belongs to `reveal` legality alone.
"""

from fastmcp.exceptions import ToolError

from ..app.protocol_errors import (
    AuthFailureError,
    ConfigMismatchError,
    ConventionMismatchError,
    LocalDefectError,
    MalformedMessageError,
    PeerProtocolError,
    ReportDisagreeError,
    StaleMessageError,
)

_BY_IDENTITY: dict[str, type[PeerProtocolError]] = {
    error.error_id: error
    for error in (
        MalformedMessageError,
        StaleMessageError,
        AuthFailureError,
        ConfigMismatchError,
        ConventionMismatchError,
        ReportDisagreeError,
        LocalDefectError,
    )
}
"""The closed table of identities that may cross. No identity was created."""

TRANSPORT_FAILURE = "E-TRANSPORT"
"""Unreachable, HTTP failure and timeout keep their existing owner."""


class TransportFailureError(Exception):
    """A delivery failure, distinct from every application outcome.

    Separate from `PeerProtocolError` on purpose: a peer that never answered has
    told us nothing about the protocol, and collapsing that into a protocol
    error would invent an accusation the evidence does not support.
    """

    error_id = TRANSPORT_FAILURE


def outbound(failure: BaseException) -> ToolError:
    """Map a server-side failure onto the wire, revealing nothing extra."""
    if isinstance(failure, PeerProtocolError):
        return ToolError(failure.error_id)
    return ToolError(LocalDefectError.error_id)


def inbound(message: str) -> PeerProtocolError:
    """Rebuild the peer's typed failure from its exact identity.

    An unrecognised or malformed identity is `E-PROTO-MALFORMED`: we will not
    parse unstable human text, and an identity we do not know is exactly a
    message we could not understand.
    """
    error = _BY_IDENTITY.get(message)
    if error is None:
        return MalformedMessageError(MalformedMessageError.error_id)
    return error(error.error_id)
