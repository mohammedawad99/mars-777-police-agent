# PRD-02 — Local FastMCP and Orchestration — group MaRs-777 (POLICE)

## 1. Document Metadata

| Field | Value |
|---|---|
| PRD | PRD-02 — Local FastMCP & Orchestration |
| Repository role | **POLICE** |
| Owns | `app.*` (orchestrator, state machine, turn service, ports) and `infra.mcp_server`, `infra.mcp_client`, `infra.gatekeeper`, `infra.clock`, `infra.series_launcher` |
| Architecture inputs | `SYSTEM_ARCHITECTURE.md`, `STATE_MACHINE.md`, `CONCURRENCY_MODEL.md`, `API_BOUNDARIES.md`, `DEPENDENCY_RULES.md`, `ERROR_MODEL.md` |
| Symmetry class | **COMMON-WITH-ROLE-SECTIONS** (only §7/§13.2 role identity differs) |

## 2. Status

**APPROVED — PHASE 2 LOCKED.** Approved after Stage 2-CLOSE supervising review.
The requirements below are unchanged by implementation progress.

**Implementation status: LOCAL FASTMCP / TWO-AGENT TRANSPORT IMPLEMENTED-E2E.**
The four tools, nine wire kinds, strict DTOs, inbound routing, outbound client
and typed error mapping are implemented and exercised by real two-agent
localhost runs. Driving a full autonomous game over that transport is **outside
this PRD** and is not yet implemented anywhere.

**Completed implementation slice:** Stage 3C — Local Application / Turn
Orchestration Foundation: `LocalTruth` (board, own position, completed steps);
typed `MoveAction` / `BarrierAction`; a role-specific `LocalTurnService`
capability; atomic local effect application; local completed-step accounting;
and max-moves action exhaustion.

**Still pending within PRD-02:** state machine · orchestrator · application
ports · strategy-API integration · protocol turn lifecycle integration · FastMCP
server/client · Gatekeeper · concurrency / serialized executor · retry and
deadline implementation · SeriesLauncher · runtime composition.

**PRD-02 is NOT implemented, NOT done and NOT complete.**

## 3. Purpose

Specify the **local peer runtime**: how this agent exposes a FastMCP surface, drives
the protocol through an explicit state machine, serializes all mutating work, enforces
deadlines and rate limits, validates inbound peer traffic, and (optionally) selects
which independent role process participates in each sub-game — **without owning game
truth and without acting as a referee**.

## 4. Problem Statement

Two independently written peers must complete a strict Commit → Ack → Reveal → Audit
sequence over an untrusted network, with duplicate, stale, malformed and hostile
messages possible at any moment. A race or an out-of-order application is
indistinguishable from cheating and can void a match. The runtime must therefore make
illegal sequencing **structurally impossible**, not merely unlikely.

## 5. Scope

Local peer process and composition root · FastMCP **server** and **client** lifecycles ·
orchestrator + turn service · explicit state machine · Gatekeeper (inbound validation,
rate limiting, backpressure) · clock/deadline/watchdog · retry orchestration ·
`SeriesLauncher` (local operational helper) · compatibility-profile selection and
freezing.

## 6. Out of Scope

Public tunnel provider, exposure and egress policy (**PRD-05**) · cryptographic
primitives, commitment/keyed auth internals (**PRD-06**) · game rules (**PRD-01**) ·
decision policy (**PRD-03**) · hint/scent interpretation, LLM (**PRD-04**) ·
reporting, GUI, replay (**PRD-07**).

## 7. Actors

This **POLICE** agent process · the opponent peer (untrusted, TB-1) · the local
operator (starts/stops the runtime; may run the `SeriesLauncher`) · the domain
(PRD-01) · the strategy plug-in (PRD-03).

## 8. Definitions

**Turn cursor** = `(sub_game, step)` — the transmitted identity of a **turn-scoped**
semantic message, used for staleness/idempotency (FR-044, FR-063). **Phase
admissibility** is a separate, receiver-side check: the receiver asks whether this
message family is admissible in **its own** `ProtocolMachine` state (FR-021, FR-062,
STATE-003) — no phase value is transmitted. *(Stage 4E-R1-FIX1 consistency correction;
this definition previously read `(sub_game, step, phase)`, contradicting FR-044/FR-063.)* **Turn Executor** = the single serialized component that applies mutating
events. **Profile** = the negotiated `AuthProfile` / `CommitmentCodec` / `ResultProfile`
set, frozen at config lock. **SeriesLauncher** = local helper that activates the
appropriate independent role process per sub-game.

