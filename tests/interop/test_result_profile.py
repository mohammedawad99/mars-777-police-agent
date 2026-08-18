"""Which bytes a result agreement is hashed over, chosen once per profile.

Two encodings, and a semantically identical result hashes differently under
each - which is exactly the interoperability failure worth preventing. Our
strict profile hashes the compact project canonical form; the pinned kit hashes
its report with `json.dumps`' spaced defaults. A verifier that reached for the
wrong one would compute a mismatch over a result both sides agree on, and the
disagreement would read as being about the *game* rather than the serializer.

Sender and verifier reach the same authority, and the profile is frozen for the
series: there is no per-message choice and no fallback.
"""

import pytest
from kit_vectors import CONSENSUS

from mars777_police.app.interop_profiles import ResultProfile
from mars777_police.protocol.result_profile import consensus_digest_for


@pytest.mark.parametrize(("report", "expected"), CONSENSUS)
def test_the_kit_profile_reproduces_the_pinned_consensus(
    report: dict[str, object], expected: str
) -> None:
    assert consensus_digest_for(ResultProfile.KIT_CORE_RESULT_V1, report) == expected


def test_the_strict_profile_uses_the_compact_project_bytes() -> None:
    import hashlib

    from mars777_police.protocol.canonical import canonical_json_bytes

    report = {"a": 1, "b": "two"}
    expected = hashlib.sha256(canonical_json_bytes(report)).hexdigest()

    assert consensus_digest_for(ResultProfile.STRICT_PROJECT_RESULT, report) == expected


def test_the_two_profiles_disagree_on_the_same_report() -> None:
    """Proved by difference, so a refactor cannot quietly unify the encodings."""
    report = {"a": 1, "b": "two"}

    assert consensus_digest_for(ResultProfile.STRICT_PROJECT_RESULT, report) != (
        consensus_digest_for(ResultProfile.KIT_CORE_RESULT_V1, report)
    )


def test_an_unhandled_profile_refuses_rather_than_guessing() -> None:
    with pytest.raises(ValueError, match="no consensus encoding"):
        consensus_digest_for(ResultProfile.LECTURER_ATTACHMENT_COMPATIBILITY, {"a": 1})
