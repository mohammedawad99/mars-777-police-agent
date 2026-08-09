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
| `domain.actions` *(4E-R4; design frozen, not yet implemented)* | **The one authoritative physical-action value** a turn consists of — the movement form (a `domain.rules.Move`) and the police barrier-placement form (an exact `domain.board.Position`), structurally exclusive. This is the value that local execution applies, `protocol.commitment` seals under the sealed record's `move` member, and Reveal exposes; **there is exactly one such representation in the process** | `domain.board`, `domain.rules` | config_model, strategy, I/O, `app`, `protocol`, `infra` | none (value types) | malformed action construction |
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
| `app.turn_service` **action-type note** *(4E-R4)* | It currently defines its **own** `ActionKind` / `MoveAction` / `BarrierAction`. Those are the *same* semantic concept `domain.actions` will own, and `app.peer_messages` and `protocol.commitment` may not import `app.turn_service`, so the local copies become a **second representation of one truth** the moment a commitment producer exists. The migration is therefore **atomic**: `domain.actions` is added and `app.turn_service` is moved onto it in **one** slice, deleting the local **definitions** — never both at once. **Precision:** `app.turn_service` or `app/__init__.py` may still *re-export or bind the same domain class object* for import compatibility; that is one representation with two names and is **allowed**. What is forbidden is two separately-`class`-defined `MoveAction`s (or `BarrierAction`s) standing for the same physical action | domain, ports | concrete adapters | — | — |
| `app.ports` | **Abstract port definitions only** (`API_BOUNDARIES.md`) | stdlib typing **+ immutable `domain` value types, as type references only** | `protocol`, `infra`, any adapter, network/FastMCP/HTTP libraries, `app` implementation modules, domain services with side effects — everything else | none | — |
| `app.strategy_api` | `Observation` in → `ProposedAction` out contract | domain.observation | infra, protocol | none | no legal action |
| `app.peer_messages` *(4E-R1; deps 4E-R2/FIX2)* | **Immutable internal peer-protocol semantic contracts** — the values application control flow consumes and produces (state-changing inbound events reach the Turn Executor) and that `protocol.messages` maps to/from; **never** wire JSON | pure stdlib **value-definition and validation primitives** only (`typing`, `dataclasses`) + immutable `domain` value types + immutable **globally-FIXED `domain` constants read as structural bounds** (currently `FIRST_SUB_GAME`, `FIXED_NUM_GAMES` from `domain.config_model`; **read-only**, never redefined) + `app.protocol_values` (**runtime use**: constructs and stores the shared semantic values its messages carry) | `protocol`, `infra`, any adapter, `app` implementation modules (`app.state_machine`, `app.orchestrator`, `app.turn_service`), `enum` (no message-local vocabulary exists — reuse `domain.rules.Move` and `app.protocol_values.FinalAuditVerdict`), `hashlib`/`hmac`/`cryptography`/`secrets`/`random`, FastMCP/network libraries, wire serialization, JSON, artifact storage, cryptographic computation, I/O, GUI, replay, reporting — everything else | none | invalid message construction |
| `app.turn_cursor` *(4E-R6; design frozen, not implemented)* | The shared **turn-identity value** `TurnCursor` (and its private int guard). Extracted because *both* future message modules need it and neither should depend on the other - not because a file filled up | pure stdlib value primitives + the globally-FIXED `domain.config_model` bounds (read-only) | `protocol`, `infra`, adapters, `app` implementation modules, `enum`, crypto, JSON, I/O | none | invalid cursor construction |
| `app.peer_turn_messages` *(4E-R6; design frozen, not implemented)* | The **per-turn** peer-visible families: `Commitment`, `Acknowledgement`, `Reveal`, and a future move-validation family if one proves transmitted | `app.turn_cursor`, `app.protocol_values`, immutable `domain` value types (incl. `domain.actions`) | same as `app.peer_messages` | none | invalid message construction |
| `app.peer_final_messages` *(4E-R6; design frozen, not implemented)* | The **end-of-sub-game** peer-visible families: `NonceRevealEntry` + `FinalNonceReveal` (one batch per peer per sub-game, 4E-R6-FIX1), and any finalization family later proved transmitted. The reusable `NonceValue` it carries lives in `app.protocol_values`, **not** here | `app.turn_cursor`, `app.protocol_values`, immutable `domain` value types | same as `app.peer_messages` | none | invalid message construction |
| `app.protocol_values` *(4F-R1)* | **Immutable shared protocol semantic value representations** — the primitives that peer-message contracts and outer protocol implementations must agree on (e.g. a SHA-256 digest result, a final-audit verdict). Representation only: it never computes, serializes or knows what was hashed | pure stdlib **value-definition and validation primitives** only (`typing`, `dataclasses`, `enum`) | `protocol`, `infra`, any adapter, `hashlib`/`hmac`/`cryptography`/`secrets`/`random`, FastMCP/network libraries, I/O, JSON or any wire/artifact serialization, cryptographic computation, GUI, replay, reporting — everything else | none | invalid value representation |

