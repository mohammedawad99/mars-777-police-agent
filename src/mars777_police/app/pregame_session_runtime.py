"""The application owner of one peer session's pregame protocol state.

Stage 5-R3 stopped on a real gap. `Step0Runtime.accept(local, exchange)` needs
the current declaration snapshot and **returns** a merged one somebody must
retain; `ConfigNegotiationRuntime.accept` needs the round's `opening` and `seen`;
`ConfigLockRuntime.accept` needs our own authoritative digest. No production
module held any of it, so the three runtimes had no production caller at all.
This is that caller.

It **composes** them and owns nothing they already own: no keyed verification, no
digest algorithm, no profile comparison, no proposal construction, no phase
machine. Every refusal below is raised by the runtime it delegates to.

**The authenticated peer identity is an output, never an input.** `accept_step0`
returns the `group_id` whose Step-0 subtree the keyed proof actually verified -
`Step0Runtime.accept` calls `auth.verify(peer, peer_team.group_id, exchange.auth)`
and refuses a peer authoring our own subtree, so a caller cannot name itself. It
is returned only *after* that verification succeeds, and only the transport
decides what to do with it: nothing here knows a session exists.

**One instance per authenticated series, one round at a time.** The declaration
and the verified peer are series facts and outlive every sub-game; the two round
runtimes, `opening`, `seen` and the adopted config are sub-game facts and are
replaced together by `open_round`.

**The lock digest is ours, never theirs.** `adopt_config` registers the config
this side agreed, and the local digest is derived from that through the digest
port `ConfigLockRuntime` already holds. Digesting the peer's proposal instead
would compare their evidence against their own bytes, which is the same defect
as deriving a sender from the payload it authenticates.
"""

from dataclasses import dataclass, field

from ..domain.negotiated_config import NegotiatedConfig
from .config_lock_runtime import ConfigLockRuntime
from .config_negotiation_runtime import ConfigNegotiationRuntime
from .declaration_values import Declaration
from .peer_pregame_messages import ConfigLockEvidence, ConfigProposal, Step0DeclarationExchange
from .protocol_errors import LocalDefectError, StaleMessageError
from .step0_runtime import Step0Runtime, sole_subtree


@dataclass(slots=True)
class PregameSessionRuntime:
    """One peer session's Step-0, negotiation and lock state, held together."""

    step0: Step0Runtime
    negotiation: ConfigNegotiationRuntime
    lock: ConfigLockRuntime
    declaration: Declaration
    peer: str | None = field(default=None)
    opening: bool = field(default=True)
    seen: frozenset[str] = field(default=frozenset())
    config: NegotiatedConfig | None = field(default=None)

    def accept_step0(self, exchange: Step0DeclarationExchange) -> str:
        """Verify the peer's Step-0, retain the merge, and return its identity.

        The order is the point: nothing is retained and no identity is returned
        until `Step0Runtime.accept` has verified the keyed proof.
        """
        if self.peer is not None:
            raise StaleMessageError("this session already completed Step-0")
        merged = self.step0.accept(self.declaration, exchange)
        _, team = sole_subtree(exchange.declaration)
        self.declaration = merged
        self.peer = team.group_id
        return team.group_id

    def open_round(self, negotiation: ConfigNegotiationRuntime, lock: ConfigLockRuntime) -> None:
        """Adopt a new authoritative config round, discarding the previous one.

        The series survives; the round does not. `Declaration` and the verified
        peer are what Step-0 established for the whole series, so they are kept -
        while `opening`, `seen` and the adopted config belonged to one sub-game
        and would be a lie in the next. Carrying `seen` into `g02` would refuse
        the opponent's legitimate opening proposal as a duplicate, and carrying
        `opening` would stop the initial-proposer rule applying at all.

        **The round comes from the caller.** Both runtimes are supplied already
        built, so nothing here derives, increments or guesses a `sub_game`; the
        future runner owns when a round opens and which one it is. Validation
        happens before any assignment, so a rejected pair leaves the current
        round exactly as it was.
        """
        if negotiation.sub_game != lock.sub_game:
            raise LocalDefectError(
                f"a round needs one sub-game, got negotiation {negotiation.sub_game}"
                f" and lock {lock.sub_game}",
            )
        self.negotiation = negotiation
        self.lock = lock
        self.opening = True
        self.seen = frozenset()
        self.config = None

    def accept_proposal(self, proposal: ConfigProposal, sender_id: str) -> bool:
        """Validate the peer's proposal for this round and advance the round.

        *sender_id* is the **authenticated** identity supplied by the caller; it
        is never read out of *proposal*, which is exactly what makes the
        runtime's participant and initial-proposer guards mean anything.
        """
        converges = self.negotiation.accept(
            proposal, sender_id, opening=self.opening, seen=self.seen
        )
        self.seen = self.seen | {sender_id}
        self.opening = False
        return converges

    def adopt_config(self, config: NegotiatedConfig) -> None:
        """Register the config **this** side agreed for the current round."""
        self.config = config

    def accept_lock(self, evidence: ConfigLockEvidence) -> None:
        """Check the peer's lock evidence against our own recomputed digest."""
        config = self.config
        if config is None:
            raise StaleMessageError("lock evidence arrived before this side agreed a config")
        self.lock.accept(evidence, self.lock.digester.digest(config))
