# PRD-06 - Security and Cryptography — group MaRs-777 (POLICE)

> **STATUS: BLUEPRINT — NOT YET APPROVED PRD**
> Stage 2A populated only *Purpose*, *Scope*, *Out of Scope*, the locked *Requirement
> IDs*, and the *Architecture Dependencies*. Detailed functional requirements,
> acceptance criteria and tests are written in **Stage 2B/2C**.
> **Authoritative source:** book v3.0.0 + the locked Stage-1 specification in
> `../spec/`. Nothing here may change a locked fact.
> **Nothing may be implemented before an approved PRD and plan.**

## Purpose

Define the cryptographic and security core: canonical byte production, the unkeyed SHA-256 commitment (`H_commit`), nonce custody and commit-reveal, source-required **keyed authentication** for Step-0 and the config signature exchange, the config lock, and the result agreement digest.

## Scope

`protocol.canonical`, `protocol.commitment`, `protocol.keyed_auth`, `protocol.config_lock`, `protocol.declaration`, secret handling in `infra.settings`, and the security test suite.

## Out of Scope

Game rules (PRD-01), transport mechanics (PRD-05), strategy (PRD-03), report assembly/delivery (PRD-07 — though `result_sha256` is specified here).

## Actors

_Stage 2B._ Expected: this **POLICE** agent, the opponent peer, the grader/lecturer, the
local operator (GUI), and — where relevant — external services (GitHub, Gmail, optional
LLM provider). Trust levels are defined in `../architecture/SYSTEM_ARCHITECTURE.md` §3.

## Locked Requirements

**CRYPTO-001…011** (commit-reveal, nonce freshness/secrecy, recompute-and-compare, signed Step-0, no false capture claim, canonical sealed record) · **SEC-001…006** (secret handling, no secrets in Git, isolation) · **GAME-001/002** (config equality and Appendix-F enforcement at lock time) · **JSON-004** (canonical hashable JSON) · conflicts **C-08** (verdict=intent), **C-09** (reporting sanction) · invariants **INV-06/14/15**.

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

`../architecture/SECURITY_ARCHITECTURE.md` (threat table, taxonomy) · `DATA_FLOW.md` §1/§2/§4 · `ARTIFACT_LIFECYCLE.md` (non-self-referential digests) · `ERROR_MODEL.md` (`E-AUTH-FAILURE`, `E-HASH-MISMATCH`, `E-NONCE-MISMATCH`, `E-TAMPERED`) · `../spec/json/SIGNATURE_AND_HASH_PROVENANCE.md` (locked taxonomy).

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

Whether the negotiated keyed primitive stays HMAC-SHA256 (project default, **not** lecturer-specified) or an asymmetric signature if the opponent requires it; key provisioning channel; whether Step-0 and config use the same or distinct keys (source-unspecified — agreed pre-match).

## Requirement IDs

See **Locked Requirements** above; full mapping in
`../architecture/ARCHITECTURE_TRACEABILITY.md`.
