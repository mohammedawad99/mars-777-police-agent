"""The one canonical text spelling of a semantic `Decimal`.

Two layers need this rule and neither may import the other. `transport` needs it
because a `Decimal` that crosses as a JSON *number* comes back lexically damaged
- the measured FastMCP behaviour is `0.10` arriving as `Decimal('0.1')`, which
changes `config_sha256` and would make two honest peers refuse each other for a
reason neither could see. The application needs it because the audit-disclosure
document is read **in `app`**, by helpers that may never reach into `transport`.

So the rule lives here, at the layer both may legally consume, and `transport`
keeps only its framework adapter. This is a relocation, not a decision: the
pattern, the parse and the render are exactly what `wire_scalars` already froze.

**Nothing is normalized.** `Decimal("0.10")` and `Decimal("0.1")` are the same
number and different canonical text, and only the text - hence the digest -
distinguishes them, so parsing constructs straight from the string and rendering
is fixed-point so no exponent form can ever appear. No `float` is constructed on
either path.
"""

from decimal import Decimal

CANONICAL_DECIMAL = r"^-?(0|[1-9][0-9]*)(\.[0-9]+)?$"
"""Plain positional decimal text - no exponent, no `+`, no leading zeros."""


def decimal_from_text(text: str) -> Decimal:
    """Rebuild a semantic `Decimal` from its canonical text.

    Direct construction from the string: no rounding, quantizing or normalising,
    because the trailing zeros are part of the value's identity.
    """
    return Decimal(text)


def text_from_decimal(value: Decimal) -> str:
    """Render a semantic `Decimal` as its canonical text.

    Fixed-point formatting, so an exponent form can never reach a wire or an
    artifact, and trailing zeros survive because they are part of the spelling.
    """
    return format(value, "f")