**Test boundary:** state-machine and contract tests with fake ports.

> **Stage 4E-R6 - peer-message module organization (design frozen; no Python yet).**
> `app.peer_messages` reached **exactly 150/150 LOC** at Stage 4E-RESUME3 with four values
> in it (`TurnCursor` 27, `Commitment` 25, `Acknowledgement` 28, `Reveal` 31, the private
> int guard 8, plus a 16-line module docstring and imports). No further family fits, and the
> reviewed prose-only compression that made `Reveal` fit must not be repeated. R6 freezes the
> organization **by measurement, not by taste**: keeping all four together in one relocated
> module would land at ~145 LOC and reproduce the same wall one family later, so the split is
> `app.turn_cursor` (~54) + `app.peer_turn_messages` (~107, room for one more turn family) +
> `app.peer_final_messages` (new, ~0 today), with **`app.peer_messages` becoming a pure
> façade** (~36) that re-exports **the same class objects**. `TurnCursor` is extracted because
> both message modules need it and neither should import the other; that is ownership
> evidence, not a capacity workaround. **Forbidden and not used:** a `PeerMessage` base class,
> a `MessageKind` enum for filing, a registry, a factory, a generic payload dict, dynamic
> import machinery or reflection - ordinary modules, imports, dataclasses and explicit
> re-exports only. The public surface `from <pkg>.app.peer_messages import …` and
> `from <pkg>.app import …` **must keep working with identity-equal classes**, since three
> test modules import that path directly and one imports the module object itself to assert
> blocked families are absent. Dependency direction is acyclic by construction:
> `turn_cursor` <- `peer_turn_messages` / `peer_final_messages` <- `peer_messages` façade.

