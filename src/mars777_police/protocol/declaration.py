"""The Step-0 authenticated core projection and its `step0_auth` adapter.

`DECLARATION_CONTRACT.md` §R12-FIX-2 enumerates the core member by member: **19
exact members**, the producing team's own subtree plus the shared game identity
and the agreed token cap. The projection is a nested object mirroring the
declaration paths - never a flattened copy, and never the whole `Declaration`.

The subtree is placed under its **canonical slot key**, `group_a` or `group_b`,
never under the participant's own `group_id`. A dynamic key would make the bytes
depend on an identifier rather than on a structure, and the project has kept
slots and ids separate everywhere else for exactly that reason.

Every member is mapped **explicitly**: no reflection, no `__dict__`, no generic
dataclass encoder and no custom `JSONEncoder`, so a member added to a semantic
value tomorrow cannot silently enter a hashed payload.

Two exclusions are structural rather than incidental - the opponent's subtree is
**not observable** at timeline event 1, and `times.game_end` is explicitly
mutable after the proof exists. `vram_gb` is **omitted, never `null`**, when
there is no GPU (`PRD06-FR-008`); its presence follows from `gpu`, so both peers
agree on presence without exchanging it.
"""

from typing import Final

from ..app.auth_values import AuthProof
from ..app.declaration_values import Declaration
from ..app.participant_slots import PARTICIPANT_SLOTS
from ..app.protocol_errors import LocalDefectError
from ..app.team_declaration_values import HardwareDeclaration, TeamDeclaration
from .keyed_auth import RESULT_CONTEXT, STEP0_CONTEXT, KeyedAuthenticator

STEP0_CORE_MEMBERS: Final[int] = 20
"""The frozen member count, with `hardware.vram_gb` present (§R12-FIX-2)."""


def locate(declaration: Declaration, group_id: str) -> tuple[str, TeamDeclaration]:
    """Return the slot and subtree *group_id* authored, or refuse the request."""
    for slot in PARTICIPANT_SLOTS:
        team = getattr(declaration.teams, slot)
        if team is not None and team.group_id == group_id:
            return slot, team
    raise LocalDefectError(f"this declaration carries no subtree for group_id {group_id!r}")


def _hardware_core(hardware: HardwareDeclaration) -> dict[str, object]:
    core: dict[str, object] = {
        "os": hardware.os,
        "cpu_cores": hardware.cpu_cores,
        "cpu_freq_ghz": hardware.cpu_freq_ghz,
        "ram_gb": hardware.ram_gb,
        "gpu": hardware.gpu,
    }
    if hardware.vram_gb is not None:
        core["vram_gb"] = hardware.vram_gb
    return core


def _team_core(team: TeamDeclaration) -> dict[str, object]:
    return {
        "group_id": team.group_id,
        "group_name": team.group_name,
        "members": list(team.members),
        "repos": {"police": team.repos.police, "thief": team.repos.thief},
        "mcp_endpoint": team.mcp_endpoint,
        "hardware": _hardware_core(team.hardware),
        "llm_model": team.llm_model,
        "code_version": team.code_version,
        "github_commits": {
            "police": team.github_commits.police.value,
            "thief": team.github_commits.thief.value,
        },
    }


def step0_core(declaration: Declaration, group_id: str) -> dict[str, object]:
    """Return the exact 19-member authenticated Step-0 core for *group_id*."""
    slot, team = locate(declaration, group_id)
    return {
        "game_id": declaration.game_id,
        "game_uid": declaration.game_uid,
        "times": {"game_start": declaration.times.game_start.value},
        "teams": {slot: _team_core(team)},
        "token_budget_per_series": declaration.token_budget_per_series,
    }


class Step0Authenticator:
    """The `Step0AuthPort` adapter over an already-provisioned authenticator."""

    def __init__(self, authenticator: KeyedAuthenticator) -> None:
        self._authenticator = authenticator

    def prove(self, declaration: Declaration, group_id: str) -> AuthProof:
        """Return this peer's proof over its own Step-0 core."""
        return self._authenticator.prove(STEP0_CONTEXT, step0_core(declaration, group_id))

    def verify(self, declaration: Declaration, group_id: str, proof: AuthProof) -> bool:
        """Return whether *proof* verifies over *group_id*'s Step-0 core."""
        return self._authenticator.verify(
            STEP0_CONTEXT,
            step0_core(declaration, group_id),
            proof,
        )


class RequestAuthenticator:
    """The `RequestAuthPort` adapter: one request's own bytes, in its own context.

    Adds no cryptography and holds no key of its own - it is the same provisioned
    `KeyedAuthenticator` Step-0 uses, asked a different question. The context
    differs, so a Step-0 proof presented here fails and a request proof presented
    at Step-0 fails, which is what domain separation is for.
    """

    def __init__(self, authenticator: KeyedAuthenticator) -> None:
        self._authenticator = authenticator

    def verify_request(self, payload: object, proof: AuthProof) -> bool:
        """Return whether *proof* verifies over *payload* in the request context."""
        return self._authenticator.verify(RESULT_CONTEXT, payload, proof)
