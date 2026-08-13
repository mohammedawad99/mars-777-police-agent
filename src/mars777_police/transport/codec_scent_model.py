"""Mapping the agreed scent model between its wire text and its semantic value.

Mapping only, in both directions, and **no validation of its own**. Every rule a
model must satisfy already has an owner: `ScentKernel` checks the radial
contract, `ScentParams` checks the three FIXED values, `ScentExample` and
`ScentModelAgreement` check composition, and `require_truthful_examples` runs
the worked numbers through the real recurrence. This module calls them and
turns what they raise into the transport's own malformed identity, so a peer
that sends a model our physics would refuse is refused **here**, at the
boundary, rather than inside a runtime that assumed a valid value.

**Malformed is not disagreement.** A model that is well-formed but different
from ours decodes successfully and travels intact: comparing two valid models is
a negotiation decision, and it does not live in a codec.

Decimals cross as canonical text through the existing helpers - there is no
second decimal codec, and no `float` is constructed on either path. The text
itself is already constrained by `DecimalText` in the schema, exactly as the
config codec relies on, so nothing here re-checks its spelling.
"""

from ..app.protocol_errors import MalformedMessageError
from ..domain.config_model import ScentParams
from ..domain.errors import DomainError
from ..domain.scent_kernel import ScentKernel
from ..domain.scent_model import ScentExample, ScentModelAgreement
from ..domain.scent_model_examples import require_truthful_examples
from .wire_scalars import decimal_from_text, text_from_decimal
from .wire_scent_model import ScentExampleWire, ScentModelWire


def decode_scent_model(wire: ScentModelWire) -> ScentModelAgreement:
    """Rebuild the agreed model, refusing anything its own validators refuse."""
    try:
        kernel = ScentKernel.from_rows(wire.kernel)
        params = ScentParams(
            decimal_from_text(wire.center_intensity),
            decimal_from_text(wire.decay),
            wire.field_size,
        )
        agreement = ScentModelAgreement(
            wire.model_id,
            kernel,
            params,
            tuple(_example(one) for one in wire.examples),
        )
        require_truthful_examples(agreement)
    except DomainError as failure:
        raise MalformedMessageError(f"scent model is not valid: {failure}") from None
    return agreement


def _example(wire: ScentExampleWire) -> ScentExample:
    """One worked number, with its three decimals rebuilt from their text."""
    return ScentExample(
        decimal_from_text(wire.tau_before),
        decimal_from_text(wire.delta),
        decimal_from_text(wire.expected),
    )


def encode_scent_model(agreement: ScentModelAgreement) -> ScentModelWire:
    """Render the agreed model, every number as its canonical text."""
    return ScentModelWire(
        model_id=agreement.model_id,
        center_intensity=text_from_decimal(agreement.center_intensity),
        decay=text_from_decimal(agreement.decay_rate),
        field_size=agreement.field_size,
        kernel=[[text_from_decimal(weight) for weight in row] for row in agreement.kernel.weights],
        examples=[_example_wire(one) for one in agreement.examples],
    )


def _example_wire(example: ScentExample) -> ScentExampleWire:
    """One worked number on the wire, in the one decimal spelling."""
    return ScentExampleWire(
        tau_before=text_from_decimal(example.tau_before),
        delta=text_from_decimal(example.delta),
        expected=text_from_decimal(example.expected),
    )