## 9. Locked Source Requirements

| ID | Modality | Requirement |
|---|---|---|
| ARCH-001 | MUST | Run police and thief as two completely separate OS processes |
| ARCH-002 | **MUST NOT** | No shared memory / variables / live-state module |
| ARCH-003 | MUST | Separate config directories per role |
| ARCH-004 | MUST | Each agent is FastMCP **server + client** (symmetric) |
| ARCH-005 | MUST | JSON config overlays/overrides private TOML |
| STATE-001 | MUST | Orchestrator is the single gateway to all sub-systems |
| STATE-002 | MUST | Manage game phases with a **strict state machine** |
| STATE-003 | MUST | Reject any illegal state transition immediately; `TECHNICAL_LOSS` terminal |
| STATE-004 | MUST | Deadline Tracker: every MCP request carries an expiry; controlled retry on timeout |
| STATE-005 | MUST | Watchdog monitoring heartbeat; controlled shutdown on prolonged freeze |
| NET-001 | MUST | MCP endpoint published (no secret in the URL) |
| NET-004 | MUST | MCP via FastMCP, not replaceable |
| JSON-003/004 | MUST | Artifact identity and canonical JSON as consumed here |

## 10. Project / Architecture Decisions

| Decision | Type |
|---|---|
| Single asyncio loop; one serialized Turn Executor | ARCHITECTURE-CONSTRAINT (`CONCURRENCY_MODEL.md`) |
| Turn-cursor guard + idempotent re-delivery | ARCHITECTURE-CONSTRAINT (`STATE_MACHINE.md` R6/R8) |
| Application depends on `PeerTransportPort` / `PeerServerPort`, never a concrete adapter | ARCHITECTURE-CONSTRAINT (D3/D4) |
| Tool names `negotiate`, `receive_turn`, `submit_audit`, `receive_control` | **REFERENCE-COMPATIBILITY DEFAULT — NOT BOOK-MANDATED** |
| Series convention (fixed vs alternating roles) | **NEGOTIATED-PRE-MATCH** — agreed, recorded and frozen by PRD-05; executed by `SeriesLauncher`. Alternation is a REFERENCE/ATTACHMENT convention (AE-01), never a game rule, and **`FIXED_ROLE` is equally not source-mandated** |
| Timeout values | **NEGOTIATED-PRE-MATCH** from locked config (App F defaults 30 s / 60 s, status NEGOTIABLE) |

## 11. Inputs

Local settings + secrets from environment (PRD-06 owns secret handling) · the locked
config and its identity (`config_sha256`) · inbound peer messages · clock events ·
strategy proposals · domain verdicts.

## 12. Outputs

Outbound peer messages · state-machine transitions + evidence records · deadline and
retry events · sub-game/series completion signals · profile selection record.

## 13. Functional Requirements

### 13.1 Process model

| ID | Requirement | Traces to |
|---|---|---|
| **PRD02-FR-001** | Exactly **one** peer runtime per active role implementation, running as its **own OS process**. | ARCH-001 |
| **PRD02-FR-002** | The Police and Thief repositories remain **independently runnable**; neither imports the other's package, and no module path crosses the two roots. | ARCH-002; TB-3 |
| **PRD02-FR-003** | No shared mutable game state, shared memory, shared venv or shared artifact directory between the two role processes. | **ARCH-002** |
| **PRD02-FR-004** | Exactly **one composition root** constructs concrete adapters and injects them behind ports. | `DEPENDENCY_RULES.md` D3/D4 |
| **PRD02-FR-005** | Per-role configuration directories are separate. | ARCH-003 |
| **PRD02-FR-006** | Local JSON config overlays the private per-peer TOML; the **binding** signed config still has exactly one source and no override chain. | ARCH-005; `CONFIG_ARCHITECTURE.md` R2 |
| **PRD02-FR-007** | Startup order: load settings/secrets → refuse start if a required secret is missing → start FastMCP server → readiness gate → `STEP0_NEGOTIATION`. | `STATE_MACHINE.md` BOOT |
| **PRD02-FR-008** | Graceful shutdown drains the executor queue, seals in-flight evidence, then stops the server; a half-written artifact is never left behind. | `ARTIFACT_LIFECYCLE.md` rule 2 |

### 13.2 SeriesLauncher

