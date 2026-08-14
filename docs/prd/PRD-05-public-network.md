# PRD-05 — Public Network and Tunnel — group MaRs-777 (POLICE)

## 1. Document Metadata

| Field | Value |
|---|---|
| PRD | PRD-05 — Public Network & Tunnel |
| Repository role | **POLICE** |
| Owns | Public reachability, tunnel lifecycle, endpoint identity/exchange, network readiness gate, series-convention agreement, connectivity failure semantics |
| Architecture inputs | `SYSTEM_ARCHITECTURE.md` §3 (TB-1), `CONCURRENCY_MODEL.md` §4, `SECURITY_ARCHITECTURE.md` T8/T15, `API_BOUNDARIES.md` (`PeerTransportPort`, `PeerServerPort`) |
| Symmetry class | **COMMON-WITH-ROLE-SECTIONS** (role identity only) |

## 2. Status

**APPROVED — PHASE 2 LOCKED.** Approved after Stage 2-CLOSE supervising review.
**Implementation status: IMPLEMENTED-INTEGRATED / LIVE E2E PROOF PENDING.**
The public-ingress path exists and is unit- and integration-tested:
`infra/ngrok_ingress.py`, `infra/ngrok_process.py`, `infra/agent_api.py`
(strict parsing measured against the installed agent), `app/public_ingress.py`,
`app/public_endpoint_binding.py`, `app/public_readiness_gate.py` and
`app/public_network_workflow.py`, behind the provider-neutral
`PublicIngressPort`. **No remote end-to-end run has been demonstrated:** the
live suite is skipped unless `MARS777_RUN_LIVE_NGROK=1` is set and the agent is
installed, which is why all 13 of those tests are reported as skipped. Public
network play must not be claimed as proven until that suite runs green.

## 3. Purpose

Make the agent **reachable by a real opponent over the public internet**, prove that
reachability **before** counted play begins, keep the advertised endpoint bound to the
process actually playing, and define exactly how connectivity failures differ from
protocol/integrity failures.

## 4. Problem Statement

A locally healthy process proves nothing about the public path. A counted league game
played over localhost is not a counted game (NET-003). Worse, a **stale** tunnel URL, or
a silent disagreement about which peer plays which role in a sub-game, produces a match
that looks live but is invalid. All three must be structurally prevented.

## 5. Scope

Public exposure of the local FastMCP server · tunnel lifecycle · public endpoint identity
and re-advertisement · opponent endpoint exchange · bidirectional readiness gate ·
series-convention agreement (fixed vs alternating roles) · connectivity failure taxonomy
· network secrets boundary · connectivity evidence.

## 6. Out of Scope

Local FastMCP application semantics, state machine, retry **scheduling** (**PRD-02**) ·
cryptographic message validity, peer authentication (**PRD-06**) · game rules
(**PRD-01**) · reporting/Gmail (**PRD-07**).

## 7. Actors

This **POLICE** agent · the opponent peer (untrusted) · the tunnel provider
(untrusted infrastructure) · the local operator (provisions credentials) · `SeriesLauncher`
(PRD-02, operational only).

## 8. Definitions

| Term | Meaning |
|---|---|
| **Local bind address** | Host/port the FastMCP server listens on (e.g. loopback) — **never** a counted-match endpoint |
| **Public tunnel URL** | Publicly resolvable URL that forwards to the local bind address |
| **Opponent endpoint** | The peer's public URL we call |
| **Advertised endpoint** | The public URL we publish in the declaration for a given sub-game |
| **Series convention** | The agreed role assignment across sub-games: `FIXED_ROLE` or `REFERENCE_ODD_EVEN_ALTERNATION` |
| **Readiness gate** | The pre-counted-play check that must pass before any counted turn |

## 9. Locked Source Requirements

