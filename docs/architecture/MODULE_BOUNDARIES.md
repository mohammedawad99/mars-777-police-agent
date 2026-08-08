# Module Boundaries — group MaRs-777 (POLICE)

**Status: STAGE 2A ARCHITECTURE FREEZE — proposed modules. NONE created yet.**

Package root: **`mars777_police`**. Layers per `DEPENDENCY_RULES.md`:
**domain → application → protocol/adapters → infrastructure** (arrows point inward;
inner layers never import outer ones).

**Sizing rule.** Every future Python file must fit the course's **≤150 lines**
expectation. The design achieves this with **cohesive components split by
responsibility**, not by shredding logic into meaningless micro-files. Where a
component needs more than ~150 lines it is split along a *real* seam (e.g. legality
rules vs. scoring), and that seam is named below.

## Domain layer — `mars777_police.domain` (pure, deterministic, no I/O)

| Module | Responsibility | Allowed deps | Forbidden deps | State owned | Failure modes |
|---|---|---|---|---|---|
| `domain.board` | Grid geometry, coordinates, adjacency, bounds | stdlib | anything outer | none (value types) | out-of-bounds |
| `domain.config_model` | Typed view of the signed config + Appendix F status semantics (FIXED/MINIMUM/NEGOTIABLE) | `domain.board` | I/O, protocol | immutable config value | invalid/absent value |
| `domain.rules` | Movement legality, barrier legality, capture, terminal conditions | board, config_model | strategy, I/O | none (pure functions) | illegal move/barrier |
| `domain.scoring` | Appendix F scoring incl. technical_loss 0/0 (C-07) | config_model | I/O | none | unknown outcome |
| `domain.scent` | Pheromone emission/decay field (0.9 / 0.10 / 5) | board, config_model | I/O | field snapshot (value) | parameter mismatch |
| `domain.barriers` | Barrier set, quota, irreversibility | board, config_model | I/O | barrier set (value) | quota exceeded |
| `domain.truth` | **Local truth**: own position, step, own barrier budget | board | opponent data | **authoritative own truth** | invalid transition |
| `domain.belief` | Opponent belief estimate from permitted observations only | board, scent | `domain.truth` of opponent (does not exist) | belief distribution | degenerate belief |
| `domain.observation` | Builds the role-legal `Observation` handed to strategy | truth, belief, scent, barriers, config_model | protocol, infra | none | — |

**Test boundary:** pure unit + property tests, no fixtures, no network, no clock.

## Application layer — `mars777_police.app`

| Module | Responsibility | Allowed deps | Forbidden deps | State owned | Failure modes |
|---|---|---|---|---|---|
| `app.state_machine` | Legal states + transitions (`STATE_MACHINE.md`); refuses out-of-order events | domain | protocol, infra | **current state** | illegal transition |
| `app.orchestrator` | Drives a sub-game/series; calls ports in the order the state machine permits | domain, ports | concrete adapters | turn cursor, sub-game index | deadline exceeded |
| `app.turn_service` | One turn: decide → validate → commit → ack → reveal → verify | domain, ports | concrete adapters | pending turn record | nonce/hash mismatch |
| `app.ports` | **Abstract port definitions only** (`API_BOUNDARIES.md`) | stdlib typing **+ immutable `domain` value types, as type references only** | `protocol`, `infra`, any adapter, network/FastMCP/HTTP libraries, `app` implementation modules, domain services with side effects — everything else | none | — |
| `app.strategy_api` | `Observation` in → `ProposedAction` out contract | domain.observation | infra, protocol | none | no legal action |

**Test boundary:** state-machine and contract tests with fake ports.

> **Stage 4D-R1 reconciliation (implementation-discovered, internal).** The
> `app.ports` row originally allowed `stdlib typing` only, yet `API_BOUNDARIES.md`
> defines ports whose operands and results *are* domain values (`GameRulesPort`
> takes board state and a proposed action; `ScoringPort` takes an outcome and
> returns per-role scores). Those contracts were therefore unrepresentable in the
> very module the architecture assigns them to, without duplicating domain types
> or erasing them behind `Any`/`object` — both of which break
> `STATE_OWNERSHIP.md`'s one-owner rule or the typing gates. The row now permits
> **type references to immutable `domain` value types** and nothing else outward.
> Rationale: port contracts may *name* existing immutable semantic values without
> duplicating them, and dependency inversion (D3) is directed against **concrete
> adapters**, not against the domain model — `app` may already import `domain`
> (see `app.orchestrator` / `app.turn_service` above), so this adds no new edge to
> the layer DAG. No other module row is broadened. No requirement, PRD, JDEC,
> NDEC, INV or Conflict-Register entry changes.

