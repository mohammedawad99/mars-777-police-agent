"""The four tool-level request envelopes and their closed `kind` vocabularies.

This is the module that unblocked Stage 4E-R17. Three semantic variants share
`negotiate`, three share `receive_turn` and two share `submit_audit`, and until
the discriminator was frozen the only way to route was to guess which payload
keys happened to be present - which two independent implementations would have
guessed differently.

**Each tool declares its own kind set.** There is deliberately no single union of
all nine kinds: a `commitment` arriving at `negotiate` must fail, and it fails in
the published schema because `negotiate`'s enum never contained it. That is the
`E-PROTO-MALFORMED` outcome the contract requires, with no cross-tool redispatch.

Both envelope members are required and `extra="forbid"` applies at every level,
so `additionalProperties: false` reaches the wire schema itself.
"""

from typing import Annotated, Literal

from pydantic import BaseModel, Field

from .wire_config import ConfigLockEvidenceWire, ConfigProposalWire
from .wire_config_sections import WIRE
from .wire_declaration import Step0ExchangeWire
from .wire_final import (
    FinalNonceRevealWire,
    ResultAgreementWire,
)
from .wire_turn import (
    AcknowledgementWire,
    CommitmentWire,
    RevealWire,
)

AuditDisclosure = dict[str, object]
"""The frozen JSON-native audit-disclosure document (O6).

`dict`/`list`/`str`/`int`/`bool` material only - never a filesystem path, a URL,
base64, a pickle or a locally-derived verification annotation.
"""


class Step0Request(BaseModel):
    """`negotiate` carrying a Step-0 declaration exchange."""

    model_config = WIRE
    kind: Literal["step0"]
    payload: Step0ExchangeWire


class ConfigProposalRequest(BaseModel):
    """`negotiate` carrying a complete config proposal."""

    model_config = WIRE
    kind: Literal["config_proposal"]
    payload: ConfigProposalWire


class ConfigLockRequest(BaseModel):
    """`negotiate` carrying authenticated config-lock evidence."""

    model_config = WIRE
    kind: Literal["config_lock"]
    payload: ConfigLockEvidenceWire


class CommitmentRequest(BaseModel):
    """`receive_turn` carrying a commitment."""

    model_config = WIRE
    kind: Literal["commitment"]
    payload: CommitmentWire


class AcknowledgementRequest(BaseModel):
    """`receive_turn` carrying an acknowledgement."""

    model_config = WIRE
    kind: Literal["acknowledgement"]
    payload: AcknowledgementWire


class RevealRequest(BaseModel):
    """`receive_turn` carrying a reveal. The result is the legality bool."""

    model_config = WIRE
    kind: Literal["reveal"]
    payload: RevealWire


class FinalNonceRequest(BaseModel):
    """`submit_audit` carrying the batched nonce disclosure."""

    model_config = WIRE
    kind: Literal["final_nonce_reveal"]
    payload: FinalNonceRevealWire


class AuditDisclosureRequest(BaseModel):
    """`submit_audit` carrying the JSON-native disclosure document."""

    model_config = WIRE
    kind: Literal["audit_disclosure"]
    payload: AuditDisclosure


class ResultAgreementRequest(BaseModel):
    """`receive_control` carrying the one result agreement. Returns a digest."""

    model_config = WIRE
    kind: Literal["result_agreement"]
    payload: ResultAgreementWire


NegotiateRequest = Annotated[
    Step0Request | ConfigProposalRequest | ConfigLockRequest, Field(discriminator="kind")
]
ReceiveTurnRequest = Annotated[
    CommitmentRequest | AcknowledgementRequest | RevealRequest, Field(discriminator="kind")
]
SubmitAuditRequest = Annotated[
    FinalNonceRequest | AuditDisclosureRequest, Field(discriminator="kind")
]
ReceiveControlRequest = Annotated[ResultAgreementRequest, Field(discriminator="kind")]

TOOL_KINDS: dict[str, tuple[str, ...]] = {
    "negotiate": ("step0", "config_proposal", "config_lock"),
    "receive_turn": ("commitment", "acknowledgement", "reveal"),
    "submit_audit": ("final_nonce_reveal", "audit_disclosure"),
    "receive_control": ("result_agreement",),
}
"""The frozen matrix: four tools, nine kinds, no heartbeat, no alias."""
