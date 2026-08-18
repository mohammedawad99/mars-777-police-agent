"""Our own side of one KIT sub-game: the domain, driven by the kit's cadence.

Nothing here re-implements a rule. Movement and placement go through
`LocalTurnService`, the scent recurrence is `ScentField`'s, the geometry is the
board's, and the opening position is the locked config's. What this layer owns
is **when** each of them is asked, which is the only thing the pinned wire
actually changes: one message per half-turn instead of three, and the action
disclosed at the audit rather than during play.

**The peer's smell grid stays the peer's.** It arrives as binary64 and our
physics is exact `Decimal`, and the two are `MODEL_FORM_MATCH` and **not**
vector-exact. So a peer field is folded into a belief only when every cell it
carries is representable in our own state domain, and otherwise the belief stays
`NO_SCENT` - silence rather than an equivalence we have measured and refused to
publish.

`observe_barrier` is `capture_rules.adopt_barrier`, not `place_barrier`: what a
receiver can do is record the cell the peer publicly declared blocked, because
validating the *placer's* adjacency needs a position we are not allowed to know.
"""

from dataclasses import dataclass, replace
from decimal import Decimal, InvalidOperation

from ..domain.actions import BarrierAction, PhysicalAction
from ..domain.board import Board, Position
from ..domain.negotiated_config import NegotiatedConfig
from ..domain.scent import ScentField
from ..domain.scent_belief import NO_SCENT, ScentBelief
from ..domain.scent_model import ScentModelAgreement
from ..domain.truth import LocalTruth
from .capture_rules import adopt_barrier
from .config_rules import opening_truth
from .sealed_record_values import ActorRole
from .turn_service import LocalTurnService

SmellGrid = tuple[tuple[str, float], ...]
"""`("r,c", intensity)` pairs - the pinned wire's own spelling, sorted."""


@dataclass(frozen=True, slots=True)
class KitPlayState:
    """Everything our side of one KIT sub-game authoritatively holds."""

    truth: LocalTruth
    field: ScentField
    step: int = 0
    barriers_placed: int = 0

    @classmethod
    def opening(cls, config: NegotiatedConfig, role: ActorRole) -> "KitPlayState":
        """Where this role stands before the first turn, on an empty board."""
        truth = opening_truth(config, role)
        return cls(truth, ScentField.zero(truth.board))

    def advance(
        self, action: PhysicalAction, turns: LocalTurnService, model: ScentModelAgreement
    ) -> "KitPlayState":
        """Apply one action of ours, then let the field evolve around where it left us.

        The service validates first and returns new truth only on acceptance, so
        an action our own rules refuse leaves this value untouched.
        """
        applied = turns.apply(self.truth, action)
        evolved = self.field.evolve(model.kernel, (applied.truth.own_position,), model.params)
        placed = self.barriers_placed + (1 if type(action) is BarrierAction else 0)
        return KitPlayState(applied.truth, evolved, self.step + 1, placed)

    def observe_barrier(self, target: Position | None) -> "KitPlayState":
        """Record a cell the peer publicly declared blocked. Nothing else moves."""
        if target is None:
            return self
        return replace(
            self, truth=replace(self.truth, board=adopt_barrier(self.truth.board, target))
        )

    def smell_grid(self) -> SmellGrid:
        """Our own field after this turn, in the pinned `{'r,c': number}` spelling."""
        board = self.truth.board
        base = board.start_index
        return tuple(
            (f"{base + row},{base + col}", float(value))
            for row, line in enumerate(self.field.values)
            for col, value in enumerate(line)
            if value > 0
        )


def peer_belief(grid: SmellGrid, board: Board) -> ScentBelief:
    """The peer's field as evidence, or silence when our domain cannot hold it."""
    values = [[Decimal(0)] * board.cols for _ in range(board.rows)]
    base = board.start_index
    try:
        for key, intensity in grid:
            row, col = (int(part) - base for part in key.split(","))
            values[row][col] = Decimal(str(intensity))
    except (ValueError, IndexError, InvalidOperation):
        return NO_SCENT
    try:
        observed = ScentField(board.rows, board.cols, base, tuple(tuple(one) for one in values))
    except Exception:
        return NO_SCENT
    return ScentBelief(observed, 1)


@dataclass(frozen=True, slots=True)
class PeerScent:
    """A `ScentBeliefSource` over the field the peer last sent, and nothing else.

    Already folded, because the peer sends a whole field rather than the
    emissions our own projector would fold - so the board it answers about is
    the one it was built from, and asking it about another would be a question
    it has no evidence for.
    """

    belief: ScentBelief

    def for_board(self, board: Board) -> ScentBelief:
        """The belief we folded when the peer's field arrived."""
        return self.belief
