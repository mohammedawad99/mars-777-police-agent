"""Config negotiation: who proposes, what may change, and when it converges.

Timeline event 2, once per sub-game. The cadence is deterministic and bounded,
and every rule below is a live contract rather than a policy invented here.

**Who proposes first.** The peer whose `group_id` sorts **first under exact
byte-wise ascending comparison** of the two ids in `agreed_between`. Never "first
sender wins", never a race - and deliberately **not** the `group_a` slot, which
is a position and implies no ordering.

**What a proposal is.** Always a *complete* core, never a delta: byte-identity is
a property of a whole document, and a delta would need shared prior state whose
equality is exactly what has not been established yet.

**What may change.** Structural admissibility - FIXED values exact, MINIMUM
values at or above their floors - is already enforced by `NegotiatedConfig` and
its sections at construction, so it is not re-implemented here. What this module
owns is the part a constructor cannot see: `token_budget_per_series` is
**equality-only** after Step-0, since it was agreed before `BOOT` and is
authenticated inside both peers' Step-0 cores; a differing value is
`E-CONFIG-MISMATCH` and never an offer. The eleven series-wide profiles must be
**identical in every sub-game's proposal**, and a differing series convention has
its own owning identity.

**How it ends.** By convergence - member-for-member equal cores and equal
profiles - which is *proved at the lock*, not announced. There is no accept
message, no `accepted` flag and no ninth family. Termination is bounded by the
negotiation window the state already owns; no new bound is invented, and an
exhausted window refuses counted play rather than inventing a technical loss.
"""

from dataclasses import dataclass

from ..domain.config_model import FIRST_SUB_GAME
from ..domain.negotiated_config import NegotiatedConfig
from .interop_profiles import InteropProfileSet
from .peer_pregame_messages import ConfigProposal
from .protocol_errors import (
    ConfigMismatchError,
    ConventionMismatchError,
    LocalDefectError,
    StaleMessageError,
)


def initial_proposer(config: NegotiatedConfig) -> str:
    """Return the `group_id` that sends the first proposal for this sub-game."""
    return min(config.agreed_between)


@dataclass(frozen=True, slots=True)
class ConfigNegotiationRuntime:
    """The local negotiation service for one sub-game."""

    group_id: str
    sub_game: int
    token_budget_per_series: int
    profiles: InteropProfileSet

    def __post_init__(self) -> None:
        if type(self.sub_game) is not int or self.sub_game < FIRST_SUB_GAME:
            raise LocalDefectError(f"sub_game must be an int >= {FIRST_SUB_GAME}")

    def propose(self, config: NegotiatedConfig, *, opening: bool) -> ConfigProposal:
        """Return our proposal, refusing to open the exchange out of turn."""
        if self.group_id not in config.agreed_between:
            raise LocalDefectError(f"{self.group_id!r} is not a party to this config")
        if opening and initial_proposer(config) != self.group_id:
            raise LocalDefectError(
                "the byte-wise lower group_id opens the exchange;"
                f" {initial_proposer(config)!r} does, not {self.group_id!r}",
            )
        self._check_terms(config)
        return ConfigProposal(self.sub_game, config, self.profiles)

    def accept(
        self,
        proposal: ConfigProposal,
        sender_id: str,
        *,
        opening: bool,
        seen: frozenset[str] = frozenset(),
    ) -> bool:
        """Validate an inbound proposal and report whether it converges with ours."""
        if proposal.sub_game != self.sub_game:
            raise StaleMessageError(
                f"proposal is for sub-game {proposal.sub_game}, expected {self.sub_game}",
            )
        if sender_id == self.group_id:
            raise StaleMessageError("a proposal cannot arrive from ourselves")
        if sender_id not in proposal.config.agreed_between:
            raise StaleMessageError(f"{sender_id!r} is not a party to this config")
        if opening and initial_proposer(proposal.config) != sender_id:
            raise StaleMessageError(
                f"only {initial_proposer(proposal.config)!r} may open the exchange",
            )
        if not opening and sender_id in seen:
            raise StaleMessageError(f"{sender_id!r} already proposed in this round")
        self._check_terms(proposal.config)
        self._check_profiles(proposal.profiles)
        return True

    def converges(self, ours: ConfigProposal, theirs: ConfigProposal) -> bool:
        """True when both sides hold equal cores and equal profiles."""
        return (
            ours.sub_game == theirs.sub_game
            and ours.config == theirs.config
            and ours.profiles == theirs.profiles
        )

    def _check_terms(self, config: NegotiatedConfig) -> None:
        cap = config.network_and_league.token_budget_per_series
        if cap != self.token_budget_per_series:
            raise ConfigMismatchError(
                "token_budget_per_series is equality-only after Step-0;"
                f" expected {self.token_budget_per_series}, got {cap}",
            )

    def _check_profiles(self, profiles: InteropProfileSet) -> None:
        if profiles.series_convention is not self.profiles.series_convention:
            raise ConventionMismatchError(
                "the series convention differs and is never resolved by preference",
            )
        if profiles != self.profiles:
            raise ConfigMismatchError("the echoed interoperability profile set differs")
