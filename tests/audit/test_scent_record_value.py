"""The value the scent history is made of, and where the inbound one lives.

Two members and no third. The sub-game and the sender are already identified by
the document that carries these rows, where the emitter stood is sealed until the
audit, and whether an emission is *physically* right is a different question from
whether it is the one that was sent - so a role, a source cell, a model or a
verdict here would be either duplicated identity or an answer to a question this
value is not asking.

The inbound rows are not stored at all: `TurnEvidence.scent` has been the
authority since Reveal V2 and the audit projects them from it, so there is no
second history to drift from the one that was witnessed.
"""

import dataclasses
import inspect

import audit_builders as build
import pytest
import scent_builders as scent
from audit_builders import SUB_GAME
from scent_builders import emission, rows

from mars777_police.app.audit_runtime import AuditRuntime
from mars777_police.app.scent_records import ScentRecord
from mars777_police.app.turn_cursor import TurnCursor
from mars777_police.protocol.audit_commitment import CommitmentRecomputer


def test_the_record_carries_exactly_a_cursor_and_an_emission() -> None:
    names = tuple(field.name for field in dataclasses.fields(ScentRecord))
    assert names == ("cursor", "emission")


def test_the_record_is_frozen_and_slotted_like_every_other_semantic_row() -> None:
    record = ScentRecord(TurnCursor(SUB_GAME, 1), emission(1))
    assert ScentRecord.__dataclass_params__.frozen is True
    assert not hasattr(record, "__dict__")
    with pytest.raises(dataclasses.FrozenInstanceError):
        record.cursor = TurnCursor(SUB_GAME, 2)  # type: ignore[misc]


def test_the_record_names_no_position_role_model_or_verdict() -> None:
    """The two members are the whole value: nothing here locates anybody."""
    text = inspect.getsource(ScentRecord)
    for forbidden in ("role", "source", "own_position", "model", "expected", "verdict"):
        assert f"{forbidden}:" not in text


@pytest.mark.parametrize(
    ("cursor", "value"),
    [((1, 1), None), (TurnCursor(SUB_GAME, 1), "0.9")],
)
def test_the_record_refuses_a_member_of_the_wrong_type(cursor: object, value: object) -> None:
    with pytest.raises(ValueError, match=r"needs a TurnCursor|must be a ScentEmission"):
        ScentRecord(cursor, value)  # type: ignore[arg-type]


def test_the_record_carries_no_import_that_could_close_a_cycle() -> None:
    """A value only: it knows nothing of transcripts, audits or the framework."""
    from mars777_police.app import scent_records

    imports = [
        line
        for line in inspect.getsource(scent_records).splitlines()
        if line.startswith(("import ", "from "))
    ]
    assert imports == [
        "from dataclasses import dataclass",
        "from ..domain.scent_emission import ScentEmission",
        "from .turn_cursor import TurnCursor",
    ]


def test_the_inbound_authority_is_still_the_live_turn_evidence() -> None:
    """No second inbound collection: the audit projects the rows it already holds."""
    live = scent.v2_runtime()
    assert live.expected_scent == rows()
    assert all(one.scent is not None for one in live.evidence)


def test_the_projection_skips_a_turn_that_carried_no_emission() -> None:
    live = AuditRuntime(build.context(), build.evidence(), CommitmentRecomputer())
    assert live.expected_scent == ()


def test_the_audit_stores_no_scent_of_its_own() -> None:
    names = {field.name for field in dataclasses.fields(AuditRuntime)}
    assert "scent" not in names, "expected rows are derived from evidence, never stored twice"
