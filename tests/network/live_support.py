"""Opt-in gate and shared wiring for the live ngrok suite.

Normal CI must never need a tunnel, a credential or the internet, so every test
in this group is skipped unless the operator sets a **non-secret** switch whose
value is the literal `"1"`. It is not a credential and never reaches production.

The R17 peer helpers live in `tests/transport`, which pytest puts on a different
path root, so they are reached by extending `sys.path` rather than by
duplicating a second peer harness that could drift from the first.
"""

import os
import sys
from pathlib import Path

import pytest

from mars777_police.app.public_endpoint_policy import SystemHostResolver
from mars777_police.app.public_network_workflow import PublicNetworkService
from mars777_police.infra.ngrok_ingress import NgrokPublicIngress
from mars777_police.infra.ngrok_process import NgrokProcess
from mars777_police.infra.ngrok_settings import NgrokSettings

LIVE_SWITCH = "MARS777_RUN_LIVE_NGROK"
NGROK = Path.home() / ".local/bin/ngrok"
TIMEOUT = 40.0
UNREACHABLE = "https://mars777-r18-no-such-route.ngrok-free.dev/mcp"

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "transport"))

requires_live_ngrok = pytest.mark.skipif(
    os.environ.get(LIVE_SWITCH) != "1" or not NGROK.exists(),
    reason=f"live ngrok suite runs only when {LIVE_SWITCH}=1 and the agent is installed",
)


def ingress() -> NgrokPublicIngress:
    """The production adapter, pointed at the operator's own agent."""
    return NgrokPublicIngress(NgrokProcess(NgrokSettings(NGROK, discovery_seconds=60.0)))


def service(route: NgrokPublicIngress) -> PublicNetworkService:
    """The production public-network owner over a live route."""
    from net_builders import runtime

    return PublicNetworkService(route, SystemHostResolver(), runtime())
