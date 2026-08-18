"""The canonical form an external KIT peer hashes, beside our strict one.

Two authorities exist deliberately. `protocol.canonical` serves the **strict
project domain**: it refuses `None` and binary `float`, carries decimals as
exact text, and is what every published project hash is computed over. This
module serves the **KIT external profile** - the JSON-native domain the pinned
kit actually uses - so a peer's bytes can be reproduced exactly as that peer
produced them.

**Why not one permissive function.** Widening the strict authority would let a
binary float reach a project hash, and the decimal-as-text design exists
precisely because `0.10` arriving as a float changes `config_sha256` and makes
two honest peers refuse each other for a reason neither can see. One authority
per profile keeps that impossible instead of merely unlikely.

**The form itself**, from the pinned kit (`ad65576`, SPEC §2):
`json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))`,
UTF-8. Keys sort by Unicode **code point**, so U+FF5E precedes U+1F642 - a
UTF-16 code-unit sort reverses them and produces different bytes for the same
object. Numbers are Python's shortest round-trip repr, exponent forms included.

Nothing here normalises Unicode. The kit hashes what the peer sent, and a
receiver that silently NFC-folded an incoming payload would compute a digest
over bytes its peer never produced.
"""

import json
from typing import Final

_JSON: Final = (str, int, float, bool, type(None), list, dict)
"""The JSON-native domain, and nothing beyond it - no dates, sets or objects."""


def require_json_value(value: object) -> None:
    """Refuse anything `json.dumps` would accept only by improvising."""
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"KIT canonical object keys must be str, got {type(key).__name__}")
            require_json_value(item)
        return
    if isinstance(value, list):
        for item in value:
            require_json_value(item)
        return
    if not isinstance(value, _JSON):
        raise ValueError(f"KIT canonical JSON accepts only JSON values, got {type(value).__name__}")


def kit_canonical_text(value: object) -> str:
    """Return *value* in the pinned KIT canonical form."""
    require_json_value(value)
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def kit_canonical_bytes(value: object) -> bytes:
    """The UTF-8 bytes a KIT peer hashes."""
    return kit_canonical_text(value).encode("utf-8")
