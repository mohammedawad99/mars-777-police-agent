"""The settlement digest, and the one place the release does not hash compact bytes.

Every other construction in the pinned kit uses `separators=(",", ":")`. The
final report uses `json.dumps`' **defaults** - `(", ", ": ")` - and the
difference is load-bearing: a verifier that reuses the compact authority here
computes a different digest over a report both sides agree on, and the
mismatch reads as a disagreement about the *result* rather than about the
serializer. Keeping it in its own module is how that stays visible.

**Sign then insert.** The signature is computed before its own key exists in
the object, so a verifier pops the key, re-serializes spaced and re-hashes. A
signer that inserted first would sign a different object than any verifier can
reconstruct.

Sorting, `ensure_ascii=False` and UTF-8 are unchanged from the compact form -
the reports are written in Hebrew and must stay native.
"""

import hashlib
import json

from .kit_canonical import require_json_value


def kit_consensus_text(report: object) -> str:
    """The spaced canonical text of *report*, exactly as the kit hashes it."""
    require_json_value(report)
    return json.dumps(report, sort_keys=True, ensure_ascii=False)


def kit_consensus_digest(report: object) -> str:
    """The consensus signature over *report*, computed before its key is inserted."""
    return hashlib.sha256(kit_consensus_text(report).encode("utf-8")).hexdigest()