| ID | Modality | Scope | Requirement |
|---|---|---|---|
| **NET-001** | MUST | BOTH | Expose the local FastMCP server to the **public internet via a tunnelling tool** (e.g. ngrok / Localtonet); localhost is not sufficient |
| **NET-003** | MUST | BOTH | Communicate over the negotiated **public** transport in counted league games (**not localhost**) |
| NET-004 | MUST | BOTH | MCP via FastMCP, not replaceable *(owned by PRD-02; constrains the tunnel target)* |
| STATE-004/005 | MUST | BOTH | Deadline tracker / watchdog *(owned by PRD-02; consumed here)* |
| SEC-003/004 | MUST / MUST NOT | BOTH | Never push secrets; git-ignore credential files *(owned by PRD-06; applied here to tunnel credentials)* |
| GIT-003 | MUST | BOTH | Exact played commit recorded per game *(owned by PRD-07; endpoint/commit must describe the same running process)* |

The book names ngrok/Localtonet **as examples**. This PRD is therefore **provider-neutral**.

## 10. Project / Architecture Decisions

| Decision | Type |
|---|---|
| Provider-neutral tunnel abstraction; no provider lock-in | **PROJECT-CONTRACT** (source says "e.g.") |
| Ports 8801 / 8802 and `127.0.0.1` | **REFERENCE-COMPATIBILITY ONLY** — never binding |
| Series convention is an **explicit pre-series agreement** | **NEGOTIATED-PRE-MATCH** |
| Endpoint published in the declaration; identity via `game_id`/`game_uid`/`group_id` | **ARCHITECTURE-CONSTRAINT** (INV-01) |
| Tunnel credentials are local secrets | **ARCHITECTURE-CONSTRAINT** (TB-6) |
| Application logic stays behind `PeerTransportPort`/`PeerServerPort` | **ARCHITECTURE-CONSTRAINT** (D3) |

## 11. Inputs

Local bind host/port (local settings) · tunnel provider configuration + **credentials from
environment** · our `group_id`, `game_id`, `game_uid`, active role · opponent's advertised
endpoint (from declaration exchange) · negotiated series convention.

## 12. Outputs

Our advertised public endpoint · readiness verdict (`READY` / `NOT_READY` + reason) ·
connectivity evidence records · endpoint-change notifications · connectivity failure events
for PRD-02 to schedule against.

## 13. Functional Requirements

### 13.1 Public reachability

| ID | Requirement | Provenance |
|---|---|---|
| **PRD05-FR-001** | The local FastMCP server MUST be exposed to the public internet through a tunnelling tool for any counted league game. | **SOURCE-MANDATORY** (NET-001) |
| **PRD05-FR-002** | A counted league game MUST use the negotiated **public** transport. **Localhost/loopback endpoints are rejected as counted-match endpoints.** | **SOURCE-MANDATORY** (NET-003) |
| **PRD05-FR-003** | The system MUST distinguish three separate values and never substitute one for another: **local bind address**, **public tunnel URL**, **opponent endpoint**. | **ARCHITECTURE-CONSTRAINT** |
| **PRD05-FR-004** | An advertised endpoint whose host resolves to loopback (`127.0.0.0/8`, `::1`, `localhost`) or to a link-local/private-only address MUST be rejected for counted play with reason `E-NET-NOT-PUBLIC`. | **SOURCE-MANDATORY** (NET-003) |
| **PRD05-FR-005** | The tunnel provider is **abstracted behind a port**; application and domain logic MUST NOT reference any provider name, SDK, or URL scheme specific to a provider. | **PROJECT-CONTRACT** |
| **PRD05-FR-006** | Ports `8801`/`8802` and `127.0.0.1` are **REFERENCE-ONLY defaults** and are **not binding**; local bind values come from local settings. | **REFERENCE-COMPATIBILITY** |
| **PRD05-FR-007** | Uncounted warm-up games MAY run over a non-public transport, but MUST be recorded as **uncounted**. | **SOURCE-PERMITTED** (LEAGUE-005 allows uncounted warm-ups) |

### 13.2 Endpoint identity

