"""The port that produces a fresh commitment nonce, and nothing else.

**Why this is a port and not a helper.** `NonceValue` is deliberately
representation-only: its own contract says the type *"proves how a string is
written, never how it was produced"*, leaving freshness, entropy and CSPRNG
provenance to the producer (**CRYPTO-010**, D34). Until now that producer did
not exist, which is exactly why Stage 5-R4 could not build an outbound
commitment. This is the seam it was missing.

Generation is a **security capability**, so it is injected rather than imported:
`app` never reaches for `secrets`, a test can supply a known sequence without
monkeypatching a module, and there is exactly one place in the system that
decides what "fresh" means. `API_BOUNDARIES.md` carries the registered row; the
port count moves 20 → 21 by explicit authorization, not by accident.

The return is a `NonceValue`, never `str` or `bytes`: a caller that received raw
material could pass it somewhere a validated value was required, and the whole
point of the semantic type is that it cannot be skipped.
"""

from typing import Protocol

from .protocol_values import NonceValue


class NonceSourcePort(Protocol):
    """A source of fresh, unpredictable commitment nonces."""

    def fresh(self) -> NonceValue:
        """Return a new nonce that has never been returned before.

        The obligation is the implementation's: uniqueness and unpredictability
        cannot be checked by inspecting the value that comes back, so a consumer
        that needs to be sure it never reuses one keeps its own record.
        """
        ...
