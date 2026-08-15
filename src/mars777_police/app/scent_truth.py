"""Whether the scent a reveal carried is the scent its own action produces.

Parts 1A and 1B proved the peer told the audit and the log what it told us live.
A peer that lied *live* and then disclosed that lie faithfully passes both, so
neither answers the physical question - and Ch 4 §4.4 assumes it never has to be
asked, because in the book's shared environment the movement mechanism emits the
map itself. Two isolated peers share no environment (C-14 / JDEC-017), so the
emission travels, and the premise has to be enforced rather than assumed.

`JDEC-018` is that enforcement, and its whole correctness rests on where the
expected emission comes from. Every input is anchored independently of the
emission being judged: the cell from the trajectory `Replay` rebuilt out of the
config-locked start cells and the sealed actions, the board from the same replay,
and the model from the series lock. Reading the centre out of the scent would
prove only that the scent equals itself.

**Not tampering.** A wrong emission is a truthful record of impossible play -
every hash can verify - so the finding is scored, never disqualifying.
"""

from ..domain.scent_model import ScentModelAgreement
from ..domain.scent_observation import emission_of
from .scent_records import ScentRecord
from .sealed_record_values import ActorRole
from .semantic_replay import PlayedTurn, Replay
from .semantic_values import CONSISTENT, SemanticFinding, SemanticVerdict

ScentHistory = dict[tuple[int, ActorRole], ScentRecord]
"""The retained emissions of both sides, addressed by the turn that made them."""


def history_of(
    ours: tuple[ScentRecord, ...],
    own_role: ActorRole,
    theirs: tuple[ScentRecord, ...],
    peer_role: ActorRole,
) -> ScentHistory:
    """Both directions' retained scent, keyed by the reveal each row belongs to.

    Ours came from the transcript that watched us send it and theirs from the
    evidence that watched it arrive; neither is recomputed here, because what
    this module checks is exactly whether those retained values are possible.
    """
    rows: ScentHistory = {(row.cursor.step, own_role): row for row in ours}
    rows.update({(row.cursor.step, peer_role): row for row in theirs})
    return rows


def require_truthful_scent(
    replay: Replay,
    played: tuple[PlayedTurn, ...],
    history: ScentHistory,
    model: ScentModelAgreement,
) -> SemanticFinding:
    """Refuse a reveal whose emission its own disclosed action cannot produce.

    Called while the step is still un-applied, which is what makes the board
    correct: each emitter is judged on the world **it** had - the board it began
    the step with plus its own placement, never the opponent's same-step one,
    because both commitments were sealed before either reveal.

    A turn with no retained emission is a pre-V2 reveal and is not judged here;
    whether a counted turn is allowed to have none is Part 1A/1B's question.
    """
    for turn in played:
        retained = history.get((turn.step, turn.role))
        if retained is None:
            continue
        expected = emission_of(
            replay.board_after(turn), model.kernel, replay.cell_after(turn), model.params
        )
        if retained.emission != expected:
            return SemanticFinding(SemanticVerdict.DISHONEST_SCENT_EMISSION, turn.step, turn.role)
    return CONSISTENT
