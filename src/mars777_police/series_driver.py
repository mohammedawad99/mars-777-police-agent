"""Six sub-games, in order, played by this agent instead of by a test.

App F Table 18 #1 fixes the series at six sub-games, and `LocalOrchestrator`
already enforces it - a seventh `READY` is refused and `SERIES_COMPLETE` before
the sixth is refused. So this loop follows that cursor rather than counting to
six itself: the authority stays where it was.

**Sequence only.** Every fact belongs to somebody else and stays there. The
cursor is the orchestrator's, the outcome lines and all four artifact writes are
`SeriesRuntime`'s, the audit verdict is `SeriesAuditGate`'s, the agreed config
and the frozen scent model are `PregameSessionRuntime`'s, the score is
`domain.scoring`'s, and one whole sub-game of gameplay is `SubGameDriver`'s -
used through its existing surface and not modified for this.

**It lives beside `SeriesRuntime`, not inside `app`.** Both compose application
owners *and* the running agent, which is exactly why `SeriesRuntime` is not an
`app` module either; putting the loop under `app` would have meant importing
outward.

**Each sub-game starts from its own locked config.** A fresh `SubGameDriver`,
fresh evidence and audit runtimes, and a `LocalTruth` built by `config_rules`
from *that* sub-game's board and start cells. Nothing about `g01`'s final
position, barriers or step count reaches `g02` - the final audit replays each
sub-game from its own start, so carrying anything would disclose a game that
never happened.

**It waits; it never polls.** The two boundaries a single turn never crosses - a
config round the byte-wise lower `group_id` must open, and a result agreement
only the deterministic proposer may open - are awaited on the milestones their
own owners set after mutating state.

Deliberately absent: the CLI, process boot, and any knowledge of which role this
repository is. Series orchestration is role-neutral; the strategy behind
`StrategyPort` is where the roles differ.
"""

import asyncio
from collections.abc import Callable
from dataclasses import dataclass

from .app import artifact_store as artifacts
from .app.audit_runtime import AuditRuntime
from .app.outbound_evidence_runtime import OutboundEvidenceRuntime
from .app.round_opening import open_round_for
from .app.sealed_record_values import ActorRole
from .app.series_agreements import agree_config, agree_result
from .app.state_machine import ProtocolPhase
from .app.strategy_api import StrategyPort
from .app.sub_game_launch import launch_sub_game
from .domain.negotiated_config import NegotiatedConfig
from .domain.terminal import Outcome
from .series_runtime import SeriesRuntime

SubGameRuntimes = Callable[[int], tuple[OutboundEvidenceRuntime, AuditRuntime]]
"""Builds one sub-game's producer and verifier; the composition root owns how."""


@dataclass(slots=True)
class SeriesDriver:
    """Plays all six sub-games of one series through the owners that exist."""

    series: SeriesRuntime
    strategy: StrategyPort
    role: ActorRole
    config: NegotiatedConfig
    runtimes: SubGameRuntimes
    deadline: float

    def open(self) -> None:
        """Open the config round for the sub-game about to be played, and adopt it.

        Split out for the same reason `SubGameDriver.open` is: a message for a
        round nobody opened is refused as stale, so both sides open before either
        speaks, and every later round opens the moment the previous one closes -
        which the mutual audit already synchronises.

        **Adopting here is what makes the round able to answer.**
        `accept_lock` verifies the peer's evidence against *our* digest of *our*
        config and rightly refuses when there is none; adopting only just before
        sending our own lock left a window where our lock outran the peer's
        adoption and both sides refused each other. The config is this series'
        boot input, so the round can hold it from the moment it exists - the
        convergence check still happens through the proposal exchange.

        **Opening the round we are already on does nothing**, because two real
        processes cannot agree who opens first: the peer may have proposed for
        `gNN` before we got here, and re-opening would discard the proposal it
        will never send again. `open_round_for` owns that decision, so no guard
        and no reset rule had to change to make either order safe.
        """
        open_round_for(self.series.composition.pregame, self.series.sub_game, self.config)

    async def play_series(self) -> artifacts.StoredArtifact:
        """Play six sub-games and return the stored official result."""
        self.series.record_declaration()
        while self.series.orchestrator.machine.phase is not ProtocolPhase.SERIES_COMPLETE:
            await self.play_sub_game(self.series.sub_game)
        self.series.build_result()
        exchange = self.series.composition.runtime_context.current_result()
        await agree_result(exchange, self.series.composition.peer_runner, self._await)
        return self.series.persist_result()

    async def play_sub_game(self, sub_game: int) -> Outcome:
        """One whole sub-game: agree its config, play it, audit it, close it."""
        runner = self.series.composition.peer_runner
        pregame = self.series.composition.pregame
        await agree_config(pregame, runner, self.config, self._await)
        self.series.lock_config(self.config)
        evidence, audit = self.runtimes(sub_game)
        self.series.open_sub_game(evidence, audit)
        outcome = await self._play_rounds(evidence, sub_game)
        await runner.send_final_nonce_reveal()
        await runner.send_audit_disclosure()
        # the review replays the peer's own disclosed play: sending ours proves nothing
        await self._await(audit.milestones.complete)
        self.series.close_sub_game(outcome)
        if self.series.orchestrator.machine.phase is not ProtocolPhase.SERIES_COMPLETE:
            self.open()
        return outcome

    async def _play_rounds(self, evidence: OutboundEvidenceRuntime, sub_game: int) -> Outcome:
        """Drive one fresh `SubGameDriver` to its natural terminal."""
        context = self.series.composition.runtime_context
        driver = launch_sub_game(
            self.strategy,
            self.series.composition.peer_runner,
            context,
            self.series.composition.pregame,
            self.config,
            self.role,
            evidence.context.config_sha256,
            sub_game,
            self.deadline,
        )
        driver.open()
        settled = driver.settled()
        while settled is None:
            played = context.current_turn()
            await driver.play_round()
            self.series.close_turn(played)
            settled = driver.settled()
        return settled

    async def _await(self, arrived: object) -> None:
        """Suspend until the owner records it, within the agreed deadline."""
        assert isinstance(arrived, asyncio.Event)
        await asyncio.wait_for(arrived.wait(), self.deadline)