| ID | Requirement | Traces to |
|---|---|---|
| **PRD02-FR-010** | The `SeriesLauncher` is a **local operational helper** that selects which independent role process participates in a given sub-game. | `SYSTEM_ARCHITECTURE.md` §5 |
| **PRD02-FR-011** | It executes the **agreed series convention** — `FIXED_ROLE` or `REFERENCE_ODD_EVEN_ALTERNATION` — as negotiated and frozen by **PRD-05** (PRD05-FR-030…035). **Neither value is source-mandated, and there is NO silent default**: if the convention is unset or the peers echo different values, counted play is **refused** (`E-NET-CONVENTION-UNSET` / `E-NET-CONVENTION-MISMATCH`). The launcher never chooses a convention on its own. | AE-01; **NEGOTIATED-PRE-MATCH**; PRD-05 §13.4 |
| **PRD02-FR-012** | It **owns no game truth**, performs no validation, computes no score, and is **not a referee**. | ARCH-001/002 |
| **PRD02-FR-013** | It MUST NOT import one role package into the other; it starts/stops processes only. | `MODULE_BOUNDARIES.md` cross-cutting rule |
| **PRD02-FR-014** | This repository implements **one** role. The lecturer's single-repository dual-role design is **not** adopted. | ARCH-001; `LECTURER_REFERENCE_AUDIT.md` §5 |
| **PRD02-FR-015** | Persistent process/tunnel lifetime across sub-games is **deferred to PRD-05** where it crosses public exposure. | scope boundary |

### 13.3 State machine

| ID | Requirement | Traces to |
|---|---|---|
| **PRD02-FR-020** | The state machine is the **sole** authority on what may happen next; the orchestrator asks and never assumes. | **STATE-001, STATE-002** |
| **PRD02-FR-021** | Any event that does not match the current state **and** the expected turn cursor is **rejected immediately** without side effects. | **STATE-003** |
| **PRD02-FR-022** | Implemented states: `BOOT`, `STEP0_NEGOTIATION`, `CONFIG_NEGOTIATION`, `CONFIG_LOCKED`, `READY`, `TURN_DECISION`, `COMMIT_SENT`, `ACKNOWLEDGED`, `REVEAL`, `VALIDATING`, `TURN_COMPLETE`, `SUBGAME_COMPLETE`, `SERIES_COMPLETE`, `FINAL_AUDIT`, `REPORT_READY`, plus terminals `FAILED`, `TAMPERED`, `TECHNICAL_LOSS`. | `STATE_MACHINE.md` |
| **PRD02-FR-023** | **No counted turn** is reachable unless Step-0 keyed authentication verified **and** the config lock succeeded. | INV-14/15 |
| **PRD02-FR-024** | `COMMIT_SENT` cannot reach `REVEAL` without `ACKNOWLEDGED`. | R1 |
| **PRD02-FR-025** | No transition releases a nonce before `FINAL_AUDIT`. | CRYPTO-002; R2 |
| **PRD02-FR-026** | Effects apply only on `VALIDATING → TURN_COMPLETE`. | R4 |
| **PRD02-FR-027** | `TAMPERED` and `FAILED` are terminal and never return to play; `TECHNICAL_LOSS` terminates the sub-game. | R5; **STATE-003** |
| **PRD02-FR-028** | Every transition emits an evidence record sufficient for offline replay. | REPLAY-001/002; R7 |
| **PRD02-FR-029** | Re-delivery of an already-applied step is answered from the recorded result and never re-applied. | R8 |

**Per-state operational table** (entry / inbound / outbound / next / timeout source /
evidence / idempotence / forbidden):

