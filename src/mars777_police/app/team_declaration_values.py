"""One participant's declaration subtree and its two nested values.

The declaration *subject data* for a single team, exactly as the live field
inventory names it. Structural validation only: nothing here knows which team
sent it, whether the endpoint answers, or whether the commit exists. Sender
entitlement over a subtree is a LIVE Step-0 duty, so no ``sender_id`` appears.

Hardware numeric types are the frozen ones (`DECLARATION_CONTRACT.md`
R14-R1-FIX-3): ``cpu_cores`` and ``ram_gb`` are exact ``int``, ``cpu_freq_ghz`` a
``Decimal``, ``vram_gb`` an ``int`` conditional on ``gpu``. **Hash membership
never determined a numeric type** - every one of these sits in the hashed Step-0
core, and that says nothing about whether a quantity is integral.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

from .artifact_values import GitCommitSha


class InvalidTeamDeclarationError(ValueError):
    """Raised when a participant declaration subtree is malformed."""


def _require_str(value: object, name: str) -> str:
    if type(value) is not str:
        raise InvalidTeamDeclarationError(f"{name} must be a str, got {type(value).__name__}")
    if not value:
        raise InvalidTeamDeclarationError(f"{name} must be non-empty")
    return value


def _require_positive_int(value: object, name: str) -> int:
    if type(value) is not int:
        raise InvalidTeamDeclarationError(f"{name} must be an int, got {type(value).__name__}")
    if value <= 0:
        raise InvalidTeamDeclarationError(f"{name} must be > 0, got {value}")
    return value


@dataclass(frozen=True, slots=True)
class RepositoryLinks:
    """The declaring team's two repository addresses."""

    police: str
    thief: str

    def __post_init__(self) -> None:
        _require_str(self.police, "police")
        _require_str(self.thief, "thief")


@dataclass(frozen=True, slots=True)
class RoleCommits:
    """The exact commit each of the declaring team's two repositories played.

    Role-keyed rather than a single scalar because a series alternates roles: the
    odd sub-games are played from one repository and the even ones from the
    other, so one commit could only ever describe half of them. The keys mirror
    `RepositoryLinks` exactly, which is what makes the repository a commit
    belongs to structural instead of conventional.
    """

    police: GitCommitSha
    thief: GitCommitSha

    def __post_init__(self) -> None:
        for name, value in (("police", self.police), ("thief", self.thief)):
            if type(value) is not GitCommitSha:
                raise InvalidTeamDeclarationError(
                    f"{name} commit must be a GitCommitSha, got {type(value).__name__}",
                )

    def for_role(self, role: str) -> GitCommitSha:
        """The commit declared for *role*, or a typed refusal for anything else."""
        if role == "police":
            return self.police
        if role == "thief":
            return self.thief
        raise InvalidTeamDeclarationError(f"no commit is declared for role {role!r}")


@dataclass(frozen=True, slots=True)
class HardwareDeclaration:
    """The Step-0 machine specification of one participant (Ch 5 p.55).

    ``gpu`` is the frozen ``string/bool`` union - a model name, or exactly
    ``False`` for "no GPU"; ``True`` is meaningless and refused. ``vram_gb``
    follows it: absent when there is no GPU, a strict positive ``int`` when there
    is. Whole gigabytes, so an integral type is exact by construction.
    """

    os: str
    cpu_cores: int
    cpu_freq_ghz: Decimal
    ram_gb: int
    gpu: str | Literal[False]
    vram_gb: int | None

    def __post_init__(self) -> None:
        _require_str(self.os, "os")
        _require_positive_int(self.cpu_cores, "cpu_cores")
        if type(self.cpu_freq_ghz) is not Decimal:
            raise InvalidTeamDeclarationError(
                f"cpu_freq_ghz must be a Decimal, got {type(self.cpu_freq_ghz).__name__}",
            )
        if not self.cpu_freq_ghz.is_finite() or self.cpu_freq_ghz <= 0:
            raise InvalidTeamDeclarationError("cpu_freq_ghz must be finite and > 0")
        _require_positive_int(self.ram_gb, "ram_gb")
        if self.gpu is not False:
            _require_str(self.gpu, "gpu")
        if self.gpu is False:
            if self.vram_gb is not None:
                raise InvalidTeamDeclarationError("vram_gb must be None when gpu is False")
        else:
            _require_positive_int(self.vram_gb, "vram_gb")


@dataclass(frozen=True, slots=True)
class TeamDeclaration:
    """One participant's complete declaration subtree."""

    group_id: str
    group_name: str
    members: tuple[str, ...]
    repos: RepositoryLinks
    mcp_endpoint: str
    hardware: HardwareDeclaration
    llm_model: str
    code_version: str
    github_commits: RoleCommits

    def __post_init__(self) -> None:
        _require_str(self.group_id, "group_id")
        _require_str(self.group_name, "group_name")
        if type(self.members) is not tuple:
            raise InvalidTeamDeclarationError(
                f"members must be a tuple, got {type(self.members).__name__}",
            )
        if not self.members:
            raise InvalidTeamDeclarationError("members must list at least one member")
        for member in self.members:
            _require_str(member, "member")
        for name, value, expected in (
            ("repos", self.repos, RepositoryLinks),
            ("hardware", self.hardware, HardwareDeclaration),
            ("github_commits", self.github_commits, RoleCommits),
        ):
            if type(value) is not expected:
                raise InvalidTeamDeclarationError(
                    f"{name} must be a {expected.__name__}, got {type(value).__name__}",
                )
        _require_str(self.mcp_endpoint, "mcp_endpoint")
        _require_str(self.llm_model, "llm_model")
        _require_str(self.code_version, "code_version")
