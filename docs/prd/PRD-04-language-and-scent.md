# PRD-04 - Language and Scent — group MaRs-777 (POLICE)

> **STATUS: BLUEPRINT — NOT YET APPROVED PRD**
> Stage 2A populated only *Purpose*, *Scope*, *Out of Scope*, the locked *Requirement
> IDs*, and the *Architecture Dependencies*. Detailed functional requirements,
> acceptance criteria and tests are written in **Stage 2B/2C**.
> **Authoritative source:** book v3.0.0 + the locked Stage-1 specification in
> `../spec/`. Nothing here may change a locked fact.
> **Nothing may be implemented before an approved PRD and plan.**

## Purpose

Define the bounded natural-language hint subsystem (including deliberate, legally-declared bluffing via `intent`) and the pheromone/scent subsystem driven by the signed configuration; plus token/cost accounting for any LLM use.

## Scope

`protocol.hints`, `domain.scent`, `infra.llm` (optional advisor), `infra.metrics` token accounting, and the T0/T1/T2 tier policy.

## Out of Scope

Movement legality and selection (PRD-01/03), transport (PRD-05), cryptographic sealing of the hint inside the commitment (PRD-06), result formatting (PRD-07).

## Actors

_Stage 2B._ Expected: this **POLICE** agent, the opponent peer, the grader/lecturer, the
local operator (GUI), and — where relevant — external services (GitHub, Gmail, optional
LLM provider). Trust levels are defined in `../architecture/SYSTEM_ARCHITECTURE.md` §3.

## Locked Requirements

**LLM-001…005** (algorithmic default, map area, hint generation, `hint_max_words`, MAY-exception) · **SCENT-001…003** (scent model lock, Appendix F 0.9 / 0.10 / 5, observation) · **PERF-001…003** (token reporting, token lock, budget) · **C-08** (`verdict` = `intent`, one field only).

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

`../architecture/LLM_BOUNDARY.md` (tiers, validator gate, zero-token fallback) · `STRATEGY_ARCHITECTURE.md` §6 · `OBSERVABILITY.md` §4 (token metrics) · `SECURITY_ARCHITECTURE.md` T12 (prompt injection).

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

LLM provider/SDK (no dependency added yet); prompt templates; hint quality evaluation; whether tier T2 is ever enabled (requires a documented mutual agreement).

## Requirement IDs

See **Locked Requirements** above; full mapping in
`../architecture/ARCHITECTURE_TRACEABILITY.md`.
