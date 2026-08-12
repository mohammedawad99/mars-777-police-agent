"""Observing a peer's reveal: what we accept, and what we answer about capture.

Split out of `TurnProtocolRuntime` so the runtime keeps sequencing and this
keeps judgement. Both halves are small on purpose - the runtime decides *when* a
reveal may be observed, and this decides *what* we can honestly say about one.

Nothing here reaches for the mover's hidden state: `accepted` covers public
facts, and the capture answer comes from our own position through
`capture_rules`.
"""

from collections.abc import Callable
from dataclasses import replace

from ..domain.actions import BarrierAction
from ..domain.truth import LocalTruth
from .capture_rules import adopt_barrier, answer_for_barrier, answer_for_claim
from .capture_values import CaptureAnswer, TurnOutcome
from .peer_turn_messages import Reveal
from .sealed_record_values import ActorRole


def require_claim_shape(
    reveal: Reveal, peer_role: ActorRole, refuse: Callable[[str], Exception]
) -> None:
    """Only the police may declare a capture, and never alongside a barrier."""
    if reveal.capture_claim is None:
        return
    if peer_role is not ActorRole.POLICE:
        raise refuse("only the police may declare a capture")
    if isinstance(reveal.action, BarrierAction):
        raise refuse("a barrier declares its own target; it carries no capture claim")


def observe_reveal(reveal: Reveal, truth: LocalTruth) -> tuple[TurnOutcome, LocalTruth]:
    """Return what we report for *reveal*, and the truth after adopting it.

    Only a public barrier changes anything of ours, and only its board: their
    movement is theirs, so our own position is returned untouched.
    """
    action, here = reveal.action, truth.own_position
    if isinstance(action, BarrierAction):
        target = action.target
        if not truth.board.contains(target) or truth.board.is_blocked(target):
            return TurnOutcome(False, CaptureAnswer.NO_QUESTION), truth
        answer = answer_for_barrier(truth.board, target, here)
        return TurnOutcome(True, answer), replace(truth, board=adopt_barrier(truth.board, target))
    claim = reveal.capture_claim
    if claim is None:
        return TurnOutcome(True, CaptureAnswer.NO_QUESTION), truth
    return TurnOutcome(True, answer_for_claim(claim, here)), truth
