"""Step-0: build our own exchange, verify the peer's, merge, and gate.

Timeline event 1. Each side sends its **own** subtree with a proof over its own
19-member core, because at that moment neither has seen the other's. The merge
therefore produces a **new** `Declaration` carrying both subtrees; neither input
snapshot is mutated, and the merged value is what every later stage joins to.

Every LIVE duty this stage owns is a *comparison against something we already
hold*, and each is refused rather than repaired:

* the proof is verified against the **locally provisioned** profile and key, so
  the message can never choose the verifier (`E-AUTH-FAILURE`);
* the sender may author **only its own subtree** - a snapshot arriving with two
  populated slots is a peer speaking for us, refused outright;
* game identity and the agreed `game_start` must equal what we hold, and
  `token_budget_per_series` must be **equal**: it was agreed before `BOOT` and is
  authenticated inside both cores, so a difference is a mismatch, never an offer;
* a second exchange from the same participant is stale, not an update.

No sanction is applied here. A pre-play failure **refuses counted play**; the
technical-loss score is a counted-play consequence and is never manufactured
from a Step-0 disagreement.
"""

from dataclasses import dataclass

from .declaration_values import Declaration, DeclarationTeams
from .peer_pregame_messages import Step0DeclarationExchange
from .ports import Step0AuthPort
from .protocol_errors import (
    AuthFailureError,
    ConfigMismatchError,
    LocalDefectError,
    StaleMessageError,
)
from .team_declaration_values import TeamDeclaration

PARTICIPANT_SLOTS = ("group_a", "group_b")


def sole_subtree(declaration: Declaration) -> tuple[str, TeamDeclaration]:
    """Return the one populated slot of a partial snapshot, or refuse it."""
    populated = [
        (slot, team)
        for slot in PARTICIPANT_SLOTS
        if (team := getattr(declaration.teams, slot)) is not None
    ]
    if len(populated) != 1:
        raise StaleMessageError(
            "a Step-0 exchange carries exactly one participant subtree;"
            f" this snapshot carries {len(populated)}",
        )
    return populated[0]


def merge(local: Declaration, peer: Declaration) -> Declaration:
    """Return a new merged snapshot; neither input is read for anything else."""
    local_slot, local_team = sole_subtree(local)
    peer_slot, peer_team = sole_subtree(peer)
    if local_slot == peer_slot:
        raise StaleMessageError(f"both participants claim the {local_slot} slot")
    teams = DeclarationTeams(
        group_a=local_team if local_slot == "group_a" else peer_team,
        group_b=local_team if local_slot == "group_b" else peer_team,
    )
    return Declaration(
        local.game_id,
        local.game_uid,
        local.token_budget_per_series,
        local.times,
        teams,
    )


@dataclass(frozen=True, slots=True)
class Step0Runtime:
    """The local Step-0 application service for one participant."""

    group_id: str
    auth: Step0AuthPort

    def outbound(self, declaration: Declaration) -> Step0DeclarationExchange:
        """Return our single Step-0 exchange over our own partial snapshot."""
        _, team = sole_subtree(declaration)
        if team.group_id != self.group_id:
            raise LocalDefectError(
                f"our snapshot declares {team.group_id!r}, not our own {self.group_id!r}",
            )
        return Step0DeclarationExchange(declaration, self.auth.prove(declaration, self.group_id))

    def accept(self, local: Declaration, exchange: Step0DeclarationExchange) -> Declaration:
        """Verify the peer's exchange against *local* and return the merged snapshot."""
        peer = exchange.declaration
        _, peer_team = sole_subtree(peer)
        if peer_team.group_id == self.group_id:
            raise StaleMessageError("a peer may not author our own participant subtree")
        for name in ("game_id", "game_uid"):
            if getattr(peer, name) != getattr(local, name):
                raise StaleMessageError(f"peer {name} does not match the local game")
        if peer.times.game_start != local.times.game_start:
            raise ConfigMismatchError("peer game_start differs from the agreed start time")
        if peer.token_budget_per_series != local.token_budget_per_series:
            raise ConfigMismatchError(
                "token_budget_per_series was agreed before BOOT and is equality-only;"
                " a differing value refuses counted play",
            )
        if not self.auth.verify(peer, peer_team.group_id, exchange.auth):
            raise AuthFailureError("the peer Step-0 proof did not verify")
        return merge(local, peer)


@dataclass(frozen=True, slots=True)
class Step0Completion:
    """The frozen local completion gate for timeline event 1.

    Both directions are required. Having sent our own evidence proves nothing
    about the peer, and having verified the peer's proves nothing about ours -
    only a snapshot holding **both** subtrees, produced by a verified exchange,
    permits `STEP0_NEGOTIATION -> CONFIG_NEGOTIATION`. Until then the negotiation
    runtime is not entitled to run and counted play must not proceed.
    """

    sent: bool
    merged: Declaration | None

    @property
    def is_complete(self) -> bool:
        """True only when our evidence exists and the peer's produced a merge."""
        return self.sent and self.merged is not None and self.merged.teams.is_merged
