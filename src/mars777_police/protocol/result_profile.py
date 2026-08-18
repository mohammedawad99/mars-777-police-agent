"""Which bytes a result agreement is hashed over, decided once per profile.

Two semantically identical results hash differently under the two encodings,
and that is the interoperability failure this owns. Our strict profile hashes
the compact project canonical form. The pinned kit hashes its report with
`json.dumps`' **spaced** defaults - the one construction in that release which
is not compact - and a verifier reaching for the wrong one computes a mismatch
over a result both sides agree on. The disagreement then reads as being about
the game rather than about a serializer, which is the hardest kind of bug to
find from the other side of a tunnel.

Sender and verifier reach this same function, and the profile is frozen for the
series: no per-message choice, no fallback, and an unhandled profile refuses
rather than guessing an encoding on someone's behalf.
"""

import hashlib

from ..app.interop_profiles import ResultProfile
from .canonical import canonical_json_bytes
from .kit_consensus import kit_consensus_digest


def consensus_digest_for(profile: ResultProfile, report: object) -> str:
    """The agreement digest over *report* under *profile*."""
    if profile is ResultProfile.KIT_CORE_RESULT_V1:
        return kit_consensus_digest(report)
    if profile is ResultProfile.STRICT_PROJECT_RESULT:
        return hashlib.sha256(canonical_json_bytes(report)).hexdigest()
    raise ValueError(f"{profile.value} has no consensus encoding in this build")
