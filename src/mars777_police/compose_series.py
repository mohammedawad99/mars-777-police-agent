"""Assembling and running one strict internal series, start to finish.

This is the composition the counted command line has always performed, lifted
out of it so the command line can be argument parsing and error classification
and nothing else. Not one decision moved: settings are still read once, the
launch document still carries this side's opening candidate, and `AutonomousBoot`
still owns the lifecycle from serve to stop.
"""

import os
from pathlib import Path

from . import GROUP_CODE
from .agent_runtime import AgentRuntime
from .autonomous_boot import AutonomousBoot
from .composition import compose_agent
from .identity import ROLE
from .infra.settings import load_runtime_settings
from .launch_input import read_launch_document
from .operator_requests import StrictSeriesRequest


async def run_strict_series(request: StrictSeriesRequest) -> Path:
    """Compose the agent, let the boot coordinator run its whole life, and stop.

    Returns where this process wrote its own official artifacts - the one fact
    the operator needs afterwards, and the only one that leaves this function.
    """
    settings = load_runtime_settings(os.environ, expected_role=ROLE)
    document = read_launch_document(request.launch)
    composition = compose_agent(
        settings,
        document.identity,
        GROUP_CODE,
        request.external_mode,
        document.kit_terms,
    )
    runtime = AgentRuntime(composition, settings.local.host, settings.local.port)
    await AutonomousBoot(runtime, settings, document.config, ROLE, request.viewer).run()
    return settings.artifact_root
