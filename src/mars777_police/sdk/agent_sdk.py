"""The one entry point every consumer uses: menus, CLI, GUI, third parties.

**This class decides nothing.** Every method forwards to the composition module
that already owns the work and returns what it answered. That is the whole
contract: a facade that computed anything of its own would be a second authority
for something already owned below, and the first thing to disagree.

**What it does own** is the guarantee that a process using this software really
is this software - the local integrity check runs once, at construction, before
any operation can be reached.

Framework types never appear here. A caller works with paths, project values and
project errors; whether the wire underneath is one framework or another is not
part of the promise.
"""

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path

from .. import compose_backend, compose_gateway, compose_replay, compose_series, compose_verify
from ..app.config_artifact_values import ConfigArtifactContent
from ..app.replay_session import ReplaySession
from ..app.replay_values import ReplaySummary
from ..kit_backend import KitRoleBackend
from ..kit_backend_boot import KitBackendBoot
from ..kit_public_launcher import KitPublicLauncher
from ..operator_requests import (
    PublicGatewayRequest,
    RoleBackendRequest,
    StrictSeriesRequest,
)
from ..shared.version import verify_installation


@dataclass(frozen=True, slots=True)
class AgentSdk:
    """This repository's public operations, in one place.

    *lookup* exists so the integrity check's failure path is reachable in a test
    without installing a wrong build; `None` means the real installed metadata.
    """

    lookup: Callable[[str], str] | None = None

    def __post_init__(self) -> None:
        verify_installation(lookup=self.lookup)

    async def run_strict_series(self, request: StrictSeriesRequest) -> Path:
        """Play one complete series and return where the artifacts were written."""
        return await compose_series.run_strict_series(request)

    def compose_role_backend(self, request: RoleBackendRequest) -> KitBackendBoot:
        """Assemble this role's friendly backend. Nothing is served or dialled."""
        return compose_backend.compose_role_backend(request)

    def write_contribution(self, backend: KitRoleBackend, root: Path) -> str:
        """Write a finished backend's development evidence and say where."""
        return compose_backend.write_contribution(backend, root)

    def compose_public_gateway(self, request: PublicGatewayRequest) -> KitPublicLauncher:
        """Assemble the group's public front door. No route is opened yet."""
        return compose_gateway.compose_public_gateway(request)

    def verify_config_artifact(self, document: Mapping[str, object]) -> ConfigArtifactContent:
        """Return what a stored config artifact proves, or refuse it."""
        return compose_verify.verify_stored_config(document)

    def open_replay(self, log: Path, config: Path, root: Path | None = None) -> ReplaySession:
        """Return a navigable replay of one sub-game log and its configuration."""
        return compose_replay.open_replay(log, config, root)

    def verify_replay(self, log: Path, config: Path, root: Path | None = None) -> ReplaySummary:
        """Replay one sub-game and return what the replay establishes."""
        return compose_replay.open_replay(log, config, root).summary()
