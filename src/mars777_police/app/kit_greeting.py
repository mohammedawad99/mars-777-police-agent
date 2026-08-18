"""The pinned pre-game greeting, and the pairing two peers can reach separately.

The greeting is the kit's `negotiate` message: the flat signed `terms`, the
nonce that signed them, the signature, and the sender's group id - with the
pairing and locked-model declarations riding *beside* the terms rather than
inside them, because adding a key to `terms` breaks the signature.

**Omission never refuses**, in either direction (pinned SPEC sections 7-7.3).
The unmodified reference peer declares none of the optional members, and a guard
that fail-fasts on silence forfeits the game to itself.

**The signature here is not authentication.** `kit_terms_digest` is unkeyed:
anyone holding the terms and the nonce recomputes it, so a match proves both
sides are reading the same values and nothing at all about who is speaking. Our
`AuthProfile.HMAC_SHA256` Step-0 proof stays separately mandatory, and this
pairing view deliberately carries no authority to satisfy it.
"""

from dataclasses import dataclass, field

from .kit_messages import KitRole
from .kit_payload import PeerPayload


@dataclass(frozen=True, slots=True)
class KitGreeting:
    """One `negotiate` message, required members first and silence for the rest."""

    terms: PeerPayload
    nonce: str
    signature: str
    group_id: str
    role: KitRole | None = None
    sub_game_number: int | None = None
    identity: PeerPayload | None = None
    game_uid: str | None = None
    locks: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    """The declared model hashes, as `(family, digest)` - declared ones only."""

    def lock(self, family: str) -> str | None:
        """The digest the peer declared for *family*, or `None` for silence."""
        for name, digest in self.locks:
            if name == family:
                return digest
        return None


@dataclass(frozen=True, slots=True)
class KitPairing:
    """What one accepted greeting establishes, and what it deliberately does not.

    `authenticated` is a member rather than an assumption. It is `False` for
    every greeting this wire can carry, because the pinned message has no place
    for a keyed proof and the pinned receiver drops unknown keys - so a peer
    could not send us one and could not read ours. Recording that as a value
    keeps the gap visible to every caller instead of leaving it to a comment.
    """

    game_id: str
    game_uid: str
    our_group: str
    peer_group: str
    our_role: KitRole
    peer_role: KitRole | None
    sub_game_number: int
    terms_agreed: bool
    authenticated: bool = False
