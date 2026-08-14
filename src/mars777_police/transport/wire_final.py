"""Wire DTOs for the two end-of-series families.

They left `wire_turn` when the turn families grew the live scent adjunct: a
nonce batch and a result agreement belong to the end of a series, not to a turn,
and keeping them together only made one module hold two lifecycles.

Nothing about either shape changed in the move - same members, same strictness,
same scalars.
"""

from pydantic import BaseModel

from .wire_config_sections import WIRE
from .wire_scalars import NonceText, NonEmptyText, TimestampText
from .wire_turn import TurnCursorWire


class NonceRevealEntryWire(BaseModel):
    """One disclosed nonce, bound to the turn it belongs to."""

    model_config = WIRE

    cursor: TurnCursorWire
    nonce: NonceText


class FinalNonceRevealWire(BaseModel):
    """The batched end-of-sub-game nonce disclosure."""

    model_config = WIRE

    entries: list[NonceRevealEntryWire]


class ResultContributionEntryWire(BaseModel):
    """One sub-game of a participant's sender-owned contribution."""

    model_config = WIRE

    sub_game: int
    github_commit: str
    tokens: int


class ResultContributionWire(BaseModel):
    """Everything one participant owns that the opponent cannot derive."""

    model_config = WIRE

    group_id: NonEmptyText
    entries: list[ResultContributionEntryWire]


class ResultAgreementWire(BaseModel):
    """Identity, the shared timestamp, then the sender's own contribution.

    No `result_sha256`: the common digest cannot exist until a peer holds the
    opponent's contribution, so it is the operation's *response*.
    """

    model_config = WIRE

    game_id: NonEmptyText
    game_uid: NonEmptyText
    declaration_ref: NonEmptyText
    timestamp: TimestampText
    contribution: ResultContributionWire
