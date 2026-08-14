"""Writing the scent into a document, and reading a hostile one back out.

The writer and the reader are a deliberate pair: what our own disclosure emits is
exactly what a peer's `AuditRuntime` parses, with nothing adapted on the way. One
member is added beside `capture`, carrying the turn and the deposits and nothing
that would locate anybody.

Intensities cross as canonical decimal text through the one shared authority the
transport adapter also delegates to, so `0.10` survives as `0.10` and a binary
float never becomes a value at all. The deposits are handed to the domain's own
`ScentEmission`, so ordering, uniqueness and positivity are judged exactly once,
where they already live - this module never restates a scent rule.
"""

import inspect
import json
from decimal import Decimal

import audit_builders as build
import pytest
from audit_builders import CONFIG, GAME_ID, GAME_UID, PEER, SUB_GAME
from scent_builders import emission, rows, scent_json, v2_document

from mars777_police.app import audit_scent
from mars777_police.app.audit_disclosure_writer import document as render
from mars777_police.app.audit_scent import scent_rows
from mars777_police.app.outbound_evidence_values import LocalEvidenceContext
from mars777_police.app.protocol_errors import MalformedMessageError

OURS = LocalEvidenceContext(GAME_ID, GAME_UID, SUB_GAME, CONFIG, PEER)


def test_the_document_gains_exactly_one_new_member() -> None:
    """Six members before this checkpoint, seven after - `scent` and nothing else."""
    written = render(OURS, (), (), rows())
    assert set(written) == {
        "game_id",
        "game_uid",
        "sub_game",
        "config_sha256",
        "entries",
        "capture",
        "scent",
    }


def test_a_disclosed_row_carries_the_step_and_its_deposits_only() -> None:
    (row, _) = scent_json(rows())
    assert set(row) == {"step", "emission"}
    deposits = row["emission"]
    assert isinstance(deposits, list) and deposits
    for deposit in deposits:
        assert set(deposit) == {"cell", "intensity"}


def test_every_disclosed_intensity_is_canonical_decimal_text() -> None:
    (row, _) = scent_json(rows())
    deposits = row["emission"]
    assert isinstance(deposits, list)
    for deposit in deposits:
        assert isinstance(deposit["intensity"], str), "text in the document, never a float"
    values = {deposit["intensity"] for deposit in deposits}
    assert "0.90" in values or "0.9" in values


def test_the_document_stays_json_native() -> None:
    written = render(OURS, (), (), rows())
    assert json.loads(json.dumps(written)) == written


def test_the_disclosed_rows_round_trip_to_the_same_semantic_values() -> None:
    assert scent_rows(v2_document()) == rows()


def test_the_decoded_intensities_are_exact_decimals() -> None:
    (first, _) = scent_rows(v2_document())
    assert all(isinstance(one.intensity, Decimal) for one in first.emission.deposits)
    assert first.emission == emission(1)


@pytest.mark.parametrize("spelling", ["0.10", "0.9", "0.90", "0.81", "1", "3.5"])
def test_a_canonical_spelling_survives_the_document_exactly(spelling: str) -> None:
    disclosed = [{"step": 1, "emission": [{"cell": [1, 1], "intensity": spelling}]}]
    (row,) = scent_rows(build.document(scent=disclosed))
    assert str(row.emission.deposits[0].intensity) == spelling


def test_the_parser_reads_no_binary_float() -> None:
    disclosed = [{"step": 1, "emission": [{"cell": [1, 1], "intensity": 0.9}]}]
    with pytest.raises(MalformedMessageError, match="intensity"):
        scent_rows(build.document(scent=disclosed))


@pytest.mark.parametrize(
    "spelling", ["", " 0.1", "0.1 ", "+0.9", "1e-1", "1E+2", "00.9", ".9", "9.", "NaN", "0.9\n"]
)
def test_a_non_canonical_spelling_is_refused(spelling: str) -> None:
    disclosed = [{"step": 1, "emission": [{"cell": [1, 1], "intensity": spelling}]}]
    with pytest.raises(MalformedMessageError, match="intensity"):
        scent_rows(build.document(scent=disclosed))


@pytest.mark.parametrize(
    ("scent", "reason"),
    [
        ("rewritten", "unreadable"),
        ([{"step": 1}], "emission"),
        ([{"step": 1, "emission": "0.9"}], "emission"),
        ([{"step": 1, "emission": [{"cell": [1], "intensity": "0.9"}]}], "position"),
        ([{"step": 1, "emission": [{"cell": [1, 1], "intensity": "0"}]}], "not valid"),
        ([{"emission": []}], "step"),
        (["not an object"], "scent row"),
    ],
)
def test_a_structurally_broken_scent_member_is_malformed(scent: object, reason: str) -> None:
    with pytest.raises(MalformedMessageError, match=reason):
        scent_rows(build.document(scent=scent))


def test_deposits_out_of_canonical_order_are_refused_by_the_domain() -> None:
    (row, _) = scent_json(rows())
    listing = row["emission"]
    assert isinstance(listing, list)
    reversed_row = {"step": 1, "emission": list(reversed(listing))}
    with pytest.raises(MalformedMessageError, match="not valid"):
        scent_rows(build.document(scent=[reversed_row]))


def test_the_parser_reaches_no_framework_adapter() -> None:
    """The app-owned reader consumes the shared decimal authority, not transport."""
    source = inspect.getsource(audit_scent)
    imports = [line for line in source.splitlines() if line.startswith(("import ", "from "))]
    assert not [line for line in imports if "transport" in line]
    assert "from .decimal_text import CANONICAL_DECIMAL, decimal_from_text" in imports
    assert "Decimal(" not in source, "one parser authority, called by name"
