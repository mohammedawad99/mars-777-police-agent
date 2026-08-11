"""Wire DTOs for the declaration subtree and the Step-0 exchange.

`vram_gb` is the one conditional member and it stays conditional here: it is
`int | None` with a default of `None`, and the codec **omits** it rather than
sending `null` when there is no GPU. That mirrors the Step-0 projection exactly,
which is what keeps a CPU-only participant's authenticated core at 18 present
leaves instead of making it unauthenticatable.

`cpu_freq_ghz` is a semantic `Decimal` and therefore crosses as canonical text.
"""

from pydantic import BaseModel, ConfigDict

from .wire_config import AuthProofWire
from .wire_config_sections import WIRE
from .wire_scalars import CommitText, DecimalText, NonEmptyText, TimestampText


class RepositoryLinksWire(BaseModel):
    """The declaring team's two repository addresses."""

    model_config = WIRE

    police: NonEmptyText
    thief: NonEmptyText


class HardwareWire(BaseModel):
    """The Step-0 machine specification.

    `gpu` is the frozen `string | False` union - a model name, or exactly
    `False`. `vram_gb` follows it and is absent, never null, when there is none.
    """

    model_config = ConfigDict(extra="forbid", strict=True)

    os: NonEmptyText
    cpu_cores: int
    cpu_freq_ghz: DecimalText
    ram_gb: int
    gpu: NonEmptyText | bool
    vram_gb: int | None = None


class TeamDeclarationWire(BaseModel):
    """One participant's complete declaration subtree."""

    model_config = WIRE

    group_id: NonEmptyText
    group_name: NonEmptyText
    members: list[str]
    repos: RepositoryLinksWire
    mcp_endpoint: NonEmptyText
    hardware: HardwareWire
    llm_model: NonEmptyText
    code_version: NonEmptyText
    github_commit: CommitText


class DeclarationTimesWire(BaseModel):
    """`game_end` is absent until close, exactly as the semantic value holds it."""

    model_config = WIRE

    game_start: TimestampText
    game_end: TimestampText | None = None


class DeclarationTeamsWire(BaseModel):
    """The two participant slots; a pre-exchange snapshot fills exactly one."""

    model_config = WIRE

    group_a: TeamDeclarationWire | None = None
    group_b: TeamDeclarationWire | None = None


class DeclarationWire(BaseModel):
    """A declaration snapshot at one lifecycle moment."""

    model_config = WIRE

    game_id: NonEmptyText
    game_uid: NonEmptyText
    token_budget_per_series: int
    times: DeclarationTimesWire
    teams: DeclarationTeamsWire


class Step0ExchangeWire(BaseModel):
    """`Step0DeclarationExchange(declaration, auth)` - subject then evidence."""

    model_config = WIRE

    declaration: DeclarationWire
    auth: AuthProofWire