| State | Entry | Inbound | Outbound | Next | Timeout source | Evidence | Idempotent? | Forbidden |
|---|---|---|---|---|---|---|---|---|
| BOOT | process start, secrets present | — | start server | STEP0_NEGOTIATION, FAILED | local start-up budget | boot record | n/a | any game action |
| STEP0_NEGOTIATION | server ready | peer Step-0 + auth envelope | own Step-0 + auth envelope | CONFIG_NEGOTIATION, FAILED | negotiation window (local) | declaration | yes (re-send tolerated) | counted turns |
| CONFIG_NEGOTIATION | Step-0 verified both ways | proposed values | counter-proposal | CONFIG_LOCKED, FAILED | negotiation window | negotiation record | yes | lowering MINIMUM, changing FIXED, **changing the pre-Step-0 `token_budget_per_series`** *(4E-R12-R3)* |
| CONFIG_LOCKED | hash equal **and** auth tag valid | lock ack | freeze + publish handle | READY, FAILED | — | config + hash/tag | yes | any config write |
| READY | sub-game initialised | start turn | — | TURN_DECISION, SUBGAME_COMPLETE | — | sub-game start | yes | reveal/commit |
| TURN_DECISION | our turn | — | strategy call → validate → commit build | COMMIT_SENT, FAILED | `response_timeout_sec` (config) | decision metrics | n/a | send before validate |
| COMMIT_SENT | `H_commit` sent | peer ack | resend on transport error | ACKNOWLEDGED, FAILED, TECHNICAL_LOSS | `response_timeout_sec` | commit entry | **yes** | nonce release |
| ACKNOWLEDGED | ack matches cursor | — | prepare reveal | REVEAL, FAILED | `response_timeout_sec` | ack entry | yes | early nonce |
| REVEAL | ack matched | peer reveal | own reveal (no nonce) | VALIDATING, FAILED, TECHNICAL_LOSS | `response_timeout_sec` | reveal entry | yes | effects pre-validation |
| VALIDATING | both reveals present | — | domain validation | TURN_COMPLETE, TAMPERED, TECHNICAL_LOSS | `response_timeout_sec` | validation record | yes | LLM legality |
| TURN_COMPLETE | validation passed | — | apply effects, advance cursor | TURN_DECISION, SUBGAME_COMPLETE | — | turn record | yes | mutate past turn |
| SUBGAME_COMPLETE | terminal detected | — | seal log, record score | READY, SERIES_COMPLETE | — | sealed log + score | yes | change sealed score |
| SERIES_COMPLETE | all sub-games played | — | compute cumulative | FINAL_AUDIT | — | cumulative | yes | report before audit |
| FINAL_AUDIT | series complete | peer nonces | release nonces, recompute all | REPORT_READY, TAMPERED | audit window | audit result | yes | selective disclosure |
| REPORT_READY | audit verified | **peer `ResultAgreement` request** (identity + agreed `timestamp` + peer `ResultContribution`); the peer's returned `Sha256Digest` for our own request *(4E-R13-R2; this cell read "peer result hash", which named the operation **response** rather than the inbound request)* | own single `ResultAgreement` request, then the local `Sha256Digest` response; build + send result | (terminal) | reporting window | result artifact | yes (transport retry re-sends the **same immutable** semantic request) | mutate game state; regenerate the timestamp; send a second semantic request |
| FAILED / TAMPERED / TECHNICAL_LOSS | fault / mismatch / protocol condition | — | halt, preserve evidence | (terminal) | — | fault record | n/a | continuing counted play |

### 13.4 FastMCP surface

| ID | Requirement | Traces to |
|---|---|---|
| **PRD02-FR-030** | This agent is **both** a FastMCP server and a FastMCP client (symmetric peer). | **ARCH-004** |
| **PRD02-FR-031** | MCP transport is FastMCP and is not replaceable by an ad-hoc protocol. | **NET-004** |
| **PRD02-FR-032** | Application logic accesses the peer **only** through `PeerTransportPort` (egress) and `PeerServerPort` (ingress). No `app` module imports a transport library. | `API_BOUNDARIES.md`; D3 |
| **PRD02-FR-033** | The runtime needs these **semantic operations**: (a) exchange Step-0 declaration + auth envelope, (b) exchange/lock config, (c) send commitment, (d) acknowledge commitment, (e) send reveal, (f) exchange final-audit material, (g) exchange result approval, (h) optional control/heartbeat. | STATE-001…005; CRYPTO-008 |
| **PRD02-FR-034** | The reference-compatible default tool names `negotiate`, `receive_turn`, `submit_audit`, `receive_control` MAY be exposed and are labelled **REFERENCE-COMPATIBILITY DEFAULT — NOT BOOK-MANDATED**. The book names no tools. | `LECTURER_REFERENCE_AUDIT.md`; Q2 |
| **PRD02-FR-035** | Concrete Python signatures are **not** fixed by this PRD; they are settled in Stage 2C with the negotiated profile. ***[Discharged at Stage 4E-R17-R1.]*** The deferral was correct while no transport existed and became the blocker the moment one was attempted: Stage 4E-R17 stopped `BLOCKED-BEFORE-CODE` because three semantic variants share `negotiate`, three share `receive_turn` and two share `submit_audit`, with no frozen way for a receiver to tell them apart. The binding is now frozen in `API_BOUNDARIES.md` §Stage 4E-R17-R1 — one `request` argument carrying exactly `{kind, payload}`, a closed per-tool `kind` vocabulary, canonical-text `Decimal`, and the success/error transport contract. **This row is not deleted**: it records that the deferral was deliberate, and that what replaced it is **PROJECT-CONTRACT**, never book-mandated. | R-24; `API_BOUNDARIES.md` §4E-R17-R1 |
| **PRD02-FR-036** | The published endpoint carries **no secret**; authority derives from keyed auth and hashes, not URL secrecy. | NET-001; T15 |
| **PRD02-FR-037** | **No FastMCP dependency is added at this stage.** ***[Scope statement of Stage 2; superseded at Stage 4E-R17-R1.]*** The dependency is now declared and exactly pinned in both repositories as **`fastmcp==3.4.6`**, resolving `mcp==1.29.0` and `pydantic==2.13.4`, with **Streamable HTTP** as the peer transport. **`pydantic==2.13.4` is a second exact direct dependency** *(Stage 4E-R17-R1-FIX)*: R17 production DTOs import `BaseModel`, `ConfigDict(extra="forbid")` and the string constraints directly, and a package this project imports itself is a package this project owns rather than inherits. Measured justification: only a Pydantic model emits `additionalProperties: false` and refuses an extra envelope member - a `dataclass` and a `TypedDict` both accept one - so the frozen envelope is unenforceable without it. `mcp`, `pydantic-core` and `pydantic-settings` stay **transitive**; adding the direct pin moved no resolved version. | scope; Stage 4E-R17-R1 |

