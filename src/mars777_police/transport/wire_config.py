"""Wire DTOs for the binding config core, the profile set and the lock evidence.

The 35-member core and the eleven series-wide profiles, exactly as their semantic
types hold them. The profile tokens are typed as the closed literal unions the
semantic enums publish, so a token this project has never frozen is refused in
the schema rather than at construction.

`config_sha256` and the `AuthProof` envelope stay **outside** the core here as
they do everywhere else: the digest and the proof travel in the lock context and
the evidence, never inside the bytes they cover.
"""

from typing import Literal

from pydantic import BaseModel

from .wire_config_sections import (
    WIRE,
    BoardAndAgentsWire,
    MovementAndBarriersWire,
    NetworkAndLeagueWire,
    PheromonesWire,
    RateLimiterWire,
    ScoringWire,
    WorldWire,
)
from .wire_scalars import DigestText, KeyIdText, NonEmptyText, ProofText
from .wire_scent_model import ScentModelWire


class NegotiatedConfigWire(BaseModel):
    """`schema_version` + `agreed_between` + the 33 Appendix-B value keys."""

    model_config = WIRE

    schema_version: NonEmptyText
    agreed_between: list[str]
    board_and_agents: BoardAndAgentsWire
    world: WorldWire
    movement_and_barriers: MovementAndBarriersWire
    scoring: ScoringWire
    pheromones: PheromonesWire
    network_and_league: NetworkAndLeagueWire
    rate_limiter_gatekeeper: RateLimiterWire


class InteropProfileSetWire(BaseModel):
    """The eleven series-wide values the lock context binds.

    Each token is a closed literal: an unrecognised spelling never becomes an
    enum lookup failure deep in the codec, it fails the schema.
    """

    model_config = WIRE

    series_convention: Literal["FIXED_ROLE", "REFERENCE_ODD_EVEN_ALTERNATION"]
    auth_profile: Literal["HMAC_SHA256", "ED25519"]
    key_id: KeyIdText
    commitment_codec: Literal["STRICT_PROJECT_COMMITMENT", "LECTURER_REFERENCE_COMMITMENT"]
    result_profile: Literal["STRICT_PROJECT_RESULT", "LECTURER_ATTACHMENT_COMPATIBILITY"]
    compatibility_profile: Literal[
        "STRICT_COUNTED_MATCH",
        "STRICT_COUNTED_MATCH_TURN_OUTCOME_V1",
        "LECTURER_REFERENCE_COMPATIBILITY",
        "LECTURER_ATTACHMENT_COMPATIBILITY",
    ]
    tool_name_profile: Literal["PROJECT_LOGICAL_OPERATIONS", "LECTURER_REFERENCE_ALIASES"]
    canonicalization_profile: Literal["CANONICAL_JSON_V1"]
    sealed_record_profile: Literal["SEALED_RECORD_V1"]
    state_representation_profile: Literal["SEALED_STATE_V1"]
    nonce_representation_profile: Literal["LOWER_HEX_32"]


class AuthProofWire(BaseModel):
    """The `{auth_alg, key_id, auth_tag}` envelope, as a semantic `AuthProof`.

    Only `key_id` ever appears - never key material - and the proof width is
    re-checked by the semantic type against its declared profile.
    """

    model_config = WIRE

    profile: Literal["HMAC_SHA256", "ED25519"]
    key_id: KeyIdText
    value: ProofText


class ConfigProposalWire(BaseModel):
    """`ConfigProposal` - always a complete core, and the complete scent model.

    `scent_model` is absent for a posture that predates the model exchange and
    present in full for one that requires it (SCENT-003). Which postures require
    it is negotiation's decision; this shape only carries what it is given.
    """

    model_config = WIRE

    sub_game: int
    config: NegotiatedConfigWire
    profiles: InteropProfileSetWire
    scent_model: ScentModelWire | None = None


class ConfigLockContextWire(BaseModel):
    """Identity, sub-game, the two unkeyed digests and the eleven profiles.

    `scent_model_sha256` is the agreed model's content identity, never the model
    itself: the full descriptor already crossed in the proposal, and what the
    lock authenticates is which model that was.
    """

    model_config = WIRE

    game_id: NonEmptyText
    game_uid: NonEmptyText
    sub_game: int
    config_sha256: DigestText
    profiles: InteropProfileSetWire
    scent_model_sha256: DigestText


class ConfigLockEvidenceWire(BaseModel):
    """`ConfigLockEvidence(context, auth)` - the proof stays outside the context."""

    model_config = WIRE

    context: ConfigLockContextWire
    auth: AuthProofWire
