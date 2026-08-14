"""The live emission on the wire: deposits, and deliberately nothing else.

`wire_scent_model` carries the *agreed model* before the series; this carries
what one turn actually deposited under it. The two are separate shapes for a
reason - the model is a contract both peers must hold identically, an emission
is one observation one peer is offering.

**No centre, no source, no role.** The schema has exactly one member, and every
intensity crosses as the same canonical decimal text the config and the model
use, so no binary float ever touches a scent number. Strict like every wire
model here: an unknown member is refused rather than ignored.
"""

from pydantic import BaseModel

from .wire_config_sections import WIRE
from .wire_scalars import DecimalText


class ScentDepositWire(BaseModel):
    """One emitted cell and its intensity, as canonical decimal text."""

    model_config = WIRE

    cell: list[int]
    intensity: DecimalText


class ScentEmissionWire(BaseModel):
    """What one action deposited - deposits only, and never a source cell."""

    model_config = WIRE

    deposits: list[ScentDepositWire]