| ID | Requirement | Provenance |
|---|---|---|
| **PRD05-FR-010** | The advertised endpoint for a sub-game MUST be the endpoint that actually serves **the process participating in that sub-game** (correct role, correct repository). | **ARCHITECTURE-CONSTRAINT** |
| **PRD05-FR-011** | The endpoint is published in the **declaration** and is bound to the game identity: `game_id`, `game_uid`, `group_id`, active role. | INV-01; **ARCHITECTURE-CONSTRAINT** |
| **PRD05-FR-012** | An endpoint value MUST NOT create or imply a **second game identity**. Identity is `game_id`/`game_uid` only; the URL is an attribute of the peer, never an identifier of the game. | INV-01 |
| **PRD05-FR-013** | Before counted play, each peer MUST verify that the endpoint it will call is the one advertised **for this `game_uid` and this sub-game**; a mismatch is `E-NET-STALE-ENDPOINT` and blocks counted play. | **ARCHITECTURE-CONSTRAINT** |
| **PRD05-FR-014** | The advertised endpoint MUST carry **no secret** (no token in path, query or fragment). | **SOURCE-MANDATORY** (SEC-003 spirit); T15 |
| **PRD05-FR-015** | **[CLOSE-F2]** The declared endpoint is a **stable GROUP-level public ingress for the declared series** — the locked declaration carries **one `mcp_endpoint` per team (`teams.<g>.mcp_endpoint`, cardinality 1/team), not one per role**. It is **static whole-series data** and MUST remain consistent with the locked declaration for the whole series. | **SOURCE-SEMANTIC** (Ch 9 p.78 static declaration); FIELD_MATRIX `1/team` |
| **PRD05-FR-015a** | **[CLOSE-F2]** **Local** changes behind that ingress — local bind host/port, restarting a process, or switching which independent role process is active — are permitted and **do not change the declared endpoint**, provided the tunnel/router abstraction preserves the same public ingress value. | **ARCHITECTURE-CONSTRAINT**; ARCH-001/002 |
| **PRD05-FR-015b** | **[CLOSE-F2]** If the **declared public ingress itself** becomes unavailable and can only be replaced by a **different public URL** mid-series: the system MUST **NOT silently mutate the locked declaration**, and MUST **NOT merely re-advertise and continue** as though the declaration were unchanged. Counted play **pauses/refuses**; recovery of the *same* declared ingress is attempted first; if identity-critical replacement is unavoidable, the current locked declaration is **no longer valid for silent continuation** and a defined **re-negotiation / new declaration-game boundary** is required before further counted play. | **ARCHITECTURE-CONSTRAINT**; INV-01 (identity) |
| **PRD05-FR-015c** | **[CLOSE-F2]** Endpoint unavailability is a **transport failure, not an integrity failure**, and **no score sanction is invented for it**. Only the locked sanctions apply. | `ERROR_MODEL.md`; C-07/C-09 unchanged |
| **PRD05-FR-016** | Endpoint changes MUST be recorded as connectivity evidence with the sub-game and step at which they occurred. | REPLAY-001/002 (evidence) |

### 13.3 Network readiness gate