### 13.5 Concurrency

| ID | Requirement | Traces to |
|---|---|---|
| **PRD02-FR-040** | One asyncio event loop; **no threads and no multiprocessing for game logic**. | `CONCURRENCY_MODEL.md` |
| **PRD02-FR-041** | Exactly **one serialized Turn Executor** applies all mutating events; one event completes (including its evidence write) before the next begins. | §2 rule |
| **PRD02-FR-042** | Inbound requests never mutate directly: the server validates, converts to an event, and enqueues it. | `CONCURRENCY_MODEL.md` |
| **PRD02-FR-043** | **Two concurrent peer requests MUST NOT mutate the same turn state** — enforced by serialization + turn-cursor guard + idempotency. | primary concurrency rule |
| **PRD02-FR-044** | Every **turn-scoped** inbound protocol message carries the turn cursor `(sub_game, step)`; a mismatch is `E-PROTO-STALE` and is rejected, not queued. Series- and sub-game-control and finalization messages carry their own already-authoritative identity context instead. The **phase** check stays receiver-side (**FR-062**, STATE-003): the receiver compares against **its own** `ProtocolMachine`, so no phase value is transmitted. *(Stage 4E-R1 correction — implementation-discovered internal PRD consistency fix; the original wording said "every inbound message carries `(sub_game, step, phase)`", which is over-broad: **FR-063**, the requirement that actually names the "cursor guard" and traces to R8 like this one, lists only sub-game and step, while the phase rejection is FR-062 under STATE-003. Traceability to R8 / idempotency is preserved; no source rule, requirement count, JDEC, NDEC, INV or Conflict-Register entry changes.)* | R8 |
| **PRD02-FR-045** | The inbound queue is **bounded** (`queue_depth`, default 100, **MINIMUM**); overflow applies backpressure/rejection, never unbounded growth. | App F T19 |
| **PRD02-FR-046** | Outbound concurrency is capped by `concurrent_requests` (default 2, **MINIMUM**). | App F T19 |
| **PRD02-FR-047** | Outbound calls pass a **token bucket** at `requests_per_minute` (default 30, **MINIMUM**): `tokens ← min(C, tokens + r·Δt)`, send iff `tokens ≥ 1`. | NET-002; App F T19 |
| **PRD02-FR-048** | Cancellation is cooperative and leaves no partial mutation; a cancelled turn is either fully applied or not applied. | `CONCURRENCY_MODEL.md` |
| **PRD02-FR-049** | The GUI channel is subscribe-only and **lossy by design**; GUI backpressure MUST NOT block or alter the game loop. | R-22; GUI-003 |

### 13.6 Deadlines, retries, watchdog

