"""Real compositions bound to OS-assigned ports, shared by the boot tests.

Everything here is used by more than one boot test file. The machinery that only
the real `python -m` tests need - spawning, HTTP readiness, platform stop control
and the launch document - lives in `executable_process` instead.
"""

import socket

import composed_builders as compose
from r16_builders import GROUP_A, GROUP_B

from mars777_police.agent_runtime import AgentRuntime
from mars777_police.app.sealed_record_values import ActorRole
from mars777_police.composition_values import AgentComposition

HOST = "127.0.0.1"
SECRET = "out-of-band-provisioned-secret"
"""A synthetic test key; the real one never appears in this repository."""


def free_port() -> int:
    """Ask the OS for a port rather than guessing one."""
    with socket.socket() as probe:
        probe.bind((HOST, 0))
        return int(probe.getsockname()[1])


def runtime_for(composition: AgentComposition, port: int | None = None) -> AgentRuntime:
    """The production lifecycle owner over a real composition."""
    return AgentRuntime(composition, HOST, port if port is not None else free_port())


def agent(
    group_id: str = GROUP_A,
    slot: str = "group_a",
    role: ActorRole = ActorRole.POLICE,
    opponent: str = "http://127.0.0.1:1/mcp",
) -> AgentComposition:
    """One real composed agent pointed at *opponent*."""
    return compose.compose(group_id, slot, role, opponent)


def pair_urls() -> tuple[int, int]:
    """Two ports chosen before either agent is composed."""
    return free_port(), free_port()


def other() -> tuple[str, str, ActorRole]:
    """The opposing side's identity."""
    return GROUP_B, "group_b", ActorRole.THIEF
