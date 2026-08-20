"""The benchmark opponents: deterministic, legal, and no better informed than us.

**An opponent that cheats produces invalid evidence**, so every policy here is
handed exactly one `Observation` - the same value type the production strategy
port receives, whose four members are the board, its own cell, its own quota and
its own lawfully folded scent belief. There is no field for the other actor's
cell, an unrevealed intent, a nonce, a future draw or the opponent's parameters,
so an omniscient opponent is not something this corpus could express.

**Deterministic without a shared random stream.** A policy that needs to break a
tie arbitrarily derives its choice from a seed and the position it is standing
on, so the same seed replays the same game and no policy can peek at another's
draw. `random` is never used.

**A police-side opponent may place barriers, because the rules let that role
and only that role place them.** Its placement rule is written here and is
deliberately simpler than any shipped policy: place when the lawful evidence on
a placeable neighbour beats the evidence where we would otherwise move. It is an
independent research policy, never a copy of another repository's production
strategy - `research` imports nothing from a sibling repository at all.

Every action returned here is revalidated by the same legality authorities the
counted agent uses; nothing in this file decides what is legal.
"""

import hashlib
from dataclasses import dataclass
from decimal import Decimal

from mars777_police.app.sealed_record_values import ActorRole
from mars777_police.domain.actions import BarrierAction, MoveAction, PhysicalAction
from mars777_police.domain.barriers import is_placeable
from mars777_police.domain.board import Position
from mars777_police.domain.observation import Observation
from mars777_police.domain.reachability import reachable_from
from mars777_police.domain.rules import Move, destination_of, legal_moves

OBSERVATION_BUDGET = "board, own cell, own quota, own folded scent belief"
"""Identical for every family. Stated once because it is the fairness claim."""


def _pick(seed: int, cell: Position, moves: tuple[Move, ...]) -> Move:
    """A stable arbitrary choice: seeded, positional, and never `random`."""
    material = f"{seed}/{cell.row}/{cell.col}".encode()
    return moves[int.from_bytes(hashlib.sha256(material).digest()[:4], "big") % len(moves)]


def _landing(observation: Observation, move: Move) -> Position:
    return destination_of(observation.own_position, move)


def _spread(observation: Observation, move: Move) -> int:
    """How much board stays reachable from where this move lands."""
    return sum(reachable_from(observation.board, _landing(observation, move)).values())


def _mobility(observation: Observation, move: Move) -> int:
    """How many onward moves this move leaves. A dead end scores one."""
    return len(legal_moves(observation.board, _landing(observation, move)))


def _scent(observation: Observation, move: Move) -> Decimal:
    """The lawful evidence at the destination. Zero when nothing was heard."""
    return observation.scent.intensity_at(_landing(observation, move))


PLACING_FAMILIES: tuple[str, ...] = ("pursuit", "barrier_aware", "adversarial_corner")
"""The police-side families willing to spend a placement when evidence backs it."""


@dataclass(frozen=True, slots=True)
class Opponent:
    """One named benchmark policy, and the rule it ranks candidate moves by."""

    family: str
    seed: int = 0
    role: ActorRole = ActorRole.THIEF
    """Which role this policy plays. Only a police-side policy may place a barrier."""

    def choose_action(self, observation: Observation) -> PhysicalAction:
        """This family's action: a move, or a placement when it is police and backed."""
        moves = legal_moves(observation.board, observation.own_position)
        if not moves:
            raise ValueError("a trapped actor is a terminal, not a decision")
        move = self._chosen(observation, moves)
        placement = self._placement(observation, move)
        return MoveAction(move) if placement is None else BarrierAction(placement)

    def _placement(self, observation: Observation, move: Move) -> Position | None:
        """A lawful placement that beats where we would move, or nothing.

        Only the police may place at all, and only a family that opted in. The
        comparison is exact `Decimal` from the scent authority; equal or absent
        evidence always yields the move, so a silent sub-game plays identically
        to a policy that never places.
        """
        if self.role is not ActorRole.POLICE or self.family not in PLACING_FAMILIES:
            return None
        here = observation.own_position
        targets = [
            cell
            for cell in observation.board.orthogonal_neighbours(here)
            if is_placeable(observation.board, here, cell, observation.quota)
        ]
        standard = observation.scent.intensity_at(_landing(observation, move))
        backed = [cell for cell in targets if observation.scent.intensity_at(cell) > standard]
        if not backed:
            return None
        return min(
            backed, key=lambda cell: (-observation.scent.intensity_at(cell), cell.row, cell.col)
        )

    def _chosen(self, observation: Observation, moves: tuple[Move, ...]) -> Move:
        if self.family == "random_legal":
            return _pick(self.seed, observation.own_position, moves)
        if self.family == "center_mobility":
            return min(moves, key=lambda one: (-_mobility(observation, one), one.value))
        if self.family == "evasive":
            return min(
                moves, key=lambda one: (-_spread(observation, one), _scent(observation, one))
            )
        if self.family == "pursuit":
            return min(
                moves, key=lambda one: (-_scent(observation, one), -_spread(observation, one))
            )
        if self.family == "barrier_aware":
            return min(
                moves, key=lambda one: (-_mobility(observation, one), -_spread(observation, one))
            )
        if self.family == "scent_aware":
            return min(moves, key=lambda one: (_scent(observation, one), one.value))
        return min(moves, key=lambda one: (_spread(observation, one), one.value))


FAMILIES: tuple[str, ...] = (
    "random_legal",
    "center_mobility",
    "evasive",
    "pursuit",
    "barrier_aware",
    "scent_aware",
    "adversarial_corner",
)
"""Seven policies. `adversarial_corner` deliberately walks into tight regions -
the case a pursuer should exploit and an evader should never choose - so it
probes a real weakness without needing anything it may not see."""


def opponent(family: str, seed: int, role: ActorRole = ActorRole.THIEF) -> Opponent:
    """The named policy, seeded for its tie-breaks and told which role it plays."""
    if family not in FAMILIES:
        raise ValueError(f"unknown opponent family {family!r}")
    return Opponent(family, seed, role)
