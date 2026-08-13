"""The full agreed scent model, across the existing config-proposal wire.

SCENT-003 wants the whole model exchanged, so the whole model is what travels:
the named interpretation, the three Appendix-F values, all twenty-five weights
and every worked number. Nothing here compares two models - a valid model that
differs from ours is transported faithfully, because deciding whether to accept
it is negotiation's job and not a codec's.
"""

import dataclasses
from decimal import Decimal

import pytest
from pydantic import ValidationError
from r16_builders import PROFILES, config

from mars777_police.app.peer_pregame_messages import ConfigProposal
from mars777_police.app.protocol_errors import MalformedMessageError
from mars777_police.domain.scent_kernel import ScentKernel
from mars777_police.domain.scent_model import ScentExample
from mars777_police.domain.scent_model_default import FIGURE_4_WEIGHTS, default_scent_model
from mars777_police.protocol.canonical import canonical_json_bytes
from mars777_police.protocol.scent_model import scent_model_core, scent_model_sha256
from mars777_police.transport.codec_pregame import decode_proposal, encode_proposal
from mars777_police.transport.codec_scent_model import decode_scent_model, encode_scent_model
from mars777_police.transport.wire_scent_model import ScentExampleWire, ScentModelWire

MODEL = default_scent_model()
GOLDEN = "e587d487716a9cb67688fc8b51b2a895a0dd75a5c49ae0fc9b86683574257600"
CANONICAL_BYTES = 344


def wire_of(model: object = MODEL) -> ScentModelWire:
    """The model on the wire, through the production encoder."""
    return encode_scent_model(model)  # type: ignore[arg-type]


def altered(**changes: object) -> ScentModelWire:
    """A wire model with one member replaced - valid or not, as the test needs."""
    return ScentModelWire(**{**wire_of().model_dump(), **changes})


def outer_ring(weight: str) -> ScentKernel:
    """A different but still radial kernel: the farthest ring moved."""
    rows = [list(row) for row in FIGURE_4_WEIGHTS]
    for row, col in ((0, 0), (0, 4), (4, 0), (4, 4)):
        rows[row][col] = weight
    return ScentKernel.from_rows(rows)


def test_the_default_model_round_trips_to_the_same_semantic_value() -> None:
    assert decode_scent_model(wire_of()) == MODEL


def test_all_twenty_five_weights_survive_the_trip() -> None:
    kernel = decode_scent_model(wire_of()).kernel
    assert [len(row) for row in kernel.weights] == [5] * 5
    assert kernel.weights == MODEL.kernel.weights
    assert wire_of().kernel[2][2] == "0.90", "verbatim text, never a rounded float"


def test_both_worked_examples_survive_the_trip() -> None:
    assert decode_scent_model(wire_of()).examples == MODEL.examples
    assert [one.expected for one in wire_of().examples] == ["0.81", "0.9"]


def test_every_number_crosses_as_canonical_text() -> None:
    written = wire_of()
    assert written.decay == "0.10", "the Appendix-F text, not 0.1"
    assert written.center_intensity == "0.9"
    assert isinstance(written.field_size, int)
    assert all(isinstance(weight, str) for row in written.kernel for weight in row)


def test_the_frozen_vectors_survive_the_trip() -> None:
    back = decode_scent_model(wire_of())
    assert len(canonical_json_bytes(scent_model_core(back))) == CANONICAL_BYTES
    assert scent_model_sha256(back).value == GOLDEN


def test_a_valid_but_different_model_is_transported_faithfully() -> None:
    """Agreement is negotiation's decision; a codec carries what it is given."""
    other = dataclasses.replace(MODEL, kernel=outer_ring("0.03"))
    assert decode_scent_model(wire_of(other)) == other
    assert scent_model_sha256(decode_scent_model(wire_of(other))).value != GOLDEN


def test_a_proposal_carries_the_whole_model_across_the_wire() -> None:
    proposal = ConfigProposal(1, config(), PROFILES, MODEL)
    assert decode_proposal(encode_proposal(proposal)) == proposal


def test_a_proposal_without_a_model_round_trips_as_none() -> None:
    """Nothing is defaulted in: absent stays absent."""
    proposal = ConfigProposal(1, config(), PROFILES)
    assert proposal.scent_model is None
    written = encode_proposal(proposal)
    assert written.scent_model is None
    assert decode_proposal(written).scent_model is None


def test_a_proposal_refuses_a_scent_model_that_is_not_one() -> None:
    with pytest.raises(ValueError, match="scent_model must be a ScentModelAgreement"):
        ConfigProposal(1, config(), PROFILES, "BOUNDED_SATURATING_RADIAL_V1")  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "changes",
    [
        {"kernel": [["0.9"] * 5] * 4},
        {"kernel": [["0.9"] * 4] * 5},
        {"kernel": [["0.04", "0.9", "0.9", "0.9", "0.9"]] * 5},
        {"center_intensity": "0.8"},
        {"decay": "0.20"},
        {"field_size": 7},
        {"model_id": "RADIAL_V2"},
        {"examples": []},
    ],
)
def test_a_malformed_model_is_refused_by_its_own_owners(changes: dict[str, object]) -> None:
    with pytest.raises(MalformedMessageError, match="scent model is not valid"):
        decode_scent_model(altered(**changes))


def test_an_untruthful_example_is_refused_at_the_boundary() -> None:
    """A model whose stated number our physics does not produce never decodes."""
    lying = [ScentExampleWire(tau_before="0.9", delta="0", expected="0.5").model_dump()]
    with pytest.raises(MalformedMessageError, match=r"produces 0\.81"):
        decode_scent_model(altered(examples=lying))


@pytest.mark.parametrize(
    "changes",
    [
        {"kernel": [[0.9] * 5] * 5},
        {"center_intensity": 0.9},
        {"decay": Decimal("0.10")},
        {"field_size": True},
        {"field_size": "5"},
        {"model_id": 7},
        {"examples": [{"tau_before": "0.9", "delta": "0"}]},
        {"examples": [{"tau_before": "0.9", "delta": "0", "expected": "0.81", "note": "x"}]},
        {"center_intensity": "+0.9"},
        {"decay": "1e-1"},
    ],
)
def test_the_strict_schema_refuses_a_wrong_shape_before_any_semantics(
    changes: dict[str, object],
) -> None:
    with pytest.raises(ValidationError):
        altered(**changes)


def test_an_unknown_member_is_refused_by_the_existing_strict_policy() -> None:
    with pytest.raises(ValidationError):
        ScentModelWire(**{**wire_of().model_dump(), "scent_source": [2, 3]})


def test_an_example_row_is_exactly_its_three_numbers() -> None:
    assert set(ScentExampleWire.model_fields) == {"tau_before", "delta", "expected"}
    assert ScentExample(Decimal("0.9"), Decimal(0), Decimal("0.81")) == MODEL.examples[0]
