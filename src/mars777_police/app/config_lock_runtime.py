"""Config lock: build our evidence, verify the peer's, then transition.

Both peers act symmetrically and independently: derive the same core from the
converged negotiation, compute `config_sha256` **locally**, build a
`ConfigLockContext`, prove it, exchange the evidence, verify - and only then
transition. There is no unilateral first-sender winner: neither side's evidence
alone permits the lock.

The verification order is fixed (`CONFIG_CONTRACT.md` §R12-E): the profile and
`key_id` are compared against the provisioned expectation, then the proof is
verified, then the digest is compared. The proof comes **before** the digest so
an unauthenticated core is never even compared.

Two values are never taken on trust. The peer's `config_sha256` is compared
against our own recomputation, never adopted as the value of their core; and the
peer's `profiles` are compared member-for-member, never merged. Equal digests
alone do not authorise counted play, and a verified proof does not mean either
side has committed - those are three different layers, and the fourth, the local
`CONFIG_LOCKED` transition, has no bytes at all.
"""

from dataclasses import dataclass

from ..domain.negotiated_config import NegotiatedConfig
from .interop_profiles import InteropProfileSet
from .peer_pregame_messages import ConfigLockContext, ConfigLockEvidence
from .ports import ConfigDigestPort, ConfigLockAuthPort
from .protocol_errors import (
    AuthFailureError,
    ConfigMismatchError,
    ConventionMismatchError,
    StaleMessageError,
)
from .protocol_values import Sha256Digest
from .state_machine import ProtocolMachine, ProtocolPhase, TransitionResult


@dataclass(frozen=True, slots=True)
class ConfigLockRuntime:
    """The local config-lock service for one sub-game."""

    game_id: str
    game_uid: str
    sub_game: int
    profiles: InteropProfileSet
    digester: ConfigDigestPort
    auth: ConfigLockAuthPort

    def context_for(self, digest: Sha256Digest) -> ConfigLockContext:
        """Return the lock context binding identity, sub-game, digest and profiles."""
        return ConfigLockContext(
            self.game_id,
            self.game_uid,
            self.sub_game,
            digest,
            self.profiles,
        )

    def outbound(self, config: NegotiatedConfig) -> ConfigLockEvidence:
        """Return our evidence over the locally recomputed digest of *config*."""
        context = self.context_for(self.digester.digest(config))
        return ConfigLockEvidence(context, self.auth.prove(context))

    def accept(self, evidence: ConfigLockEvidence, local_digest: Sha256Digest) -> None:
        """Verify the peer's evidence against our own recomputed digest."""
        context = evidence.context
        if context.game_id != self.game_id or context.game_uid != self.game_uid:
            raise StaleMessageError("lock evidence does not name this game")
        if context.sub_game != self.sub_game:
            raise StaleMessageError(
                f"lock evidence is for sub-game {context.sub_game}, expected {self.sub_game}",
            )
        if context.profiles.series_convention is not self.profiles.series_convention:
            raise ConventionMismatchError(
                "the series convention differs and is never resolved by preference",
            )
        if context.profiles != self.profiles:
            raise ConfigMismatchError("the locked interoperability profile set differs")
        if not self.auth.verify(context, evidence.auth):
            raise AuthFailureError("the peer config lock proof did not verify")
        if context.config_sha256 != local_digest:
            raise ConfigMismatchError(
                "the peer config digest differs from our local recomputation",
            )


@dataclass(frozen=True, slots=True)
class ConfigLockGate:
    """The frozen local gate onto `CONFIG_LOCKED`.

    Every condition is required, and the transition is refused - not deferred,
    not retried - when any one is missing. `advance` delegates to the existing
    state machine rather than re-deciding legality, so there is exactly one
    authoritative transition graph.
    """

    converged: bool
    local_digest: Sha256Digest | None
    own_evidence: ConfigLockEvidence | None
    peer_verified: bool

    @property
    def may_lock(self) -> bool:
        """True only when negotiation, both evidences and verification all hold."""
        return (
            self.converged
            and self.local_digest is not None
            and self.own_evidence is not None
            and self.peer_verified
        )

    def advance(self, machine: ProtocolMachine) -> TransitionResult:
        """Transition to `CONFIG_LOCKED`, or refuse because a gate is unmet."""
        if not self.may_lock:
            raise ConfigMismatchError(
                "CONFIG_LOCKED requires convergence, a local digest, our own evidence"
                " and a verified peer evidence; no state changes without all four",
            )
        return machine.advance(ProtocolPhase.CONFIG_LOCKED)
