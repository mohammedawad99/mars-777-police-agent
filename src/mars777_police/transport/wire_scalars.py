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

from typing import Annotated

from pydantic import StringConstraints

from ..app.decimal_text import CANONICAL_DECIMAL, decimal_from_text, text_from_decimal

__all__ = [
    "CANONICAL_DECIMAL",
    "CommitText",
    "DecimalText",
    "DigestText",
    "KeyIdText",
    "NonEmptyText",
    "NonceText",
    "ProofText",
    "TimestampText",
    "decimal_from_text",
    "text_from_decimal",
]
"""The scalar spellings this adapter publishes, including the two it re-exports.

`decimal_from_text`/`text_from_decimal` and the pattern they belong to are
**not implemented here**: `app.decimal_text` owns the one canonical rule, and
this module re-exports it so every existing transport import keeps working while
the application layer consumes exactly the same authority."""

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
