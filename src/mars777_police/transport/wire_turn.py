"""Wire DTOs for the turn families and the end-of-series families.

`Reveal` carries the cursor, the action and the hint - **and no nonce**. That is
not an oversight to be fixed later: Ch 5 §5.3.2 withholds the nonce until final
audit, so a nonce member here would break commit-reveal itself. The nonces travel
exactly once, in `final_nonce_reveal`.

The action is a tagged union with the same two-key shape the sealed record uses,
so a movement token and a barrier cell are never told apart by guessing which
field happens to be present.
"""

from typing import Literal

from pydantic import BaseModel

from .wire_config_sections import WIRE
from .wire_scalars import DigestText, NonceText, NonEmptyText, TimestampText


class TurnCursorWire(BaseModel):
    """The sub-game and step this message belongs to."""

    model_config = WIRE

    sub_game: int
    step: int


class MoveActionWire(BaseModel):
    """A movement: one `move_set` token, no placement target."""

    model_config = WIRE

    kind: Literal["MOVE"]
    value: NonEmptyText


class BarrierActionWire(BaseModel):
    """A police barrier placement: the exact placed cell as `[row, col]`."""

    model_config = WIRE

    kind: Literal["BARRIER"]
    value: list[int]


ActionWire = MoveActionWire | BarrierActionWire


class CommitmentWire(BaseModel):
    """`Commitment(cursor, h_commit)`."""

    model_config = WIRE

    cursor: TurnCursorWire
    h_commit: DigestText


class AcknowledgementWire(BaseModel):
    """`Acknowledgement(cursor, h_commit)` - the exact existing contract.

    Deliberately **not** a generalized ack, and it carries no `accepted` member:
    it echoes the commitment it acknowledges and nothing more.
    """

    model_config = WIRE

    cursor: TurnCursorWire
    h_commit: DigestText


class RevealWire(BaseModel):
    """`Reveal(cursor, action, hint)` plus the optional capture claim.

    No nonce: the outcome is the *operation result*, never a request member.
    `capture_claim` follows the reference's `[row, col]`; `null` means no claim.
    """

    model_config = WIRE

    cursor: TurnCursorWire
    action: ActionWire
    hint: str
    capture_claim: list[int] | None = None


class TurnOutcomeWire(BaseModel):
    """The frozen result of the operation that carried a Reveal (O5, amended).

    `accepted` is public-fact acceptance, never remote spatial legality, and the
    `capture` vocabulary is closed. PROJECT-CONTRACT: the reference answers later.
    """

    model_config = WIRE

    accepted: bool
    capture: str


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
