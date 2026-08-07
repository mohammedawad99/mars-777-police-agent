# PRD-03 - Baseline Strategy — group MaRs-777 (POLICE)

> **STATUS: BLUEPRINT — NOT YET APPROVED PRD**
> Stage 2A populated only *Purpose*, *Scope*, *Out of Scope*, the locked *Requirement
> IDs*, and the *Architecture Dependencies*. Detailed functional requirements,
> acceptance criteria and tests are written in **Stage 2B/2C**.
> **Authoritative source:** book v3.0.0 + the locked Stage-1 specification in
> `../spec/`. Nothing here may change a locked fact.
> **Nothing may be implemented before an approved PRD and plan.**

## Purpose

Define the first replaceable, deterministic, **zero-token** POLICE strategy behind the `StrategyPort` seam: how it consumes a role-legal `Observation` and returns a validated-legal `ProposedAction`, plus the guaranteed fallback action.

## Scope

The strategy plug-in only: decision policy, seeding/determinism, time-boxing, fallback behaviour, and the metrics it emits.

## Out of Scope

Any transport, cryptography, artifact writing, or nonce/hash handling (structurally forbidden to strategy); LLM tactics (PRD-04, and only under the locked mutual-agreement exception); advanced/competitive strategy tuning (later stages).

## Actors

_Stage 2B._ Expected: this **POLICE** agent, the opponent peer, the grader/lecturer, the
local operator (GUI), and — where relevant — external services (GitHub, Gmail, optional
LLM provider). Trust levels are defined in `../architecture/SYSTEM_ARCHITECTURE.md` §3.

## Locked Requirements

**STRAT-001…003** (strategy obligations/freedom) · **LLM-001** (movement algorithmic by default) · **LLM-005** (MAY: LLM move only by documented mutual agreement) · **GUI-001/002** (privacy wall constrains legal strategy inputs) · role-scoped **GAME**/**BAR** rules the strategy must respect.

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

`../architecture/STRATEGY_ARCHITECTURE.md` (the seam, legal inputs/outputs, forbidden powers) · `API_BOUNDARIES.md` (`StrategyPort`, `BeliefPort`) · `DATA_FLOW.md` §3 (privacy proof) · `DEPENDENCY_RULES.md` §2.

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

Baseline policy family (heuristic vs search); belief representation detail; seed provenance and how it is recorded as replay evidence; decision time budget within the step deadline.

## Requirement IDs

See **Locked Requirements** above; full mapping in
`../architecture/ARCHITECTURE_TRACEABILITY.md`.
