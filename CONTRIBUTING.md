# Contributing - group MaRs-777

This is an academic competition project. Contributions follow a strict,
reviewable workflow.

## Workflow

1. Work from a **feature branch** (`feature/<req-id>-short-slug`).
2. Keep changes **small and scoped** - one requirement or concern per PR.
3. Reference a **requirement ID** from `docs/REQUIREMENTS_TRACEABILITY.md`.
4. Add or update **tests** for every behavior change.
5. Pass **all quality gates** locally before opening a PR:
   - `uv run ruff check .`
   - `uv run ruff format --check .`
   - `uv run mypy --strict src`
   - `uv run pytest --cov --cov-report=term-missing --cov-fail-under=90`
   - `uv build`
6. Never include **secrets** of any kind.
7. Never claim completion without evidence (exact commands + results).
8. Never access the **opposing agent's** private state, config, or strategy.

## Commit / PR expectations

- Descriptive messages that reference the requirement ID.
- The PR template must be filled in truthfully.
- Reviews happen before merge; unreviewed "done" claims are not accepted.

## Source of truth

All behavior must trace to book v3.0.0 (see `docs/SOURCES.md`). No rule or
numeric value may be introduced from memory.
