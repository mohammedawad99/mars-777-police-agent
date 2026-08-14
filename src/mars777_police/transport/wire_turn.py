"""Wire DTOs for the three turn families and the result of a revealed turn.

`Reveal` carries the cursor, the action and the hint - **and no nonce**: Ch 5
§5.3.2 withholds it until final audit, so a nonce member here would break
commit-reveal itself, and nonces travel exactly once in `final_nonce_reveal`. The
action is a tagged union with the sealed record's two-key shape, so a movement
token and a barrier cell are never told apart by guessing.
"""

from typing import Literal

from pydantic import BaseModel

from .wire_config_sections import WIRE
from .wire_scalars import DigestText, NonEmptyText
from .wire_scent_turn import ScentEmissionWire


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
    """`Reveal(cursor, action, hint)` plus the two unsealed adjuncts.

    No nonce: the outcome is the *operation result*, never a request member.
    `capture_claim` follows the reference's `[row, col]`; `null` means no claim.
    `scent_emission` is `null` before `..._SCENT_V2` and present under it - which
    is legal is the runtime's decision, not this schema's.
    """

    model_config = WIRE

    cursor: TurnCursorWire
    action: ActionWire
    hint: str
    capture_claim: list[int] | None = None
    scent_emission: ScentEmissionWire | None = None


class TurnOutcomeWire(BaseModel):
    """The frozen result of the operation that carried a Reveal (O5, amended).

    `accepted` is public-fact acceptance, never remote spatial legality, and the
    `capture` vocabulary is closed. PROJECT-CONTRACT: the reference answers later.
    """

    model_config = WIRE

    accepted: bool
    capture: str
