# mars-777-police-agent

**2026 Distributed Police-Thief Peer-to-Peer - Final Project**

- **Group code:** `MaRs-777`
- **Repository role:** **POLICE**
- **Status:** **Protocol and evidence stack implemented; autonomous play not yet
  implemented.** See *Implementation status* below for the exact boundary.

This repository is the **POLICE** agent. Its sibling, the **THIEF** agent,
lives in a separate, independent repository (see *Paired repository* below). The
two repositories never share live state.

## Implementation status

Stated precisely, because "done" and "not done" are both misleading here. The
agent is a complete, authenticated **responder**: it boots, serves its four
FastMCP tools and answers a peer correctly. It does **not** yet start or play a
game of its own accord.

**Implemented and covered by tests**

- deterministic domain / game mechanics — board, orthogonal movement, `STAY`,
  barriers and quota, capture, scoring, terminal conditions
- protocol state machine, transition evidence and the sub-game cursor
- Commit-Reveal cryptography over SHA-256 — sealed eight-member record, secure
  nonce, keyed Step-0 / config authentication, final nonce reveal, commitment
  recomputation, `TAMPERED` on hash mismatch, golden vectors
- FastMCP peer transport — four tools, nine wire kinds, eight peer families,
  strict DTOs, real two-agent localhost runs
- runtime composition and the agent lifecycle (serve / connect / stop)
- series lifecycle **services** (`SeriesRuntime`, orchestrator, audit gate)
- capture claim/answer, live transcript retention and the semantic replay audit
- scent: model agreement, cryptographic model lock, series freeze, Reveal V2
  live emission transport, historical audit correspondence and log persistence
- the four official artifact families and the fourteen files a complete
  six-sub-game series produces

**Not yet implemented**

- autonomous strategy for either role (no action is chosen by the agent)
- a production game owner — nothing drives Step-0, turns or the six sub-games;
  the series services above are exercised by tests, not by the executable
- belief / uncertainty modelling over the opponent's scent
- the natural-language hint channel (the field is sealed; nothing writes it)
- physical scent truthfulness — historical correspondence is proven, physics is
  not re-verified (authorized as **JDEC-018**, scheduled for Part 2B)
- accumulated scent-field evolution and full-turn decay
- a user-facing Replay Viewer, the live GUI, and Gmail result reporting
- public-network play is implemented but **not yet demonstrated end-to-end**;
  its live tests are skipped unless explicitly enabled

The project is therefore neither "foundation only" nor "complete".

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
