"""Local series orchestrator: the sub-game cursor plus the phase machine.

`STATE_OWNERSHIP.md` gives `app.orchestrator` exactly one live fact here - the
**current sub-game index** (lifetime SERIES, reset at series start). Everything
else stays where the table puts it: the phase in `app.state_machine`, turn/step
and own position in `domain.truth`, barriers in `domain.barriers`, evidence in
`infra.logger`. So this module composes a :class:`ProtocolMachine` rather than
copying its phase, and `STATE_MACHINE.md` keeps the only transition graph - "the
orchestrator asks; it never assumes".

The one branch it may decide itself is the sub-game boundary, because it owns
the deciding fact. `STATE_MACHINE.md` §1 draws it as "SUBGAME_COMPLETE -> (next
sub-game -> READY)" and gives SERIES_COMPLETE the entry condition "all sub-games
played (``num_games``=6 FIXED)", so continuing needs an unplayed sub-game and
ending needs the last one - no caller boolean is trusted for what the cursor
already proves. Advancement happens only on that one edge, so a technical loss
(which reaches the same boundary, §4) yields the same cursor sequence.

Deliberately absent: turn execution, game effects, outcome and score, capture,
hash/tamper/audit truth, deadlines, persistence, transport and cryptography.
Concurrency is out of scope too - `CONCURRENCY_MODEL.md` keeps game logic
deterministic and single-threaded, and only I/O (which this module has none of)
is asynchronous.
"""

from dataclasses import dataclass, replace

from ..domain.config_model import FIRST_SUB_GAME, SeriesConfig
from .state_machine import ProtocolMachine, ProtocolPhase, TransitionEvidence


class IllegalSubGameBranchError(Exception):
    """An orchestrator-owned guard refused: the request contradicts the cursor.

    Local, caught before anything is sent, so `ERROR_MODEL.md` classes it with
    `E-LOCAL-VALIDATION`; an impossible constructed cursor is `E-LOCAL-DEFECT`.
    Phase legality is not decided here - that raises ``IllegalTransitionError``.
    """


@dataclass(frozen=True, slots=True)
class LocalOrchestrator:
    """The series position: the phase machine, the locked series, the cursor.

    ``series`` is a read-only immutable config projection, not owned state:
    `STATE_OWNERSHIP.md` gives the locked config to `protocol.config_lock` with
    "all layers (read-only value)" as readers.
    """

    machine: ProtocolMachine
    series: SeriesConfig
    sub_game: int

    def __post_init__(self) -> None:
        if not isinstance(self.machine, ProtocolMachine):
            raise IllegalSubGameBranchError("machine must be a ProtocolMachine")
        _require_series(self.series)
        if type(self.sub_game) is not int:
            raise IllegalSubGameBranchError(
                f"sub_game must be an int, got {type(self.sub_game).__name__}",
            )
        if not FIRST_SUB_GAME <= self.sub_game <= self.series.num_games:
            raise IllegalSubGameBranchError(
                f"sub_game must be in [{FIRST_SUB_GAME}, {self.series.num_games}],"
                f" got {self.sub_game}",
            )

    @classmethod
    def start(cls, series: SeriesConfig) -> "LocalOrchestrator":
        """Return the normal initial position: BOOT, at the first sub-game.

        Bootstrap is not a transition, so no evidence exists to emit for it.
        """
        _require_series(series)
        return cls(ProtocolMachine.start(), series, FIRST_SUB_GAME)

    @property
    def is_last_sub_game(self) -> bool:
        """Whether the cursor is already on the final sub-game of the series."""
        return self.sub_game == self.series.num_games

    def advance(self, target: ProtocolPhase) -> "OrchestratorResult":
        """Ask the machine to move to *target*, then apply the cursor rule.

        The cursor guard runs first because it asks a different question from
        legality; a refusal therefore emits no evidence at all. Legality itself
        is never re-implemented - the machine raises and this method does not
        catch it, so a failure leaves every field untouched.
        """
        step = self._cursor_step(target)
        result = self.machine.advance(target)
        moved = replace(self, machine=result.machine, sub_game=self.sub_game + step)
        return OrchestratorResult(moved, result.evidence)

    def _cursor_step(self, target: ProtocolPhase) -> int:
        if self.machine.phase is not ProtocolPhase.SUBGAME_COMPLETE:
            return 0
        if target is ProtocolPhase.READY:
            if self.is_last_sub_game:
                raise IllegalSubGameBranchError(
                    f"sub-game {self.sub_game} is the last of {self.series.num_games};"
                    " the series cannot continue",
                )
            return 1
        if target is ProtocolPhase.SERIES_COMPLETE and not self.is_last_sub_game:
            raise IllegalSubGameBranchError(
                f"sub-game {self.sub_game} of {self.series.num_games} is not played out;"
                " the series cannot end",
            )
        return 0


@dataclass(frozen=True, slots=True)
class OrchestratorResult:
    """A successful orchestrated transition: new position + the machine's evidence."""

    orchestrator: LocalOrchestrator
    evidence: TransitionEvidence

    def __post_init__(self) -> None:
        if not isinstance(self.evidence, TransitionEvidence):
            raise IllegalSubGameBranchError("result needs a TransitionEvidence")
        if self.evidence.target_phase is not self.orchestrator.machine.phase:
            raise IllegalSubGameBranchError("evidence does not match the new phase")


def _require_series(value: object) -> SeriesConfig:
    if not isinstance(value, SeriesConfig):
        raise IllegalSubGameBranchError(
            f"series must be a SeriesConfig, got {type(value).__name__}",
        )
    return value
