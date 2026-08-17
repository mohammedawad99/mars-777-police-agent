# mars-777-police-agent

**2026 Distributed Police-Thief Peer-to-Peer - Final Project**

- **Group code:** `MaRs-777`
- **Repository role:** **POLICE**
- **Status:** **A permanent autonomous agent: `python -m …` boots, plays a
  complete six-sub-game series against a real peer process and exits.** What is
  still missing is a counted match against another group's agent. See
  *Implementation status* below for the exact boundary.

This repository is the **POLICE** agent. Its sibling, the **THIEF** agent,
lives in a separate, independent repository (see *Paired repository* below). The
two repositories never share live state.

## Implementation status

Stated precisely, because "done" and "not done" are both misleading here. The
agent is autonomous: it boots, serves its four FastMCP tools, reaches its
configured opponent, plays a whole series and stops. What it has **not** done is
play a counted match against another group's real agent.

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

- a **baseline physical strategy** (Stage 6B): each agent chooses its own legal,
  deterministic action from own position, the public board and the locked barrier
  quota alone — no belief, no scent, no hints, no LLM, no randomness
- **one autonomous sub-game** (Stage 6C-B): `SubGameDriver` runs the real
  lockstep loop — terminal check, observation, strategy, commit/acknowledge/reveal,
  capture answer, one-time local-truth adoption — and derives the end event from
  `domain.terminal`. Two real agents play a whole sub-game to a natural terminal
  with no fixture supplying an action or an outcome
- an **exact-six autonomous series** (Stage 6C-C1): `SeriesDriver` negotiates and
  locks a config per sub-game, opens one `SubGameDriver` per sub-game, closes each
  through the final-nonce / audit / semantic-review stack, agrees the result with
  the peer and persists it — exactly `g01`…`g06`, six natural outcomes and the
  fourteen official files, with no fixture supplying an action, an outcome or a
  lifecycle call
- **permanent autonomous boot** (Stage 6C-C2): `python -m …` serves, opens a
  bounded outbound session to the configured opponent - retrying only while the
  peer is not listening yet - exchanges Step-0, invokes exactly one
  `SeriesDriver`, and stops when the series ends. The boot document carries this
  side's opening `NegotiatedConfig` candidate and `MARS777_ARTIFACT_ROOT` says
  where its own official files go; neither crosses the wire as anything new.
  **Proved as real OS processes**: the shipped CLI plays a full `g01`…`g06`
  series over FastMCP against a separate process, writes its fourteen artifacts
  and exits 0, and a legal-but-different boot config is still refused by the
  existing config lock
- a **deterministic natural-language hint channel** (Stage 7B): every turn seals a
  truthful pre-written sentence chosen by code - zero tokens, no network, no model.
  A validator owns every outgoing hint: Unicode NFC, deterministic word counting
  against the **negotiated** `hint_max_words`, and a narrow detector that refuses
  direct coordinate syntax such as `(3,4)` or `row 3 col 4` while leaving ordinary
  numeric prose ("I checked 3 corridors") sayable. A candidate that fails is
  replaced by a safe template, never sent in violation

**Not yet implemented**

- a **counted match against another group's agent**. The process proof above
  uses a *synthetic distinct-group non-counted integration opponent*: our own
  Police and Thief repositories are two roles of **MaRs-777**, and Step-0
  correctly refuses a peer that authors our own participant subtree, so they
  cannot play each other. A counted result needs an externally supplied
  different-group counterparty
- **belief-level scent interpretation**: emissions are exchanged, retained and
  audited, but nothing yet folds them into a signal a strategy reads
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
