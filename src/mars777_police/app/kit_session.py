"""What one KIT-mode process knows out of band, and what it refuses on the record.

A kit turn numbers only its own chain and a kit greeting names only the sender,
so the sub-game, our role and our terms have to come from somewhere the wire
cannot reach: the operator's pre-boot selection. That is this context. It is the
same discipline the external audit already uses - role from the authenticated
direction, cursor from the turn we witnessed, configuration from the verified
lock - and never a fact read back out of the message being judged.

**Refusals are the pinned ones, in our own error identities.** Terms that do not
value-equal ours are a constitution disagreement (`E-CONFIG-MISMATCH`); a
signature that does not verify over matching terms is a serialization fault, the
same identity; a role collision or a sub-game mismatch belongs to a different
game (`E-PROTO-STALE`); a declared `game_uid` that differs from the one we derive
means their derive step read a wider input than the flat terms
(`E-CONFIG-MISMATCH`).

**Nothing here authenticates anything.** Accepting a greeting binds no session
identity, because the pinned message carries no keyed proof to bind one from.
"""

from dataclasses import dataclass, field

from ..protocol.kit_identity import kit_game_id, kit_game_uid, kit_terms_digest
from .kit_greeting import KitGreeting, KitPairing
from .kit_messages import KitControlKind, KitRole
from .kit_payload import PeerPayload
from .protocol_errors import ConfigMismatchError, StaleMessageError
from .turn_cursor import TurnCursor


@dataclass(slots=True)
class KitSessionContext:
    """One process's out-of-band context for a KIT series."""

    our_group: str
    our_role: KitRole
    terms: PeerPayload
    sub_game_number: int
    peer_group: str | None = field(default=None)
    pairing: KitPairing | None = field(default=None)
    last_control: KitControlKind | None = field(default=None)
    """The last status signal received. It settles nothing and scores nothing."""

    friendly: object | None = field(default=None)
    """The development friendly session, present exactly when the run is one.

    Its presence is decided before boot and never by a message. When it is here
    the inbound KIT path delivers to it and the counted runtime is not merely
    gated but **unreached**; when it is absent every KIT operation meets the
    unchanged authentication gate."""

    def cursor(self, step: int) -> TurnCursor:
        """The cursor a turn belongs to: its own step, our sub-game."""
        return TurnCursor(self.sub_game_number, step)

    def our_greeting(self, nonce: str, sub_game: int) -> KitGreeting:
        """The greeting we open a sub-game with, signed over the agreed terms.

        The signature is the kit's **unkeyed content agreement**: anyone holding
        the terms and the nonce recomputes it, so it proves both sides read the
        same fourteen values and nothing about who is speaking. It is not, and
        never becomes, producer authentication.

        The uid is declared only once the opponent is known - it is a pure
        function of the terms and the two sorted group ids - and omission never
        refuses in either direction.
        """
        peer = self.peer_group
        return KitGreeting(
            self.terms,
            nonce,
            kit_terms_digest(self.terms.value, nonce),
            self.our_group,
            self.our_role,
            sub_game,
            None,
            kit_game_uid(self.terms.value, self.our_group, peer) if peer else None,
        )

    def accept(self, greeting: KitGreeting) -> KitPairing:
        """Check an inbound greeting against what we already hold, or refuse it."""
        self._require_terms(greeting)
        self._require_pairing(greeting)
        peer = greeting.group_id
        derived = kit_game_uid(self.terms.value, self.our_group, peer)
        if greeting.game_uid is not None and greeting.game_uid != derived:
            raise ConfigMismatchError(
                "the peer derived a different game_uid from terms that already value-equal ours,"
                " so its derive step read a wider input than the flat terms",
            )
        pairing = KitPairing(
            kit_game_id(self.our_group, peer),
            derived,
            self.our_group,
            peer,
            self.our_role,
            greeting.role,
            self.sub_game_number,
            terms_agreed=True,
        )
        self.peer_group, self.pairing = peer, pairing
        return pairing

    def _require_terms(self, greeting: KitGreeting) -> None:
        """Value equality first, then the signature over those exact bytes."""
        if greeting.terms.value != self.terms.value:
            raise ConfigMismatchError(
                "the peer's terms do not value-equal ours - a constitution disagreement,"
                " not a wire fault",
            )
        if kit_terms_digest(greeting.terms.value, greeting.nonce) != greeting.signature:
            raise ConfigMismatchError(
                "the terms signature does not verify although the terms matched, so the"
                " difference is in the serialization rather than in the values",
            )

    def _require_pairing(self, greeting: KitGreeting) -> None:
        """Same game, complementary sides. A bystander belongs to another game."""
        theirs = greeting.sub_game_number
        if theirs is not None and theirs != self.sub_game_number:
            raise StaleMessageError(
                f"we are playing sub-game {self.sub_game_number} and the peer declared"
                f" {theirs}; one game cannot carry two indices",
            )
        if greeting.role is not None and greeting.role is self.our_role:
            raise StaleMessageError(
                f"role collision: both peers declared {self.our_role.value!r}, and two of the"
                " same side can only deadlock",
            )
        if self.peer_group is not None and greeting.group_id != self.peer_group:
            raise StaleMessageError(
                f"a different group ({greeting.group_id!r}) answered a series opened with"
                f" {self.peer_group!r}; one series has one opponent",
            )
