"""The four KIT wire messages as semantic values, framework-free.

The pinned kit's transport surface (`ad65576`, `vectors/turn_message.json`,
status **PROMOTED**) is de-facto interoperability practice, not book law: the
course book stays supreme and nothing here relaxes a binding rule.

**A KIT turn is not our turn.** It carries the sealed `commit` *and* the
unsealed adjuncts - hint, smell grid, claims - in one message, and never the
action: under that wire the action is disclosed only in the end-of-sub-game
audit. So the commitment half maps exactly onto our `Commitment`, and the
adjuncts are kept here beside it rather than folded into a `Reveal` we would
have had to invent an action for.

**The smell grid stays the peer's.** It arrives as binary64 and is retained as
binary64. Our own physics is exact `Decimal`; converting the peer's cells here
would silently assert an equivalence that is `MODEL_FORM_MATCH` and **not**
vector-exact, which is precisely the claim the scent audit refuses to make.

`sender` is `police`/`thief` - the kit's spelling, never our `ActorRole` tokens.
"""

from dataclasses import dataclass
from enum import StrEnum

from ..domain.board import Position
from .capture_values import CaptureClaim
from .kit_payload import PeerPayload
from .peer_turn_messages import Commitment
from .protocol_values import Sha256Digest
from .turn_cursor import TurnCursor


class KitRole(StrEnum):
    """The kit's two `sender` words (`rules/outcome.Role`)."""

    POLICE = "police"
    THIEF = "thief"


class KitControlKind(StrEnum):
    """The complete pinned control vocabulary (`proto/messages.ControlMessage`).

    The channel touches no game state and is never sealed or scored, so nothing
    here reaches a runtime: answering is conformant, and a command outside these
    four words is refused rather than guessed at.
    """

    ENABLE = "enable"
    STATUS = "status"
    RESTART = "restart"
    QUIT = "quit"


class KitResultClaim(StrEnum):
    """What a peer says its sub-game ended as (`rules/outcome.Outcome`).

    Five members, not the three the vector's field note names: the pinned driver
    calls `send_audit(outcome.value)` with whatever `_play_one` returned, so a
    lawful peer can claim a technical loss or a tamper forfeit. Refusing those
    would refuse an honest opponent. The claim is never the settlement - the
    opponent's audit decides, exactly as the pinned note says.
    """

    CAPTURE = "capture"
    SURVIVAL = "survival"
    TIMEOUT = "timeout"
    TECHNICAL_LOSS = "technical_loss"
    TAMPER_FORFEIT = "tamper_forfeit"

    SERIES_CONSENSUS = "series_consensus"
    """Not a sub-game outcome at all: the peer's digest of the settled series.

    It arrives once, after the last sub-game is disclosed, carries no records and
    settles nothing about any single game. Refusing it as malformed - which is
    what an outcome-only enum does - leaves the final exchange of a counted
    series unanswered, and a series with no mutual settlement is scored 0 for
    both groups.
    """


@dataclass(frozen=True, slots=True)
class KitClaimResponse:
    """The thief's obligatory honest answer: `{'claim': [r, c], 'caught': bool}`."""

    claim: Position
    caught: bool


@dataclass(frozen=True, slots=True)
class KitTurn:
    """One half-turn on the pinned wire, as a value our own layers can hold."""

    step: int
    sender: KitRole
    hint: str
    smell_grid: tuple[tuple[str, float], ...]
    commit: Sha256Digest
    timestamp: str
    barrier_placed: Position | None = None
    capture_claim: CaptureClaim | None = None
    claim_response: KitClaimResponse | None = None
    survival_claimed: bool = False

    def commitment(self, sub_game: int) -> Commitment:
        """The sealed half, joined to the sub-game the handshake established.

        A kit turn numbers only its own chain, so the sub-game is context and
        never wire: reading one out of the message would let a peer renumber a
        series it does not own.
        """
        return Commitment(TurnCursor(sub_game, self.step), self.commit)


@dataclass(frozen=True, slots=True)
class KitRecord:
    """One revealed record: the payload it sealed, its nonce, and its digest."""

    payload: PeerPayload
    nonce: str
    commit: Sha256Digest


@dataclass(frozen=True, slots=True)
class KitAuditReveal:
    """A sub-game's chain with its nonces, or the series settlement digest.

    One shape for both because the peer sends both through `submit_audit`. The
    two are told apart by the claim and never by the record count: an empty
    chain is a legitimate sub-game disclosure to *refuse*, while a series
    settlement is a different kind of message that happens to carry none.
    """

    sender: KitRole
    records: tuple[KitRecord, ...]
    result_claim: KitResultClaim
    consensus_sha: str | None = None

    @property
    def settles_the_series(self) -> bool:
        """Whether this disclosure ends the series rather than one sub-game."""
        return self.result_claim is KitResultClaim.SERIES_CONSENSUS


@dataclass(frozen=True, slots=True)
class KitControl:
    """A status signal. It carries no game state and settles nothing."""

    kind: KitControlKind
    sender: KitRole
    sub_game_number: int = 1
    status: str = ""
    step_budget: float = 0.0
    payload: PeerPayload | None = None
