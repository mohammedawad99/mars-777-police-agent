"""Building the two per-sub-game owners a series driver asks for, in production.

`SeriesDriver` takes a factory rather than the runtimes themselves, because a
sub-game's evidence and audit are *its own*: fresh nonces, an empty record set
and a phase that starts at the beginning. Stage 6C-C1 proved that with a factory
written in the test builders; this is the same construction where a real process
can reach it, so nothing production runs is defined under `tests/`.

**Every value is read from state that already exists.** The series identity comes
from the composition, the peer's `group_id` from the declaration Step-0 merged,
and `config_sha256` from the very port `ConfigLockRuntime` uses to verify a
lock - so the digest our evidence is bound to is the digest our lock compares.
Nothing is passed in twice and risked disagreeing.

**The peer's role is derived, not configured.** `ActorRole` has exactly two
members and a match has exactly one of each, so the opponent's role is a fact
about ours - not an operator input that could contradict the sealed bytes.
"""

from collections.abc import Callable

from .app.audit_runtime import AuditRuntime
from .app.audit_values import SubGameContext
from .app.outbound_evidence_runtime import OutboundEvidenceRuntime
from .app.outbound_evidence_values import LocalEvidenceContext
from .app.sealed_record_values import ActorRole
from .composition_values import AgentComposition
from .domain.negotiated_config import NegotiatedConfig
from .protocol.audit_commitment import CommitmentRecomputer
from .protocol.secure_nonce import SecretsNonceSource

SubGameRuntimes = Callable[[int], tuple[OutboundEvidenceRuntime, AuditRuntime]]


def peer_role_of(role: ActorRole) -> ActorRole:
    """The other side of a match, from ours; the enum has no third member."""
    return ActorRole.THIEF if role is ActorRole.POLICE else ActorRole.POLICE


def sub_game_runtimes(
    composition: AgentComposition, role: ActorRole, peer_group_id: str, config: NegotiatedConfig
) -> SubGameRuntimes:
    """Return the factory `SeriesDriver` calls once per sub-game.

    The closure holds only series-scoped facts; everything sub-game-scoped -
    the nonce source, the records, the phases - is built fresh on each call,
    which is what stops one sub-game's evidence reaching another's audit.
    """
    identity = composition.identity
    digest = composition.pregame.lock.digester.digest(config)
    peer_role = peer_role_of(role)

    def build(sub_game: int) -> tuple[OutboundEvidenceRuntime, AuditRuntime]:
        evidence = OutboundEvidenceRuntime(
            LocalEvidenceContext(identity.game_id, identity.game_uid, sub_game, digest, role),
            SecretsNonceSource(),
            CommitmentRecomputer(),
        )
        audit = AuditRuntime(
            SubGameContext(
                identity.game_id, identity.game_uid, sub_game, digest, peer_role, peer_group_id
            ),
            (),
            CommitmentRecomputer(),
        )
        return evidence, audit

    return build
