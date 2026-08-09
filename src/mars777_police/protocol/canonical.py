"""Canonical text and canonical JSON bytes for hashed payloads.

The frozen current-v1 parameters (JDEC-002, NDEC-003, PRD06-FR-002/003/004/005):
sorted keys, `(",",":")` separators, `ensure_ascii=False`, UTF-8, NFC-normalised
text, LF, and no trailing newline inside a hashed payload. Both peers must
produce byte-identical output or a correct match reports a false TAMPERED, so
every one of these is fixed here rather than chosen at call time.

This module owns **bytes, not meaning**. It never sees a `SealedState`, a
`PhysicalAction` or a digest - only JSON-native material a caller already mapped
explicitly. Its runtime domain is therefore deliberately narrow: `str`, `int`,
`list`, `dict`. A sealed commitment record contains no `float`, `null` or `bool`,
so this first canonical implementation refuses them rather than guessing at rules
the wider contract only freezes for other artifacts; extending the domain is a
later decision, made when a payload actually needs it.

Strings must already be NFC when they arrive. A caller that skipped
`canonical_text` on free text has a defect worth surfacing, and repairing it
silently one step before hashing would hide exactly the divergence this module
exists to prevent.
"""

import json
import unicodedata

_ALLOWED = (str, int, list, dict)


def canonical_text(value: str) -> str:
    """Return *value* in Unicode NFC. Normalisation only - never trim or fold."""
    if type(value) is not str:
        raise ValueError(f"canonical text must be a str, got {type(value).__name__}")
    return unicodedata.normalize("NFC", value)


def _require_canonical(value: object) -> None:
    """Refuse anything outside the sealed-record JSON domain, recursively."""
    if type(value) is str:
        if value != unicodedata.normalize("NFC", value):
            raise ValueError(
                "canonical strings must already be NFC-normalised;"
                " call canonical_text before serializing"
            )
        return
    if type(value) is int:
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
        f"canonical JSON accepts only {', '.join(t.__name__ for t in _ALLOWED)}"
        f" in a sealed record, got {type(value).__name__}"
    )


def canonical_json_bytes(value: object) -> bytes:
    """Serialize already-canonical JSON-native material to the frozen bytes."""
    _require_canonical(value)
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
