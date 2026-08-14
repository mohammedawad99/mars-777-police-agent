"""One turn's emission across the existing reveal, and what it never carries.

The emission travels as an adjunct on the reveal that already existed - no tenth
wire kind, no fifth tool, no second RPC - and it carries deposits only. There is
no source cell on the wire, because the receiver is being given an observation,
not a position.

Every number crosses as the project's canonical decimal text, and the semantic
validators stay the only authority: a shape the domain refuses never becomes a
value, it becomes this layer's malformed identity.
"""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from mars777_police.app.peer_turn_messages import Reveal
from mars777_police.app.protocol_errors import MalformedMessageError
from mars777_police.app.turn_cursor import TurnCursor
from mars777_police.domain.actions import MoveAction
from mars777_police.domain.board import Position
from mars777_police.domain.config_model import GridConfig
from mars777_police.domain.rules import Move
from mars777_police.domain.scent_model_default import default_scent_model
from mars777_police.domain.scent_observation import emission_of
from mars777_police.transport.codec_scent_turn import decode_emission, encode_emission
from mars777_police.transport.codec_turn import decode_reveal, encode_reveal
from mars777_police.transport.wire_scent_turn import ScentDepositWire, ScentEmissionWire
from mars777_police.transport.wire_turn import RevealWire

BOARD = GridConfig.from_grid_size(7, 0).to_board()
MODEL = default_scent_model()
START = TurnCursor(1, 1)
EMISSION = emission_of(BOARD, MODEL.kernel, Position(3, 3), MODEL.params)


def reveal(scent: object = EMISSION) -> Reveal:
    """A V2 reveal carrying the real projected emission."""
    return Reveal(START, MoveAction(Move.N), "heading north", None, scent)  # type: ignore[arg-type]


def altered(**changes: object) -> ScentEmissionWire:
    """The wire emission with one member replaced - valid or not, as needed."""
    return ScentEmissionWire(**{**encode_emission(EMISSION).model_dump(), **changes})


def test_the_emission_round_trips_to_the_same_semantic_value() -> None:
    assert decode_emission(encode_emission(EMISSION)) == EMISSION


def test_the_whole_reveal_round_trips_with_its_emission() -> None:
    original = reveal()
    assert decode_reveal(encode_reveal(original)) == original


def test_a_v1_reveal_round_trips_with_no_emission_at_all() -> None:
    """Legacy shape stays parseable: absent stays absent in both directions."""
    legacy = Reveal(START, MoveAction(Move.N), "heading north")
    written = encode_reveal(legacy)
    assert written.scent_emission is None
    assert decode_reveal(written) == legacy


def test_every_intensity_crosses_as_canonical_decimal_text() -> None:
    written = encode_reveal(reveal())
    assert written.scent_emission is not None
    for deposit in written.scent_emission.deposits:
        assert isinstance(deposit.intensity, str), "text on the wire, never a float"
    values = {deposit.intensity for deposit in written.scent_emission.deposits}
    assert "0.90" in values or "0.9" in values


def test_the_decoded_intensities_are_exact_decimals() -> None:
    back = decode_emission(encode_emission(EMISSION))
    assert back is not None
    assert all(isinstance(one.intensity, Decimal) for one in back.deposits)
    assert back.deposits[0].intensity == EMISSION.deposits[0].intensity


def test_the_wire_emission_carries_deposits_and_nothing_else() -> None:
    """No centre, no source cell, no role - the schema has one member."""
    assert set(ScentEmissionWire.model_fields) == {"deposits"}
    assert set(ScentDepositWire.model_fields) == {"cell", "intensity"}
    written = encode_reveal(reveal()).model_dump()
    assert set(written) == {"cursor", "action", "hint", "capture_claim", "scent_emission"}
    text = str(written)
    for forbidden in ("source", "own_position", "opponent", "true_position", "role"):
        assert forbidden not in text


def test_a_reveal_wire_refuses_an_unknown_scent_member() -> None:
    with pytest.raises(ValidationError):
        ScentEmissionWire(deposits=[], source_position=[1, 1])  # type: ignore[call-arg]
    with pytest.raises(ValidationError):
        RevealWire(**{**encode_reveal(reveal()).model_dump(), "scent_source": [1, 1]})


def test_a_binary_float_intensity_is_refused_by_the_schema() -> None:
    with pytest.raises(ValidationError):
        ScentDepositWire(cell=[1, 1], intensity=0.9)  # type: ignore[arg-type]


def test_a_malformed_deposit_cell_is_refused() -> None:
    with pytest.raises(MalformedMessageError, match=r"exactly \[row, col\]"):
        decode_emission(altered(deposits=[{"cell": [1], "intensity": "0.9"}]))


def test_deposits_out_of_canonical_order_are_refused_by_the_domain() -> None:
    written = encode_emission(EMISSION).model_dump()
    written["deposits"] = list(reversed(written["deposits"]))
    with pytest.raises(MalformedMessageError, match="scent emission is not valid"):
        decode_emission(ScentEmissionWire(**written))


def test_a_non_positive_intensity_is_refused_by_the_domain() -> None:
    with pytest.raises(MalformedMessageError, match="scent emission is not valid"):
        decode_emission(altered(deposits=[{"cell": [1, 1], "intensity": "0"}]))


def test_an_intensity_above_the_locked_bound_is_still_a_decimal_the_domain_judges() -> None:
    """The deposit type owns its own rules; the codec never second-guesses them."""
    back = decode_emission(altered(deposits=[{"cell": [1, 1], "intensity": "0.05"}]))
    assert back is not None and back.deposits[0].intensity == Decimal("0.05")
