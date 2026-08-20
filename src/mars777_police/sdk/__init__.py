"""`mars777_police.sdk` - the public programmatic surface of this agent.

**What it is.** One import path for every consumer of this repository: the
command lines shipped here, a future graphical interface, a future replay
viewer, and any third party who installed the distribution. Guideline §4.1 asks
for exactly one such boundary, and this is it.

**What it is not.** Not a layer with rules of its own. It holds no game logic, no
cryptography, no strategy, no transport and no provider mechanics; it forwards to
the composition modules that own them. Nothing here is a second opinion about
anything.

    from mars777_police.sdk import AgentSdk, StrictSeriesRequest

    artifacts = asyncio.run(AgentSdk().run_strict_series(StrictSeriesRequest(launch)))

`KitBackendBoot` and `KitPublicLauncher` are exported because they are what the
two `compose_*` operations return, and a typed caller has to be able to name
them. They are project session objects, not framework types.

**The live view is a seam, not a screen.** `LiveViewSink`, `LatestSnapshot` and
`LiveViewSnapshot` are exported because a viewer has to be able to attach to a
running series and name what it receives. The drawing itself lives in
`mars777_police.gui`, which *consumes* this facade: a presentation package
imported by the facade would point the dependency the wrong way, and would make
every command line load an imaging library to parse an argument.

**Stability.** The names in `__all__` are the promise; anything else in this
package is an implementation detail and may move without notice.
"""

from ..app.kit_messages import KitRole
from ..app.kit_preset import ExternalMode
from ..app.live_view_sink import NO_VIEWER, LatestSnapshot, LiveViewSink
from ..app.live_view_values import LIVE, LiveViewSnapshot
from ..app.replay_board import LEGEND, board_lines
from ..app.replay_session import ReplaySession
from ..app.replay_status import audit_complete
from ..app.replay_values import (
    ReplayCheck,
    ReplayError,
    ReplayStep,
    ReplaySummary,
    ReplayTurn,
)
from ..identity import ROLE
from ..kit_backend import KitRoleBackend
from ..kit_backend_boot import KitBackendBoot
from ..kit_public_launcher import KitPublicLauncher
from ..operator_requests import (
    PublicGatewayRequest,
    RoleBackendRequest,
    StrictSeriesRequest,
)
from ..shared.version import VERSION as SOFTWARE_VERSION
from .agent_sdk import AgentSdk
from .errors import (
    LaunchInputError,
    LocalDefectError,
    PeerProtocolError,
    PublicIngressError,
    SdkError,
    SettingsError,
    SoftwareVersionError,
    TransportFailureError,
)

__all__ = [
    "LEGEND",
    "LIVE",
    "NO_VIEWER",
    "ROLE",
    "SOFTWARE_VERSION",
    "AgentSdk",
    "ExternalMode",
    "KitBackendBoot",
    "KitPublicLauncher",
    "KitRole",
    "KitRoleBackend",
    "LatestSnapshot",
    "LaunchInputError",
    "LiveViewSink",
    "LiveViewSnapshot",
    "LocalDefectError",
    "PeerProtocolError",
    "PublicGatewayRequest",
    "PublicIngressError",
    "ReplayCheck",
    "ReplayError",
    "ReplaySession",
    "ReplayStep",
    "ReplaySummary",
    "ReplayTurn",
    "RoleBackendRequest",
    "SdkError",
    "SettingsError",
    "SoftwareVersionError",
    "StrictSeriesRequest",
    "TransportFailureError",
    "audit_complete",
    "board_lines",
]
