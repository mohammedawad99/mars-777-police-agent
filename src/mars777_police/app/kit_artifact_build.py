"""Turning one played sub-game into the two official documents it owes.

The backend that played a sub-game is the only process holding what those
documents are made of: the terms and nonce its greeting agreed, the chain it
sealed, and the chain the peer disclosed. So it builds them here and contributes
them to the gateway, which is where a two-process group's halves meet.

**Built from what happened, never from what should have happened.** The config
artifact records the agreement the greeting actually carried; the log records
the commitments actually exchanged. Neither is reconstructed from configuration
that merely ought to match - a document assembled from expectations would pass
every schema check while describing a game nobody played.

**A sub-game with no disclosure owes no documents.** Its own builders refuse,
and that refusal is left to travel: an unaudited sub-game must not contribute a
log that implies it was audited.
"""

from dataclasses import dataclass
from typing import Any

from ..domain.negotiated_config import NegotiatedConfig
from ..domain.scent_model import ScentModelAgreement
from .kit_greeting import KitGreeting
from .kit_log_document import kit_finalized_log
from .kit_messages import KitAuditReveal, KitRecord
from .peer_pregame_messages import ConfigLockContext
from .protocol_errors import LocalDefectError
from .terms_agreement_values import TermsAgreementEvidence

Document = dict[str, Any]


@dataclass(frozen=True, slots=True)
class SubGameArtifacts:
    """The two per-sub-game official documents, and the numbers they belong to."""

    sub_game: int
    config: Document
    log: Document


def terms_evidence(
    *,
    greeting: KitGreeting,
    context: ConfigLockContext,
) -> TermsAgreementEvidence:
    """The agreement this sub-game's greeting carried, as artifact evidence.

    The signature is taken from the greeting rather than recomputed: recomputing
    it would record what our own canonicalization produces, which is exactly the
    thing a reader wants to check independently.
    """
    return TermsAgreementEvidence(context, greeting.nonce, greeting.signature)


def sub_game_artifacts(
    *,
    sub_game: int,
    greeting: KitGreeting | None,
    context: ConfigLockContext,
    config: NegotiatedConfig,
    model: ScentModelAgreement,
    ours: tuple[KitRecord, ...],
    disclosure: KitAuditReveal | None,
    peer_verified: bool,
    result: str,
    build_config: Any,
) -> SubGameArtifacts:
    """Both documents for one played sub-game, or a refusal naming what is absent.

    `build_config` is `artifact_documents.terms_config_document`, injected rather
    than imported: this module lives in the application layer and that writer
    reaches the transport codecs, so taking it as an argument keeps the
    dependency pointing the way the rest of the project points.
    """
    if greeting is None:
        raise LocalDefectError(
            f"sub-game {sub_game} has no recorded greeting;"
            " its config artifact would state an agreement nobody made",
        )
    if context.sub_game != sub_game:
        raise LocalDefectError(
            f"the lock context names sub-game {context.sub_game}, not {sub_game}",
        )
    evidence = terms_evidence(greeting=greeting, context=context)
    return SubGameArtifacts(
        sub_game=sub_game,
        config=dict(build_config(config, model, evidence)),
        log=dict(
            kit_finalized_log(
                game_id=context.game_id,
                game_uid=context.game_uid,
                sub_game=sub_game,
                config_sha256=context.config_sha256.value,
                ours=ours,
                disclosure=disclosure,
                peer_verified=peer_verified,
                result=result,
            )
        ),
    )
