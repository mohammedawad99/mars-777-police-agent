"""The application owner of one peer session's pregame protocol state.

Stage 5-R3 stopped on a real gap: three runtimes each needed round state nobody
held, so none of them had a caller. This is that caller. It **composes** them
and owns nothing they already own - no keyed verification, digest algorithm,
profile comparison, proposal construction or phase machine - so every refusal
below is raised by the runtime it delegates to.

**The authenticated peer identity is an output, never an input.** `accept_step0`
returns the `group_id` the keyed proof verified, only *after* it did - and
signals `step0_seen` only after that identity is installed, so a coordinator
that wakes reads a merged declaration rather than a promise of one.

**One instance per authenticated series, one round at a time.** The declaration
and the verified peer outlive every sub-game; the round runtimes, `opening`,
`seen`, the config, the lock and the milestones are what `open_round` replaces.

**The lock digest is ours, never theirs.** `adopt_config` registers the config
this side agreed and the digest comes from that, through `ConfigLockRuntime`.

**The agreed scent model is a series fact too** (SCENT-001): `scent_freeze` is
established by the first sub-game whose lock verified, then required unchanged
by every later one - and `open_round` leaves it alone.
"""

from dataclasses import dataclass, field

from ..domain.negotiated_config import NegotiatedConfig
from .config_lock_runtime import ConfigLockRuntime
from .config_negotiation_runtime import ConfigNegotiationRuntime
from .declaration_values import Declaration
from .peer_pregame_messages import ConfigLockEvidence, ConfigProposal, Step0DeclarationExchange
from .protocol_errors import LocalDefectError, StaleMessageError
from .series_milestones import PregameMilestones
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

    milestones: PregameMilestones = field(default_factory=PregameMilestones)
    locked_evidence: ConfigLockEvidence | None = field(default=None)
    """The evidence this round verified - the only thing an artifact may report."""

    def accept_step0(self, exchange: Step0DeclarationExchange) -> str:
        """Verify Step-0, retain the merge, and return the peer's identity.

        Nothing is retained until `Step0Runtime.accept` verified the proof."""
        if self.peer is not None:
            raise StaleMessageError("this session already completed Step-0")
        merged = self.step0.accept(self.declaration, exchange)
        _, team = sole_subtree(exchange.declaration)
        self.declaration = merged
        self.peer = team.group_id
        self.milestones.step0_seen.set()
        return team.group_id

    def open_round(self, negotiation: ConfigNegotiationRuntime, lock: ConfigLockRuntime) -> None:
        """Adopt a new authoritative config round, discarding the previous one.

        The series survives; the round does not. The declaration, the peer and
        the frozen scent model are kept, while `opening`, `seen`, the config and
        the lock belonged to one sub-game: carrying `seen` would refuse the
        opponent's legitimate `g02` opening, carrying `opening` would disable the
        proposer rule, and carrying the evidence would let `g02`'s artifact
        report `g01`'s lock.

        **The round comes from the caller**, already built, so nothing here
        guesses a `sub_game`; validation precedes every assignment.
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
        self.locked_evidence = None
        self.milestones = PregameMilestones()

    def accept_proposal(self, proposal: ConfigProposal, sender_id: str) -> bool:
        """Validate the peer's proposal for this round and advance the round.

        *sender_id* is the **authenticated** identity supplied by the caller and
        never read out of *proposal* - which is what makes the guards mean anything.
        """
        converges = self.negotiation.accept(
            proposal, sender_id, opening=self.opening, seen=self.seen
        )
        self.seen = self.seen | {sender_id}
        self.opening = False
        self.milestones.proposal_seen.set()
        return converges

    def prepare_proposal(self, config: NegotiatedConfig) -> ConfigProposal:
        """Build **our** proposal for this round and record that we made it.

        The round state has to move for a proposal we send, not only for one we
        receive: otherwise `opening` would still be true after we opened the
        exchange - judging the peer's reply against the proposer rule twice.
        `propose` runs first, so a refused proposal leaves the round untouched.
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
        self.locked_evidence = evidence
        self.milestones.lock_verified.set()
