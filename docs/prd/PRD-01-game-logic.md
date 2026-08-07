# PRD-01 - Game Logic — group MaRs-777 (POLICE)

> **STATUS: BLUEPRINT — NOT YET APPROVED PRD**
> Stage 2A populated only *Purpose*, *Scope*, *Out of Scope*, the locked *Requirement
> IDs*, and the *Architecture Dependencies*. Detailed functional requirements,
> acceptance criteria and tests are written in **Stage 2B/2C**.
> **Authoritative source:** book v3.0.0 + the locked Stage-1 specification in
> `../spec/`. Nothing here may change a locked fact.
> **Nothing may be implemented before an approved PRD and plan.**

## Purpose

Define the deterministic game domain: board topology and coordinates, movement legality, barrier legality and irreversibility, capture conditions, turn order, terminal/status conditions, and Appendix-F scoring (including the technical-loss 0/0 rule whose provenance is Ch 3 + App E #48, **not** Appendix F — C-07).

## Scope

The pure `domain` layer: `domain.board`, `domain.rules`, `domain.scoring`, `domain.barriers`, `domain.config_model`, `domain.truth`. All logic here is deterministic, side-effect free, and independently unit-testable.

## Out of Scope

Networking and FastMCP (PRD-02/05), cryptography and commit-reveal (PRD-06), strategy decision-making (PRD-03), hints/scent inference (PRD-04), GUI/replay/reporting (PRD-07). Movement **legality** belongs here; movement **choice** does not.

## Actors

_Stage 2B._ Expected: this **POLICE** agent, the opponent peer, the grader/lecturer, the
local operator (GUI), and — where relevant — external services (GitHub, Gmail, optional
LLM provider). Trust levels are defined in `../architecture/SYSTEM_ARCHITECTURE.md` §3.

## Locked Requirements

**GAME-001…009** (config equality/enforcement, move set, board, scoring incl. technical_loss, step ceiling) · **BAR-001…005** (open truthful declaration, no lying, capture-by-barrier, placement rule, quota) · **LLM-001** (legality never delegated to an LLM — constraint on this PRD) · conflicts **C-01** (board ≥7), **C-05** (num_games 6/FIXED), **C-07** (technical_loss).

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

`../architecture/MODULE_BOUNDARIES.md` (domain layer) · `STATE_OWNERSHIP.md` · `STATE_MACHINE.md` (VALIDATING/TURN_COMPLETE) · `ERROR_MODEL.md` (`E-LOCAL-VALIDATION`, `E-PROTO-ILLEGAL-MOVE`, `E-PROTO-BARRIER`) · `DEPENDENCY_RULES.md` (domain imports nothing outward).

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

Exact internal representation of board/coordinates; how rules and scoring are split to respect the ≤150-line rule; validator error-reporting granularity.

## Requirement IDs

See **Locked Requirements** above; full mapping in
`../architecture/ARCHITECTURE_TRACEABILITY.md`.
