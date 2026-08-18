"""The one place a commitment is computed, whichever construction is in force.

A sender and a verifier that each implemented the same formula would be two
chances to get it wrong and no way to notice: the pair agrees with itself while
disagreeing with everyone else, and every local test passes. So local sealing,
peer verification, audit recomputation and replay all arrive here, and the
codec that governs them is a series-wide frozen decision rather than a
per-message guess.

**No try-both, ever.** A verifier that hashed a payload under each construction
and accepted whichever matched would accept a peer that changed its mind
mid-series, and would silently convert an integrity failure into a profile
switch. There is one interpretation of a commitment, and a mismatch is a
mismatch.

Verification returns a verdict rather than raising: whether the bytes
correspond is a *cryptographic* question, and what a mismatch means for the
game belongs to the audit layer above. This module never interprets a payload.
"""

from ..app.commitment_codecs import CommitmentCodec
from .kit_commitment import kit_commitment


def commitment_for(codec: CommitmentCodec, payload: object, nonce: str) -> str:
    """The digest *codec* produces for *payload* sealed under *nonce*."""
    if codec is CommitmentCodec.KIT_CORE_COMMITMENT_V1:
        return kit_commitment(payload, nonce)
    raise ValueError(
        f"{codec.value} seals typed project members, not a raw payload;"
        " build its record through protocol.commitment instead"
    )


def verify_commitment(codec: CommitmentCodec, payload: object, nonce: str, expected: str) -> bool:
    """Whether *payload* under *nonce* really produces *expected* under *codec*."""
    return commitment_for(codec, payload, nonce) == expected
