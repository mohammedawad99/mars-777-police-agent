"""Two role backends, one group series: the contribution shape and the merge.

Police and Thief play different sub-games of the **same** series, in different
processes and different repositories, so the only way they meet is after the
fact. Each writes what it witnessed; a collector merges them into one series.

**A contribution carries settled facts and immutable references, never live
game state.** No board, no position, no barrier set, no nonce - those belonged
to the process that owned them, and a merge is not a place to resurrect them.

**One identity, or a refusal.** Every contribution names the series it played;
if two disagree they are two series, and a merge that quietly picked one would
turn a real defect into a plausible-looking file.
"""

from ..domain.terminal import Outcome
from .artifact_store import ArtifactDocument, require_game_id
from .friendly_evidence import (
    ABSENT,
    EVIDENCE_CLASS,
    FRIENDLY_PREFIX,
    SERIES_LENGTH,
    sub_game_document,
)
from .friendly_evidence_values import FriendlySubGameEvidence
from .interop_profiles import SeriesConvention
from .kit_messages import KitRole
from .protocol_errors import LocalDefectError
from .run_class import RunClassification
from .series_record import cumulative_of, outcome_line


def friendly_contribution_name(game_id: str, role: KitRole) -> str:
    """`friendly_<game_id>_<role>.json` - one per role backend, written by it."""
    return f"{FRIENDLY_PREFIX}_{require_game_id(game_id)}_{role.value}.json"


def contribution_document(
    *,
    role: KitRole,
    game_id: str,
    game_uid: str,
    our_group: str,
    peer_group: str,
    rows: tuple[FriendlySubGameEvidence, ...],
) -> ArtifactDocument:
    """One role backend's own rows, in a role-neutral shape the collector merges.

    Settled facts and immutable references only. A contribution deliberately
    cannot carry a board, a position, a barrier set or a nonce: those are live
    game state, they belong to the process that owned them, and a merge is not
    a place to resurrect them.
    """
    return {
        "evidence_class": EVIDENCE_CLASS,
        "role": role.value,
        "game_id": game_id,
        "game_uid": game_uid,
        "group_id": our_group,
        "opponent_group_id": peer_group,
        "sub_games": [sub_game_document(one) for one in rows],
    }


def merge_contributions(
    contributions: tuple[ArtifactDocument, ...], classification: RunClassification
) -> ArtifactDocument:
    """One group series from the role backends that played it, or a refusal.

    Police and Thief are **role contributors to one series**, never two series.
    So the identity every contribution names must be the same identity, and the
    six sub-games must be there exactly once each.
    """
    identity = {key: {one[key] for one in contributions} for key in _IDENTITY}
    disagreed = sorted(key for key, values in identity.items() if len(values) != 1)
    if disagreed:
        raise LocalDefectError(
            f"role contributions disagree on {disagreed}; one group series has one identity",
        )
    rows: list[ArtifactDocument] = []
    for one in contributions:
        rows.extend(one["sub_games"])  # type: ignore[arg-type]
    rows.sort(key=_number)
    played = tuple(_number(entry) for entry in rows)
    if played != tuple(range(1, SERIES_LENGTH + 1)):
        raise LocalDefectError(
            f"a merged development series needs sub-games 1..{SERIES_LENGTH}; got {played}",
        )
    first = contributions[0]
    totals = cumulative_of(
        tuple(outcome_line(_number(e), Outcome(str(e["outcome"]))) for e in rows)
    )
    return {
        "evidence_class": EVIDENCE_CLASS,
        "counted_eligible": classification.counted_capable,
        "keyed_step0_authentication": ABSENT,
        "mutual_result_agreement": ABSENT,
        "kit_terms_agreement": classification.kit_terms_agreement,
        "game_id": first["game_id"],
        "game_uid": first["game_uid"],
        "group_id": first["group_id"],
        "opponent_group_id": first["opponent_group_id"],
        "series_convention": SeriesConvention.REFERENCE_ODD_EVEN_ALTERNATION.value,
        "schedule": [str(entry["role"]) for entry in rows],
        "role_totals": {"cop": totals.cop_total, "thief": totals.thief_total},
        "sub_games": rows,
    }


def _number(row: ArtifactDocument) -> int:
    """One row's sub-game number, read as the integer the contribution wrote."""
    return int(str(row["sub_game"]))


_IDENTITY = ("game_id", "game_uid", "group_id", "opponent_group_id")
"""The four values every role contribution of one series must agree on."""
