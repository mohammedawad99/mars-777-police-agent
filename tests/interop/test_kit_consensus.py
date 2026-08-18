"""The settlement consensus digest - the kit's deliberate *second* canonical form.

Everything else in the release hashes compact bytes; the report is hashed with
`json.dumps`' default **spaced** separators. That is not an inconsistency to
paper over: a verifier that reuses the compact form here computes a different
digest over a report both sides agree on, and the mismatch reads as a
disagreement about the result rather than about the serializer.

Sign-then-insert: the signature is computed **before** its own key exists in
the object, so verification pops the key, re-serializes spaced and re-hashes.
"""

import pytest
from kit_vectors import CONSENSUS

from mars777_police.protocol.kit_consensus import kit_consensus_digest, kit_consensus_text


@pytest.mark.parametrize(("report", "expected"), CONSENSUS)
def test_the_pinned_consensus_digests_reproduce_exactly(
    report: dict[str, object], expected: str
) -> None:
    assert kit_consensus_digest(report) == expected


def test_the_form_is_spaced_not_compact() -> None:
    """The one place the release does not use compact separators."""
    text = kit_consensus_text({"b": 1, "a": 2})

    assert text == '{"a": 2, "b": 1}'
    assert ',"' not in text


def test_non_ascii_stays_native() -> None:
    """`ensure_ascii=False` here too - the reports are written in Hebrew."""
    assert kit_consensus_text({"קבוצה": "team-aleph"}) == '{"קבוצה": "team-aleph"}'


def test_the_compact_authority_is_not_used_for_reports() -> None:
    """Proved by difference, so a future refactor cannot quietly unify them."""
    from mars777_police.protocol.kit_canonical import kit_canonical_text

    report = CONSENSUS[0][0]

    assert kit_consensus_text(report) != kit_canonical_text(report)
