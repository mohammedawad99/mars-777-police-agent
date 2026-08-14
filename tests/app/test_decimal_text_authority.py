"""One canonical decimal spelling, at a layer both sides may legally consume.

The rule did not change - it moved. `transport` still publishes the same names
and the same annotated wire types, but the parse, the render and the pattern are
implemented once, in `app`, so the application layer can read a decimal out of
an audit document without importing the framework adapter.

Every expectation below is the **pre-relocation** behaviour, asserted against the
values the project already froze.
"""

import inspect
from decimal import Decimal

import pytest

from mars777_police.app import decimal_text
from mars777_police.app.decimal_text import CANONICAL_DECIMAL, decimal_from_text, text_from_decimal
from mars777_police.transport import wire_scalars

FROZEN = ["0.10", "0.9", "0.90", "0.81", "0", "1", "3.5", "100", "-0.5"]


def imports_of(module: object) -> list[str]:
    """Every import line the module actually executes."""
    lines = inspect.getsource(module).splitlines()  # type: ignore[arg-type]
    return [line for line in lines if line.startswith(("import ", "from "))]


def test_the_authority_is_pure_and_imports_nothing_but_decimal() -> None:
    """No pydantic, no transport, no domain, no filesystem, no network."""
    assert imports_of(decimal_text) == ["from decimal import Decimal"]
    assert "float(" not in inspect.getsource(decimal_text)


def test_transport_publishes_the_same_objects_it_no_longer_implements() -> None:
    """Delegation, not a second copy: the adapter re-exports the authority."""
    assert wire_scalars.decimal_from_text is decimal_from_text
    assert wire_scalars.text_from_decimal is text_from_decimal
    assert wire_scalars.CANONICAL_DECIMAL is CANONICAL_DECIMAL
    adapter = inspect.getsource(wire_scalars)
    assert "def decimal_from_text" not in adapter
    assert "def text_from_decimal" not in adapter


def test_the_application_layer_can_import_it_without_transport() -> None:
    """The whole point of the move, asserted as an import fact."""
    assert decimal_text.__name__ == "mars777_police.app.decimal_text"
    assert not [line for line in imports_of(decimal_text) if "transport" in line]


@pytest.mark.parametrize("spelling", FROZEN)
def test_every_frozen_spelling_round_trips_to_itself(spelling: str) -> None:
    assert text_from_decimal(decimal_from_text(spelling)) == spelling


def test_a_trailing_zero_survives_because_it_is_part_of_the_spelling() -> None:
    assert decimal_from_text("0.10") == Decimal("0.10") == Decimal("0.1")
    assert text_from_decimal(Decimal("0.10")) == "0.10"
    assert text_from_decimal(Decimal("0.1")) == "0.1"


def test_the_renderer_never_emits_an_exponent_form() -> None:
    assert text_from_decimal(Decimal("1E+2")) == "100"
    assert "E" not in text_from_decimal(Decimal("0.0000001"))


def test_the_parser_builds_no_float_on_the_way_in() -> None:
    value = decimal_from_text("0.10")
    assert isinstance(value, Decimal) and str(value) == "0.10"
    assert decimal_from_text("0.9") == Decimal("0.90"), "one number"
    assert text_from_decimal(decimal_from_text("0.9")) != text_from_decimal(
        decimal_from_text("0.90")
    ), "two spellings"


@pytest.mark.parametrize("spelling", FROZEN)
def test_the_frozen_pattern_accepts_every_frozen_spelling(spelling: str) -> None:
    import re

    assert re.match(CANONICAL_DECIMAL, spelling)


@pytest.mark.parametrize(
    "rejected",
    [
        "",
        " 0.1",
        "0.1 ",
        "+0.9",
        "1e-1",
        "1E+2",
        "00.9",
        ".9",
        "9.",
        "NaN",
        "Infinity",
        "-Infinity",
    ],
)
def test_the_frozen_pattern_still_rejects_what_it_always_rejected(rejected: str) -> None:
    import re

    assert re.match(CANONICAL_DECIMAL, rejected) is None
