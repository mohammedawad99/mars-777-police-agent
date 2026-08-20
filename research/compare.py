"""Replaying a candidate over exactly the scenarios the baseline played.

A candidate is never given its own sweep. It is handed the baseline's own result
rows and replays each one - same configuration, same opponent family, same
seed, same two opening cells - so every comparison is paired by `scenario_id`
and no candidate can look better for having met easier conditions.

The comparison reports flips, not only rates: a candidate that wins three games
it used to lose and loses two it used to win has a positive delta and a real
regression, and only the flip counts show both.

**A replayed row carries the identity of the policy that produced it**, not the
identity of the row it was paired against. Copying the baseline's name and hash
onto a candidate's results would file every candidate's evidence under the
baseline's name, so the identity is a required argument rather than an
inherited field.
"""

from dataclasses import dataclass

from mars777_police.app.sealed_record_values import ActorRole
from mars777_police.domain.board import Position
from mars777_police.domain.scoring import score_for

from .configs import BenchConfig, corpus
from .game import SubGame
from .opponents import opponent
from .records import SCHEMA_VERSION, GameRecord
from .runner import OPPONENT_ROLE, OWN_ROLE, ROLE_UNDER_TEST
from .strategy_port import Policy

BY_NAME: dict[str, BenchConfig] = {one.name: one for one in corpus()}


def _cell(text: str) -> Position:
    row, col = text.split(",")
    return Position(int(row), int(col))


def replay(policy: Policy, row: GameRecord, identity: tuple[str, str]) -> GameRecord:
    """Play *row*'s exact scenario with *policy*, and record what happened.

    *identity* is the `(name, sha256)` of *policy*, and it is required: a
    defaulted identity is how a candidate's rows end up filed under the
    baseline's name.
    """
    config = BY_NAME[row.config]
    rival = opponent(row.opponent_family, row.seed, OPPONENT_ROLE)
    police, thief = (policy, rival) if OWN_ROLE is ActorRole.POLICE else (rival, policy)
    game = SubGame(config, police, thief, _cell(row.police_start), _cell(row.thief_start))
    outcome = game.play()
    line = score_for(outcome)
    return GameRecord(
        schema=SCHEMA_VERSION,
        role=ROLE_UNDER_TEST,
        commit=row.commit,
        strategy=identity[0],
        strategy_sha256=identity[1],
        opponent_family=row.opponent_family,
        seed_set=row.seed_set,
        seed=row.seed,
        scenario_id=row.scenario_id,
        police_start=row.police_start,
        thief_start=row.thief_start,
        config=row.config,
        grid=row.grid,
        quota=row.quota,
        horizon=row.horizon,
        outcome=outcome.value,
        captured=int(game.captured),
        steps=game.steps,
        barriers_placed=game.barriers_placed,
        own_score=line.cop if OWN_ROLE is ActorRole.POLICE else line.thief,
        opponent_score=line.thief if OWN_ROLE is ActorRole.POLICE else line.cop,
    )


def replay_all(
    policy: Policy, rows: tuple[GameRecord, ...], identity: tuple[str, str]
) -> tuple[GameRecord, ...]:
    """Replay every scenario in *rows*, in the order given, deterministically."""
    return tuple(replay(policy, row, identity) for row in rows)


@dataclass(frozen=True, slots=True)
class Paired:
    """One paired comparison: what moved, and in which direction."""

    n: int
    baseline_wins: int
    candidate_wins: int
    gains: int
    losses: int
    baseline_barriers: float
    candidate_barriers: float

    @property
    def delta(self) -> float:
        """The paired win-rate difference. Positive means the candidate won more."""
        return (self.candidate_wins - self.baseline_wins) / self.n if self.n else 0.0

    def as_record(self) -> dict[str, object]:
        """Flat output for a table."""
        return {
            "n": self.n,
            "baseline_wins": self.baseline_wins,
            "candidate_wins": self.candidate_wins,
            "gains": self.gains,
            "losses": self.losses,
            "win_delta": round(self.delta, 6),
            "baseline_barriers": round(self.baseline_barriers, 4),
            "candidate_barriers": round(self.candidate_barriers, 4),
        }


def compare(before: tuple[GameRecord, ...], after: tuple[GameRecord, ...]) -> Paired:
    """Pair *before* and *after* by scenario, refusing anything that does not line up."""
    left = {one.scenario_id: one for one in before}
    right = {one.scenario_id: one for one in after}
    if set(left) != set(right):
        raise ValueError("a paired comparison needs the same scenarios on both sides")
    keys = sorted(left)
    gains = sum(1 for one in keys if not left[one].won and right[one].won)
    losses = sum(1 for one in keys if left[one].won and not right[one].won)
    return Paired(
        n=len(keys),
        baseline_wins=sum(left[one].won for one in keys),
        candidate_wins=sum(right[one].won for one in keys),
        gains=gains,
        losses=losses,
        baseline_barriers=sum(left[one].barriers_placed for one in keys) / max(len(keys), 1),
        candidate_barriers=sum(right[one].barriers_placed for one in keys) / max(len(keys), 1),
    )


def by_group(
    before: tuple[GameRecord, ...], after: tuple[GameRecord, ...], key: str
) -> dict[str, Paired]:
    """The same comparison, split by one attribute, in sorted order."""
    groups = sorted({str(getattr(one, key)) for one in before})
    return {
        name: compare(
            tuple(one for one in before if str(getattr(one, key)) == name),
            tuple(one for one in after if str(getattr(one, key)) == name),
        )
        for name in groups
    }
