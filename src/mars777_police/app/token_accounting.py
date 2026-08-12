"""Counting the tokens this side actually spent, per sub-game.

`ResultContribution` needs a real number for every sub-game we played, and
`RESULT_CONTRACT.md` lists `sub_games[].tokens` among the members that are **not
jointly derivable**: each side meters its own. So this is a ledger, not an
estimate - it reports what was charged to it and nothing else.

**Zero is a truthful answer, and only when it is true.** A sub-game in which no
LLM call happened really did cost nothing, so an unspent sub-game reads 0. What
the ledger will not do is forget: charges accumulate, nothing resets between
sub-games, and there is no way to lower a number once it is recorded.

`TOKEN-ACCOUNTING-CRYPTO-EVIDENCE` stays out of scope: this proves bookkeeping,
never that a peer's reported usage is honest.
"""

from dataclasses import dataclass, field
from typing import Protocol

from ..domain.config_model import FIRST_SUB_GAME, FIXED_NUM_GAMES


class InvalidTokenUsageError(ValueError):
    """A charge is not a real, non-negative count of tokens for a real sub-game."""


class TokenAccountingPort(Protocol):
    """What the series layer needs from `infra.metrics`: one number per sub-game."""

    def usage(self, sub_game: int) -> int:
        """Return the tokens this side actually spent in *sub_game*."""
        ...


def _require_sub_game(sub_game: int) -> int:
    if type(sub_game) is not int:
        raise InvalidTokenUsageError(
            f"sub_game must be an int, got {type(sub_game).__name__}",
        )
    if not FIRST_SUB_GAME <= sub_game <= FIXED_NUM_GAMES:
        raise InvalidTokenUsageError(
            f"sub_game must be in [{FIRST_SUB_GAME}, {FIXED_NUM_GAMES}], got {sub_game}",
        )
    return sub_game


@dataclass(slots=True)
class SeriesTokenLedger:
    """The production `TokenAccountingPort`: one running total per sub-game."""

    charges: dict[int, int] = field(default_factory=dict)

    def charge(self, sub_game: int, tokens: int) -> None:
        """Add *tokens* actually consumed in *sub_game* to its running total.

        `type(tokens) is not int` rejects `bool` deliberately: `True` is an
        `int` in Python and would silently become one token.
        """
        _require_sub_game(sub_game)
        if type(tokens) is not int:
            raise InvalidTokenUsageError(
                f"tokens must be an int, got {type(tokens).__name__}",
            )
        if tokens < 0:
            raise InvalidTokenUsageError(f"tokens must not be negative, got {tokens}")
        self.charges[sub_game] = self.charges.get(sub_game, 0) + tokens

    def usage(self, sub_game: int) -> int:
        """Return what *sub_game* cost - 0 only because nothing was charged to it."""
        return self.charges.get(_require_sub_game(sub_game), 0)

    def total(self) -> int:
        """The series total, derived from the per-sub-game numbers, never held."""
        return sum(self.charges.values())