> **Stage 4E-R2 reconciliation (implementation-discovered, internal).** The
> `app.peer_messages` row was written before `app.protocol_values` existed and carried
> two defects, both paid off here before any Stage-4E Python is written. (i) It allowed
> only "stdlib typing", which — exactly as Stage 4F-R1-FIX1 found for
> `app.protocol_values` — cannot define an immutable validated value at all; it now
> allows the pure stdlib value-definition and validation primitives it actually needs.
> `enum` is **deliberately excluded**: no peer message defines a vocabulary of its own,
> and the two it will reference already exist (`domain.rules.Move`,
> `app.protocol_values.FinalAuditVerdict`). Should a future family genuinely need a new
> closed vocabulary, `enum` is added then, with the evidence. (ii) It could not name
> `app.protocol_values` at all, so a message could not carry `Sha256Digest` — the value
> the Stage-4F reconciliation was built to serve. That dependency is **runtime use**
> (message constructors accept and store these values), not annotation-only, and it is
> intra-layer: both modules are `app` contract modules, so no edge is added to the layer
> DAG (D1) and `app.ports`' precedent for naming immutable values is unchanged.
> **Acyclicity is structural, not conventional:** `app.protocol_values` allows *only*
> pure stdlib primitives, so it cannot import `app.peer_messages` — the back edge is
> already impossible under its own allow-list, and D2 holds without a new rule.
> `protocol.messages` → `app.peer_messages` stays the outer→inner mapper and is
> untouched. No new shared layer, no requirement, PRD, JDEC, NDEC, INV,
> Conflict-Register or FIELD_MATRIX entry changes.
>
> **Stage 4E-R2-FIX2 addendum.** The row said "immutable `domain` value **types**", which
> names classes. `TurnCursor`'s frozen structural bound `FIRST_SUB_GAME <= sub_game <=
> FIXED_NUM_GAMES` needs two module-level `Final[int]` **constants**, and reading "value
> types" to cover them would be exactly the generous reading this project refused twice
> (Stage 4D-R1 for `app.ports`, Stage 4F-R1-FIX1 for `app.protocol_values`). The row now
> names them explicitly and nothing else. The alternatives were rejected on evidence: a
> literal `6` inside `app.peer_messages` would create a **second** numeric authority for a
> value Appendix F marks FIXED ("deviation disqualifies"), and moving or copying the
> constants would do the same; taking the bound from a `SeriesConfig` instance — already a
> permitted value type — would either add a third field to a cursor frozen at two or make
> a *transmitted* cursor appear to depend on locked configuration it does not carry, when
> the bound it needs is the global constant, not a config value. **Single authority is
> mechanically verified:** `FIXED_NUM_GAMES: Final[int] = 6` in `domain.config_model` is
> the only `= 6` series length in the source tree, and `app.orchestrator` already imports
> `FIRST_SUB_GAME` from that module at runtime, so this widening adds **no new layer edge**
> — `app` already depends inward on `domain` (D1), and no domain service, mutable state,
> truth ownership or rule execution becomes reachable. Read-only use only: a message module
> may never redefine, shadow or re-export these constants.
>
> *Reported, deliberately not changed:* `protocol.messages` still says
> `app.peer_messages` **(type references only)**. A wire⇄semantic mapper *constructs*
> semantic values, so that phrasing has the same defect this note just fixed twice.
> It is left alone because `protocol.messages` is not resuming, exactly as Stage
> 4F-R1-FIX1 left this row alone for the same reason, and it is tracked as a mandatory
> preflight for the protocol stage instead of being fixed speculatively here.

> **Stage 4F-R1 reconciliation (implementation-discovered, internal).** Stage 4F found
> that a SHA-256 digest result is needed by `app.peer_messages` (messages carry
> `H_commit`, `config_sha256`, `result_sha256`), by `protocol.commitment` (which
> produces `H_commit`) and by `protocol.config_lock` (which produces `config_sha256`) —
> with no module reachable by all three — and stopped rather than duplicate the
> validator or invent a `types.py`. Two corrections resolve it. First, the blocker
> analysis was **too broad**: `infra.logger`, `infra.artifacts` and `infra.reporter` are
> **mappers**, not semantic consumers — they serialize whatever structured record they
> are handed, which already reaches them through `app.ports` (LoggerPort), so `infra`
> needs no new dependency and `DEPENDENCY_RULES.md` is unchanged. Second, the genuine
> consumers are satisfied by one inner contract module, `app.protocol_values`, plus a
> narrow type-reference dependency for exactly the two protocol producers — the same
> outer→inner pattern Stage 4E-R1 already authorized for `protocol.messages` →
> `app.peer_messages`. `app.protocol_values` holds representations only: it performs no
> hashing, no canonicalization (that stays `protocol.canonical`) and knows nothing about
> which core was hashed. State owned: none. No requirement, PRD, JDEC, NDEC, INV,
> Conflict-Register or FIELD_MATRIX entry changes.
>
> **Stage 4F-R1-FIX1.** Two wording defects in the above were corrected. (i) The two
> protocol rows first said "type references only" — wording borrowed from `app.ports`,
> where annotation-only is genuinely enough. It is **not** enough here:
> `protocol.commitment` and `protocol.config_lock` **produce** these values, so they
> must construct and return them at runtime. Their permission now says so, and it still
> reaches no other application module. (ii) `app.protocol_values` first allowed only
> "stdlib typing", which could not support defining an immutable validated value at all;
> it now allows the pure stdlib **value-definition and validation primitives**
> (`typing`, `dataclasses`, `enum`) and nothing more — `hashlib`, `hmac`,
> `cryptography`, `secrets`, `random`, I/O and every form of serialization stay
> forbidden. Sibling note, reported not changed: `app.peer_messages` carries the same
> "stdlib typing" phrasing and will need the same widening when Stage 4E resumes.

> **Stage 4E-R1 reconciliation (implementation-discovered, internal).** Stage 4E
> tried to build the internal semantic peer-message values inside
> `protocol.messages` and was blocked twice. The home was wrong first: that row is
> a **wire** boundary ("wire schema validation", failure "malformed JSON"), while
> `CONCURRENCY_MODEL.md` has the MCP server "validate, convert to an **event**, and
> submit it to the executor queue" — and the Turn Executor is `app`. Since
> `app` may never import `protocol`, a semantic value the executor consumes
> **cannot** live in `protocol`; that is a proof, not a preference. `app.peer_messages`
> is therefore added as an application **contract** module, in the same spirit as
> `app.ports` and `app.strategy_api`, and `protocol.messages` stays the wire mapper
> that translates between the two. It keeps **no state** and remains forbidden from
> infra transport. No requirement, PRD numbering, JDEC, NDEC, INV or
> Conflict-Register entry changes.

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
| `protocol.commitment` | `H_commit` over the 8-field sealed record; verify at audit | canonical, domain, `app.protocol_values` (**runtime use**: constructs and returns the value contracts it produces) | transport | pending nonce (secret) | mismatch ⇒ TAMPERED |
| `protocol.keyed_auth` | Keyed authentication (HMAC-SHA256 default) over `context‖core`; `step0`/`config` domain separation | canonical | transport, logging of keys | none (**never key bytes**) | bad tag / unknown `key_id` |
| `protocol.config_lock` | Canonical config, `config_sha256`, auth exchange, immutable lock | canonical, keyed_auth, domain.config_model, `app.protocol_values` (**runtime use**: constructs and returns the value contracts it produces) | strategy | locked config handle | hash/tag mismatch |
| `protocol.messages` | Wire schema validation + mapping wire bytes ⇄ `app.peer_messages` semantic values | canonical, domain, `app.peer_messages` (type references only) | infra transport | none | malformed JSON |
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
- `app` imports `domain` and its own contract modules (`app.ports`, `app.peer_messages`, `app.protocol_values`) only — **never** `protocol`, `infra` or a concrete adapter.
- Strategy plug-ins import `app.strategy_api` + `domain` value types **only**.
- `infra.replay` imports **artifacts**, never `app`/`domain` live state.
- `infra.reporter` is **write-only** with respect to game state.
- Nothing imports `mars777_police` from `mars777_thief` or vice-versa (TB-3).
- `infra.series_launcher` **starts processes**; it never imports the other role's package,
  never holds game truth, and never validates a move (it is not a referee).
