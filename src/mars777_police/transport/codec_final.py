"""Codec for the two end-of-series families.

Split from `codec_turn` by lifecycle: the per-turn exchange there, the
end-of-sub-game nonce disclosure and the series-closing result agreement here.

The nonces travel exactly once, in this module - `Reveal` withholds them until
final audit. `ResultAgreement` carries no `result_sha256`: the common digest is
the operation's *response*, not a member of the request.
"""

from ..app.artifact_values import GitCommitSha, UtcTimestamp
from ..app.peer_final_messages import FinalNonceReveal, NonceRevealEntry, ResultAgreement
from ..app.protocol_values import NonceValue
from ..app.result_values import ResultContribution, ResultContributionEntry
from ..app.turn_cursor import TurnCursor
from .wire_final import (
    FinalNonceRevealWire,
    NonceRevealEntryWire,
    ResultAgreementWire,
    ResultContributionEntryWire,
    ResultContributionWire,
)
from .wire_turn import (
    TurnCursorWire,
)


def _cursor(wire: TurnCursorWire) -> TurnCursor:
    return TurnCursor(wire.sub_game, wire.step)


def _cursor_wire(cursor: TurnCursor) -> TurnCursorWire:
    return TurnCursorWire(sub_game=cursor.sub_game, step=cursor.step)


def decode_final_nonce(wire: FinalNonceRevealWire) -> FinalNonceReveal:
    """Rebuild the batched nonce disclosure."""
    return FinalNonceReveal(
        tuple(
            NonceRevealEntry(_cursor(entry.cursor), NonceValue(entry.nonce))
            for entry in wire.entries
        )
    )


def encode_final_nonce(value: FinalNonceReveal) -> FinalNonceRevealWire:
    """Render the batched nonce disclosure."""
    return FinalNonceRevealWire(
        entries=[
            NonceRevealEntryWire(cursor=_cursor_wire(entry.cursor), nonce=entry.nonce.value)
            for entry in value.entries
        ]
    )


def decode_result_agreement(wire: ResultAgreementWire) -> ResultAgreement:
    """Rebuild the result agreement; the digest is the response, not a member."""
    return ResultAgreement(
        wire.game_id,
        wire.game_uid,
        wire.declaration_ref,
        UtcTimestamp(wire.timestamp),
        ResultContribution(
            wire.contribution.group_id,
            tuple(
                ResultContributionEntry(
                    entry.sub_game, GitCommitSha(entry.github_commit), entry.tokens
                )
                for entry in wire.contribution.entries
            ),
        ),
    )


def encode_result_agreement(value: ResultAgreement) -> ResultAgreementWire:
    """Render the result agreement."""
    return ResultAgreementWire(
        game_id=value.game_id,
        game_uid=value.game_uid,
        declaration_ref=value.declaration_ref,
        timestamp=value.timestamp.value,
        contribution=ResultContributionWire(
            group_id=value.contribution.group_id,
            entries=[
                ResultContributionEntryWire(
                    sub_game=entry.sub_game,
                    github_commit=entry.github_commit.value,
                    tokens=entry.tokens,
                )
                for entry in value.contribution.entries
            ],
        ),
    )
