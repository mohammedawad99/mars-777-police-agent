"""The frozen shared game contract for one counted pairing, and its digests.

Both peers hold a **byte-identical** copy of this document, and the pre-game
exchange refuses to play on any mismatch - so the bytes, not a parsed view of
them, are the authority. The raw digest is therefore taken over the file exactly
as received: reformatting it, reordering its keys or tidying its wording would
break the agreement even though no value changed.

The canonical digest is a second, independent statement over the same content
under the section-2 compact form, so the two peers can compare an agreement that
survived transport reformatting. They live in different domains and neither is
derived from the other: this document's hashes are **not** the terms signature,
**not** ``config_sha256``, **not** the scent registration digest and **not** the
Step-0 HMAC.
"""

import hashlib
import json
import os
from pathlib import Path
from typing import Final

SHIPPED_PATH: Final[Path] = Path(__file__).resolve().parents[3] / "config" / "game.MaRs-777.json"
"""The shipped copy, beside the rate limits it sits alongside."""

CONTRACT_OVERRIDE: Final[str] = "MARS777_GAME_CONTRACT"
"""Names a different contract file, for a synthetic pairing only.

A real counted pairing plays the shipped agreement, and `is_frozen()` is how a
counted entrypoint proves that is what it actually loaded: the override changes
the digests, so a substituted contract is **detectable**, never silent. The seam
exists because a synthetic two-process series runs two real CLI processes under
group ids the shipped agreement does not name, and inventing roles for them was
the alternative - which is exactly what this module refuses to do.
"""


def contract_path() -> Path:
    """The contract this process loads: the shipped one unless overridden."""
    return Path(os.environ[CONTRACT_OVERRIDE]) if CONTRACT_OVERRIDE in os.environ else SHIPPED_PATH


RAW_SHA256: Final[str] = "2b401af481725fcf50e9143d44c50ab712b976e688b54cecd061b4546a60fbef"
"""The agreed digest of the file exactly as the pairing froze it."""

CANONICAL_SHA256: Final[str] = "290b4bcefc3824868d47070eade2564b0ecdb0b78560e163db348000b4caa1fb"
"""The agreed digest of the same content under the compact canonical form."""


def contract_bytes(path: Path | None = None) -> bytes:
    """Return the contract exactly as stored, with no normalisation at all."""
    return (contract_path() if path is None else path).read_bytes()


def raw_digest(path: Path | None = None) -> str:
    """Digest the stored bytes - the form the pairing actually agreed."""
    return hashlib.sha256(contract_bytes(path)).hexdigest()


def canonical_digest(path: Path | None = None) -> str:
    """Digest the same content re-serialised to the compact canonical form."""
    document = json.loads(contract_bytes(path))
    canonical = json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def first_role_of(group_id: str) -> str:
    """The side *group_id* takes in sub-game 1, as the pairing agreed it.

    A series-level fact, not a per-process one: both of this group's role
    backends must schedule from the same first role, so it is read from the
    shared contract rather than from whichever repository is asking.
    """
    document = json.loads(contract_bytes())
    roles = document["series_protocol"]["sub_game_1_roles"]
    role = roles.get(group_id)
    if role not in ("police", "thief"):
        raise KeyError(f"the shared contract declares no sub-game-1 role for {group_id!r}")
    return str(role)


def is_frozen(path: Path | None = None) -> bool:
    """Whether the loaded contract is byte-identical to the frozen agreement.

    A counted run must be able to say yes. A synthetic one legitimately says no,
    and saying so out loud is what keeps the override from being an escape hatch.
    """
    return raw_digest(path) == RAW_SHA256 and canonical_digest(path) == CANONICAL_SHA256
