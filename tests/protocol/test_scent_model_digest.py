"""The agreed model's canonical bytes and the unkeyed digest that identifies it.

Two peers must produce byte-identical material or an honest pair would refuse
each other, so the mapping is explicit and the bytes are pinned here - including
the verbatim `0.10`, which is the exact loss a JSON float would cause.
"""

import dataclasses
from decimal import Decimal

import pytest

from mars777_police.domain.config_model import InvalidScentError
from mars777_police.domain.scent_kernel import ScentKernel
from mars777_police.domain.scent_model import ScentExample
from mars777_police.domain.scent_model_default import (
    DECAY_EXAMPLE,
    FIGURE_4_WEIGHTS,
    default_scent_model,
)
from mars777_police.protocol.canonical import canonical_json_bytes
from mars777_police.protocol.scent_model import (
    example_core,
    kernel_core,
    scent_model_core,
    scent_model_sha256,
)

MODEL = default_scent_model()
VECTOR = "e587d487716a9cb67688fc8b51b2a895a0dd75a5c49ae0fc9b86683574257600"
"""The frozen digest of the project-default agreement. Both repositories, every
platform, every hash seed: one model, one identity."""


def digest_of(model: object) -> str:
    return scent_model_sha256(model).value  # type: ignore[arg-type]


def test_the_default_model_has_the_frozen_digest() -> None:
    assert digest_of(MODEL) == VECTOR


def test_the_canonical_bytes_are_stable_and_carry_verbatim_decimals() -> None:
    written = canonical_json_bytes(scent_model_core(MODEL)).decode()
    assert '"decay":0.10' in written, "the Appendix-F text, not a rounded float"
    assert '"center_intensity":0.9' in written
    assert '"model_id":"BOUNDED_SATURATING_RADIAL_V1"' in written
    assert written == canonical_json_bytes(scent_model_core(default_scent_model())).decode()


def test_every_one_of_the_twenty_five_weights_reaches_the_bytes() -> None:
    rows = kernel_core(MODEL.kernel)
    assert [len(row) for row in rows] == [5] * 5
    assert all(isinstance(weight, Decimal) for row in rows for weight in row)
    assert rows[2][2] == Decimal("0.90")


def test_every_example_member_reaches_the_bytes() -> None:
    assert example_core(DECAY_EXAMPLE) == {
        "tau_before": Decimal("0.9"),
        "delta": Decimal("0"),
        "expected": Decimal("0.81"),
    }


def outer_ring(weight: str) -> ScentKernel:
    """The default kernel with its farthest ring moved - still radial, still valid."""
    rows = [list(row) for row in FIGURE_4_WEIGHTS]
    for row, col in ((0, 0), (0, 4), (4, 0), (4, 4)):
        rows[row][col] = weight
    return ScentKernel.from_rows(rows)


def test_one_changed_off_centre_ring_changes_the_identity() -> None:
    other = dataclasses.replace(MODEL, kernel=outer_ring("0.03"))
    assert digest_of(other) != VECTOR


def test_a_single_cell_change_never_reaches_a_digest_at_all() -> None:
    """The radial authority refuses it first: one corner cannot differ alone."""
    rows = [list(row) for row in FIGURE_4_WEIGHTS]
    rows[0][0] = "0.03"
    with pytest.raises(InvalidScentError, match="squared radius 8 must share one intensity"):
        ScentKernel.from_rows(rows)


def test_a_changed_expected_example_changes_the_identity() -> None:
    """The worked numbers are part of the agreement, not commentary."""
    other = dataclasses.replace(
        MODEL, examples=(ScentExample(Decimal("0.9"), Decimal(0), Decimal("0.810")),)
    )
    assert digest_of(other) != VECTOR


def test_dropping_an_example_changes_the_identity() -> None:
    assert digest_of(dataclasses.replace(MODEL, examples=(DECAY_EXAMPLE,))) != VECTOR


@pytest.mark.parametrize("member", ["model_id", "center_intensity", "decay", "field_size"])
def test_every_core_member_is_actually_mapped(member: str) -> None:
    assert member in scent_model_core(MODEL)


def test_the_core_is_json_native_and_holds_no_object() -> None:
    core = scent_model_core(MODEL)
    assert isinstance(core["kernel"], list) and isinstance(core["examples"], list)
    assert isinstance(core["field_size"], int) and not isinstance(core["field_size"], bool)
    assert isinstance(core["model_id"], str)