| ID | Requirement | Provenance |
|---|---|---|
| **PRD05-FR-020** | Counted play MUST NOT begin until the **readiness gate** passes. A healthy local process is explicitly **not** sufficient evidence. | **SOURCE-MANDATORY** (NET-001/003) |
| **PRD05-FR-021** | The gate MUST establish, in order: (a) local server running and bound; (b) public tunnel established; (c) our public URL known and non-loopback; (d) opponent endpoint known; (e) **outbound** reachability to the opponent proven; (f) **inbound** reachability proven (the opponent actually reached us); (g) the responding peer is the **expected** peer for this game identity; (h) **Step-0 authentication has completed and was not bypassed**; (i) the binding config has not been mutated since lock; (j) the required **profile and series convention are agreed and frozen**. | **ARCHITECTURE-CONSTRAINT** + INV-14/15 |
| **PRD05-FR-022** | **Bidirectional** reachability is mandatory: one-way success is insufficient. Both directions MUST be demonstrated within the readiness window. | **ARCHITECTURE-CONSTRAINT** |
| **PRD05-FR-023** | The gate produces a machine-readable verdict with a specific failure reason; `NOT_READY` blocks the transition out of `STEP0_NEGOTIATION`/`CONFIG_LOCKED` toward counted turns. | PRD-02 state machine |
| **PRD05-FR-024** | The readiness probe MUST NOT bypass authentication, and MUST NOT be usable as a substitute for Step-0 verification. | INV-14; **SOURCE-MANDATORY** (CRYPTO-006) |
| **PRD05-FR-025** | The gate is re-run after any endpoint change, tunnel restart, or role/process switch. | **ARCHITECTURE-CONSTRAINT** |

### 13.4 Series convention (role assignment across sub-games)

| ID | Requirement | Provenance |
|---|---|---|
| **PRD05-FR-030** | The **series convention** MUST be one of `FIXED_ROLE` or `REFERENCE_ODD_EVEN_ALTERNATION`, and MUST be **explicitly agreed before the first affected sub-game**. | **NEGOTIATED-PRE-MATCH** |
| **PRD05-FR-031** | **Role alternation is NOT source-mandated.** It is a reference/attachment convention (AE-01). **`FIXED_ROLE` is equally NOT source-mandated.** Neither may be presented as a book requirement. | **REFERENCE-COMPATIBILITY** / **ATTACHMENT-COMPATIBILITY** |
| **PRD05-FR-032** | There MUST be **no default that can silently differ between peers**. If the convention is not explicitly agreed and echoed by both sides, counted play is refused with `E-NET-CONVENTION-UNSET`. | **ARCHITECTURE-CONSTRAINT** |
| **PRD05-FR-033** | A convention **mismatch** (each peer echoing a different value) MUST block counted play with `E-NET-CONVENTION-MISMATCH`; it MUST NOT be resolved by preferring either side's value. | **ARCHITECTURE-CONSTRAINT** |
| **PRD05-FR-034** | **[CLOSE-F1]** The agreed convention is **NEGOTIATED-PRE-MATCH protocol metadata**. It MUST be proposed, **echoed by the opponent**, mutually agreed, **authenticated as part of the pre-series negotiation evidence**, and **frozen no later than `CONFIG_LOCKED`**. It is recorded in the **negotiation record / profile evidence** — the same already-approved, non-authoritative evidence mechanism used for canonical-serialization parameters, sealed-record composition and `state` representation (NDEC-001/002/003). | **NEGOTIATED-PRE-MATCH**; NDEC-003 pattern; PRD-02 FR-080/082; PRD-06 FR-122 |
| **PRD05-FR-034a** | **[CLOSE-F1]** It **MUST NOT** be represented as a field of `declaration_<game_id>.json`. The locked declaration contract — **16 fields when this requirement was written, 15 since Stage 4E-R12-R1 removed `token_usage_locked`** — contains **no series-convention slot**, and **no field may be added**: the official four-artifact matrix stays at **75** (declaration 16 / config 39 / log 9 / result 11) and **no new JDEC is created** for this. | **ARCHITECTURE-CONSTRAINT**; FIELD_MATRIX (locked) |
| **PRD05-FR-034b** | **[CLOSE-F1]** The frozen convention MUST be available to `SeriesLauncher`/orchestration and **persisted as negotiation/profile evidence sufficient for later audit and replay**. | REPLAY-001/002; PRD-02 FR-082 |
| **PRD05-FR-035** | Under `REFERENCE_ODD_EVEN_ALTERNATION`, for each sub-game the peers MUST also agree **which concrete endpoint** serves which role, since the active process changes (see §13.5). | **ARCHITECTURE-CONSTRAINT** |

### 13.5 Tunnel and process lifecycle

