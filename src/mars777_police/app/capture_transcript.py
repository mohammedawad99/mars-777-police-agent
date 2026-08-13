"""What each side observed a turn ask and answer about capture.

`capture_claim` and `CaptureAnswer` are **not** members of `H_commit` - they are
live interaction facts, not sealed ones - so nothing stops a peer from disclosing
a different story at the final audit than the one it actually told. That is
exactly what this exists to prevent: each side keeps the rows it really observed
during the authenticated session, and the peer's disclosure is compared against
them row for row.

**One row per semantic turn outcome, including the boring ones.** An ordinary
turn records `NO_QUESTION`; omitting it would let a peer make a whole
interaction disappear and call the transcript complete.

**A row carries only what both sides can compare**: the cursor it belongs to,
the claim (or its absence) and the answer. The action, the sender's role and the
sealed members are already authoritative elsewhere, and no position, nonce or
verdict is ever written here.
"""

from dataclasses import dataclass, field

from .capture_values import CaptureAnswer, CaptureClaim, TurnOutcome
from .peer_turn_messages import Reveal
from .protocol_errors import StaleMessageError
from .turn_cursor import TurnCursor


class TranscriptMismatchError(StaleMessageError):
    """A disclosed transcript is not what the live session actually produced.

    A peer-protocol failure, not a local one: the side that sent the document
    is the side that contradicted itself, so it leaves by the existing
    `E-PROTO-STALE` identity - the same one a disclosed log that does not match
    the played turns already uses. No new error identity exists for this.
    """


@dataclass(frozen=True, slots=True)
class CaptureRecord:
    """One turn's capture question and its answer, as it really happened.

    The guards below are about *our* construction of a row: a peer's JSON is
    already typed by `audit_capture` before it reaches here, so a bad value at
    this point is a local defect and raises the plain `ValueError` that is.
    """

    cursor: TurnCursor
    claim: CaptureClaim | None
    answer: CaptureAnswer

    def __post_init__(self) -> None:
        if type(self.cursor) is not TurnCursor:
            raise ValueError(
                f"a capture record needs a TurnCursor, got {type(self.cursor).__name__}",
            )
        if self.claim is not None and type(self.claim) is not CaptureClaim:
            raise ValueError(
                f"claim must be a CaptureClaim, got {type(self.claim).__name__}",
            )
        if not isinstance(self.answer, CaptureAnswer):
            raise ValueError(
                f"answer must be a CaptureAnswer, got {type(self.answer).__name__}",
            )


@dataclass(slots=True)
class TurnTranscript:
    """One live turn's capture rows, kept apart in the two directions.

    They are not interchangeable. `inbound` is what we were asked and what *we*
    answered - the rows the peer must disclose unchanged. `outbound` is what we
    asked and what the peer answered, which is what our own disclosure carries
    for the peer to check in turn. Merging them would let one side's story stand
    in for the other's, which is the whole thing being prevented.
    """

    inbound: tuple[CaptureRecord, ...] = field(default=())
    outbound: tuple[CaptureRecord, ...] = field(default=())
    declared: bool = field(default=False)

    def observe_inbound(self, reveal: Reveal, outcome: TurnOutcome) -> None:
        """Retain the answer we just gave to the peer's reveal."""
        self.inbound += (CaptureRecord(reveal.cursor, reveal.capture_claim, outcome.capture),)
        self.declared = self.declared or reveal.capture_claim is not None

    def observe_outgoing(self, reveal: Reveal, outcome: TurnOutcome) -> None:
        """Retain the answer the peer gave to our reveal, once it really arrived."""
        self.outbound += (CaptureRecord(reveal.cursor, reveal.capture_claim, outcome.capture),)
        self.declared = self.declared or reveal.capture_claim is not None


def require_same_transcript(
    observed: tuple[CaptureRecord, ...], disclosed: tuple[CaptureRecord, ...]
) -> None:
    """Refuse a disclosure that differs from what we watched happen.

    Compared as an ordered sequence, so an added row, a removed row, a duplicate,
    a reordering, a changed cursor, a claim that appeared or vanished and a
    rewritten answer are all the same kind of failure: the peer is telling the
    audit something other than what it told us.
    """
    if len(observed) != len(disclosed):
        raise TranscriptMismatchError(
            f"the disclosed capture transcript has {len(disclosed)} rows,"
            f" but {len(observed)} turns were actually answered",
        )
    for seen, told in zip(observed, disclosed, strict=True):
        if seen != told:
            raise TranscriptMismatchError(
                f"the disclosed capture row for {told.cursor} is not the one observed",
            )
