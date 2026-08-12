"""What an official artifact store is, and what the four official files are called.

`API_BOUNDARIES.md` registered `ArtifactStorePort` long before anything could
write one; this is that port, plus the only place the official filenames are
spelled. Naming is a semantic contract - `NAMING_AND_IDENTITY.md` fixes the four
patterns and JDEC-004 fixes the two-digit `g<NN>` - so it belongs beside the port
rather than inside whichever adapter happens to write bytes.

**Names are derived, never accepted.** A caller supplies a `game_id` and a
sub-game, and the identifier is checked against the frozen `[a-z0-9-]` alphabet
before it can reach a path: a separator, a dot segment or an absolute prefix
cannot survive that check, so no `game_id` can escape the artifact root.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final, Protocol

from ..domain.config_model import FIRST_SUB_GAME, FIXED_NUM_GAMES
from .protocol_values import Sha256Digest

ArtifactDocument = Mapping[str, object]
"""One official artifact as JSON-native values, before it is serialized."""

_SAFE: Final[frozenset[str]] = frozenset("abcdefghijklmnopqrstuvwxyz0123456789-")
"""JDEC-005's identifier alphabet; anything else is refused, never sanitised."""


class InvalidArtifactNameError(ValueError):
    """The identifiers cannot name an official artifact. Local, never a peer fault."""


@dataclass(frozen=True, slots=True)
class StoredArtifact:
    """Where an official artifact was written, and the digest of what was written."""

    path: str
    digest: Sha256Digest


class ArtifactStorePort(Protocol):
    """Durable storage for one official artifact, named by its official filename.

    The port is deliberately narrow: a name and a document in, a path and a
    digest out. It does not know which artifact family it is holding, and it
    never decides whether the document is truthful - that is decided by whoever
    owns the values, before the write is attempted.
    """

    def store(self, name: str, document: ArtifactDocument) -> StoredArtifact:
        """Persist *document* under the official *name* and describe the result."""
        ...


def require_game_id(game_id: str) -> str:
    """Return *game_id* once it is a filesystem-safe identifier, or refuse it."""
    if type(game_id) is not str:
        raise InvalidArtifactNameError(
            f"game_id must be a str, got {type(game_id).__name__}",
        )
    if not game_id:
        raise InvalidArtifactNameError("game_id must not be empty")
    if not _SAFE.issuperset(game_id):
        raise InvalidArtifactNameError(
            "game_id must be lowercase [a-z0-9-]; separators, dots and uppercase"
            " are refused rather than rewritten",
        )
    return game_id


def sub_game_token(sub_game: int) -> str:
    """Return the frozen two-digit `g<NN>` token for a real sub-game."""
    if type(sub_game) is not int:
        raise InvalidArtifactNameError(
            f"sub_game must be an int, got {type(sub_game).__name__}",
        )
    if not FIRST_SUB_GAME <= sub_game <= FIXED_NUM_GAMES:
        raise InvalidArtifactNameError(
            f"sub_game must be in [{FIRST_SUB_GAME}, {FIXED_NUM_GAMES}], got {sub_game}",
        )
    return f"g{sub_game:02d}"


def declaration_name(game_id: str) -> str:
    """`declaration_<game_id>.json` - one per series."""
    return f"declaration_{require_game_id(game_id)}.json"


def config_name(game_id: str, sub_game: int) -> str:
    """`config_<game_id>_g<NN>.json` - the config a sub-game actually locked."""
    return f"config_{require_game_id(game_id)}_{sub_game_token(sub_game)}.json"


def log_name(game_id: str, sub_game: int) -> str:
    """`log_<game_id>_g<NN>.json` - the finalized record of one sub-game."""
    return f"log_{require_game_id(game_id)}_{sub_game_token(sub_game)}.json"


def result_name(game_id: str) -> str:
    """`result_<game_id>.json` - written once, after the series is agreed."""
    return f"result_{require_game_id(game_id)}.json"
