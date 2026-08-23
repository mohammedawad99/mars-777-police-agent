"""The other way a sub-game's configuration can be proven agreed.

Our counted single-process path proves it with a keyed lock: `ConfigLockEvidence`
carries an `AuthProof` over the lock context. That is stricter than the course
requires, and it is not the only lawful provenance.

**What the book actually mandates.** `config/game.json` is JSON precisely so it
is canonically serializable and therefore consistently hashable as
`config_sha256` - byte-for-byte identical across teams who may have written
their agents in different languages. Nothing in the book requires an additional
keyed per-sub-game exchange; the one mandatory signed artifact is the report.
Requiring a lock our opponent's runner never performs would have meant changing
a wire both implementations had already proven, to satisfy a rule that does not
exist.

**So this is the second provenance**, the one the reference wire already
carries: the flat agreed terms, the fresh nonce that bound them for this
sub-game, and `SHA256(canonical(terms)|nonce)` over the two. It sits beside
`ConfigLockEvidence` rather than replacing it - a series that *did* lock with a
key keeps the stronger record.

**It is agreement, not authentication, and it never pretends otherwise.** The
digest is unkeyed: anyone holding the terms and the nonce reproduces it, so it
proves both sides read the same values and nothing about who spoke. Identity for
the series is established once, by the authenticated Step-0, which remains
separately mandatory and which this may never stand in for.

Representation and self-consistency only. Nothing here hashes the terms or
compares against a peer - `artifact_verification` holds these values to each
other, exactly as it does for the keyed form.
"""

from dataclasses import dataclass

from ..protocol.kit_identity import kit_terms_digest
from .peer_pregame_messages import ConfigLockContext
from .protocol_errors import LocalDefectError

DIGEST_TEXT = 64
"""A SHA-256 rendered as lowercase hex, the only form that crosses the wire."""


@dataclass(frozen=True, slots=True)
class TermsAgreementEvidence:
    """One sub-game's configuration, agreed by nonce-bound terms rather than a key."""

    context: ConfigLockContext
    nonce: str
    terms_signature: str
    """`SHA256(canonical(terms)|nonce)`, as the greeting carried it."""

    def __post_init__(self) -> None:
        if type(self.nonce) is not str or not self.nonce:
            raise LocalDefectError("a terms agreement needs the non-empty nonce that bound it")
        if type(self.terms_signature) is not str:
            raise LocalDefectError("a terms signature is text")
        signature = self.terms_signature
        if len(signature) != DIGEST_TEXT or signature.lower() != signature:
            raise LocalDefectError(
                "a terms signature is 64 lowercase hex characters;"
                f" got {len(signature)} character(s)",
            )
        try:
            int(signature, 16)
        except ValueError:
            raise LocalDefectError("a terms signature is hexadecimal") from None

    def reproduces(self, terms: object) -> bool:
        """Whether *terms* under this nonce really do produce the stored signature.

        The check the artifact exists to make possible: a stored signature that
        the stored terms cannot reproduce is a record of nothing.
        """
        return kit_terms_digest(terms, self.nonce) == self.terms_signature
