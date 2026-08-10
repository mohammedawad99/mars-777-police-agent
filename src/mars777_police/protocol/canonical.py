"""Canonical text and canonical JSON bytes for hashed payloads.

The frozen current-v1 parameters (JDEC-002, NDEC-003, PRD06-FR-002/003/004/005):
sorted keys, `(",",":")` separators, `ensure_ascii=False`, UTF-8, NFC-normalised
text, LF, and no trailing newline inside a hashed payload. Both peers must
produce byte-identical output or a correct match reports a false TAMPERED, so
every one of these is fixed here rather than chosen at call time.

This module owns **bytes, not meaning**. It never sees a `SealedState`, a
`PhysicalAction` or a digest - only JSON-native material a caller already mapped
explicitly.

The runtime domain is `str`, `int`, `bool`, `Decimal`, `list` and `dict`.
`bool` and `Decimal` were **added at Stage 4E-R16**, when a payload first needed
them: the Step-0 core carries `hardware.gpu`, whose frozen type is
`string | False`, and the config core carries the two FIXED pheromone values.
The v1 module refused them because a sealed commitment record contains neither
and it declined to guess at rules the wider contract had only frozen elsewhere -
`CANONICALIZATION_CONTRACT.md` fixes booleans as JSON `true`/`false` and decimal
values as their **verbatim Appendix-F text** (`0.9`, `0.10`), with exponent form
and `-0` forbidden. `float` stays refused, and that is the whole point: `0.10`
has no `float` spelling, so binary rounding could silently perturb the bytes.
`None` also stays refused - a hashed payload omits an absent member rather than
emitting `null` (`PRD06-FR-008`).

Strings must already be NFC when they arrive. A caller that skipped
`canonical_text` on free text has a defect worth surfacing, and repairing it
silently one step before hashing would hide exactly the divergence this module
exists to prevent.
"""

import json
import re
import unicodedata
from decimal import Decimal
from typing import Final

_ALLOWED = (str, int, bool, Decimal, list, dict)

_DECIMAL_TEXT: Final[re.Pattern[str]] = re.compile(r"^-?(0|[1-9][0-9]*)(\.[0-9]+)?$")
"""Plain positional decimal text only - no exponent, no `+`, no leading zeros."""

_SENTINEL: Final[str] = "\ue000"
"""A private-use character marking decimal placeholders during substitution.

The placeholder round-trip is how a `Decimal` reaches the output as a JSON
*number*: `json.dumps` has no verbatim-decimal hook, and every alternative - a
`float` subclass, a custom encoder, a hand-rolled serializer - either loses the
exact `0.10` text or forks the one canonical policy.

Safety comes from the **substitution asserting a unique match**, not from hoping
the mark is rare. A payload whose own data happens to spell a generated token is
refused outright rather than silently mis-substituted, which is the fail-closed
behaviour every other byte-level rule here follows.
"""


def canonical_text(value: str) -> str:
    """Return *value* in Unicode NFC. Normalisation only - never trim or fold."""
    if type(value) is not str:
        raise ValueError(f"canonical text must be a str, got {type(value).__name__}")
    return unicodedata.normalize("NFC", value)


def decimal_text(value: Decimal) -> str:
    """Return the verbatim canonical text of *value*, refusing ambiguous forms."""
    text = format(value, "f") if value.is_finite() else str(value)
    if not _DECIMAL_TEXT.match(text):
        raise ValueError(f"canonical decimals must be plain positional text, got {text!r}")
    if text.startswith("-") and Decimal(text) == 0:
        raise ValueError("canonical decimals must not be negative zero")
    return text


def _require_canonical(value: object) -> None:
    """Refuse anything outside the canonical JSON domain, recursively."""
    if type(value) is str:
        if value != unicodedata.normalize("NFC", value):
            raise ValueError(
                "canonical strings must already be NFC-normalised;"
                " call canonical_text before serializing"
            )
        return
    if type(value) is int or type(value) is bool:
        return
    if type(value) is Decimal:
        decimal_text(value)
        return
    if type(value) is list:
        for item in value:
            _require_canonical(item)
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"canonical object keys must be str, got {type(key).__name__}")
            _require_canonical(key)
            _require_canonical(item)
        return
    raise ValueError(
        f"canonical JSON accepts only {', '.join(t.__name__ for t in _ALLOWED)},"
        f" got {type(value).__name__}"
    )


def _substitute(value: object, decimals: list[tuple[str, str]]) -> object:
    """Replace every `Decimal` with a unique placeholder string, recursively."""
    if type(value) is Decimal:
        token = f"{_SENTINEL}d{len(decimals)}{_SENTINEL}"
        decimals.append((token, decimal_text(value)))
        return token
    if type(value) is list:
        return [_substitute(item, decimals) for item in value]
    if type(value) is dict:
        return {key: _substitute(item, decimals) for key, item in value.items()}
    return value


def canonical_json_bytes(value: object) -> bytes:
    """Serialize already-canonical JSON-native material to the frozen bytes."""
    _require_canonical(value)
    decimals: list[tuple[str, str]] = []
    text = json.dumps(
        _substitute(value, decimals),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    for token, literal in decimals:
        quoted = f'"{token}"'
        if text.count(quoted) != 1:
            raise ValueError("canonical decimal placeholder was not uniquely substitutable")
        text = text.replace(quoted, literal)
    return text.encode("utf-8")
