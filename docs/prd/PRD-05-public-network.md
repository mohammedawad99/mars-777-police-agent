# PRD-05 - Public Network and Peer Transport — group MaRs-777 (POLICE)

> **STATUS: BLUEPRINT — NOT YET APPROVED PRD**
> Stage 2A populated only *Purpose*, *Scope*, *Out of Scope*, the locked *Requirement
> IDs*, and the *Architecture Dependencies*. Detailed functional requirements,
> acceptance criteria and tests are written in **Stage 2B/2C**.
> **Authoritative source:** book v3.0.0 + the locked Stage-1 specification in
> `../spec/`. Nothing here may change a locked fact.
> **Nothing may be implemented before an approved PRD and plan.**

## Purpose

Define public exposure of the FastMCP endpoint through a tunnel, outbound peer transport, and the Gatekeeper policy: token-bucket rate limiting, concurrency cap, retry/backoff, queue depth, and HTTP-429 handling.

## Scope

`infra.mcp_client`, `infra.gatekeeper`, tunnel/endpoint publication, transport-level error taxonomy and retry policy.

## Out of Scope

Game semantics (PRD-01), cryptographic verification of message contents (PRD-06), strategy (PRD-03), report delivery content (PRD-07 — though the same rate-limit rules apply to Gmail egress).

## Actors

_Stage 2B._ Expected: this **POLICE** agent, the opponent peer, the grader/lecturer, the
local operator (GUI), and — where relevant — external services (GitHub, Gmail, optional
LLM provider). Trust levels are defined in `../architecture/SYSTEM_ARCHITECTURE.md` §3.

## Locked Requirements

**NET-001…004** (public endpoint, token-bucket limiter, retry/backoff, transport obligations) · **REPORT-003** (respect HTTP 429: back off to the next window, never retry blindly) · **STATE-004/005** (response timeout 30s, watchdog 60s) · Appendix F Table 19 rate-limiter rows (all MINIMUM).

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

`../architecture/CONCURRENCY_MODEL.md` §4 (limiter/backoff) · `API_BOUNDARIES.md` (`PeerTransportPort`) · `SECURITY_ARCHITECTURE.md` T8/T15 (DoS, endpoint exposure) · `ERROR_MODEL.md` (`E-TRANSPORT`, `E-RATE-429`, `E-RETRY-EXHAUSTED`).

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

Tunnel provider and endpoint rotation policy; connection reuse; precise backoff curve within the Appendix-F minimums; peer identity pinning beyond keyed authentication.

## Requirement IDs

See **Locked Requirements** above; full mapping in
`../architecture/ARCHITECTURE_TRACEABILITY.md`.
