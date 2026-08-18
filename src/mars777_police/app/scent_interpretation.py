"""Reading the emissions a peer actually sent, into a belief a policy may use.

PRD-01 owns the scent physics and PRD-04 owns the reading of it
(`PRD04-FR-001`), so this module folds and never computes: `observed_field` is
the sole accumulated-field authority and no decay, deposit, saturation or
kernel is restated below. What is added is the *sequencing* a live game needs
and a replay does not.

**One row is one full turn.** Ch 4 decays the environment once a turn has been
completed by both actors, and `observed_field` documents its input as exactly
one opponent emission per completed full turn. The live evidence retains
precisely that - `TurnEvidence.scent` is written once per round, when the peer's
reveal arrives - so the sequence needs ordering, not regrouping. It is sorted by
step here rather than trusted to arrive sorted, because a field folded in the
wrong order is a different field and nothing else would notice.

**Only what already arrived.** The source is read at the moment of the question
rather than captured when this object was built: a decision at round `k` sees
the rows closed at rounds `1…k-1`, because `SeriesDriver` calls `close_turn`
after `play_round` returns and the decision is the first statement inside it.
The turn being decided is structurally invisible, and so is the next sub-game -
each one gets a fresh `AuditRuntime`, so `g01`'s field cannot reach `g02`.

**The locked model, never a default.** The parameters are the ones the peers
agreed and authenticated before the series (`SCENT-001`, C-14/JDEC-017), passed
in by the composition that holds them. Reading a project default here would let
two peers believe different things about the same evidence.

Nothing here reads a position, a role, a nonce, a digest or a disclosure. The
final audit verifies these same emissions later against a reconstructed
trajectory; that is a different question asked with information a live decision
does not have, and this module never waits for it.
"""

from collections.abc import Callable
from dataclasses import dataclass

from ..domain.board import Board
from ..domain.config_model import ScentParams
from ..domain.scent_belief import NO_SCENT, ScentBelief
from ..domain.scent_observation import observed_field
from .scent_records import ScentRecord

ScentHistorySource = Callable[[], tuple[ScentRecord, ...]]
"""How the live rows are reached, without naming the runtime that holds them."""


def interpret_scent(
    board: Board, history: tuple[ScentRecord, ...], params: ScentParams
) -> ScentBelief:
    """Fold *history* into the belief it implies under the locked *params*.

    An empty history is the neutral belief rather than an empty field, so the
    no-evidence case is one value everywhere instead of one per board.
    """
    if not history:
        return NO_SCENT
    ordered = sorted(history, key=lambda record: record.cursor.step)
    emissions = tuple(record.emission for record in ordered)
    return ScentBelief(observed_field(board, emissions, params), len(emissions))


@dataclass(frozen=True, slots=True)
class LiveScentBelief:
    """The running game's answer to "what has the opponent's scent shown us?"

    It holds a way to *ask* rather than an answer: a belief captured when this
    object was built would freeze the opening view for the whole sub-game.
    """

    history: ScentHistorySource
    params: ScentParams

    def for_board(self, board: Board) -> ScentBelief:
        """The belief on *board* from every peer emission received so far."""
        return interpret_scent(board, self.history(), self.params)
