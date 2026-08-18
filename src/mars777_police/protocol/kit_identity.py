"""The match identity two peers reach separately and still agree on.

Both ids are pure functions of shared inputs, so neither peer has to be told
which order to use and a pairing has no convention left to settle. The kit
records what happens otherwise: in a live 2026-07-25 cross-team series *both*
join keys diverged at once - the `game_id` because each side named itself
first, and the `game_uid` because one side hashed a wider object than the flat
terms - leaving two reports that agreed on every value and could be joined by
neither key.

**`terms_digest` is agreement, not authentication.** It is unkeyed: anyone
holding the terms and the nonce recomputes it, so it proves both sides are
looking at the same fourteen values and nothing about who is speaking. Our
`AuthProfile.HMAC_SHA256` Step-0 proof remains separately mandatory, and a
matching digest here may never stand in for it.

The separator is a single U+007C, the same one the commitment uses and for the
same reason.
"""

import hashlib
import uuid

from .kit_canonical import kit_canonical_text
from .kit_commitment import SEPARATOR


def _pair(group_a: str, group_b: str) -> tuple[str, ...]:
    """The two group ids in the one order both peers can derive: sorted."""
    for name in (group_a, group_b):
        if type(name) is not str or not name:
            raise ValueError("a KIT match needs two non-empty group ids")
    return tuple(sorted((group_a, group_b)))


def kit_game_id(group_a: str, group_b: str) -> str:
    """`"-vs-".join(sorted(pair))` - the name the four artifact families carry."""
    return "-vs-".join(_pair(group_a, group_b))


def kit_game_uid(terms: object, group_a: str, group_b: str) -> str:
    """`UUID(SHA256(canonical(terms)|sorted-pair)[:16])`, order-independent."""
    seed = f"{kit_canonical_text(terms)}{SEPARATOR}{SEPARATOR.join(_pair(group_a, group_b))}"
    return str(uuid.UUID(bytes=hashlib.sha256(seed.encode("utf-8")).digest()[:16]))


def kit_terms_digest(terms: object, nonce: str) -> str:
    """The unkeyed content-agreement digest over the terms - **not** authentication."""
    if type(nonce) is not str or not nonce:
        raise ValueError("a KIT terms digest needs a non-empty nonce text")
    return hashlib.sha256(f"{kit_canonical_text(terms)}{SEPARATOR}{nonce}".encode()).hexdigest()