| ID | Requirement | Provenance |
|---|---|---|
| **PRD05-FR-040** | Permitted lifecycle models (none pre-selected here): **(a)** persistent per-role endpoint reused across the series; **(b)** restart/rebind between sub-games; **(c)** `SeriesLauncher` activating independent role processes per sub-game. | **PROJECT-CONTRACT** (open decision) |
| **PRD05-FR-041** | Whichever model is implemented MUST guarantee: no shared Police/Thief game state; no cross-repo imports; stale endpoints invalidated; changed endpoints re-advertised; opponent acknowledgement before continued counted play. | **SOURCE-MANDATORY** (ARCH-001/002) + FR-015 |
| **PRD05-FR-042** | The `SeriesLauncher` remains **operational only** — it starts/stops processes and selects which endpoint is advertised. It **owns no game truth and is never a referee**. | **SOURCE-MANDATORY** (ARCH-001/002); PRD-02 FR-012 |
| **PRD05-FR-043** | **[CLOSE-F2]** After a role/process switch **behind the same declared ingress**, the ingress value is unchanged; the **local route** MUST be re-verified as serving the newly active role process before counted play resumes. A *different public ingress* is governed by FR-015b. | FR-013; FR-015a/b |
| **PRD05-FR-044** | Tunnel establishment MUST be verified (URL obtained **and** reachable), not merely requested. | FR-020/022 |

### 13.5a Endpoint cardinality and role routing (CLOSE-F2)

**Cardinality (locked):** `teams.<g>.mcp_endpoint`, **one per team/group**, `1/team` in the
FIELD_MATRIX — **not** one per role. The declaration therefore already describes a
**group-level** ingress.

**Can strict counted-match role alternation work without new declaration fields? YES.**

```
        opponent peer
              |  (single stable declared public ingress per group)
              v
   PUBLIC GROUP ENDPOINT   <-- the value in teams.<g>.mcp_endpoint (static, whole-series)
              |
     local routing / SeriesLauncher      <-- operational only; holds no game truth
         |                    |
         v                    v
  POLICE process         THIEF process    <-- separate OS processes, separate repos,
  (mars777_police)       (mars777_thief)      no shared mutable state, no cross-import
```

The router/ingress **does not**: hold game truth · act as a referee · merge the Police and
Thief packages · share role-mutable state. Exactly one role process is active per
sub-game; switching which one is active is a **local** operation invisible to the declared
endpoint value, so **no declaration field changes and the four-artifact matrix stays 74**.

### 13.6 Network secrets

| ID | Requirement | Provenance |
|---|---|---|
| **PRD05-FR-050** | Tunnel/provider credentials (auth tokens, API keys, reserved-domain secrets) are **local secrets**, loaded from the environment only. | **SOURCE-MANDATORY** (SEC-003) |
| **PRD05-FR-051** | Credentials MUST NOT appear in: shared config, declaration, log, result, Git, GUI, error messages, metric labels, or LLM prompts. | **SOURCE-MANDATORY** (SEC-003/004); T18 |
| **PRD05-FR-052** | Credential files MUST be git-ignored; a leaked credential MUST be **rotated at the provider**, not merely deleted from the working tree. | **SOURCE-MANDATORY** (SEC-004, SEC-005) |
| **PRD05-FR-053** | The **public URL itself is not a secret**, but MUST still carry no embedded token (FR-014). Documentation and tests MUST NOT contain values resembling real credentials. | **PROJECT-CONTRACT** |

### 13.7 Connectivity failure model

