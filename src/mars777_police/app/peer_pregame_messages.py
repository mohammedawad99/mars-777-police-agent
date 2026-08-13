"""The four pre-game peer semantic values.

Immutable composites only. Nothing here opens a socket, computes or verifies a
proof, reads a key or a clock, or decides a phase: these are the values the
application control flow produces and consumes, and ``protocol.messages`` will
map them to and from the wire (`MODULE_BOUNDARIES.md`, D32).

Two boundaries are deliberate. ``Step0DeclarationExchange`` composes the single
authoritative ``Declaration`` with its ``AuthProof`` rather than flattening a
second declaration schema; and ``ConfigLockEvidence`` refuses a proof whose
profile or key label disagrees with the context it travels with - a structural
self-contradiction, checked before any peer, network, key or clock exists.
"""

from dataclasses import dataclass

from ..domain.config_model import FIRST_SUB_GAME
from ..domain.negotiated_config import NegotiatedConfig
from ..domain.scent_model import ScentModelAgreement
from .auth_values import AuthProof
from .declaration_values import Declaration
from .interop_profiles import InteropProfileSet
from .protocol_values import Sha256Digest


class InvalidPregameMessageError(ValueError):
    """Raised when a pre-game peer semantic value is structurally malformed."""


def _require_type(value: object, name: str, expected: type) -> None:
    if type(value) is not expected:
        raise InvalidPregameMessageError(
            f"{name} must be a {expected.__name__}, got {type(value).__name__}",
        )


def _require_sub_game(value: object) -> None:
    if type(value) is not int:
        raise InvalidPregameMessageError(
            f"sub_game must be an int, got {type(value).__name__}",
        )
    if value < FIRST_SUB_GAME:
        raise InvalidPregameMessageError(
            f"sub_game must be >= {FIRST_SUB_GAME}, got {value}",
        )


def _require_identity(value: object, name: str) -> None:
    if type(value) is not str:
        raise InvalidPregameMessageError(f"{name} must be a str, got {type(value).__name__}")
    if not value:
        raise InvalidPregameMessageError(f"{name} must be non-empty")


@dataclass(frozen=True, slots=True)
class Step0DeclarationExchange:
    """Timeline event 1: a declaration snapshot and the proof over its core.

    Series-control scope: no sub-game, step, phase or cursor, and no secret. The
    proof is carried **beside** the subject data, never inside it, so there is
    exactly one authoritative authentication value.
    """

    declaration: Declaration
    auth: AuthProof

    def __post_init__(self) -> None:
        _require_type(self.declaration, "declaration", Declaration)
        _require_type(self.auth, "auth", AuthProof)


@dataclass(frozen=True, slots=True)
class ConfigProposal:
    """Timeline event 2: one complete proposed config plus the series profiles.

    Always a **complete** core, never a delta: a delta would presume shared prior
    state whose equality is exactly what has not yet been established. Whether
    the opponent agrees, and which members a counter-proposal may alter, are LIVE
    questions this value does not answer.
    """

    sub_game: int
    config: NegotiatedConfig
    profiles: InteropProfileSet
    scent_model: ScentModelAgreement | None = None
    """The full agreed emission and decay model (SCENT-003), or none yet.

    Optional at the value level because a proposal is also the shape older
    compatibility postures parse; **whether** a posture may leave it out is a
    negotiation decision, not a composition rule, and is decided elsewhere."""

    def __post_init__(self) -> None:
        _require_sub_game(self.sub_game)
        _require_type(self.config, "config", NegotiatedConfig)
        _require_type(self.profiles, "profiles", InteropProfileSet)
        if self.scent_model is not None:
            _require_type(self.scent_model, "scent_model", ScentModelAgreement)


@dataclass(frozen=True, slots=True)
class ConfigLockContext:
    """What the config authentication proof covers.

    The agreed physics enters only through ``config_sha256`` - binding the digest
    rather than the 35 members keeps the Appendix-B core free of protocol
    metadata while still binding it exactly. ``config_auth`` itself is absent:
    a proof is never inside the bytes it authenticates.
    """

    game_id: str
    game_uid: str
    sub_game: int
    config_sha256: Sha256Digest
    profiles: InteropProfileSet

    def __post_init__(self) -> None:
        _require_identity(self.game_id, "game_id")
        _require_identity(self.game_uid, "game_uid")
        _require_sub_game(self.sub_game)
        _require_type(self.config_sha256, "config_sha256", Sha256Digest)
        _require_type(self.profiles, "profiles", InteropProfileSet)


@dataclass(frozen=True, slots=True)
class ConfigLockEvidence:
    """Timeline event 3: the lock context and the proof over it.

    The context already names the agreed profile and key label, so a proof
    declaring a different profile or key is self-contradictory and is refused
    here. That is a **structural** check: it verifies no cryptography, and the
    provisioned-expectation comparison, the actual MAC or signature check, peer
    identity, phase and digest equality all remain LIVE duties.
    """

    context: ConfigLockContext
    auth: AuthProof

    def __post_init__(self) -> None:
        _require_type(self.context, "context", ConfigLockContext)
        _require_type(self.auth, "auth", AuthProof)
        if self.auth.profile is not self.context.profiles.auth_profile:
            raise InvalidPregameMessageError(
                "auth.profile must equal context.profiles.auth_profile, got"
                f" {self.auth.profile.value} and {self.context.profiles.auth_profile.value}",
            )
        if self.auth.key_id != self.context.profiles.key_id:
            raise InvalidPregameMessageError(
                "auth.key_id must equal context.profiles.key_id",
            )
