"""Turning one operator JSON document into the series facts settings cannot hold.

`RuntimeSettings` refuses to carry `game_id`, `game_uid` or the declaration -
series identity is established at Step-0, not read from an environment - so a
real process has to be told them. This is the only place that reads that file,
and it invents nothing.

**No new schema.** The `declaration` object is exactly `DeclarationWire`, the
frozen JSON contract the peer transport already validates and decodes,
`profiles` is exactly `InteropProfileSetWire`, and `config` is exactly
`NegotiatedConfigWire`. Validation belongs to those models and to the semantic
constructors behind `decode_declaration` / `decode_profiles` / `decode_config`;
repeating it here would be a second opinion that can drift.

**The config is a candidate, not an agreement.** It is what this process opens
the negotiation with; the peer still has to converge, and `ConfigLockRuntime`
still refuses a digest that differs from the one we recomputed. Handing a
process its own opening terms is operator input, not a gameplay decision.

**Everything derivable is derived.** `game_id`, `game_uid` and the token budget
are members of the declaration itself, so they are read from it rather than
supplied twice and risked disagreeing. Only `first_sub_game` is a separate
scalar, because which round a process starts on is an operator decision the
declaration does not record.
"""

import json
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel, ValidationError

from .composition_values import SeriesIdentity
from .domain.errors import DomainError
from .domain.negotiated_config import NegotiatedConfig
from .transport.codec_auth import decode_profiles
from .transport.codec_config import decode_config
from .transport.codec_declaration import decode_declaration
from .transport.wire_config import InteropProfileSetWire, NegotiatedConfigWire
from .transport.wire_config_sections import WIRE
from .transport.wire_declaration import DeclarationWire


class LaunchInputError(ValueError):
    """The launch document is missing, unreadable or not a valid series input.

    A local operator failure, deliberately **not** a peer protocol identity: no
    peer is involved and nothing has started. Its message names the field or the
    path, never a secret - key material arrives through settings, never here.
    """


class LaunchDocumentWire(BaseModel):
    """The exact launch document: three frozen wire objects and two scalars.

    `kit_terms` is the one optional member, and it is operator input rather than
    a peer contract: the flat signed set an external KIT pairing agreed. It is
    absent for every internal series, and required only when the operator also
    selects the external compatibility mode - the two statements are checked
    against each other at composition, never reconciled silently.
    """

    model_config = WIRE
    declaration: DeclarationWire
    profiles: InteropProfileSetWire
    config: NegotiatedConfigWire
    first_sub_game: int
    kit_terms: dict[str, object] | None = None


@dataclass(frozen=True, slots=True)
class LaunchDocument:
    """What one operator document tells a process: who it is, and what to open with.

    Two values rather than one, because they belong to different owners:
    `SeriesIdentity` is what composition needs, and the config candidate is what
    the boot coordinator hands to the series it starts.
    """

    identity: SeriesIdentity
    config: NegotiatedConfig
    kit_terms: dict[str, object] | None = None


def parse_launch_document(text: str) -> LaunchDocument:
    """Build the launch facts from *text*, or refuse with a local error.

    The semantic constructors refuse too - a grid below the Appendix-F floor is
    a `DomainError` from the section that owns it, not a wire problem - so both
    refusals are reported as the one local error a process can act on.
    """
    try:
        wire = LaunchDocumentWire.model_validate_json(text)
    except ValidationError as failure:
        raise LaunchInputError(
            f"the launch document is not valid: {failure.error_count()} problem(s)"
        ) from None
    declaration = decode_declaration(wire.declaration)
    try:
        config = decode_config(wire.config)
    except (ValueError, DomainError) as failure:
        raise LaunchInputError(f"the launch config is not a valid agreement: {failure}") from None
    return LaunchDocument(
        SeriesIdentity(
            declaration.game_id,
            declaration.game_uid,
            wire.first_sub_game,
            declaration,
            decode_profiles(wire.profiles),
            declaration.token_budget_per_series,
        ),
        config,
        wire.kit_terms,
    )


def read_launch_document(path: Path) -> LaunchDocument:
    """Read and parse the launch document at *path*."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as failure:
        raise LaunchInputError(f"the launch document at {path} could not be read") from failure
    if not text.strip():
        raise LaunchInputError(f"the launch document at {path} is empty")
    try:
        json.loads(text)
    except json.JSONDecodeError as failure:
        raise LaunchInputError(f"the launch document at {path} is not JSON") from failure
    return parse_launch_document(text)
