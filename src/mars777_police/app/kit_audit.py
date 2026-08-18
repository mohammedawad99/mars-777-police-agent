"""Auditing an external peer: what its bytes prove, and what they leave open.

The pinned kit standardises **cryptographic correspondence**, not payload
meaning - peers need not seal the same keys, and each side re-hashes what the
other revealed. So a KIT peer's chain can verify perfectly while telling us
almost nothing about whether it played legally, and pretending otherwise would
be the whole failure this module exists to avoid.

**Gate 1** recomputes the digest under the frozen codec. It interprets nothing:
whether the bytes correspond is a cryptographic question, and a faithfully
sealed illegal move passes it.

**Gate 2** weighs semantic evidence and answers with four values rather than
two. `NOT_CHECKABLE` sits between them and is the point of the design: a peer
that sealed a leaner record has not proved it played legally, so recording that
as `VERIFIED` would score it as if it had - and it has not been caught doing
anything either, so recording it as `FAILED` would accuse an honest opponent of
cheating for using a lawful schema.

**We never ask a peer for a fact we already own.** The role comes from the
authenticated session direction, the cursor from the turn we witnessed, the
configuration from the verified lock, and the public barriers from the
placements we saw declared. Where a payload happens to carry one of those, it
is *cross-checked* - a contradiction is a finding - but its absence costs
nothing, because the peer never agreed to repeat what we already know.

Nothing here reads a hint for meaning. Intent is a sealed classification with
exactly two lawful words (C-08); inferring it from the language of a hint would
invent evidence and would punish deception the rules permit.
"""

from dataclasses import dataclass

from ..protocol.commitment_codec import verify_commitment
from .audit_policy import CheckOutcome
from .audit_status import CheckProvenance, CheckStatus
from .commitment_codecs import CommitmentCodec
from .kit_payload import PeerPayload
from .sealed_record_values import ActorRole, Intent
from .turn_cursor import TurnCursor

_BINDING = CheckProvenance.SOURCE_BINDING
_INTENT_WORDS = frozenset(one.value for one in Intent)


@dataclass(frozen=True, slots=True)
class ExternalTurn:
    """One peer turn as an external profile delivers it, with what we witnessed."""

    cursor: TurnCursor
    role: ActorRole
    payload: PeerPayload
    nonce: str
    commit: str


def crypto_gate(turn: ExternalTurn, codec: CommitmentCodec) -> CheckStatus:
    """Whether the revealed payload really produces the commitment we hold."""
    if verify_commitment(codec, turn.payload.value, turn.nonce, turn.commit):
        return CheckStatus.VERIFIED
    return CheckStatus.FAILED


def _context_check(found: object, known: object) -> CheckStatus:
    """Cross-check a fact we own outright: absence loses us nothing.

    Deliberately not the same rule as an *optional* field would need. Role, step
    and sub-game are established by the authenticated session and the turn we
    witnessed, so a payload that omits them has withheld nothing - only a
    payload that *contradicts* them has said something we can act on.
    """
    if found is None:
        return CheckStatus.VERIFIED
    return CheckStatus.VERIFIED if found == known else CheckStatus.FAILED


def _intent_status(payload: PeerPayload) -> CheckStatus:
    """Two lawful words, or nothing. Never inferred from the hint."""
    found = payload.text("intent")
    if found is None:
        return CheckStatus.NOT_CHECKABLE
    return CheckStatus.VERIFIED if found in _INTENT_WORDS else CheckStatus.FAILED


def semantic_checks(turn: ExternalTurn, witnessed: TurnCursor) -> tuple[CheckOutcome, ...]:
    """What the peer's disclosed payload does and does not establish."""
    payload = turn.payload
    return (
        CheckOutcome("role", _BINDING, _context_check(payload.text("role"), turn.role.value)),
        CheckOutcome("step", _BINDING, _context_check(payload.whole("step"), witnessed.step)),
        CheckOutcome(
            "sub_game", _BINDING, _context_check(payload.whole("sub_game"), witnessed.sub_game)
        ),
        CheckOutcome("intent", _BINDING, _intent_status(payload)),
    )
