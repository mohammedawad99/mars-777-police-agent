"""Starting a process that plays its own series, and stopping it afterwards.

Stage 6C-C1 made `SeriesDriver` the production owner of six sub-games; the
shipped process still only served and waited, because nothing joined the two.
This is that join, and it owns **process lifecycle and nothing else**: bring the
ingress up, reach the opponent, exchange Step-0, hand the series to its driver
exactly once, and put everything away whatever happened.

**It decides nothing a game owner decides.** No action, no outcome, no round, no
config cadence, no audit, no result agreement - those are `SeriesDriver`'s and
its collaborators'. What is left here is genuinely lifecycle: readiness before
dialling, a bounded search for a peer that may not be up yet, the one wait that
two independent processes need and one in-process pair did not, and a `finally`.

**The Step-0 wait is a wait on a fact, not on a promise.** `accept_step0`
installs the merged declaration and the verified peer id *before* it signals, so
the check below reads real state and would refuse an unset one - the event only
decides *when* to look.

**Both sides dial.** Each process serves one ingress and holds one outbound
session, so the pair is two sessions in opposite directions; who proposes a
config or a result is a different question, decided by the owners that own it.
"""

import asyncio
from dataclasses import dataclass
from pathlib import Path

from .agent_runtime import AgentRuntime
from .app.artifact_store import StoredArtifact
from .app.live_view_sink import NO_VIEWER, LiveViewSink
from .app.orchestrator import LocalOrchestrator
from .app.pregame_session_runtime import PregameSessionRuntime
from .app.protocol_errors import LocalDefectError
from .app.sealed_record_values import ActorRole
from .app.token_accounting import SeriesTokenLedger
from .boot_runtimes import sub_game_runtimes
from .compose_report import send_game_report
from .domain.config_model import SeriesConfig
from .domain.negotiated_config import NegotiatedConfig
from .infra.artifacts import JsonArtifactStore
from .infra.settings import RuntimeSettings
from .series_driver import SeriesDriver
from .series_runtime import SeriesRuntime
from .startup_budget import StartupBudget

RETRY_PAUSE_SECONDS = 1.0
"""How long to wait between connection attempts - implementation timing only.

Not a source value and not negotiated: it bounds nothing a peer can observe,
and the operation as a whole is bounded by the locked config's own watchdog
threshold. It is fixed rather than random so a failed startup reproduces, and
it is a whole second rather than a few milliseconds because each attempt is a
real session open that the client reports in full when it fails: a tighter
cadence would bury an operator's console in the same failure hundreds of times.
"""


def startup_budget(config: NegotiatedConfig) -> StartupBudget:
    """The bound on reaching a peer, taken from the config's own watchdog."""
    return StartupBudget(
        total_seconds=float(config.network_and_league.watchdog_timeout_sec),
        pause_seconds=RETRY_PAUSE_SECONDS,
    )


@dataclass(frozen=True, slots=True)
class AutonomousBoot:
    """One process's whole life: serve, join, play one series, stop."""

    runtime: AgentRuntime
    settings: RuntimeSettings
    config: NegotiatedConfig
    role: ActorRole
    viewer: LiveViewSink = NO_VIEWER
    """Handed straight to the series owner; this class never draws anything."""

    @property
    def deadline(self) -> float:
        """How long one protocol wait may block: the locked watchdog threshold.

        The same member `Watchdog.for_config` reads, so peer liveness and the
        coordinator's own waits are bounded by one negotiated number.
        """
        return float(self.config.network_and_league.watchdog_timeout_sec)

    def series(self) -> SeriesRuntime:
        """The existing series owner, over this process's own artifact root."""
        return SeriesRuntime(
            self.runtime,
            JsonArtifactStore(self.settings.artifact_root),
            SeriesTokenLedger(),
            LocalOrchestrator.start(SeriesConfig()),
        )

    @staticmethod
    def reporter(result: Path) -> None:
        """Report a finished series automatically, as Appendix E rule 32 requires.

        The boot is where a real provider belongs: `SeriesDriver` owns the moment
        a result becomes reportable and must not learn what Gmail is, while this
        already owns process lifecycle and the outside world.

        Delegates to the same `send_game_report` the operator command uses, so
        there is one reporting path with one gate, one recipient and one message
        contract - the only difference is that nobody has to type it.
        """
        send_game_report(result)

    def driver(self, series: SeriesRuntime, peer: str) -> SeriesDriver:
        """The one production series owner, built from state that already exists."""
        composition = series.composition
        return SeriesDriver(
            series=series,
            strategy=composition.strategy,
            role=self.role,
            config=self.config,
            runtimes=sub_game_runtimes(composition, self.role, peer, self.config),
            deadline=self.deadline,
            viewer=self.viewer,
            reporter=self.reporter,
        )

    async def await_peer_step0(self, pregame: PregameSessionRuntime) -> str:
        """Wait for the peer's Step-0, then read the state it installed.

        The event says *when*; `peer` is the fact. A signal without the identity
        behind it would be a defect in the owner, and this refuses it rather
        than starting a series against nobody.
        """
        await asyncio.wait_for(pregame.milestones.step0_seen.wait(), self.deadline)
        peer = pregame.peer
        if peer is None:
            raise LocalDefectError("Step-0 was signalled without an authenticated peer")
        return peer

    async def run(self) -> StoredArtifact:
        """Serve, join the opponent, play the series, and stop. Once each."""
        await self.runtime.serve()
        try:
            await self.runtime.connect_until_ready(startup_budget(self.config))
            series = self.series()
            await series.start()
            peer = await self.await_peer_step0(series.composition.pregame)
            driver = self.driver(series, peer)
            driver.open()
            return await driver.play_series()
        finally:
            await self.runtime.stop()
