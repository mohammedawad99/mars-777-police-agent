"""The constrained wire spellings of the project's scalar semantic values.

Every type here is a `str` with an exact pattern, so the refusal happens in the
published JSON Schema and in Pydantic's strict mode rather than deep inside a
semantic constructor. A wire value that does not match never reaches the
application runtime at all.

**Decimal is the one that matters.** Measured against the installed FastMCP,
a `Decimal`-annotated parameter handed the JSON *number* `0.10` arrives as
`Decimal('0.1')` - a silent lexical loss that changes `config_sha256` and would
make two honest peers refuse each other for a reason neither could see. Semantic
decimals therefore cross as **canonical text** and are rebuilt with
`Decimal(text)` directly: no float is ever constructed on the path.
"""

from decimal import Decimal
from typing import Annotated

from pydantic import StringConstraints

CANONICAL_DECIMAL = r"^-?(0|[1-9][0-9]*)(\.[0-9]+)?$"
"""Plain positional decimal text - no exponent, no `+`, no leading zeros."""

DecimalText = Annotated[str, StringConstraints(pattern=CANONICAL_DECIMAL)]
"""A semantic `Decimal` on the wire. Never a JSON number."""

DigestText = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
"""A `Sha256Digest`: exactly 64 lowercase hex characters."""

NonceText = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{32}$")]
"""A `NonceValue` in the current-v1 representation."""

CommitText = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{40}$")]
"""A `GitCommitSha`: exactly 40 lowercase hex characters."""

TimestampText = Annotated[str, StringConstraints(pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")]
"""A `UtcTimestamp` in the one frozen lexical form."""

KeyIdText = Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9._-]{1,64}$")]
"""A `KeyId`: the non-secret label, never key material."""

NonEmptyText = Annotated[str, StringConstraints(min_length=1)]
"""Identity strings that carry no further frozen grammar."""

ProofText = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]+$")]
"""An `AuthProof` value; its exact width is checked by the semantic type."""


def decimal_from_text(text: str) -> Decimal:
    """Rebuild a semantic `Decimal` from its canonical wire text.

    Direct construction from the string. There is deliberately no `float` in
    this function, and no rounding, quantizing or normalising: `Decimal("0.10")`
    and `Decimal("0.1")` are the same *number* and different *canonical text*,
    and only the text - hence the digest - distinguishes them.
    """
    return Decimal(text)


def text_from_decimal(value: Decimal) -> str:
    """Render a semantic `Decimal` as canonical wire text.

    Uses fixed-point formatting so an exponent form can never reach the wire,
    and preserves trailing zeros because they are part of the canonical text.
    """
    return format(value, "f")