## Protocol / adapter layer — `mars777_police.protocol`

| Module | Responsibility | Allowed deps | Forbidden deps | State owned | Failure modes |
|---|---|---|---|---|---|
| `protocol.canonical` | Canonical JSON bytes (sorted keys, `(",",":")`, UTF-8, NFC, LF, no trailing NL) — JDEC-002 | stdlib | domain mutation | none | non-canonical input |
| `protocol.commitment` | `H_commit` over the 8-field sealed record; verify at audit | canonical, domain | transport | pending nonce (secret) | mismatch ⇒ TAMPERED |
| `protocol.keyed_auth` | Keyed authentication (HMAC-SHA256 default) over `context‖core`; `step0`/`config` domain separation | canonical | transport, logging of keys | none (**never key bytes**) | bad tag / unknown `key_id` |
| `protocol.config_lock` | Canonical config, `config_sha256`, auth exchange, immutable lock | canonical, keyed_auth, domain.config_model | strategy | locked config handle | hash/tag mismatch |
| `protocol.messages` | Wire schema validation + domain command/event mapping | canonical, domain | infra transport | none | malformed JSON |
| `protocol.declaration` | Step-0 declaration assembly + `step0_auth` envelope | canonical, keyed_auth | transport | none | missing field |
| `protocol.profiles` *(2A-R2)* | Negotiated `AuthProfile` / `CommitmentCodec` / `ResultProfile` selection; frozen at config lock | canonical | infra transport | active profile set | unknown/weakening profile |
| `protocol.hints` | Hint bounds (`hint_max_words`) and `intent` tagging | domain.config_model | LLM SDK | none | over-length hint |

**Test boundary:** golden-vector byte tests + negative/adversarial protocol tests.

## Infrastructure layer — `mars777_police.infra`

| Module | Responsibility | Allowed deps | Forbidden deps | State owned | Failure modes |
|---|---|---|---|---|---|
| `infra.mcp_server` | Inbound FastMCP surface | protocol, app.ports | domain mutation | server lifecycle | bind/tunnel failure |
| `infra.mcp_client` | Outbound peer calls | protocol, gatekeeper | domain | connection pool | transport error |
| `infra.gatekeeper` | Token-bucket rate limit, concurrency cap, retry/backoff, queue depth (App F T19) | stdlib | domain | limiter counters | retry exhaustion, 429 |
| `infra.clock` | Monotonic time, deadlines, watchdog (injected) | stdlib | domain | timers | deadline exceeded |
| `infra.logger` | Append-only structured evidence writer | protocol.canonical | domain mutation | log file handle | write failure |
| `infra.artifacts` | Reads/writes the four official artifacts | protocol.canonical | domain | file paths | I/O error |
| `infra.replay` | Independent verifier over persisted evidence **only** | protocol.commitment, artifacts | live app/domain state | none | replay mismatch |
| `infra.reporter` | Builds + sends the final result (JSON attachment) | artifacts, protocol.canonical | domain mutation | none | send failure |
| `infra.metrics` | Latency/retry/token/cost counters | stdlib | domain | counters | — |
| `infra.gui` | Read-only projection consumer | app events | domain aggregate, truth | view model | render error |
| `infra.llm` | Optional advisor client | protocol.hints | domain, validator bypass | token counters | provider failure ⇒ fallback |
| `infra.series_launcher` *(2A-R2)* | Starts the appropriate **independent** role process per sub-game (role-alternation support) | app.ports | domain, opponent state | process handles only | role process unavailable |
| `infra.settings` | Local runtime settings + secret loading from env | stdlib | game config mutation | settings object | missing setting |

**Test boundary:** integration tests with a local fake peer; no public internet required.

## Cross-cutting rules

- `domain` imports **nothing** from `app`, `protocol`, or `infra`.
- `app` imports `domain` and `app.ports` only — **never** a concrete adapter.
- Strategy plug-ins import `app.strategy_api` + `domain` value types **only**.
- `infra.replay` imports **artifacts**, never `app`/`domain` live state.
- `infra.reporter` is **write-only** with respect to game state.
- Nothing imports `mars777_police` from `mars777_thief` or vice-versa (TB-3).
- `infra.series_launcher` **starts processes**; it never imports the other role's package,
  never holds game truth, and never validates a move (it is not a referee).
