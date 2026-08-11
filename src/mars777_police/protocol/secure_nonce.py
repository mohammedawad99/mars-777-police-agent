"""The production `NonceSourcePort`: 16 CSPRNG bytes, written as hex.

`secrets` is the only cryptographically secure source in the standard library,
and it lives here rather than in `app` for the same reason every other
primitive does - the application depends on the port, and the capability is
provided from the outer side.

The width is not a choice made here. `NONCE_HEX_LENGTH` freezes the current-v1
profile at 32 lowercase hex characters, `secrets.token_hex` emits exactly that
alphabet, and the byte count is derived from the frozen length rather than
restated - so the two can never drift apart. `secrets.token_hex(16)` is the
REFERENCE-EXAMPLE the source material names, and this is it.

No seed, no counter, no clock, no `random`, no UUID: each of those is
predictable to somebody, and a predictable nonce lets an opponent test guesses
against a commitment it has already received.
"""

import secrets
from dataclasses import dataclass

from ..app.protocol_values import NONCE_HEX_LENGTH, NonceValue

NONCE_BYTES = NONCE_HEX_LENGTH // 2
"""Bytes of entropy per nonce, derived from the frozen hex width - 16."""


@dataclass(frozen=True, slots=True)
class SecretsNonceSource:
    """The `NonceSourcePort` over the standard library's CSPRNG."""

    def fresh(self) -> NonceValue:
        """Return 16 fresh cryptographically secure bytes as a `NonceValue`.

        The result is handed to `NonceValue` rather than trusted: if the source
        ever produced something outside the frozen profile, this raises instead
        of letting a malformed nonce reach a sealed record.
        """
        return NonceValue(secrets.token_hex(NONCE_BYTES))
