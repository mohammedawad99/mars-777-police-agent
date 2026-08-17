"""One classification per turn, even when a peer spells it twice.

C-08 settled that the book's English code comment `verdict` and its Hebrew prose
`intent classification` name the **same** commit-time value, and that the sealed
payload carries `intent` alone. The reference implementation nonetheless writes
both keys with the same value, so a disclosure may legally arrive carrying the
pair - and PRD04-FR-018 requires that when it does, they must agree.

**This is parser consistency, not a new game rule.** A contradiction is a
malformed document on the existing refusal path: it creates no tampering
verdict, no technical loss and no sanction. `RevealWire`, `H_commit` and the
compatibility profile are untouched, and a document without `verdict` behaves
exactly as it always has - the key is still not an input to anything.
"""

import pytest
from audit_builders import audited, capture_json, document, entry

from mars777_police.app.protocol_errors import MalformedMessageError
from mars777_police.app.protocol_values import FinalAuditVerdict
from mars777_police.app.sealed_record_values import Intent


def _disclosure(*rows: dict[str, object]) -> dict[str, object]:
    """The well-formed document with its entries replaced, transcript intact."""
    return document(entries=list(rows), capture=capture_json())


def test_a_disclosure_without_a_verdict_key_is_unaffected() -> None:
    """The historical shape: `intent` alone, still the only classification read."""
    live = audited()

    assert live.verdict is FinalAuditVerdict.VERIFIED_OK


def test_a_matching_verdict_is_accepted_and_maps_to_the_one_intent() -> None:
    """Both keys, same value - the reference implementation's own shape."""
    rows = [entry(step) | {"verdict": Intent.TRUTH.value} for step in (1, 2)]

    live = audited(_disclosure(*rows))

    assert live.verdict is FinalAuditVerdict.VERIFIED_OK


def test_a_contradictory_verdict_is_refused_as_malformed() -> None:
    """No dual truth: the two keys cannot name two different classifications."""
    rows = [entry(1) | {"verdict": Intent.LIE.value}, entry(2)]

    with pytest.raises(MalformedMessageError):
        audited(_disclosure(*rows))


def test_a_verdict_of_an_unknown_word_is_refused() -> None:
    """An unrecognised classification is not silently ignored once it is read."""
    rows = [entry(1) | {"verdict": "maybe"}, entry(2)]

    with pytest.raises(MalformedMessageError):
        audited(_disclosure(*rows))


def test_a_verdict_that_is_not_a_string_is_refused() -> None:
    rows = [entry(1) | {"verdict": 1}, entry(2)]

    with pytest.raises(MalformedMessageError):
        audited(_disclosure(*rows))


def test_an_agreeing_pair_leaves_the_existing_verdict_to_decide() -> None:
    """The new check rules on consistency alone, and hands the rest back.

    Both keys say `lie` and agree, so nothing here refuses the document. What
    the peer disclosed still has to match what it committed, and it does not -
    the sealed record carried `truth` - so the **existing** correspondence check
    reports `TAMPERED`. That separation is the point: a contradiction between
    two keys is malformed input, while a disclosure that contradicts a digest is
    a verdict, and Stage 7B moved neither boundary.
    """
    rows = [
        entry(step) | {"intent": Intent.LIE.value, "verdict": Intent.LIE.value} for step in (1, 2)
    ]

    live = audited(_disclosure(*rows))

    assert live.verdict is FinalAuditVerdict.TAMPERED
    assert not live.verified


def test_other_peer_annotations_are_still_ignored() -> None:
    """Only `verdict` gained a consistency rule; the rest stay non-inputs."""
    rows = [entry(step) | {"verified": True, "note": "hello"} for step in (1, 2)]

    live = audited(_disclosure(*rows))

    assert live.verdict is FinalAuditVerdict.VERIFIED_OK
