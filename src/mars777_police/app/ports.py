"""The application-side port contracts the Stage-4E-R16 runtimes depend on.

`API_BOUNDARIES.md` declares ports in `app.ports` and their adapters in
`protocol`/`infra`, and `MODULE_BOUNDARIES.md` forbids `app` from importing
`protocol` at all. Both hold here: every port below is a structural `Protocol`
over **already-valid semantic values**, the concrete implementations live in
`protocol.declaration`, `protocol.config_lock`, `protocol.result_core` and
`protocol.keyed_auth`, and the composition root wires them (D3).

Consequences that are the point rather than a side effect:

* **no canonicalization, digest or key material reaches `app`.** A port returns
  an `AuthProof`, a `Sha256Digest` or a verdict - never bytes, never a key
  (**P2**), and never a transport object (`§AR`);
* **the runtimes are synchronous and deterministic.** `async` is an I/O property
  (**O1**), and no port here performs I/O, so none is `async`. `TimestampPort`
  is the single injected non-determinism, exactly as **P3** requires;
* **verification returns a verdict, construction raises.** A peer proof that
  fails to verify is a `False`, which the calling runtime turns into the owning
  error identity; a locally impossible request is the adapter's own failure.
"""

from typing import Protocol

from ..domain.actions import PhysicalAction
from ..domain.negotiated_config import NegotiatedConfig
from .artifact_values import UtcTimestamp
from .auth_values import AuthProof
from .declaration_values import Declaration
from .peer_pregame_messages import ConfigLockContext
from .protocol_values import NonceValue, Sha256Digest
from .result_core_values import ResultApprovalCore
from .sealed_record_values import ActorRole, Intent, SealedState
from .turn_cursor import TurnCursor


class Step0AuthPort(Protocol):
    """Keyed authentication over `"step0" ‖ canonical(Step-0 core)` (NDEC-005).

    *group_id* names whose subtree is projected: the core is the **producing
    team's own** subtree plus the shared identity, because at timeline event 1
    no peer has yet seen the opponent's.
    """

    def prove(self, declaration: Declaration, group_id: str) -> AuthProof:
        """Return this peer's proof over its own Step-0 core."""
        ...

    def verify(self, declaration: Declaration, group_id: str, proof: AuthProof) -> bool:
        """Return whether *proof* verifies over *group_id*'s Step-0 core."""
        ...


class ConfigDigestPort(Protocol):
    """The unkeyed content digest over the 35-member binding config core.

    Content identity only - it authenticates nobody (`PRD06-FR-044`), which is
    why the lock also needs `ConfigLockAuthPort`.
    """

    def digest(self, config: NegotiatedConfig) -> Sha256Digest:
        """Return `config_sha256` for *config*."""
        ...


class ConfigLockAuthPort(Protocol):
    """Keyed authentication over `"config" ‖ canonical(ConfigLockContext)`.

    Domain-separated from Step-0 by the context string, so a Step-0 proof can
    never be replayed as a config proof.
    """

    def prove(self, context: ConfigLockContext) -> AuthProof:
        """Return this peer's proof over *context*."""
        ...

    def verify(self, context: ConfigLockContext, proof: AuthProof) -> bool:
        """Return whether *proof* verifies over *context*."""
        ...


class ResultDigestPort(Protocol):
    """The unkeyed content digest over the result approval core.

    Non-self-referential: `result_sha256` is never a member of the core it
    covers, and no keyed proof is introduced for result approval - the source
    requires a SHA-256-backed mutual acknowledgement, not producer
    authentication.
    """

    def digest(self, core: ResultApprovalCore) -> Sha256Digest:
        """Return `result_sha256` for *core*."""
        ...


class TimestampPort(Protocol):
    """The injected source of the one agreed result timestamp.

    Only the deterministic proposer ever calls it, exactly once per agreement
    attempt; the non-proposer echoes the received value verbatim and never
    consults a clock. Tests inject a fixed instant, so no test depends on wall
    time.
    """

    def now(self) -> UtcTimestamp:
        """Return the current instant in the frozen lexical form."""
        ...


class CommitmentPort(Protocol):
    """The already-registered `API_BOUNDARIES.md` commitment port, as a seam.

    Its register row freezes the shape: inputs are "sealed record fields (8) -
    already-valid semantic values, never strings or dicts", outputs are
    "`H_commit`; later a recompute **comparison result**". This is that row made
    callable, so the audit runtime can recompute a commitment without `app`
    importing `protocol` - the D1 edge the architecture forbids.

    Exactly those two operations, and no more. A JSON projection of an action or
    a domain-coordinate constructor would be a *different* responsibility
    wearing this port's name: both are reachable inward from `app` already, so
    borrowing the cryptographic seam for them would widen a frozen contract to
    save an import.
    """

    def recompute(
        self,
        *,
        state: SealedState,
        action: PhysicalAction,
        intent: Intent,
        hint: str,
        cursor: TurnCursor,
        role: ActorRole,
        nonce: NonceValue,
    ) -> Sha256Digest:
        """Return `H_commit` over the eight-member sealed record."""
        ...

    def matches(self, expected: Sha256Digest, recomputed: Sha256Digest) -> bool:
        """Whether two digests are equal. Inequality is a result, not a failure."""
        ...
