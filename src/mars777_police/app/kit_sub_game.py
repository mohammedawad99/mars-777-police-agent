"""One KIT sub-game, played to its natural end over the symmetric-push wire.

The pinned wire is symmetric push: each peer calls the *other's* `receive_turn`
with its own half-turn, so neither side can be passive and there is no operation
that asks for the opponent's move. This loop is the consequence of that, and the
order it runs in is `reference-v3`'s own: **the thief moves first**.

Turn order is not inferred from who dialled whom. The pinned kit records what
that costs - a peer that plays police-first and one that plays thief-first each
wait for the other after a *fully successful* handshake, both time out, and each
blames the other, which is the contradictory-reports shape App. E rule 35 zeroes.

**We wait, bounded by our own budget, and only for what we are owed.** A
tolerated duplicate proves the opponent is alive and discharges nothing, so it
never renews the deadline - the inbox is what makes that true, by waking this
loop only on an authoritatively accepted message.

Nothing here decides a rule: the action is the strategy's, its legality the turn
service's, the end event `kit_adjudicate`'s, the digest the frozen codec's.
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

from ..domain.rules import Move
from ..domain.terminal import Outcome, TurnLimits
from .capture_values import CaptureAnswer
from .kit_adjudicate import KitVerdict, adjudicate, answer_claim, self_captured, terminal_owed
from .kit_half_turn import KitHalfTurnMaker
from .kit_inbox import KitTurnInbox
from .kit_messages import KitClaimResponse, KitRole, KitTurn
from .kit_play import KitPlayState, PeerScent, peer_belief
from .protocol_errors import StaleMessageError
from .turn_service import MoveAction

SendTurn = Callable[[KitTurn], Awaitable[None]]


@dataclass(slots=True)
class KitSubGame:
    """One sub-game of a fixed-role KIT friendly, from first turn to end event."""

    maker: KitHalfTurnMaker
    inbox: KitTurnInbox
    send: SendTurn
    role: KitRole
    limits: TurnLimits
    deadline: float
    state: KitPlayState
    pending: KitClaimResponse | None = field(default=None)
    peer_grid: tuple[tuple[str, float], ...] = field(default=())
    steps_seen: int = field(default=0)
    settled: bool = field(default=False)

    @property
    def moves_first(self) -> bool:
        """`reference-v3`: the thief takes the first turn of every sub-game."""
        return self.role is KitRole.THIEF

    async def play(self) -> Outcome:
        """Play until an end event, then deliver anything we still owe."""
        for _ in range(self.limits.max_moves * 2 + 2):
            if self.moves_first:
                verdict = await self._own_turn()
                if verdict.outcome is not None:
                    return await self._settle(verdict, own=True)
            verdict = await self._consume()
            if verdict.outcome is not None:
                return await self._settle(verdict, own=False)
            if not self.moves_first:
                verdict = await self._own_turn()
                # No ending is reachable from the cop's own move; kept so the loop
                # mirrors the pinned driver's shape.
                if verdict.outcome is not None:  # pragma: no cover - unreachable for the cop
                    return await self._settle(verdict, own=True)
        raise StaleMessageError(  # pragma: no cover - a valid config cannot reach it
            "the sub-game ran past twice its own step ceiling",
        )

    async def _own_turn(self) -> KitVerdict:
        """Take and send our half-turn; report an end event our own move caused."""
        if self.state.step >= self.limits.max_moves:
            return KitVerdict(None)
        half = self.maker.take(
            self.state,
            belief=PeerScent(peer_belief(self.peer_grid, self.state.truth.board)),
            answer=self.pending,
        )
        self.state, self.pending = half.state, None
        await self.send(half.message)
        return self._verdict(None, CaptureAnswer.NO_QUESTION)

    async def _consume(self) -> KitVerdict:
        """Wait for the turn we are owed, apply it, and answer what it asked."""
        try:
            applied = await self.inbox.take(self.deadline)
        except TimeoutError:
            raise StaleMessageError(
                "the opponent went silent past our own budget; no turn was ever applied"
            ) from None
        reached: list[KitVerdict] = []
        for message in applied:
            self.steps_seen = message.step
            self.state = self.state.observe_barrier(message.barrier_placed)
            self.peer_grid = message.smell_grid
            answer = answer_claim(message.capture_claim, self.state.truth.own_position)
            claim = message.capture_claim
            if claim is not None and answer is not CaptureAnswer.NO_QUESTION:
                self.pending = KitClaimResponse(claim.cell, answer is CaptureAnswer.CAUGHT)
            reached.append(self._verdict(message, answer))
        # The FIRST end event in a batch settles it; a later turn cannot un-end it.
        return next((one for one in reached if one.outcome is not None), KitVerdict(None))

    def _verdict(self, message: KitTurn | None, answer: CaptureAnswer) -> KitVerdict:
        """The end event this side may declare from what it is entitled to know."""
        return adjudicate(
            role=self.role,
            incoming=message,
            answer=answer,
            trapped=self_captured(self.state.truth.board, self.state.truth.own_position, self.role),
            step=self.state.step,
            max_steps=self.limits.max_moves,
            survival_threshold=self.limits.survival_threshold,
        )

    async def _settle(self, verdict: KitVerdict, *, own: bool) -> Outcome:
        """Deliver what we still owe **before** we stop talking, then report.

        The opponent cannot see the board. A side that walks away holding the
        answer leaves the other waiting out its budget and settling a game it
        already lost as a timeout, and two reports then describe one game
        differently - the shape App. E rule 35 zeroes on both teams.

        `own=True` with a survival verdict sends nothing, and that is not an
        omission: the survival claim already rode out on the message we just
        sent, and a second one would be a duplicate terminal.
        """
        if self.settled:
            raise StaleMessageError("this sub-game has already settled once")
        self.settled = True
        already_claimed = own and verdict.outcome is Outcome.SURVIVAL
        owed = not already_claimed and terminal_owed(
            role=self.role, pending=self.pending is not None
        )
        if owed and self.state.step < self.limits.max_moves:
            half = self.maker.take(self.state, answer=self.pending, forced=MoveAction(Move.STAY))
            self.state, self.pending = half.state, None
            await self.send(half.message)
        assert verdict.outcome is not None
        return verdict.outcome
