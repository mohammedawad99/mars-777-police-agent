"""The application owner of one peer session's pregame protocol state.

Stage 5-R3 stopped on a real gap. `Step0Runtime.accept(local, exchange)` needs
the declaration snapshot and **returns** a merged one somebody must retain;
`ConfigNegotiationRuntime.accept` needs the round's `opening` and `seen`;
`ConfigLockRuntime.accept` needs our own digest. No production module held any
of it, so the three runtimes had no caller at all. This is that caller.

It **composes** them and owns nothing they already own: no keyed verification,
digest algorithm, profile comparison, proposal construction or phase machine.
Every refusal below is raised by the runtime it delegates to.

**The authenticated peer identity is an output, never an input.** `accept_step0`
returns the `group_id` the keyed proof verified, only *after* it did, and
`Step0Runtime.accept` refuses a peer authoring our own subtree: no self-naming.

**One instance per authenticated series, one round at a time.** The declaration
and the verified peer are series facts outliving every sub-game; the two round
runtimes, `opening`, `seen` and the config are sub-game facts, replaced together
by `open_round`.

**The lock digest is ours, never theirs.** `adopt_config` registers the config
this side agreed and the digest comes from that, through the port
`ConfigLockRuntime` holds. Digesting the peer's proposal would compare their
evidence against their own bytes - as unsound as deriving a sender from payload.

**The agreed scent model is a series fact too** (SCENT-001): `scent_freeze` is
established by the first sub-game whose lock verified, then required unchanged
by every later one - and `open_round` leaves it alone, being exactly where a
switch would otherwise slip in.
"""

from dataclasses import dataclass, field

from ..domain.negotiated_config import NegotiatedConfig
from .config_lock_runtime import ConfigLockRuntime
from .config_negotiation_runtime import ConfigNegotiationRuntime
from .declaration_values import Declaration
from .peer_pregame_messages import ConfigLockEvidence, ConfigProposal, Step0DeclarationExchange
from .protocol_errors import LocalDefectError, StaleMessageError
from .series_scent_freeze import SeriesScentFreeze
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
    scent_freeze: SeriesScentFreeze = field(default=SeriesScentFreeze())
    """This series' agreed model identity - unset until its first lock verified."""

    def accept_step0(self, exchange: Step0DeclarationExchange) -> str:
        """Verify Step-0, retain the merge, and return the peer's identity.

        Nothing is retained until `Step0Runtime.accept` verified the keyed proof.
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

        The series survives; the round does not. The declaration, the verified
        peer and the frozen scent model are series facts and are kept, while
        `opening`, `seen` and the config belonged to one sub-game: carrying
        `seen` into `g02` would refuse the opponent's legitimate opening
        proposal, and carrying `opening` would disable the proposer rule.

        **The round comes from the caller**, already built, so nothing here
        derives, increments or guesses a `sub_game`. Validation happens before
        any assignment, so a rejected pair leaves the round exactly as it was.
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

        *sender_id* is the **authenticated** identity supplied by the caller,
        never read out of *proposal* - which is what makes the runtime's
        participant and initial-proposer guards mean anything.
        """
        converges = self.negotiation.accept(
            proposal, sender_id, opening=self.opening, seen=self.seen
        )
        self.seen = self.seen | {sender_id}
        self.opening = False
        return converges

    def prepare_proposal(self, config: NegotiatedConfig) -> ConfigProposal:
        """Build **our** proposal for this round and record that we made it.

        The round state has to move for a proposal we send, not only for one we
        receive: otherwise `opening` would still be true after we opened the
        exchange - judging the peer's reply against the initial-proposer rule
        twice - and nothing would stop this side proposing twice. Our identity
        comes from the negotiation runtime, never from a message, and `propose`
        runs first: a refused proposal leaves the round untouched.
        """
        us = self.negotiation.group_id
        if us in self.seen:
            raise StaleMessageError(f"{us!r} already proposed in this round")
        proposal = self.negotiation.propose(config, opening=self.opening)
        self.seen = self.seen | {us}
        self.opening = False
        return proposal

    def prepare_lock(self) -> ConfigLockEvidence:
        """Our lock evidence over the config **this side** adopted this round."""
        config = self.config
        if config is None:
            raise StaleMessageError("lock evidence needs a config this side agreed")
        return self.lock.outbound(config)

    def adopt_config(self, config: NegotiatedConfig) -> None:
        """Register the config **this** side agreed for the current round."""
        self.config = config

    def accept_lock(self, evidence: ConfigLockEvidence) -> None:
        """Verify the peer's lock evidence, then hold the series to one model.

        The freeze runs **after** `ConfigLockRuntime.accept` returned: a mutually
        verified lock over a model this side agreed, never a proposed one.
        """
        config = self.config
        if config is None:
            raise StaleMessageError("lock evidence arrived before this side agreed a config")
        self.lock.accept(evidence, self.lock.digester.digest(config))
        self.scent_freeze = self.scent_freeze.established(evidence.context.scent_model_sha256)
