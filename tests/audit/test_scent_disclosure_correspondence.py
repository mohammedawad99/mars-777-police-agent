"""The live scent history has to survive the final audit unchanged.

`scent_emission` was never a member of `H_commit`, so SHA-256 proves nothing about
it: a peer can disclose a perfectly well-formed emission it never sent and every
hash in the document will still verify. What stops that is the same thing that
stops a rewritten capture transcript - both sides kept the rows they really
observed, and the disclosure is compared against them row for row.

Two boundaries stay strictly apart. A document whose scent is *unreadable* never
becomes evidence at all and leaves by the malformed-message path, which
`test_scent_disclosure_json` owns. A document whose scent is perfectly readable
but is **not what arrived** is the peer contradicting itself, and leaves by the
existing `TranscriptMismatchError` / `E-PROTO-STALE` identity. Neither path asks
whether an emission is physically correct - nothing here recomputes one.
"""

import dataclasses
import inspect
from decimal import Decimal

import audit_builders as build
import pytest
from audit_builders import SUB_GAME
from scent_builders import audited, emission, rows, v2_document, v2_evidence, v2_runtime

from mars777_police.app.audit_runtime import AuditRuntime
from mars777_police.app.audit_scent import scent_rows
from mars777_police.app.capture_transcript import TranscriptMismatchError, require_same_scent
from mars777_police.app.scent_records import ScentRecord
from mars777_police.app.turn_cursor import TurnCursor
from mars777_police.domain.board import Position
from mars777_police.domain.scent_emission import ScentDeposit, ScentEmission
from mars777_police.protocol.audit_commitment import CommitmentRecomputer


def test_a_legacy_document_with_no_scent_member_still_parses() -> None:
    legacy = build.document()
    assert "scent" not in legacy
    assert scent_rows(legacy) == ()


def test_a_legacy_session_accepts_a_legacy_document() -> None:
    """Nothing observed, nothing disclosed: the audit completes exactly as before."""
    live = audited(build.runtime(), build.document())
    assert live.verdict is not None and live.verified


def test_a_legacy_session_refuses_smuggled_scent() -> None:
    """No document gains V2 semantics merely by carrying the field."""
    with pytest.raises(TranscriptMismatchError, match="scent transcript has 2 rows"):
        audited(build.runtime(), v2_document())


def test_a_v2_session_accepts_the_exact_scent_it_observed() -> None:
    live = audited(v2_runtime(), v2_document())
    assert live.verdict is not None and live.verified


def test_a_v2_session_refuses_a_document_that_omits_scent_entirely() -> None:
    """Legacy parseability is not legacy completeness."""
    with pytest.raises(TranscriptMismatchError, match="has 0 rows"):
        audited(v2_runtime(), build.document())


def test_a_missing_row_is_refused() -> None:
    with pytest.raises(TranscriptMismatchError, match="has 1 rows"):
        audited(v2_runtime(), v2_document(rows((1,))))


def test_an_extra_row_is_refused() -> None:
    extra = (*rows(), ScentRecord(TurnCursor(SUB_GAME, 2), emission(1)))
    with pytest.raises(TranscriptMismatchError, match="has 3 rows"):
        audited(v2_runtime(), v2_document(extra))


def test_a_duplicated_cursor_is_refused() -> None:
    with pytest.raises(TranscriptMismatchError, match="is not the one observed"):
        audited(v2_runtime(), v2_document((rows()[0], rows()[0])))


def test_a_row_moved_to_another_turn_is_refused() -> None:
    moved = (ScentRecord(TurnCursor(SUB_GAME, 2), emission(1)), rows()[1])
    with pytest.raises(TranscriptMismatchError, match="is not the one observed"):
        audited(v2_runtime(), v2_document(moved))


def test_two_emissions_attached_to_swapped_cursors_are_refused() -> None:
    first, second = rows()
    swapped = (
        ScentRecord(first.cursor, second.emission),
        ScentRecord(second.cursor, first.emission),
    )
    with pytest.raises(TranscriptMismatchError, match="is not the one observed"):
        audited(v2_runtime(), v2_document(swapped))


def test_a_reordered_transcript_is_refused() -> None:
    with pytest.raises(TranscriptMismatchError, match="is not the one observed"):
        audited(v2_runtime(), v2_document(tuple(reversed(rows()))))


def test_a_structurally_valid_but_different_emission_is_refused() -> None:
    """The whole point: readable, well-formed, and not what arrived."""
    assert emission(2) != emission(1), "the two emissions really differ"
    rewritten = (ScentRecord(rows()[0].cursor, emission(2)), rows()[1])
    with pytest.raises(TranscriptMismatchError, match="is not the one observed"):
        audited(v2_runtime(), v2_document(rewritten))


def test_the_correspondence_never_asks_whether_an_emission_is_physically_right() -> None:
    """A row no model would produce still passes, because it is the row observed."""
    invented = ScentEmission((ScentDeposit(Position(1, 1), Decimal("0.07")),))
    assert invented != emission(1), "nothing the locked model would ever deposit"
    live = AuditRuntime(
        build.context(),
        (dataclasses.replace(build.evidence((1,))[0], scent=invented), *v2_evidence((2,))),
        CommitmentRecomputer(),
        capture=build.capture(),
    )
    disclosed = (ScentRecord(TurnCursor(SUB_GAME, 1), invented), *rows((2,)))
    assert audited(live, v2_document(disclosed)).verified
    text = inspect.getsource(require_same_scent)
    for forbidden in ("emission_of", "default_scent_model", "kernel", "params", "apply_move"):
        assert forbidden not in text


def test_the_check_runs_before_the_hashes_and_after_the_capture_transcript() -> None:
    source = inspect.getsource(AuditRuntime.accept_audit_disclosure)
    order = [
        source.index("require_identity"),
        source.index("require_same_transcript"),
        source.index("require_same_scent"),
        source.index("verdict_for"),
    ]
    assert order == sorted(order)
