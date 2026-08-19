"""What a development friendly may truthfully persist, and what it must not claim.

A KIT friendly establishes real facts - six settled sub-games, chains that
reproduce in both directions, one series identity - and two **absences** just as
firmly. Keyed Step-0 authentication never happened, because the pinned peer
offers an unkeyed content agreement and nothing else; and no mutual result
agreement happened, because the pinned four-tool wire has no operation that
could perform one - the kit writes its own result artifact unilaterally.

So this evidence is written under its own names, into its own root, and names
both absences out loud rather than leaving them to be inferred from silence.

**The official counted writers are untouched.** They still refuse a declaration
without an authenticated peer, a config without a verified lock and a result
without an agreement - which is why a friendly cannot produce them, and why
reaching for fourteen files would have meant fabricating the preconditions those
files exist to record. Truth outranks the file count.

**No second result engine.** The scores are `outcome_line`'s and the totals are
`cumulative_of`'s - the counted path's own authorities. A *group* total under
alternation is a number no contract fixes, so none is published: the rows say
which side we played."""

from dataclasses import dataclass
from string import ascii_letters, digits

from .artifact_store import (
    ArtifactDocument,
    ArtifactStorePort,
    InvalidArtifactNameError,
    StoredArtifact,
)
from .friendly_evidence_values import FriendlySeriesEvidence, FriendlySubGameEvidence
from .interop_profiles import SeriesConvention
from .protocol_errors import LocalDefectError
from .series_record import cumulative_of, outcome_line

EVIDENCE_CLASS = "DEVELOPMENT_EVIDENCE"
"""The one local classification. It is never sent to a peer."""

ABSENT = "ABSENT"
"""Said out loud: a missing key reads as an oversight, and this is not one."""

FRIENDLY_PREFIX = "friendly"
"""Every development filename starts here, so no counted name can be produced."""

SERIES_LENGTH = 6

_DEVELOPMENT_SAFE = frozenset(ascii_letters + digits + "-_.")
"""Filesystem-safe, and deliberately **not** the counted rule.

`require_game_id` demands lowercase `[a-z0-9-]`, and the kit derives `game_id`
as `"-vs-".join(sorted(pair))` - so our own case-sensitive `MaRs-777` produces a
KIT `game_id` the counted namer refuses. That rule is the official contract's
and is left exactly where it is; this checks its own names instead."""


def require_development_id(game_id: str) -> str:
    """Return *game_id* once it is safe in a filename, or refuse it."""
    if not game_id or not _DEVELOPMENT_SAFE.issuperset(game_id) or game_id.startswith("."):
        raise InvalidArtifactNameError(f"{game_id!r} is not a safe development identifier")
    return game_id


def friendly_series_name(game_id: str) -> str:
    """`friendly_<game_id>.json` - one per development series."""
    return f"{FRIENDLY_PREFIX}_{require_development_id(game_id)}.json"


def friendly_sub_game_name(game_id: str, sub_game: int) -> str:
    """`friendly_<game_id>_gNN.json` - one per sub-game actually played."""
    return f"{FRIENDLY_PREFIX}_{require_development_id(game_id)}_g{sub_game:02d}.json"


def sub_game_document(row: FriendlySubGameEvidence) -> ArtifactDocument:
    """One sub-game's development record."""
    line = outcome_line(row.sub_game, row.outcome)
    return {
        "evidence_class": EVIDENCE_CLASS,
        "sub_game": row.sub_game,
        "role": row.role.value,
        "outcome": row.outcome.value,
        "steps": row.steps,
        "cop_score": line.cop_score,
        "thief_score": line.thief_score,
        "our_commits": list(row.our_commits),
        "peer_records": row.peer_records,
        "peer_result_claim": row.peer_result_claim,
        "peer_chain_reproduces": row.peer_chain_verified,
        "semantic_statuses": dict(row.semantic_statuses),
    }


def series_document(evidence: FriendlySeriesEvidence) -> ArtifactDocument:
    """The whole development series, with both absences stated."""
    played = tuple(row.sub_game for row in evidence.rows)
    if played != tuple(range(1, SERIES_LENGTH + 1)):
        raise LocalDefectError(
            f"development evidence records a whole series; got sub-games {played}",
        )
    totals = cumulative_of(tuple(outcome_line(row.sub_game, row.outcome) for row in evidence.rows))
    return {
        "evidence_class": EVIDENCE_CLASS,
        "counted_eligible": evidence.classification.counted_capable,
        "keyed_step0_authentication": ABSENT,
        "mutual_result_agreement": ABSENT,
        "kit_terms_agreement": evidence.classification.kit_terms_agreement,
        "game_id": evidence.game_id,
        "game_uid": evidence.game_uid,
        "group_id": evidence.our_group,
        "opponent_group_id": evidence.peer_group,
        "series_convention": SeriesConvention.REFERENCE_ODD_EVEN_ALTERNATION.value,
        "schedule": [role.value for role in evidence.schedule],
        "role_totals": {"cop": totals.cop_total, "thief": totals.thief_total},
        "sub_games": [sub_game_document(row) for row in evidence.rows],
    }


@dataclass(frozen=True, slots=True)
class DevelopmentEvidenceStore:
    """A store that can only ever write development names.

    Structural rather than remembered: an official filename cannot be produced
    through this path even by a caller that means to, so development evidence
    can never land where downstream logic reads counted league evidence.
    """

    inner: ArtifactStorePort

    def store(self, name: str, document: ArtifactDocument) -> StoredArtifact:
        """Persist *name*, or refuse a name the counted contract owns."""
        if not name.startswith(f"{FRIENDLY_PREFIX}_"):
            raise LocalDefectError(
                f"{name!r} is not a development evidence name; the counted artifact"
                " contract is written by its own owner and never through this path",
            )
        return self.inner.store(name, document)


def persist_friendly_evidence(
    store: DevelopmentEvidenceStore, evidence: FriendlySeriesEvidence
) -> tuple[StoredArtifact, ...]:
    """Write the series document and one document per sub-game played."""
    series = store.store(friendly_series_name(evidence.game_id), series_document(evidence))
    rows = tuple(
        store.store(friendly_sub_game_name(evidence.game_id, row.sub_game), sub_game_document(row))
        for row in evidence.rows
    )
    return (series, *rows)
