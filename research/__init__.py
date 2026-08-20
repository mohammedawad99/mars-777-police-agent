"""`research` - the competitive laboratory. Never part of a tournament runtime.

This package exists to answer one question honestly: **does a proposed strategy
deserve to replace the one that ships?** It therefore sits outside `src/`, is
not part of the distribution, and nothing in `mars777_police` imports it. The
dependency points one way only: research may compose production authorities,
production may never reach research.

**It is not a second game engine.** Legality, barriers, capture, scent,
terminal conditions and scoring are decided by the same modules the counted
agent uses; what is added here is a way to *drive* two strategies through them
deterministically and record what happened.

**It is held to the same discipline as production.** Every module obeys the
150-code-line rule, `ruff`, `mypy --strict` and full coverage, because research
that nobody can trust is worse than no research.
"""
