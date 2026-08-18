"""The KIT commitment: the nonce sits beside the payload, never inside it.

    SHA256( utf8( kit_canonical(payload) + "|" + nonce ) )

with a **single** U+007C. The pinned kit spells that out because the formula
loses the argument against a reader's habits: a bare concatenation and a
doubled pipe are both plausible readings, and the wrong one is invisible to
self-testing - sign and verify with the same mistake and every local test
passes while every real handshake fails on "signature mismatch".

**This is a profile, not a replacement.** Our strict project construction
seals the nonce as one of eight members inside the canonical record, and that
remains exactly what `STRICT_PROJECT_COMMITMENT` produces. Which construction
is in force is a series-wide frozen decision, not a per-message guess: there is
no try-both verification here and no fallback, because a verifier that accepts
whichever digest matches accepts a peer that changed its mind mid-series.

The payload is taken as given. Nothing is stripped, relocated or normalised -
a payload that carries its own `nonce` member is hashed with that member in
place *and* the nonce appended, because rewriting a peer's record before
hashing it would compute a digest over bytes the peer never sealed.
"""

import hashlib

from .kit_canonical import kit_canonical_text

SEPARATOR = "|"
"""U+007C, exactly once, between the canonical payload and the nonce."""


def kit_commitment(payload: object, nonce: str) -> str:
    """The hex digest a KIT peer computes for *payload* sealed under *nonce*."""
    if type(nonce) is not str or not nonce:
        raise ValueError("a KIT commitment needs a non-empty nonce text")
    preimage = f"{kit_canonical_text(payload)}{SEPARATOR}{nonce}"
    return hashlib.sha256(preimage.encode("utf-8")).hexdigest()