| ID | Class | Requirement | Provenance |
|---|---|---|---|
| **PRD05-FR-060** | RETRYABLE | Tunnel creation failure, DNS/URL resolution failure, TLS/HTTP connection failure, request timeout, transient 5xx, half-open peer, tunnel dies mid-turn ⇒ typed **transport** errors surfaced to PRD-02 for retry scheduling. | `ERROR_MODEL.md` `E-TRANSPORT` |
| **PRD05-FR-061** | RETRYABLE (paced) | **HTTP 429** ⇒ back off and wait for the next window; **never** retry immediately. | **SOURCE-MANDATORY** (REPORT-003 discipline; NET-002 pattern) |
| **PRD05-FR-062** | TERMINAL-ish | Retry exhaustion ⇒ `E-RETRY-EXHAUSTED`, escalated per PRD-02; connectivity does not itself decide a game outcome. | `ERROR_MODEL.md` |
| **PRD05-FR-063** | BLOCKING | Endpoint not public, stale endpoint, unverified bidirectional reachability, convention unset/mismatch ⇒ **refuse counted play** (not retried into success). | FR-004/013/022/032/033 |
| **PRD05-FR-064** | NON-RETRYABLE | Authentication, config-equality and integrity failures are **PRD-06** concerns and MUST NOT be retried as if they were transport problems. | `ERROR_MODEL.md` principle 2 |
| **PRD05-FR-065** | — | A **network failure MUST NOT be reported or logged as a cryptographic/integrity failure**, and vice-versa; the two taxonomies stay disjoint. | **ARCHITECTURE-CONSTRAINT** |
| **PRD05-FR-066** | — | Opponent disconnect and process restart produce deterministic, evidenced outcomes; the game never silently continues against an unverified endpoint. | STATE-004/005 |

### 13.8 Security boundary

| ID | Requirement | Provenance |
|---|---|---|
| **PRD05-FR-070** | **All public inbound traffic is untrusted** and MUST pass the PRD-02 Gatekeeper and PRD-06 authentication/integrity checks before reaching any application logic. | **ARCHITECTURE-CONSTRAINT** (TB-1) |
| **PRD05-FR-071** | Tunnel exposure MUST NOT grant direct access to internal domain state, the filesystem, GUI internals, or strategy internals. Only the declared FastMCP surface is reachable. | T8/T15 |
| **PRD05-FR-072** | Public exposure MUST apply the inbound bounds already required by PRD-02 (payload size, nesting depth, queue depth, rate limit) — exposure widens the attack surface, not the limits. | T8; App F T19 |
| **PRD05-FR-073** | The endpoint MUST NOT be relied upon as a secret; **authority derives from keyed authentication and hashes**, never URL obscurity. | T15; INV-14 |

## 14. Non-Functional Requirements

| ID | Requirement |
|---|---|
| **PRD05-NFR-001** | The readiness gate completes or fails within a bounded window (default **60 s**, local setting — not an Appendix-F value) with a specific reason. |
| **PRD05-NFR-002** | **Core network logic is testable offline** with a fake tunnel/transport adapter; no public internet in unit/contract/integration tests. |
| **PRD05-NFR-003** | Real public-tunnel verification is an explicitly **manual/E2E gate**, not a CI requirement. |
| **PRD05-NFR-004** | Every file ≤ **150 lines**; tunnel adapter, readiness gate and endpoint registry are separate modules. |
| **PRD05-NFR-005** | Zero provider-specific identifiers outside the single tunnel adapter module (import/grep test). |

## 15. Lifecycle / State Responsibilities

Owns: tunnel handle, advertised endpoint, opponent endpoint, readiness verdict, agreed
series convention (recorded), connectivity evidence. **Does not own:** state-machine phase
(PRD-02), retry scheduling (PRD-02), peer authenticity (PRD-06), game truth (PRD-01).

## 16. Validation Rules

Endpoint scheme/host validity · non-loopback / non-private · matches the advertised value
for this `game_uid` and sub-game · opponent identity matches the negotiated `group_id` ·
bidirectional probe succeeded within the window · convention present, agreed and echoed ·
no credential material in any advertised value.

## 17. Failure Behaviour

