# mars-777-police-agent

**2026 Distributed Police-Thief Peer-to-Peer - Final Project**

- **Group code:** `MaRs-777`
- **Repository role:** **POLICE**
- **Status:** Foundation only - no game implementation exists yet.

This repository is the **POLICE** agent. Its sibling, the **THIEF** agent,
lives in a separate, independent repository (see *Paired repository* below). The
two repositories never share live state.

## Paired repository (active)

- This repository (POLICE): https://github.com/mohammedawad99/mars-777-police-agent (private)
- Sibling repository (THIEF): https://github.com/mohammedawad99/mars-777-thief-agent (private)

> Both GitHub repositories now **exist and are private** (created in Stage 0C).
> Continuous-integration status is **not** asserted here until the remote CI run
> actually completes.

## Source-of-truth hierarchy

1. Project book **version 3.0.0** - `.project-spec/police_thief_p2p.pdf` (local, git-ignored).
2. Appendix E - mandatory rules, prohibitions, sanctions, recommendations.
3. Appendix F - mandatory numeric parameters and status definitions.
4. Moodle instructions from the lecturer.
5. Professional software-submission guidelines.
6. Example simulator - non-binding reference only.

No rule, value, or schema may be reconstructed from memory. See `docs/SOURCES.md`.

## Development workflow

Requirement -> PRD -> PLAN -> TODO -> Implement -> Verify -> Review -> Commit -> Push.

Nothing is implemented before an approved plan; nothing is committed or pushed
without an explicit, dedicated instruction.

## Local setup (uv)

```bash
uv sync            # create .venv and install dev tools
uv run pytest      # run the foundation smoke tests
```

Python is pinned to 3.12 (`.python-version`). This project uses an isolated
per-repository `.venv`; it never shares an environment with the sibling agent.

## Quality commands

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy --strict src
uv run pytest --cov --cov-report=term-missing --cov-fail-under=90
uv build
```

## Security & secret handling

Never commit credentials, tokens, OAuth files, private keys, or tunnel
configuration. If a secret is ever exposed, revoke it immediately. See
`SECURITY.md`. Runtime logs and state stay local until reviewed.

## Isolation statement

This POLICE agent shares **no live state** with the opposing THIEF agent:
separate repository, separate `.venv`, separate process, separate config, logs,
and runtime state. There is no shared package, database, cache, or memory.

## Contributors

- GitHub owner: **mohammedawad99**
- Future collaborator: **Rawey7** - access pending (not yet granted).

## Scope & honesty statement

Competitive police strategy and full compliance with book v3.0.0 remain
**future work**. This repository does **not** currently comply with the full
project book. No coverage, performance, or win-rate figure should be read as a
claim of competitive readiness; the only tests today are foundation smoke tests
that assert identity and role separation.
