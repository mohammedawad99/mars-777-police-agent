"""Minimal probe DTOs pinning the frozen transport envelope.

These are **not** the production transport layer - Stage 4E-R17-R1 implements no
adapter. They exist so the wire contract frozen in `API_BOUNDARIES.md`
§Stage 4E-R17-R1 is executable rather than aspirational: if a future FastMCP or
Pydantic release stops enforcing a closed `kind`, stops refusing extra members or
starts coercing a JSON number into a canonical decimal string, these fail.

Duplicated per test directory for the same reason every other helper here is:
`tests/*` has no package.
"""

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, StringConstraints

CANONICAL_DECIMAL = r"^-?(0|[1-9][0-9]*)(\.[0-9]+)?$"
"""The canonical decimal grammar - no exponent, no `+`, no leading zeros."""

DecimalText = Annotated[str, StringConstraints(pattern=CANONICAL_DECIMAL)]

NEGOTIATE_KINDS = ("step0", "config_proposal", "config_lock")
RECEIVE_TURN_KINDS = ("commitment", "acknowledgement", "reveal")
SUBMIT_AUDIT_KINDS = ("final_nonce_reveal", "audit_disclosure")
RECEIVE_CONTROL_KINDS = ("result_agreement",)

TOOL_KINDS = {
    "negotiate": NEGOTIATE_KINDS,
    "receive_turn": RECEIVE_TURN_KINDS,
    "submit_audit": SUBMIT_AUDIT_KINDS,
    "receive_control": RECEIVE_CONTROL_KINDS,
}
"""The frozen tool/kind matrix. Nine kinds, four tools, no heartbeat."""


class NegotiateEnvelope(BaseModel):
    """The frozen envelope: exactly `kind` and `payload`, both required."""

    model_config = ConfigDict(extra="forbid", strict=True)

    kind: Literal["step0", "config_proposal", "config_lock"]
    payload: dict[str, Any]


class PheromonesPayload(BaseModel):
    """A payload carrying the two FIXED decimals as canonical text."""

    model_config = ConfigDict(extra="forbid", strict=True)

    pheromone_center_intensity: DecimalText
    pheromone_decay: DecimalText
    pheromone_grid_size: int


class ConfigProposalEnvelope(BaseModel):
    """The same envelope with a typed payload rather than a free object."""

    model_config = ConfigDict(extra="forbid", strict=True)

    kind: Literal["config_proposal"]
    payload: PheromonesPayload
