# PRD-07 - Reporting, GUI and Replay — group MaRs-777 (POLICE)

> **STATUS: BLUEPRINT — NOT YET APPROVED PRD**
> Stage 2A populated only *Purpose*, *Scope*, *Out of Scope*, the locked *Requirement
> IDs*, and the *Architecture Dependencies*. Detailed functional requirements,
> acceptance criteria and tests are written in **Stage 2B/2C**.
> **Authoritative source:** book v3.0.0 + the locked Stage-1 specification in
> `../spec/`. Nothing here may change a locked fact.
> **Nothing may be implemented before an approved PRD and plan.**

## Purpose

Define the four official artifacts and their lifecycle, the independent replay verifier, the read-only GUI projection, league/series scoring, and the mandatory self-contained result report delivered by e-mail as a JSON attachment.

## Scope

`infra.artifacts`, `infra.replay`, `infra.gui`, `infra.reporter`, series/cumulative scoring in `app.orchestrator`, and the submission evidence set.

## Out of Scope

Game rules (PRD-01), cryptographic primitives (PRD-06 — consumed here), transport internals (PRD-05), strategy (PRD-03).

## Actors

_Stage 2B._ Expected: this **POLICE** agent, the opponent peer, the grader/lecturer, the
local operator (GUI), and — where relevant — external services (GitHub, Gmail, optional
LLM provider). Trust levels are defined in `../architecture/SYSTEM_ARCHITECTURE.md` §3.

## Locked Requirements

**REPORT-001…003** (each team reports; JSON attachment; 429 respect) · **REPLAY-001/002** (replayability, per-step verification) · **GUI-001…003** (no objective board; partial-observation view) · **JSON-001…004** (JSON-only reporting, artifact identity, canonical) · **LEAGUE-001…007** (series, diversity reward, min games, tie rule, num_games 6/FIXED) · **GIT-001…005** (exact played commit reproducibility) · **SUB-001…005** (two repos, four links, group id, Moodle) · **DOC-001…003** · **PERF-001** (token reporting) · conflicts **C-07**, **C-09** · invariants **INV-01…05, 10…13**.

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

`../architecture/ARTIFACT_LIFECYCLE.md` · `DATA_FLOW.md` §8–§11 · `OBSERVABILITY.md` · `QUALITY_GATES.md` (Match + Submission gates) · `SECURITY_ARCHITECTURE.md` T10/T11 (leak, report tampering) · `../spec/json/RESULT_CONTRACT.md` (locked contract).

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

GUI toolkit choice (must not influence the projection contract); screenshot/evidence format; Gmail delivery mechanism and credential source (environment only); exact replay report format.

## Requirement IDs

See **Locked Requirements** above; full mapping in
`../architecture/ARCHITECTURE_TRACEABILITY.md`.
