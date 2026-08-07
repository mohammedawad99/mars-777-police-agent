# PRD-02 - Local FastMCP and Orchestration — group MaRs-777 (POLICE)

> **STATUS: BLUEPRINT — NOT YET APPROVED PRD**
> Stage 2A populated only *Purpose*, *Scope*, *Out of Scope*, the locked *Requirement
> IDs*, and the *Architecture Dependencies*. Detailed functional requirements,
> acceptance criteria and tests are written in **Stage 2B/2C**.
> **Authoritative source:** book v3.0.0 + the locked Stage-1 specification in
> `../spec/`. Nothing here may change a locked fact.
> **Nothing may be implemented before an approved PRD and plan.**

## Purpose

Define the local FastMCP infrastructure and the orchestration core: the inbound tool surface, the state machine that governs legal transitions, the single serialized turn executor, and deadline/watchdog handling.

## Scope

`infra.mcp_server`, `app.state_machine`, `app.orchestrator`, `app.turn_service`, `app.ports`, `infra.clock`; local (non-public) operation and the two-process isolation model.

## Out of Scope

Public tunnel exposure and peer egress policy (PRD-05), cryptographic material (PRD-06), game rules (PRD-01), strategy (PRD-03), GUI/reporting (PRD-07).

## Actors

_Stage 2B._ Expected: this **POLICE** agent, the opponent peer, the grader/lecturer, the
local operator (GUI), and — where relevant — external services (GitHub, Gmail, optional
LLM provider). Trust levels are defined in `../architecture/SYSTEM_ARCHITECTURE.md` §3.

## Locked Requirements

**ARCH-001…005** (separate processes, no shared memory/live state, separate config dirs) · **STATE-001…005** (state model, response timeout 30s, watchdog 60s) · **NET-001** (MCP endpoint, no secret in URL) · **JSON-003/004** (identity and canonical artifacts as consumed here).

_These IDs are copied from the locked catalog (`../spec/REQUIREMENT_CATALOG.md`) and
may not be reworded here. Scope labels denote the **game role** a requirement binds._

## Inputs

_Stage 2B._

## Outputs

_Stage 2B._

## Functional Requirements

_Stage 2B/2C — not yet written._

## Non-Functional Requirements

_Stage 2B._ Must inherit the architecture-wide constraints: determinism where possible,
cross-OS byte-identity, ≤150 lines per Python file, offline testability, zero-token
viability.

## Architecture Dependencies

`../architecture/SYSTEM_ARCHITECTURE.md` · `STATE_MACHINE.md` · `CONCURRENCY_MODEL.md` (single turn executor, cursor guard, idempotency) · `API_BOUNDARIES.md` (`PeerServerPort`, `ClockPort`) · `DEPENDENCY_RULES.md`.

## Security Constraints

_Stage 2B._ Inherits `../architecture/SECURITY_ARCHITECTURE.md`: untrusted peer input,
fail-closed on integrity failure, no secret in any artifact/log/report, locked
cryptographic taxonomy (hash ≠ keyed auth ≠ signature ≠ acknowledgement).

## Failure Modes

_Stage 2B._ Must map to codes already defined in `../architecture/ERROR_MODEL.md`; no
new sanction may be invented beyond the locked specification.

## Acceptance Criteria

_Stage 2B/2C._ Must be objective and reproducible, and feed the gates in
`../architecture/QUALITY_GATES.md`.

## Planned Tests

_Stage 2B/2C._ Layers and the mandatory negative suite are defined in
`../architecture/TEST_ARCHITECTURE.md`.

## Evidence

_Stage 2B/2C._ Artifact and evidence rules: `../architecture/ARTIFACT_LIFECYCLE.md`.

## Open Design Decisions

Concrete FastMCP tool names/signatures (deliberately deferred — must survive opponent negotiation); process supervision and restart semantics; exact deadline escalation ladder.

## Requirement IDs

See **Locked Requirements** above; full mapping in
`../architecture/ARCHITECTURE_TRACEABILITY.md`.
