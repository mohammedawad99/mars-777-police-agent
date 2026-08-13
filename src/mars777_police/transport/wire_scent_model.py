"""The agreed scent model on the wire: the whole thing, in canonical text.

SCENT-003 asks the two groups to exchange the **full** emission and decay model
with a concrete numeric example, so this DTO carries every member the agreement
holds - the named interpretation, the three Appendix-F values, all twenty-five
weights and every worked number. A digest would be smaller and would not satisfy
the requirement: a peer cannot verify an interpretation it was never shown.

**Every number is `DecimalText`, never a JSON number.** The same measurement that
forced the config's two pheromone values into text applies here twenty-seven
times over: a JSON `0.10` arrives as `Decimal('0.1')`, and the model digest is
taken over the exact characters. `field_size` is the one genuine integer.

Strict and closed, like every wire type here: `extra="forbid"` and `strict=True`,
so an unknown member or a `float` where text belongs is refused in the schema
rather than deep inside a semantic constructor.
"""

from pydantic import BaseModel

from .wire_config_sections import WIRE
from .wire_scalars import DecimalText, NonEmptyText


class ScentExampleWire(BaseModel):
    """One worked number: the state before, the deposit, and the result."""

    model_config = WIRE

    tau_before: DecimalText
    delta: DecimalText
    expected: DecimalText


class ScentModelWire(BaseModel):
    """The complete agreed model, exactly as `ScentModelAgreement` holds it.

    `kernel` is five rows of five canonical decimals in the order the semantic
    kernel stores them, so the twenty-five weights arrive as a shape rather than
    as a flat list whose row boundaries a reader would have to guess.
    """

    model_config = WIRE

    model_id: NonEmptyText
    center_intensity: DecimalText
    decay: DecimalText
    field_size: int
    kernel: list[list[DecimalText]]
    examples: list[ScentExampleWire]