`E-NET-NOT-PUBLIC` · `E-NET-STALE-ENDPOINT` · `E-NET-UNREACHABLE` ·
`E-NET-ONE-WAY-ONLY` · `E-NET-CONVENTION-UNSET` · `E-NET-CONVENTION-MISMATCH` ·
`E-NET-TUNNEL-FAILED` — all **block counted play** rather than degrade.
Transport-class failures map to `E-TRANSPORT` / `E-RATE-429` / `E-RETRY-EXHAUSTED` for
PRD-02 scheduling. **No new game sanction is invented here.**

## 18. Security / Privacy

Untrusted inbound (TB-1) · untrusted provider infrastructure · credentials env-only and
never serialized · endpoint carries no secret · no internal state exposed through the
tunnel · errors and metrics carry no credential · documentation contains no token-like
strings.

## 19. Determinism / Reproducibility

Network I/O is inherently non-deterministic and is **isolated behind ports** so every
other layer stays deterministic. The **readiness decision logic** (endpoint classification,
convention comparison, staleness detection) is pure and deterministic given its inputs, and
is tested with fakes on both OSes.

## 20. Performance / Deadline Constraints

Readiness window bounded (NFR-001). Per-request deadlines and retry pacing come from the
**locked config** via PRD-02 (`response_timeout_sec` 30 NEGOTIABLE, `watchdog_timeout_sec`
60 NEGOTIABLE, `retry_backoff_sec` 5 MIN, `max_retries` 3 MIN, `requests_per_minute` 30 MIN,
`concurrent_requests` 2 MIN, `queue_depth` 100 MIN). This PRD hard-codes none of them.

## 21. Cross-Platform Constraints

Endpoint parsing/normalisation (scheme, host, port, trailing slash) yields an **identical
canonical representation on Linux and Windows**; IDN/IPv6 handling is deterministic; no
platform-specific networking assumption in the core logic.

## 22. Observability / Evidence

Advertised endpoint (no secret), readiness verdict + reason, probe latencies both
directions, endpoint-change events with sub-game/step, tunnel up/down events, transport
error counts by class, 429 counts, retry counts, agreed series convention. Connectivity
evidence is recorded for replay/report but is **never** a game-outcome authority.

## 23. Acceptance Criteria

| ID | Criterion |
|---|---|
| **PRD05-AC-001** | A healthy local server **alone** does not produce counted-match `READY`; the gate reports which sub-check failed. |
| **PRD05-AC-002** | An advertised endpoint resolving to loopback/private address is rejected with `E-NET-NOT-PUBLIC`. |
| **PRD05-AC-003** | Outbound-only reachability yields `E-NET-ONE-WAY-ONLY`; only bidirectional success yields `READY`. |
| **PRD05-AC-004** | Calling an endpoint that is not the one advertised for this `game_uid`/sub-game is rejected as `E-NET-STALE-ENDPOINT`. |
| **PRD05-AC-005** | Changing our public URL forces re-advertisement + opponent acknowledgement; counted play pauses until acknowledged. |
| **PRD05-AC-006** | A tunnel that dies mid-turn produces a transport error (not a crypto error), correct retry/backoff, and a recorded event. |
| **PRD05-AC-007** | Opponent disconnect yields a deterministic evidenced outcome; no silent continuation. |
| **PRD05-AC-008** | After a role/process switch the previous endpoint is stale and refused until re-verified. |
| **PRD05-AC-009** | Scan: no provider credential appears in config, declaration, log, result, Git, GUI, errors, metrics or prompts. |
| **PRD05-AC-010** | The agreed profile and series convention are frozen at `CONFIG_LOCKED`; a later change attempt is rejected. |
| **PRD05-AC-011** | Peer A `FIXED_ROLE` vs peer B `REFERENCE_ODD_EVEN_ALTERNATION` ⇒ counted play **blocked** with `E-NET-CONVENTION-MISMATCH`; neither value silently wins. |
| **PRD05-AC-012** | Convention absent on either side ⇒ `E-NET-CONVENTION-UNSET`; no implicit default is applied. |
| **PRD05-AC-013** | Swapping the fake tunnel adapter for a different fake requires **no change** in app/domain code (provider independence). |
| **PRD05-AC-014** | Endpoint canonicalisation produces identical results on Linux and Windows for the same input set. |
| **PRD05-AC-015** | The readiness probe cannot be used to skip Step-0 authentication (attempt is rejected). |
| **PRD05-AC-016** | Whole PRD-05 test suite runs **offline**; real tunnel verification is marked manual/E2E. |

