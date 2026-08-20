"""Sweeping the corpus: every opponent, every config, every seed, once each.

The sweep is a plain triple loop and is deliberately boring - the interesting
decisions were all made before it runs, in the seed bank, the opponent corpus
and the configuration corpus, none of which knows what is being measured.

**Scores come from the scoring authority.** `domain.scoring.score_for` is the
Appendix F Table 17 table the tournament uses; a research score invented here
could disagree with the one that decides the league, so none is.
"""

from dataclasses import dataclass

from mars777_police.app.sealed_record_values import ActorRole
from mars777_police.domain.board import Position
from mars777_police.domain.scoring import score_for

from .configs import BenchConfig, corpus
from .game import SubGame
from .identity import ROLE, BaselineIdentity
from .opponents import FAMILIES, opponent
from .records import SCHEMA_VERSION, GameRecord
from .scenario import openings, scenario_id
from .seeds import SeedBank
from .strategy_port import Policy

ROLE_UNDER_TEST = ROLE
"""This repository benchmarks its own role; the opponent plays the other one."""

OWN_ROLE = ActorRole(ROLE_UNDER_TEST)
OPPONENT_ROLE = ActorRole.THIEF if OWN_ROLE is ActorRole.POLICE else ActorRole.POLICE
"""Derived once. Only a police-side actor may place a barrier, whichever side we are."""


@dataclass(frozen=True, slots=True)
class Sweep:
    """One complete benchmark: a strategy against the whole corpus."""

    identity: BaselineIdentity
    strategy: Policy
    bank: SeedBank

    def run(self) -> tuple[GameRecord, ...]:
        """Play every distinct **scenario** exactly once.

        Scenarios rather than seeds: two seeds that produce the same opening
        produce the same game for a deterministic policy, and counting it twice
        would inflate `N` without adding evidence. `openings` draws without
        replacement, so a colliding seed is skipped rather than replayed.
        """
        return tuple(
            self._one(family, config, seed, cop_cell, thief_cell)
            for family in FAMILIES
            for config in corpus()
            for seed, cop_cell, thief_cell in openings(config, self.bank.seeds)
        )

    def _one(
        self,
        family: str,
        config: BenchConfig,
        seed: int,
        cop_cell: Position,
        thief_cell: Position,
    ) -> GameRecord:
        rival = opponent(family, seed, OPPONENT_ROLE)
        police, thief = (
            (self.strategy, rival) if OWN_ROLE is ActorRole.POLICE else (rival, self.strategy)
        )
        game = SubGame(config, police, thief, cop_cell, thief_cell)
        outcome = game.play()
        line = score_for(outcome)
        return GameRecord(
            schema=SCHEMA_VERSION,
            role=ROLE_UNDER_TEST,
            commit=self.identity.commit,
            strategy=self.identity.strategy,
            strategy_sha256=self.identity.source_sha256,
            opponent_family=family,
            seed_set=self.bank.name,
            seed=seed,
            scenario_id=scenario_id(ROLE_UNDER_TEST, family, config, seed, cop_cell, thief_cell),
            police_start=f"{cop_cell.row},{cop_cell.col}",
            thief_start=f"{thief_cell.row},{thief_cell.col}",
            config=config.name,
            grid=config.grid,
            quota=config.quota,
            horizon=config.horizon,
            outcome=outcome.value,
            captured=int(game.captured),
            steps=game.steps,
            barriers_placed=game.barriers_placed,
            own_score=line.cop if OWN_ROLE is ActorRole.POLICE else line.thief,
            opponent_score=line.thief if OWN_ROLE is ActorRole.POLICE else line.cop,
        )


def size_of(bank: SeedBank) -> int:
    """How many **distinct scenarios** one sweep over *bank* plays.

    Not `families x configs x seeds`: a configuration whose legal opening space
    is smaller than the bank - the fixed reference geometry has exactly one
    opening - contributes what it actually has.
    """
    return sum(len(openings(config, bank.seeds)) for _ in FAMILIES for config in corpus())
