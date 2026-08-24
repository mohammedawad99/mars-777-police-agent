"""What an operator - or any programmatic caller - asks this agent to do.

Three frozen requests, one per thing this repository can be told to do. They
exist so the facade's signatures are semantic values rather than a widening list
of positional arguments, and so a command line has exactly one job: turn parsed
text into one of these.

**They carry no behaviour and no defaults the protocol owns.** Everything a peer
must agree to lives in the negotiated configuration; what is here is local
operator intent - which document, which port, whom to dial, where to write.
"""

from dataclasses import dataclass
from pathlib import Path

from .app.kit_preset import ExternalMode
from .app.live_view_sink import NO_VIEWER, LiveViewSink

FRIENDLY_EVIDENCE_ROOT = Path("runtime/friendly")
"""Where a development run writes its evidence unless told otherwise."""


@dataclass(frozen=True, slots=True)
class StrictSeriesRequest:
    """Play one complete series over the wire named by *external_mode*."""

    launch: Path
    external_mode: ExternalMode = ExternalMode.STRICT_INTERNAL
    viewer: LiveViewSink = NO_VIEWER
    """Somewhere to publish the live view. Optional, lossy, never consulted."""


@dataclass(frozen=True, slots=True)
class RoleBackendRequest:
    """Serve this repository's role behind a group gateway, for a friendly."""

    launch: Path
    port: int
    opponent: str
    gateway_admin: str
    first_role: str | None = None
    """The operator's stated sub-game-1 role, or `None` when they stated none.

    Text rather than a `KitRole`, and unresolved on purpose: this is what someone
    typed, not what the series agreed. The composition resolves it against the
    frozen contract, which is the only place that may decide between them.
    """
    evidence_root: Path = FRIENDLY_EVIDENCE_ROOT


@dataclass(frozen=True, slots=True)
class PublicGatewayRequest:
    """Put the group gateway behind one public route, for a friendly."""

    police_endpoint: str
    thief_endpoint: str
    ngrok: Path
    launch: Path | None = None
    """The series launch document, when this route must also receive Step-0.

    Optional because a route that carries only per-sub-game greetings needs no
    declaration; a counted or authenticated-rehearsal route does, because Step-0
    is verified against **our own** declaration and there is nowhere else in this
    process to read it from."""

    first_role: str | None = None
    """The operator's stated sub-game-1 role, or `None` when they stated none.

    Text rather than a `KitRole`, and unresolved on purpose: this is what someone
    typed, not what the series agreed. The composition resolves it against the
    frozen contract, which is the only place that may decide between them.
    """
    evidence_root: Path = FRIENDLY_EVIDENCE_ROOT

    counted: bool = False
    """Whether this run may ever be counted or reported.

    Defaulted to `False` and carried from the operator's own command rather than
    inferred from a launch document, a secret's presence or an endpoint: what a
    run is worth is a decision somebody makes, not a state a process discovers.
    Every path that could report asks `CountedMode`, which this becomes."""