## 24. Planned Tests

| ID | Test | Layer |
|---|---|---|
| **PRD05-T-001** | Endpoint classification (public / loopback / private / malformed) | UNIT |
| **PRD05-T-002** | Readiness gate sub-check matrix (each of the 10 conditions) | UNIT |
| **PRD05-T-003** | Bidirectional vs one-way probe | INTEGRATION (fake) |
| **PRD05-T-004** | Stale endpoint detection after change/switch | INTEGRATION |
| **PRD05-T-005** | Endpoint re-advertisement + acknowledgement flow | INTEGRATION |
| **PRD05-T-006** | Tunnel death mid-turn → transport class, not crypto | INTEGRATION |
| **PRD05-T-007** | 429 back-off to next window | INTEGRATION |
| **PRD05-T-008** | Retry exhaustion escalation | INTEGRATION |
| **PRD05-T-009** | Series-convention agreement / mismatch / unset | PROTOCOL |
| **PRD05-T-010** | Convention frozen at config lock | CONTRACT |
| **PRD05-T-011** | Credential-absence scan | SECURITY |
| **PRD05-T-012** | Provider independence (adapter swap) | CONTRACT |
| **PRD05-T-013** | Endpoint canonicalisation cross-OS | PROPERTY |
| **PRD05-T-014** | Readiness cannot bypass Step-0 auth | SECURITY |
| **PRD05-T-015** | Real public tunnel reachability | **MANUAL / E2E (deferred gate)** |

## 25. Requirement Traceability

**Primary owner:** **NET-001**, **NET-003**.
**Consumes / constrained by:** NET-004 (PRD-02), STATE-004/005 (PRD-02), SEC-003/004/005
(PRD-06), CRYPTO-006/INV-14 (PRD-06), GIT-003 (PRD-07), LEAGUE-005 (uncounted warm-ups).
*(NET-002 is the **Gmail** rate-limiter and is owned by **PRD-07** — see
`PRD_01_07_CROSSWALK.md` §Reassignments.)*

## 26. Dependencies on Other PRDs

**Provides:** verified public transport + readiness verdict to PRD-02; agreed series
convention to PRD-02/PRD-06; connectivity evidence to PRD-07.
**Consumes:** PRD-02 (ports, retry scheduling, gatekeeper), PRD-06 (Step-0 auth, config
lock, profile freeze), PRD-07 (declaration/endpoint publication).

## 27. Open Design Decisions

Tunnel provider and account model · which lifecycle model of FR-040 is adopted · reserved
vs ephemeral URL · readiness-probe shape (dedicated tool vs harmless protocol call) ·
IPv6 policy · how endpoints are re-advertised mid-series (protocol message vs new
declaration revision).

## 28. Explicit Non-Goals

No provider lock-in · no local FastMCP semantics · no cryptographic validation · no retry
scheduler (PRD-02 owns it) · no Gmail · no game rules · no dependency added · real tunnel
verification is not a CI gate.

## 29. Implementation Readiness Checklist

- [x] Public-vs-local endpoint separation defined and enforced
- [x] Readiness gate with 10 explicit sub-checks and bidirectional requirement
- [x] Series convention made explicit, agreed, recorded and frozen — no silent default
- [x] Lifecycle models enumerated with invariants that any choice must satisfy
- [x] Credential boundary and rotation rule stated
- [x] Transport vs integrity failure taxonomies kept disjoint
- [x] Offline testability guaranteed; real tunnel deferred to a manual gate
- [ ] Supervising review — **pending**
- [ ] Implementation — **not started**
