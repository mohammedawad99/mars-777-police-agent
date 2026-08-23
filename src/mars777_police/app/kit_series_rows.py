"""Where one group's six finished rows are collected while both backends are alive.

The series settlement digest covers **all six** sub-games, and this group plays
them across two processes: each role backend owns three and neither holds the
series. The peer, running one process, simply has its own ledger; we have to put
ours back together before we can agree on it.

It has to happen *while the series is still live*. The exchange is bounded by the
agreed window - the peer retries for `consensus_timeout_sec` and then records the
series as unsettled - so merging after both processes have written their evidence
and exited is far too late. That is exactly how a real series ended unsettled.

**This stores rows; it does not judge them.** A row is a fact the backend that
played it already settled: its number, the two roles, the outcome word and the
two scores. Nothing here computes a score, decides an outcome, breaks a tie or
reads a board - `series_consensus` does the arithmetic, and it does it from
whatever this hands back. The gateway keeps this for the same reason it keeps
the routing cursor: it is the only part of the group that both backends can
reach, and it still decides nothing about a game.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from .kit_schedule import SUB_GAMES
from .protocol_errors import StaleMessageError

ROW_MEMBERS = ("sub_game_number", "roles", "result", "score")
"""What a settled row must carry. A row missing one of these settles nothing."""


@dataclass(slots=True)
class SeriesRowCollector:
    """One series' finished rows, contributed by whichever backend played each."""

    rows: dict[int, dict[str, Any]] = field(default_factory=dict)

    def record(self, row: Mapping[str, Any]) -> None:
        """Keep one finished row, or refuse what cannot be one.

        A second row for the same sub-game is refused rather than overwritten: a
        sub-game settles once, and silently replacing it would let a late or
        duplicated report change a digest both sides have already agreed.
        """
        missing = [name for name in ROW_MEMBERS if name not in row]
        if missing:
            raise StaleMessageError(f"a settled row is missing {missing}")
        number = int(row["sub_game_number"])
        if not 1 <= number <= SUB_GAMES:
            raise StaleMessageError(f"sub-game {number} is outside a {SUB_GAMES}-sub-game series")
        if number in self.rows:
            raise StaleMessageError(f"sub-game {number} was already settled; it settles once")
        self.rows[number] = {name: row[name] for name in ROW_MEMBERS}

    @property
    def complete(self) -> bool:
        """Whether all six rows are in, so a settlement can be computed."""
        return len(self.rows) == SUB_GAMES

    def series(self) -> tuple[dict[str, Any], ...]:
        """The six rows in sub-game order, or a refusal naming what is absent."""
        if not self.complete:
            absent = sorted(set(range(1, SUB_GAMES + 1)) - set(self.rows))
            raise StaleMessageError(f"the series cannot settle without sub-games {absent}")
        return tuple(self.rows[number] for number in range(1, SUB_GAMES + 1))
