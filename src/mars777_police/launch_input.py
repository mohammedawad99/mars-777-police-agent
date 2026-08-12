"""Turning one operator JSON document into the series facts settings cannot hold.

`RuntimeSettings` refuses to carry `game_id`, `game_uid` or the declaration -
series identity is established at Step-0, not read from an environment - so a
real process has to be told them. This is the only place that reads that file,
and it invents nothing.

**No new schema.** The `declaration` object is exactly `DeclarationWire`, the
frozen JSON contract the peer transport already validates and decodes, and
`profiles` is exactly `InteropProfileSetWire`. Validation belongs to those
models and to the semantic constructors behind `decode_declaration` /
`decode_profiles`; repeating it here would be a second opinion that can drift.

**Everything derivable is derived.** `game_id`, `game_uid` and the token budget
are members of the declaration itself, so they are read from it rather than
supplied twice and risked disagreeing. Only `first_sub_game` is a separate
scalar, because which round a process starts on is an operator decision the
declaration does not record.
"""

import json
from pathlib import Path

from pydantic import BaseModel, ValidationError

from .composition_values import SeriesIdentity
from .transport.codec_auth import decode_profiles
from .transport.codec_declaration import decode_declaration
from .transport.wire_config import InteropProfileSetWire
from .transport.wire_config_sections import WIRE
from .transport.wire_declaration import DeclarationWire


class LaunchInputError(ValueError):
    """The launch document is missing, unreadable or not a valid series input.

    A local operator failure, deliberately **not** a peer protocol identity: no
    peer is involved and nothing has started. Its message names the field or the
    path, never a secret - key material arrives through settings, never here.
    """


class LaunchDocumentWire(BaseModel):
    """The exact launch document: two frozen wire objects and one scalar."""

    model_config = WIRE
    declaration: DeclarationWire
    profiles: InteropProfileSetWire
    first_sub_game: int


def parse_launch_document(text: str) -> SeriesIdentity:
    """Build the series identity from *text*, or refuse with a local error."""
    try:
        wire = LaunchDocumentWire.model_validate_json(text)
    except ValidationError as failure:
        raise LaunchInputError(
            f"the launch document is not valid: {failure.error_count()} problem(s)"
        ) from None
    declaration = decode_declaration(wire.declaration)
    return SeriesIdentity(
        declaration.game_id,
        declaration.game_uid,
        wire.first_sub_game,
        declaration,
        decode_profiles(wire.profiles),
        declaration.token_budget_per_series,
    )


def read_launch_document(path: Path) -> SeriesIdentity:
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
