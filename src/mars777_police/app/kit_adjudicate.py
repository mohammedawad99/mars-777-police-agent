"""Deciding a KIT sub-game from what this side is entitled to know.

The pinned wire hides positions, so the two roles reach the same end event by
completely different routes, and the order below is the kit's own.

Note how little the **cop** can decide on its own: it cannot see the thief, so
every terminal condition reaches it as something the thief *said* - an answered
capture claim, a concession, or a survival claim. The **thief** by contrast sees
its own capture directly, because a barrier on its cell or the absence of any
orthogonal escape are facts about a position it owns.

Survival is **claimed, not inferred**: the cop cannot count the thief's steps for
it, so a thief that reaches the threshold and says nothing leaves the cop waiting
for a turn that never comes. That is why the thief's own ceiling appears here as
a terminal of its own, and the cop's does not.

Every rule is the domain's underneath. `is_trapped` owns GAME-005 including the
edge-counts-as-a-barrier reading, `answer_for_claim` owns the same-cell answer,
and nothing here re-derives either.
"""

from dataclasses import dataclass

from ..domain.board import Board, Position
from ..domain.terminal import Outcome, is_trapped
from .capture_rules import answer_for_claim
from .capture_values import CaptureAnswer, CaptureClaim
from .kit_messages import KitRole, KitTurn


def self_captured(board: Board, own_position: Position, role: KitRole) -> bool:
    """Whether our own cell says the game ended here - rules 46/47, **thief only**.

    A barrier standing on the cell we occupy, or no traversable neighbour at
    all. Both are endings **only the thief can see**, which is exactly why they
    have to be said out loud rather than waited out by an opponent who cannot
    see them.

    The role argument is not decoration and it is the fix for a real divergence.
    `BAR-004` lets the **police** place a barrier on its own cell and legally
    stand on a blocked one, so applying this rule to the police manufactures a
    capture out of a lawful placement - which is exactly what made us settle
    `CAPTURE` against a peer that settled `timeout` on 2026-08-18.
    """
    if role is not KitRole.THIEF or not board.contains(own_position):
        return False
    return own_position in board.blocked or is_trapped(board, own_position)


def terminal_owed(*, role: KitRole, pending: bool) -> bool:
    """Whether a final message still has to ride out before we stop talking.

    The pinned driver sends what it owes **before** returning a terminal
    verdict, and for one reason: the opponent cannot see the board, so a side
    that walks away holding the answer leaves the other waiting out its budget
    and settling a game it already lost as a timeout - both reports then
    disagree, which App. E rule 35 zeroes on both teams.

    An answer we owe is owed by whoever owes it. Everything else on this list is
    the thief's: a concession names a cell only the thief can see, and a
    survival claim is a fact only the thief can count.
    """
    return pending or role is KitRole.THIEF


def answer_claim(claim: CaptureClaim | None, own_position: Position) -> CaptureAnswer:
    """Our honest answer to the cop's declared cell, from our own truth.

    Answering truthfully is required (App. E rules 21-22) and is also the
    cheapest move available: our own sealed records carry our position, so a
    denial is contradicted by our own revealed log at the audit.
    """
    if claim is None:
        return CaptureAnswer.NO_QUESTION
    return answer_for_claim(claim, own_position)


@dataclass(frozen=True, slots=True)
class KitVerdict:
    """The end event this side reached, and why - or `None` while play continues."""

    outcome: Outcome | None
    reason: str = ""


def adjudicate(
    *,
    role: KitRole,
    incoming: KitTurn | None,
    answer: CaptureAnswer,
    trapped: bool,
    step: int,
    max_steps: int,
    survival_threshold: int,
) -> KitVerdict:
    """The pinned order, decided only from what this side may know."""
    if trapped:
        return KitVerdict(Outcome.CAPTURE, "our own cell is an ending only we can see")
    if answer is CaptureAnswer.CAUGHT:
        return KitVerdict(Outcome.CAPTURE, "we answered the cop's claim truthfully: caught")
    if incoming is not None:
        response = incoming.claim_response
        if response is not None and response.caught:
            return KitVerdict(Outcome.CAPTURE, "the thief answered or conceded a capture")
        if incoming.survival_claimed:
            return KitVerdict(Outcome.SURVIVAL, "the thief claimed the survival threshold")
    if role is KitRole.THIEF and step >= survival_threshold:
        return KitVerdict(Outcome.SURVIVAL, "we reached the survival threshold")
    if role is KitRole.THIEF and step >= max_steps:
        return KitVerdict(Outcome.SURVIVAL, "the step ceiling ended the sub-game uncaught")
    return KitVerdict(None)
