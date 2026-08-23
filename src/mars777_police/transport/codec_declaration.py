"""Codec for the declaration subtree and the Step-0 exchange.

`vram_gb` is handled by **omission** rather than by `null`, on both sides.
Encoding leaves the member unset when there is no GPU, and decoding reads the
unset member back as `None` - which is exactly what the semantic
`HardwareDeclaration` requires when `gpu is False`, and what keeps a CPU-only
participant's Step-0 core at 18 present leaves instead of unauthenticatable.

`cpu_freq_ghz` is a semantic `Decimal` and crosses as canonical text.
"""

from typing import Literal

from ..app.artifact_values import GitCommitSha, UtcTimestamp
from ..app.declaration_values import Declaration, DeclarationTeams, DeclarationTimes
from ..app.peer_pregame_messages import Step0DeclarationExchange
from ..app.team_declaration_values import (
    HardwareDeclaration,
    RepositoryLinks,
    RoleCommits,
    TeamDeclaration,
)
from .codec_auth import decode_auth, encode_auth
from .wire_declaration import (
    DeclarationTeamsWire,
    DeclarationTimesWire,
    DeclarationWire,
    HardwareWire,
    RepositoryLinksWire,
    RoleCommitsWire,
    Step0ExchangeWire,
    TeamDeclarationWire,
)
from .wire_scalars import decimal_from_text, text_from_decimal


def _decode_hardware(wire: HardwareWire) -> HardwareDeclaration:
    gpu: str | Literal[False] = wire.gpu if isinstance(wire.gpu, str) else False
    return HardwareDeclaration(
        wire.os,
        wire.cpu_cores,
        decimal_from_text(wire.cpu_freq_ghz),
        wire.ram_gb,
        gpu,
        wire.vram_gb,
    )


def _encode_hardware(hardware: HardwareDeclaration) -> HardwareWire:
    """Omit `vram_gb` entirely when absent - never emit it as `null`."""
    members: dict[str, object] = {
        "os": hardware.os,
        "cpu_cores": hardware.cpu_cores,
        "cpu_freq_ghz": text_from_decimal(hardware.cpu_freq_ghz),
        "ram_gb": hardware.ram_gb,
        "gpu": hardware.gpu,
    }
    if hardware.vram_gb is not None:
        members["vram_gb"] = hardware.vram_gb
    return HardwareWire.model_validate(members)


def _decode_team(wire: TeamDeclarationWire) -> TeamDeclaration:
    return TeamDeclaration(
        wire.group_id,
        wire.group_name,
        tuple(wire.members),
        RepositoryLinks(wire.repos.police, wire.repos.thief),
        wire.mcp_endpoint,
        _decode_hardware(wire.hardware),
        wire.llm_model,
        wire.code_version,
        RoleCommits(
            GitCommitSha(wire.github_commits.police),
            GitCommitSha(wire.github_commits.thief),
        ),
    )


def _encode_team(team: TeamDeclaration) -> TeamDeclarationWire:
    return TeamDeclarationWire(
        group_id=team.group_id,
        group_name=team.group_name,
        members=list(team.members),
        repos=RepositoryLinksWire(police=team.repos.police, thief=team.repos.thief),
        mcp_endpoint=team.mcp_endpoint,
        hardware=_encode_hardware(team.hardware),
        llm_model=team.llm_model,
        code_version=team.code_version,
        github_commits=RoleCommitsWire(
            police=team.github_commits.police.value,
            thief=team.github_commits.thief.value,
        ),
    )


def decode_declaration(wire: DeclarationWire) -> Declaration:
    """Rebuild a declaration snapshot at whatever lifecycle moment it holds."""
    end = wire.times.game_end
    return Declaration(
        wire.game_id,
        wire.game_uid,
        wire.token_budget_per_series,
        DeclarationTimes(
            UtcTimestamp(wire.times.game_start),
            UtcTimestamp(end) if end is not None else None,
        ),
        DeclarationTeams(
            _decode_team(wire.teams.group_a) if wire.teams.group_a else None,
            _decode_team(wire.teams.group_b) if wire.teams.group_b else None,
        ),
    )


def encode_declaration(declaration: Declaration) -> DeclarationWire:
    """Render a declaration snapshot; absent members stay absent."""
    teams, times = declaration.teams, declaration.times
    return DeclarationWire(
        game_id=declaration.game_id,
        game_uid=declaration.game_uid,
        token_budget_per_series=declaration.token_budget_per_series,
        times=DeclarationTimesWire(
            game_start=times.game_start.value,
            game_end=times.game_end.value if times.game_end else None,
        ),
        teams=DeclarationTeamsWire(
            group_a=_encode_team(teams.group_a) if teams.group_a else None,
            group_b=_encode_team(teams.group_b) if teams.group_b else None,
        ),
    )


def decode_step0(wire: Step0ExchangeWire) -> Step0DeclarationExchange:
    """Rebuild the Step-0 exchange: subject first, evidence second."""
    return Step0DeclarationExchange(decode_declaration(wire.declaration), decode_auth(wire.auth))


def encode_step0(exchange: Step0DeclarationExchange) -> Step0ExchangeWire:
    """Render the Step-0 exchange."""
    return Step0ExchangeWire(
        declaration=encode_declaration(exchange.declaration), auth=encode_auth(exchange.auth)
    )
