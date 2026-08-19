"""The failures a caller of this facade has to be able to tell apart.

Nothing new is defined here. Every name is the identity some layer already owns,
re-exported so that a consumer catches a documented public type instead of
reaching into `app`, `infra` or `transport` for it. A caller that can only catch
`Exception` cannot classify a refusal, and classification is exactly what these
failures are for.
"""

from ..app.protocol_errors import LocalDefectError, PeerProtocolError
from ..app.public_ingress import PublicIngressError
from ..infra.settings import SettingsError
from ..launch_input import LaunchInputError
from ..shared.version import SoftwareVersionError
from ..transport.wire_errors import TransportFailureError

__all__ = [
    "LaunchInputError",
    "LocalDefectError",
    "PeerProtocolError",
    "PublicIngressError",
    "SdkError",
    "SettingsError",
    "SoftwareVersionError",
    "TransportFailureError",
]


class SdkError(Exception):
    """A refusal that belongs to this facade and to no layer below it.

    Deliberately unused today: the facade forwards, so every current failure is
    somebody else's identity. It exists so that a future facade-level refusal has
    a home that is not somebody else's error type borrowed for the occasion.
    """