| ID | Requirement | Traces to |
|---|---|---|
| **PRD02-FR-050** | Every outbound MCP request carries an expiry; on timeout a **controlled retry** is performed. | **STATE-004** |
| **PRD02-FR-051** | The step/response deadline is `response_timeout_sec` **read from the locked config** (App F default **30 s**, status **NEGOTIABLE**). It MUST NOT be hard-coded. | STATE-004; App F T19 |
| **PRD02-FR-052** | The watchdog threshold is `watchdog_timeout_sec` **read from the locked config** (App F default **60 s**, **NEGOTIABLE**); on prolonged freeze it performs a controlled shutdown. | **STATE-005**; App F T19 |
| **PRD02-FR-053** | Retries use `retry_backoff_sec` (default 5, MINIMUM) and stop at `max_retries` (default 3, MINIMUM); exhaustion ⇒ `E-RETRY-EXHAUSTED`. | NET-003; App F T19 |
| **PRD02-FR-054** | **Only transport-class errors are retried.** Integrity/legality/auth errors are never retried. | `ERROR_MODEL.md` principle 2 |
| **PRD02-FR-055** | On HTTP 429 the runtime **backs off and waits for the next window**; it never retries immediately. | REPORT-003; NET-002 |
| **PRD02-FR-056** | A private local `turn_timeout` (e.g. the reference's 180 s) is **not** the negotiated value and never overrides `response_timeout_sec`/`watchdog_timeout_sec`. | C-02 |

### 13.7 Gatekeeper (inbound validation)

| ID | Requirement | Traces to |
|---|---|---|
| **PRD02-FR-060** | Reject any message whose `game_id`/`game_uid` does not match the active game. | INV-01 |
| **PRD02-FR-061** | Reject any message whose declared peer identity does not match the negotiated `group_id` where identity is applicable. | SUB-003 |
| **PRD02-FR-062** | Reject any message for the wrong **phase**. | STATE-003 |
| **PRD02-FR-063** | Reject any message for the wrong **sub-game** or wrong **step** (cursor guard). | R8 |
| **PRD02-FR-064** | Reject any message failing schema validation or declaring a profile that is not the frozen active profile. | `E-PROTO-MALFORMED` |
| **PRD02-FR-065** | Enforce payload **size and nesting-depth bounds**; oversized/deeply nested payloads are rejected before parsing completes. | T2/T8 |
| **PRD02-FR-066** | Apply inbound rate limiting and queue bounds; excess is rejected with backpressure. | T8; App F T19 |
| **PRD02-FR-067** | Reject stale/duplicate messages idempotently (answer from the recorded result). | R8 |
| **PRD02-FR-068** | **No counted play before authentication:** any counted-turn message arriving before Step-0 auth + config lock is rejected. | INV-14/15 |
| **PRD02-FR-069** | Malformed input is logged **truncated and escaped**, bounded in size, and never echoed verbatim to the peer. | `OBSERVABILITY.md` |
| **PRD02-FR-070** | **No exception, error message or metric label may contain key material, credentials or tokens** — only non-secret `key_id`, algorithm and verdict. | SEC-003/004; T18 |
| **PRD02-FR-071** | The Gatekeeper decides **protocol validity only**. It never decides capture, score, or any game outcome. | ARCH-001/002 |

### 13.8 Compatibility profile

| ID | Requirement | Traces to |
|---|---|---|
| **PRD02-FR-080** | The active profile set (`AuthProfile`, `CommitmentCodec`, `ResultProfile`, tool-name profile) is selected **before** counted play and **frozen at `CONFIG_LOCKED`**; it is read-only thereafter and cannot be switched mid-series. **[Amended Stage 4E-R12]** `CommitmentCodec`, `ResultProfile` and the tool-name profile are consumed **after** `CONFIG_LOCKED`, so the lock is their selection deadline. **`AuthProfile` and its `KeyId` are different**: they are consumed two states earlier, in `STEP0_NEGOTIATION`, so they are **provisioned out of band together with the key material before `BOOT`** and are never selected by an in-band message; `auth_alg`/`key_id` on the wire are **compared** against that provisioned expectation and a difference refuses counted play. They are still frozen for the series — earlier than the lock, not later. | `API_BOUNDARIES.md` P8; `SIGNATURE_AND_HASH_PROVENANCE.md` R12-A |
| **PRD02-FR-081** | A profile may **add** accepted encodings; it may **never weaken** a binding requirement in `STRICT_COUNTED_MATCH`. A weakening request ⇒ refuse counted play. | `COMPATIBILITY_PROFILES.md` |
| **PRD02-FR-082** | The active profile **and the agreed series convention** are recorded as **negotiation/profile evidence** (not as official artifact schema fields) so replay and reporting reproduce the exact interpretation used. | REPLAY-001/002; PRD-05 FR-034/034a |

## 14. Non-Functional Requirements

| ID | Requirement |
|---|---|
| **PRD02-NFR-001** | All layers up to INTEGRATION run **offline** against an in-process or subprocess fake peer; no public internet in CI. |
| **PRD02-NFR-002** | `ClockPort` is injected; tests use a deterministic fake clock — no real sleeping in unit/integration tests. |
| **PRD02-NFR-003** | Every Python file ≤ **150 lines**; the state machine, orchestrator and turn service are separate modules. |
| **PRD02-NFR-004** | Inbound validation rejects a malformed message in **< 10 ms** (measurable) so flooding cannot starve the executor. |
| **PRD02-NFR-005** | No `app` module imports a concrete adapter (enforced by the dependency test). |

## 15. State / Lifecycle Responsibilities

Owns: state-machine phase, turn cursor, sub-game index, pending turn record, deadline
timers, limiter counters, server/client lifecycles, active profile. **Does not own:**
game truth (PRD-01), nonce/commitment (PRD-06), artifacts/report (PRD-07).

## 16. Validation Rules

Identity mismatch · wrong phase · wrong sub-game/step · schema failure · unknown or
weakening profile · payload/depth over bound · rate/queue exceeded · duplicate/stale ·
counted message before auth+lock · unparsable JSON — each with a distinct machine
reason code, each rejected **without side effects**.

## 17. Error / Failure Behaviour

`E-TRANSPORT` retryable · `E-TIMEOUT-STEP` limited retry · `E-TIMEOUT-WATCHDOG` ⇒
controlled shutdown · `E-RETRY-EXHAUSTED` ⇒ escalate · `E-RATE-429` ⇒ back off to next
window · `E-PROTO-MALFORMED` / `E-PROTO-STALE` ⇒ reject, no state change ·
`E-CONFIG-MISMATCH` / `E-AUTH-FAILURE` ⇒ **refuse counted play** · `E-HASH-MISMATCH` /
`E-NONCE-MISMATCH` ⇒ **TAMPERED** (terminal) · `E-TECHNICAL-LOSS` ⇒ 0/0 per C-07 ·
`E-LOCAL-DEFECT` ⇒ fail fast. **No new sanction is invented.**

## 18. Security / Privacy Constraints

Peer is untrusted (TB-1) · validate before any effect · fail closed on auth/config
failure · no secret in logs/errors/metrics · endpoint carries no secret · bounded
everything (payload, depth, queue, retries, time) · constant-time digest comparison
where available · no opponent-truth field ever accepted or stored.

## 19. Determinism / Reproducibility

Given the same injected clock, the same inbound event sequence and the same seed, the
runtime produces the same transition sequence and the same evidence. Non-determinism is
confined to `PeerTransportPort`, `PeerServerPort`, `ClockPort` — all injected and
fakeable. Replay never depends on timing.

## 20. Performance / Deadline Constraints

All waiting is bounded by config-sourced values (`response_timeout_sec`,
`watchdog_timeout_sec`, `retry_backoff_sec`, `max_retries`). The executor must apply a
turn event and write its evidence within the step budget; queue depth is bounded at
`queue_depth`.

## 21. Cross-Platform Constraints

Identical protocol behaviour on Linux and Windows: monotonic clock via `ClockPort`, no
POSIX-only signals in the core path, path handling via `pathlib`, LF/UTF-8 canonical
bytes for anything hashed, and CI runs both OSes.

## 22. Observability / Evidence

Per-state transitions, cursor movement, inbound rejects by reason, request latency,
retry/timeout/429 counts, queue depth, token-bucket level, profile in force, shutdown
reason. **Never logged:** secrets, nonces before audit, opponent truth, full malformed
payloads.

## 23. Acceptance Criteria

| ID | Criterion |
|---|---|
| **PRD02-AC-001** | Two local peer processes complete a full Step-0 → config-lock → turn → audit flow **offline** (fake peer, no internet). |
| **PRD02-AC-002** | Server and client start and stop cleanly; a second start on a busy port fails with a defined error, not a crash. |
| **PRD02-AC-003** | A duplicate inbound message for an applied step is answered idempotently; state is byte-identical afterwards. |
| **PRD02-AC-004** | A message for a stale step is rejected with `E-PROTO-STALE`; no state change. |
| **PRD02-AC-005** | A message for the wrong phase is rejected; no state change. |
| **PRD02-AC-006** | Two simultaneous mutating requests for the same turn result in exactly one applied transition and one rejection — never interleaved mutation. |
| **PRD02-AC-007** | Deadlines use the **config** value: a config with `response_timeout_sec = 45` produces a 45 s deadline, proving no hard-coded 30. |
| **PRD02-AC-008** | Watchdog fires at the configured `watchdog_timeout_sec` and performs a controlled shutdown. |
| **PRD02-AC-009** | Retry exhaustion at `max_retries` yields `E-RETRY-EXHAUSTED` and a defined escalation, not a silent continue. |
| **PRD02-AC-010** | An HTTP 429 causes back-off to the next window; no immediate retry is observed. |
| **PRD02-AC-011** | Opponent disconnect mid-turn produces a deterministic outcome with evidence; no corruption. |
| **PRD02-AC-012** | Graceful shutdown drains and seals; no half-written artifact after SIGTERM-equivalent. |
| **PRD02-AC-013** | Static check: **zero** imports between `mars777_police` and `mars777_thief`; no shared runtime path. |
| **PRD02-AC-014** | A compatibility tool profile can be selected before `CONFIG_LOCKED` and **cannot** be changed afterwards (attempt rejected). |
| **PRD02-AC-015** | A counted-turn message arriving before Step-0 auth + config lock is rejected. |
| **PRD02-AC-016** | Oversized / deeply nested payload rejected before full parse; runtime remains responsive. |
| **PRD02-AC-017** | No error string, log line or metric label produced during an auth failure contains key material (scan). |
| **PRD02-AC-018** | `SeriesLauncher` executing the **agreed** convention activates the correct independent role process per sub-game and holds no game state (API has no truth accessor); with the convention unset or mismatched it **refuses to start counted play** rather than assuming a default. |

## 24. Planned Tests

| ID | Test | Layer |
|---|---|---|
| **PRD02-T-001** | Full offline protocol flow, two processes | CROSS-PROCESS |
| **PRD02-T-002** | State-machine transition table incl. every rejection | STATE-MACHINE |
| **PRD02-T-003** | Duplicate / stale / wrong-phase / wrong-sub-game rejection | PROTOCOL |
| **PRD02-T-004** | Concurrent mutating requests → single applied transition | INTEGRATION |
| **PRD02-T-005** | Deadline + watchdog from injected config values | INTEGRATION |
| **PRD02-T-006** | Retry/backoff/exhaustion ladder | INTEGRATION |
| **PRD02-T-007** | 429 handling (no immediate retry) | INTEGRATION |
| **PRD02-T-008** | Queue bound + token bucket under burst | INTEGRATION |
| **PRD02-T-009** | Malformed/oversized/deep payload rejection | SECURITY |
| **PRD02-T-010** | Secret-absence scan across errors/logs/metrics | SECURITY |
| **PRD02-T-011** | Cross-repo import ban | CONTRACT |
| **PRD02-T-012** | Profile freeze at config lock | CONTRACT |
| **PRD02-T-013** | Opponent disconnect + clean shutdown | CROSS-PROCESS |
| **PRD02-T-014** | `SeriesLauncher` role selection + no-truth API | CONTRACT |
| **PRD02-T-015** | Windows + Linux equivalence of the protocol flow | CROSS-PROCESS |

## 25. Requirement Traceability

**Directly owned:** ARCH-001…005, STATE-001…005, NET-004, NET-001 (endpoint publication;
public exposure itself → PRD-05). **Constrains:** CRYPTO-008 (sequencing), JSON-003/004
(identity/canonical use). **Consumed:** App F Table 19 (all rate/timeout values), C-02
(private 180 s is not the negotiated value).

## 26. Dependencies on Other PRDs

**Consumes:** PRD-01 (validation + terminal signals), PRD-06 (auth/commitment/config
lock), PRD-03 (strategy proposal), PRD-04 (hint production).
**Provides:** sequencing and evidence to PRD-07; transport contract to PRD-05.

## 27. Open Design Decisions

Concrete FastMCP tool signatures (2C) · process supervision/restart semantics ·
exact deadline escalation ladder · inbox-drain semantics after a series restart
(reference pattern D-18) · heartbeat/control-channel shape · tunnel persistence
(PRD-05).

## 28. Explicit Non-Goals

No referee · no game rules · no crypto primitives · no strategy · no public-tunnel
provisioning · no GUI/report · no FastMCP dependency yet.

## 29. Implementation Readiness Checklist

- [x] Process/isolation model specified and test-enforced
- [x] Full state table with rejections, timeouts, evidence, idempotence
- [x] Concurrency rule (single executor + cursor + idempotency) specified
- [x] All timeout/rate values sourced from locked config, none hard-coded
- [x] Gatekeeper validation list complete with secret-free error rule
- [x] Compatibility surface labelled non-mandated and frozen at lock
- [ ] Supervising review — **pending**
- [ ] Implementation — **not started**
