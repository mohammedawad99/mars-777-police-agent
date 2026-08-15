"""What retaining the scent history deliberately did **not** change.

A new member on the disclosure document is the kind of change that quietly grows:
into the sealed record, into the log artifact, into a new semantic finding, into a
sanction. None of that happened here, and this file is where that is asserted
rather than promised.

The capture transcript in particular has to keep failing as *itself*: two
independent correspondence checks over one document must not collapse into one
message, or a peer could learn which lie it was caught in from the wrong error.
"""

import inspect

import pytest
from audit_builders import entry
from scent_builders import audited, v2_document, v2_runtime

from mars777_police.app import audit_scent, log_document, log_events, scent_records
from mars777_police.app.capture_transcript import TranscriptMismatchError
from mars777_police.app.interop_profiles import CompatibilityProfile
from mars777_police.app.peer_turn_messages import Reveal
from mars777_police.app.semantic_values import (
    SCORED_AS_TECHNICAL_LOSS,
    TAMPERING,
    SemanticVerdict,
)


def test_a_capture_lie_still_fails_as_a_capture_lie() -> None:
    """Its own check, its own message - the two transcripts never merge."""
    forged = v2_document(capture=[{"step": 1, "claim": None, "answer": "CAUGHT"}])
    with pytest.raises(TranscriptMismatchError, match="capture transcript has 1 rows"):
        audited(v2_runtime(), forged)


def test_the_log_persists_the_history_and_recomputes_none_of_it() -> None:
    """Part 1B took the log surface; the truthfulness question stayed shut.

    The guard that used to say "the log knows nothing of scent" retired when the
    log legitimately learned to persist it. What must never enter these modules
    is the physics - a log that recomputed its own evidence would agree with
    itself whatever was played.
    """
    for module in (log_events, log_document):
        source = inspect.getsource(module)
        assert "deposits_value" in source or "scent" in source
        for forbidden in ("emission_of", "default_scent_model", "kernel", "apply_move"):
            assert forbidden not in source


def test_the_semantic_vocabulary_is_the_nine_member_contract() -> None:
    """JDEC-018 added the ninth verdict; the two classification sets did not merge."""
    assert len(SemanticVerdict) == 9
    assert hasattr(SemanticVerdict, "DISHONEST_SCENT_EMISSION")
    assert [one for one in SemanticVerdict if "SCENT" in one.value] == [
        SemanticVerdict.DISHONEST_SCENT_EMISSION
    ]


def test_a_physical_scent_lie_is_scored_and_is_never_tampering() -> None:
    """The whole point of JDEC-018: it can happen with every hash verifying."""
    assert SemanticVerdict.DISHONEST_SCENT_EMISSION in SCORED_AS_TECHNICAL_LOSS
    assert SemanticVerdict.DISHONEST_SCENT_EMISSION not in TAMPERING
    assert len(TAMPERING) == 5
    assert len(SCORED_AS_TECHNICAL_LOSS) == 4


def test_the_new_member_sits_beside_the_entries_and_never_inside_one() -> None:
    """The sealed eight are still the sealed eight."""
    written = entry(1)
    assert "scent" not in written and "scent" not in written["state"]


def test_the_reveal_and_the_posture_vocabulary_did_not_move() -> None:
    import dataclasses

    names = tuple(field.name for field in dataclasses.fields(Reveal))
    assert names == ("cursor", "action", "hint", "capture_claim", "scent_emission")
    assert len(CompatibilityProfile) == 5


def test_no_truthfulness_machinery_reached_the_disclosure_path() -> None:
    """Part 2 owns physics; these two modules must not learn any of it."""
    for module in (audit_scent, scent_records):
        source = inspect.getsource(module)
        for forbidden in (
            "emission_of",
            "default_scent_model",
            "ScentModelAgreement",
            "LocalTurnService",
            "apply_move",
            "observed_field",
            "absorb",
            "evolve",
        ):
            assert forbidden not in source
