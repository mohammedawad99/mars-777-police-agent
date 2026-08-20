# Product Requirements — group MaRs-777 (POLICE)

**Status: CURRENT.** This is the root product-requirements document. The
detailed, per-mechanism requirements live in `docs/prd/PRD-01…07`; this file
states what the product is, what it must achieve, and how success is measured,
and points at the document that owns each area.

> **Authority.** Nothing here creates a requirement. Every binding requirement
> comes from the project book v3.0.0 (`.project-spec/police_thief_p2p.pdf`,
> local and git-ignored), catalogued in `docs/spec/REQUIREMENT_CATALOG.md`
> (**91** requirements) and traced in `docs/REQUIREMENTS_TRACEABILITY.md`.

## 1. Overview and context

The 2026 Distributed Police–Thief final project is a **peer-to-peer game between
two independent teams' agents**. Each team ships two autonomous agents — a
POLICE and a THIEF — in two isolated repositories. Agents meet over a public
network, negotiate a signed configuration, play a six-sub-game series in
lockstep with commit–reveal cryptography, and agree a result that both sides can
verify afterwards from artifacts alone.

**This repository is the POLICE agent.** Its sibling is
`mars-777-thief-agent`. They share no live state, no package and no environment.

**The user of this product is not a player**: it is an operator who starts an
agent before a match, and an auditor (the course staff, or the counterparty) who
must be able to verify afterwards that the match was played honestly.

## 2. Goals and success measures

| Goal | Measure | Status |
|---|---|---|
| Play a complete counted series against another group's agent | six sub-games, fourteen official artifacts, mutual result agreement | **pending a counterparty** |
| Be verifiable by a hostile auditor | every claim reconstructible from committed artifacts and hashes | **met** for the artifact families that exist |
| Interoperate with a third party's implementation | live play against the pinned interoperability kit | **met** (six live sub-games, development evidence) |
| Never lose a game to a protocol fault | zero equivocation, zero unsignalled settlement, deterministic replay | **met** in every run so far |
| Meet the professional-software excellence guideline | see `docs/GUIDELINE_ALIGNMENT.md` | **partially met**; gaps are tracked, not hidden |
| Be competitive within the rules | measured win rate against a benchmark opponent | **deferred to Stage 9B** |

## 3. Functional requirements — where each area is owned

| PRD | Area | Implementation status |
|---|---|---|
| `prd/PRD-01-game-logic.md` | board, movement, barriers, capture, scoring, terminal conditions | implemented and covered |
| `prd/PRD-02-local-fastmcp.md` | protocol state machine, orchestrator, FastMCP transport | implemented and covered |
| `prd/PRD-03-baseline-strategy.md` | legal, deterministic action selection | implemented; competitive tuning deferred to Stage 9B |
| `prd/PRD-04-language-and-scent.md` | deterministic hint channel, scent model, belief | implemented at the T0 (template, zero-token) scope |
| `prd/PRD-05-public-network.md` | tunnel, public route, league participation | implemented and demonstrated end to end |
| `prd/PRD-06-security-cryptography.md` | commit–reveal, Step-0 keyed authentication, config lock | implemented and covered |
| `prd/PRD-07-reporting-gui-replay.md` | Gmail reporting, live GUI, Replay Viewer, rate-limit gatekeeper | Replay Viewer (9A-2A/2AF), live and replay GUI (9A-2B) and the provider rate-limit gatekeeper (9A-1C) implemented and covered; **Gmail reporting is not** |

## 4. Non-functional requirements

- **Correctness before capability.** A rule may not be approximated; where the
  book is silent, the decision is recorded in `docs/DECISIONS.md` rather than
  guessed at the call site.
- **Auditability.** Every counted claim must be reproducible from artifacts.
  Development evidence is structurally distinguishable from counted evidence.
- **Determinism.** Same inputs, same bytes: canonical JSON, no wall-clock in a
  hashed payload, no randomness in strategy.
- **Isolation.** No shared state, package, cache or environment with the sibling
  repository.
- **Quality gates.** ruff, `ruff format --check`, `mypy --strict`, the full test
  suite, coverage above the gate, and `uv build` — all green in CI on Ubuntu and
  Windows before anything is claimed.
- **Secret hygiene.** Secrets come from the environment only, are unprintable in
  logs and tracebacks, and never reach the process argument list.

## 5. Assumptions, dependencies, constraints, out of scope

**Assumptions.** The counterparty implements the same book; a public tunnel is
available at match time; the operator supplies the pre-shared authentication
secret out of band.

**Dependencies.** `fastmcp==3.4.6`, `pydantic==2.13.4`, Python 3.12, `uv`, an
ngrok agent installed and authenticated by the operator, and — for
interoperability work only — the pinned third-party kit, which is **never
vendored into this repository**.

**Constraints.** The group code `MaRs-777` is frozen. A counted series is
exactly six sub-games. The role of this repository cannot be overridden by the
environment.

**Out of scope.** Any LLM provider at runtime (the shipped hint path is a
deterministic template catalogue); any shared component with the sibling agent;
any modification of the third-party interoperability kit.

## 6. Timeline and milestones

The full stage-by-stage history and the forward plan live in `docs/PLAN.md`, and
the remaining task list in `docs/TODO.md`. The submission checklist that gates
delivery is `docs/SUBMISSION_CHECKLIST.md`.
