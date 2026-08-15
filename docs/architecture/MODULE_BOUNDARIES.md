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
| `domain.observation` *(implemented 6B)* | Builds the role-legal `Observation` handed to strategy. Stage-6B form is `board` + `own_position` + `quota`; belief/scent join at PRD-04 | truth, barriers, board | protocol, infra, `app` | none | malformed observation |
| `domain.reachability` *(added 6B)* | Barrier-aware BFS distance from a cell to every cell still reachable — the one distance authority a strategy may use. Owns **no** geometry: bounds, blocked cells and the four offsets stay in `domain.board` | board | rules, truth, protocol, infra, `app` | none | — |

**Test boundary:** pure unit + property tests, no fixtures, no network, no clock.

## Application layer — `mars777_police.app`

| Module | Responsibility | Allowed deps | Forbidden deps | State owned | Failure modes |
|---|---|---|---|---|---|
| `app.state_machine` | Legal states + transitions (`STATE_MACHINE.md`); refuses out-of-order events | domain | protocol, infra | **current state** | illegal transition |
| `app.orchestrator` | Drives a sub-game/series; calls ports in the order the state machine permits | domain, ports | concrete adapters | turn cursor, sub-game index | deadline exceeded |
| `app.turn_service` | One turn: decide → validate → commit → ack → reveal → verify | domain, ports | concrete adapters | pending turn record | nonce/hash mismatch |
| `app.turn_service` **action-type note** *(4E-R4)* | It currently defines its **own** `ActionKind` / `MoveAction` / `BarrierAction`. Those are the *same* semantic concept `domain.actions` will own, and `app.peer_messages` and `protocol.commitment` may not import `app.turn_service`, so the local copies become a **second representation of one truth** the moment a commitment producer exists. The migration is therefore **atomic**: `domain.actions` is added and `app.turn_service` is moved onto it in **one** slice, deleting the local **definitions** — never both at once. **Precision:** `app.turn_service` or `app/__init__.py` may still *re-export or bind the same domain class object* for import compatibility; that is one representation with two names and is **allowed**. What is forbidden is two separately-`class`-defined `MoveAction`s (or `BarrierAction`s) standing for the same physical action | domain, ports | concrete adapters | — | — |
| `app.ports` | **Abstract port definitions only** (`API_BOUNDARIES.md`) | stdlib typing **+ immutable `domain` value types, as type references only** | `protocol`, `infra`, any adapter, network/FastMCP/HTTP libraries, `app` implementation modules, domain services with side effects — everything else | none | — |
| `app.sub_game_driver` *(added 6C-B)* | **The production coordinator for one sub-game**: terminal check, `Observation`, `StrategyPort`, the existing commit/ack/reveal cadence, one-time adoption, natural `Outcome`. Owns no rule, no heuristic and **no series policy**: per-round `close_turn`, the exact-six lifecycle, result agreement and artifacts stay with the series owner, and wiring them together is Stage 6C-C | app.strategy_api, app.peer_runner, app.active_runtime_context, app.turn_protocol_runtime, app.sub_game_truth, app.t0_hint, domain.observation, domain.terminal | series policy, artifacts, result agreement, transport, crypto | current round's truth, `captured` | `E-LOCAL-DEFECT` on double adoption or a refused action |
| `app.sub_game_truth` *(added 6C-B)* | Reads one finished round into the next round's truth: ordered barrier declaration, the two-sided effect merge, and whether either direction answered `CAUGHT`. Re-validates nothing | domain.board, domain.truth, app.capture_values | any legality or capture decision | none (pure) | — |
| `app.t0_hint` *(added 6C-B, **temporary**)* | The zero-token template hint and `Intent.TRUTH`, adapting to the locked `hint_max_words`. **Deleted when PRD-04 lands** | app.sealed_record_values | providers, prompts, networks | none (pure) | refuses a limit below the contract floor |
| `app.strategy_api` *(implemented 6B)* | The `StrategyPort` Protocol: `Observation` in → `PhysicalAction` out, one operation, synchronous. `ProposedAction` reserved for PRD-04 | domain.observation, domain.actions | infra, protocol, transport | none | — |
| `app.baseline_strategy` *(added 6B)* | **ROLE-SPECIFIC** deterministic zero-token baseline satisfying `StrategyPort`. Enumerates only through `domain.rules.legal_moves`; implements no legality of its own | domain.observation, domain.reachability, domain.rules, domain.actions | infra, protocol, transport, everything peer/audit-facing | none (stateless) | `E-LOCAL-DEFECT` when invoked with no legal candidates |
| `app.peer_messages` *(4E-R1; deps 4E-R2/FIX2)* | **Immutable internal peer-protocol semantic contracts** — the values application control flow consumes and produces (state-changing inbound events reach the Turn Executor) and that `protocol.messages` maps to/from; **never** wire JSON | pure stdlib **value-definition and validation primitives** only (`typing`, `dataclasses`) + immutable `domain` value types + immutable **globally-FIXED `domain` constants read as structural bounds** (currently `FIRST_SUB_GAME`, `FIXED_NUM_GAMES` from `domain.config_model`; **read-only**, never redefined) + `app.protocol_values` (**runtime use**: constructs and stores the shared semantic values its messages carry) | `protocol`, `infra`, any adapter, `app` implementation modules (`app.state_machine`, `app.orchestrator`, `app.turn_service`), `enum` (no message-local vocabulary exists — reuse `domain.rules.Move` and `app.protocol_values.FinalAuditVerdict`), `hashlib`/`hmac`/`cryptography`/`secrets`/`random`, FastMCP/network libraries, wire serialization, JSON, artifact storage, cryptographic computation, I/O, GUI, replay, reporting — everything else | none | invalid message construction |
| `app.turn_cursor` *(4E-R6; design frozen, not implemented)* | The shared **turn-identity value** `TurnCursor` (and its private int guard). Extracted because *both* future message modules need it and neither should depend on the other - not because a file filled up | pure stdlib value primitives + the globally-FIXED `domain.config_model` bounds (read-only) | `protocol`, `infra`, adapters, `app` implementation modules, `enum`, crypto, JSON, I/O | none | invalid cursor construction |
| `app.peer_turn_messages` *(4E-R6; design frozen, not implemented)* | The **per-turn** peer-visible families: `Commitment`, `Acknowledgement`, `Reveal`. *(Stage 4E-R10-R3: no move-validation family will be added - the peer-facing legality rejection is a transport/port response, not a semantic message, C-12.)* | `app.turn_cursor`, `app.protocol_values`, immutable `domain` value types (incl. `domain.actions`) | same as `app.peer_messages` | none | invalid message construction |
| `app.peer_final_messages` *(4E-R6; design frozen, not implemented)* | The **end-of-sub-game** peer-visible families: `NonceRevealEntry` + `FinalNonceReveal` (one batch per peer per sub-game, 4E-R6-FIX1), and any finalization family later proved transmitted. The reusable `NonceValue` it carries lives in `app.protocol_values`, **not** here | `app.turn_cursor`, `app.protocol_values`, immutable `domain` value types | same as `app.peer_messages` | none | invalid message construction |
| `app.protocol_values` *(4F-R1)* | **Immutable shared protocol semantic value representations** — the primitives that peer-message contracts and outer protocol implementations must agree on (e.g. a SHA-256 digest result, a final-audit verdict). Representation only: it never computes, serializes or knows what was hashed | pure stdlib **value-definition and validation primitives** only (`typing`, `dataclasses`, `enum`) | `protocol`, `infra`, any adapter, `hashlib`/`hmac`/`cryptography`/`secrets`/`random`, FastMCP/network libraries, I/O, JSON or any wire/artifact serialization, cryptographic computation, GUI, replay, reporting — everything else | none | invalid value representation |
| `app.sealed_record_values` *(4E-R9-R1; design frozen, not implemented)* | The **sealed commitment record's semantic values**: `ActorRole` (`"police"`/`"thief"`), `Intent` (`"truth"`/`"lie"`) and `SealedState` (the own-known snapshot `config_sha256`, `self_pos`, `barriers`, `step`, `role`). Representation only — it never hashes, serializes or knows what a commitment is, and **no opponent truth is representable in it** | pure stdlib **value-definition and validation primitives** (`typing`, `dataclasses`, `enum`) + `app.protocol_values` (for `Sha256Digest`) + immutable `domain` value types (`domain.board.Position`) | `protocol`, `infra`, any adapter, `app` implementation modules (`turn_service`, `orchestrator`, `state_machine`), the peer-message modules, `hashlib`/`hmac`/`cryptography`/`secrets`/`random`, I/O, JSON or any serialization | none | invalid structural composition |

**Test boundary:** state-machine and contract tests with fake ports.

> **Stage 4E-R10-R3 ruling - there is no `MoveValidation` peer-message family either (design
> only; no Python).** Appendix E #14 requires the opponent to reject an illegal move, but that is a
> *sanction* statement: no source passage gives the rejection a payload, cadence, vocabulary or
> association, Figure 6 draws no arrow for it, and Ch 6.4-6.5 reserve legality to the local
> algorithm. Stage 4E-R10-R2 stopped `BLOCKED-BY-EXISTENCE-EVIDENCE`; supervising review then chose
> the mechanism. **`app.peer_messages` must never contain `MoveValidation`** - nor `ValidationAck`,
> `ValidationResultMessage`, `MoveAcceptedMessage` or `MoveRejectedMessage` - and the derived
> peer-visible inventory is corrected **9 → 8** (**C-12**). As with C-11, the source is **not**
> claimed to forbid such a message; it simply never requires one.
>
> The obligation does not disappear, it relocates to contracts that already exist. `domain.rules`
> decides legality and is already contracted as **`GameRulesPort`**, which *"never raises for
> legality - returns a verdict"*; `app.turn_service` consumes that verdict; **`E-PROTO-ILLEGAL-MOVE`**
> already owns the "opponent sent an illegal move" outcome with "received message + validator
> verdict" as its evidence; and the peer-facing surface is the response of the ingress operation
> (`PeerServerPort`). No new module, port, semantic concept or error ID is created.
>
> Transport must never re-implement game rules, apply a move, mutate `LocalTruth`, compute scoring
> or choose technical loss - it exposes an already-computed outcome. And four acceptances stay
> distinct: transport delivery/parsing, authentication, protocol phase/order, and **game legality**.
> Only the last is what Appendix E #14 is about; the FastMCP example's `accepted` is the second.
> The exact response shape is **not** frozen: `API_BOUNDARIES.md` defers concrete operation
> signatures to Stage 2B-2C and both peer ports are **async**, so it is recorded as
> `MOVE-REJECTION-TRANSPORT-SHAPE: BLOCKED-BY-TRANSPORT-SHAPE`.

> **Stage 4E-R10-R1 ruling - there is no `FinalAudit` peer-message family (design only; no
> Python).** Stage 4E-R10 audited the two remaining audit-adjacent families and stopped with an
> inventory contradiction; this ruling resolves it. Ch 5 §5.4 exchanges **logs** and makes each
> side's recomputation **local**; Ch 7 §7.5 puts the `Verified OK`/`TAMPERED` verdict in the
> **Replay Viewer** over a persisted file; Figure 6 (p.52) draws no audit-verdict arrow. So
> **`app.peer_messages` must never contain `FinalAudit`**, `app.peer_final_messages` will not
> gain one, and none is planned. The derived peer-visible family inventory is corrected
> **10 → 9** (**C-11**). Classification matters: the source does **not forbid** such a message -
> it simply does not require one, and the project declines to invent it.
>
> Three things survive untouched and must not be confused with a message family. **(i)**
> `app.protocol_values.FinalAuditVerdict` keeps its exact `"Verified OK"` / `"TAMPERED"`
> vocabulary as the **local audit / log / replay** result - its consumers are `infra.replay` and
> the log, never a peer. **(ii)** `ProtocolPhase.FINAL_AUDIT` remains a workflow phase in
> `app.state_machine`; a phase is not a family. **(iii)** The **source-required end-of-game
> audit-material / full-log disclosure** remains a real obligation - it is what lets the opponent
> recompute at all - but it belongs to the **artifact/transport boundary** (`infra.logger` produces,
> `infra.artifacts` stores, `PeerTransportPort` carries, the replay/audit path consumes), **not**
> to `app.peer_messages`, and its interchange shape is an open interoperability blocker rather than
> a payload this layer owns. No module row, dependency permission or Python changes.

> **Stage 4E-R9-R1 reconciliation - where the sealed-record semantic values live (design
> frozen; no Python yet).** Stage 4E-R9 stopped before writing the commitment codec because
> `role`, `intent` and `state` had no exact representation. Freezing their vocabularies is only
> half the answer; they also need a home that the *producers* and the *consumer* can both reach
> legally, and that question was settled by the dependency rules rather than by convenience.
>
> The consumer is fixed: `protocol.commitment` maps the eight-field sealed record, and
> `protocol.canonical` turns it into bytes. The producers are application-side - `app.turn_service`
> assembles a turn's commitment. So the values must sit in a layer **`protocol` may import and
> `app` may construct**, which by Rule D1 means an application-layer (or domain) module.
>
> `app.protocol_values` was the obvious first candidate and was rejected for a **boundary** reason,
> not a size one: its allowed dependencies are pure stdlib value primitives only, while
> `SealedState` must hold a `domain.board.Position`. Admitting `domain` there would widen a module
> deliberately kept stdlib-pure since 4F-R1. (It is also at 137/150 LOC, so the three types could
> not fit regardless - but the boundary argument stands on its own and is the operative one.)
> `domain` was rejected because `SealedState` carries a `Sha256Digest`, which lives in
> `app.protocol_values`, and a `domain → app` edge is forbidden; D23 already refused to move
> digests into `domain` for the mirror-image reason. Defining them inside `protocol.commitment`
> was rejected because `app.turn_service` would then have to import `protocol` - an outward edge.
> The peer-message modules were rejected on ownership: **the sealed record is never transmitted**,
> so it is not a peer-message family.
>
> What remains is one new application-layer module, `app.sealed_record_values`, holding `ActorRole`,
> `Intent` and `SealedState` together - they are one contract (`SealedState.role` *is* an
> `ActorRole`), so splitting them would create a two-module dependency for no gain. Its outward
> permission for `protocol.commitment` and `protocol.canonical` is the **same outer→inner pattern
> already authorized twice**: `protocol.messages` → `app.peer_messages` (4E-R1) and
> `protocol.commitment`/`protocol.config_lock` → `app.protocol_values` (4F-R1). Exact future
> import graph, all edges inward, no cycle:
>
> ```
> domain.board.Position ──┐
>                         ├──> app.sealed_record_values <── protocol.canonical
> app.protocol_values ────┘            ^                 <── protocol.commitment
>   (Sha256Digest)                     └── app.turn_service (producer)
> ```
>
> `DEPENDENCY_RULES.md` is **unchanged**: no new layer, no new kind of edge, and the forbidden
> list already covers everything this module must not do. No requirement, PRD, JDEC, NDEC, INV,
> Conflict-Register or FIELD_MATRIX entry changes.

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
| `protocol.canonical` | Canonical JSON bytes (sorted keys, `(",",":")`, UTF-8, NFC, LF, no trailing NL) — JDEC-002 | stdlib; `ensure_ascii=False` is fixed, not chosen at implementation time (4E-R9-R1) | domain mutation | none | non-canonical input |
| `protocol.commitment` | `H_commit` over the 8-field sealed record; verify at audit | canonical, domain, `app.protocol_values`, `app.sealed_record_values` and `app.turn_cursor` (**runtime use**: constructs and returns the value contracts it produces, and consumes the sealed-record semantic values it maps). *`app.turn_cursor` added at Stage 4E-R9-RESUME-CLOSE: the sealed-record builder frozen at 4E-R9-R1 takes an already-valid `TurnCursor` and reads `cursor.step`/`cursor.sub_game` for the scalar `step` and `sub_game` members, so this row was simply incomplete. Documentation reconciliation of an existing contract - no new decision, port, family or requirement, and no other dependency permission is broadened.* | transport | pending nonce (secret) | non-exact composed input; **digest inequality is a returned comparison result, not a failure** — `E-HASH-MISMATCH`/TAMPERED are owned by the audit consumer above it (4E-R9-R1) |
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

## Stage 4E-R14-R1 — pregame semantic value modules (design frozen, not implemented)

Planned homes for the Stage 4E-R14-R2 implementation. Every module stays **≤150
physical lines**; `domain/config_model.py` is already **150/150** and
`app/protocol_values.py` **137/150**, so neither may absorb new types.

| Module | Owns | Depends on | Must not import |
|---|---|---|---|
| `app.artifact_values` | `GitCommitSha`, `UtcTimestamp` — cross-artifact primitives shared by the declaration and the result | stdlib value/validation primitives only | `domain`, `protocol`, `infra` |
| `app.auth_values` | `AuthProfile`, `KeyId`, `AuthProof` | stdlib only | `hmac`, `hashlib`, `cryptography`, `secrets`, any key source |
| `app.declaration_values` | `Declaration`, `DeclarationTeams`, `DeclarationTimes` | `app.artifact_values`, `app.team_declaration_values` | `protocol`, `infra` |
| `app.team_declaration_values` | `TeamDeclaration`, `RepositoryLinks`, `HardwareDeclaration` | `app.artifact_values` | `protocol`, `infra` |
| `app.interop_profiles` | the nine profile enums + `InteropProfileSet` | `app.auth_values` (for `AuthProfile`, `KeyId`) | `protocol`, `infra` |
| `app.peer_pregame_messages` | `Step0DeclarationExchange`, `ConfigProposal`, `ConfigLockContext`, `ConfigLockEvidence` | `app.auth_values`, `app.declaration_values`, `app.interop_profiles`, `app.protocol_values`, `domain.negotiated_config` | `protocol`, `infra` |
| `domain.config_sections` (+ measured-LOC sibling) | the seven `NegotiatedConfig` section values | `domain.config_model`, `domain.board` | **`app`** — D1 inward-only |
| `domain.negotiated_config` | `NegotiatedConfig` | `domain.config_sections` | **`app`** |
| `app.peer_messages` | **façade re-exports only** — identity-equal, no duplicated classes (**D32**) | the defining modules | — |

**Dependency direction.** No `domain` module imports `app`; no reusable value
module imports transport or protocol runtime; the façade imports the defining
modules and never the reverse. The resulting DAG is acyclic:
`app.artifact_values` → `app.auth_values` / `app.team_declaration_values` →
`app.declaration_values` / `app.interop_profiles` → `app.peer_pregame_messages` →
`app.peer_messages`, with `domain.config_sections` → `domain.negotiated_config`
entering only at `app.peer_pregame_messages`.

**Not a junk drawer.** `app.artifact_values` exists because two artifacts share
exactly two primitives; it is cohesive by that definition and must not accumulate
unrelated types. There is no `values.py` or `types.py`.

## Stage 4E-R16 — implemented application runtime and protocol adapters

The rows below describe the architecture Stage 4E-R16 **actually implemented and
tested**, replacing the position where several of these modules had no row at
all. Nothing here changes a layer rule: it records where the implementation
landed, and the dependency directions were read from the committed imports
rather than from prose.

**The layering rule that shaped all of it.** `app` may not import `protocol`
(cross-cutting rules, above). Every byte, digest and keyed proof the runtime
needs therefore arrives through a `app.ports` Protocol implemented by a
`protocol` adapter and wired by the composition root (D3). That is why the four
runtimes are synchronous, deterministic and testable with plain fakes, and why
no canonicalization or key material ever reaches `app`.

### Application layer — contracts and runtime

| Module | Owns | Depends on | Must not import |
|---|---|---|---|
| `app.ports` | the five R16 port Protocols — `Step0AuthPort`, `ConfigDigestPort`, `ConfigLockAuthPort`, `ResultDigestPort`, `TimestampPort` | `app` semantic values, `domain.negotiated_config` (type references) | `protocol`, `infra`, transport, `bytes`/key material in any signature |
| `app.protocol_errors` | raisable classes for the **existing** `ERROR_MODEL.md` identities (`E-PROTO-MALFORMED`, `E-PROTO-STALE`, `E-AUTH-FAILURE`, `E-CONFIG-MISMATCH`, `E-NET-CONVENTION-MISMATCH`, `E-REPORT-DISAGREE`, `E-LOCAL-DEFECT`) | stdlib `typing` only | everything else; **owns no new identity** and never carries key material |
| `app.result_identity_values` | `ResultParticipants`, `GithubLinks`, and the two shared result validators | `app.result_values` | `domain`, `protocol`, `infra` |
| `app.result_core_values` | `SubGameResult`, `CumulativeResult`, `ResultApprovalCore` | `app.artifact_values`, `app.result_identity_values`, `app.result_values`, `domain.config_model`, `domain.terminal` | `protocol`, `infra`; **not a peer family and not a `FIELD_MATRIX` row** |
| `app.step0_runtime` | outbound exchange, inbound validation, immutable merge, `Step0Completion` | `app.declaration_values`, `app.peer_pregame_messages`, `app.ports`, `app.protocol_errors`, `app.team_declaration_values` | `protocol`, `infra`; owns no sanction |
| `app.config_negotiation_runtime` | deterministic initial proposer, bounded cadence, LIVE proposal validation, convergence | `app.interop_profiles`, `app.peer_pregame_messages`, `app.protocol_errors`, `domain.config_model`, `domain.negotiated_config` | `protocol`, `infra`; never re-implements Appendix-F status checks the sections already own |
| `app.config_lock_runtime` | lock evidence construction/verification and the `CONFIG_LOCKED` gate | `app.interop_profiles`, `app.peer_pregame_messages`, `app.ports`, `app.protocol_errors`, `app.protocol_values`, `app.state_machine`, `domain.negotiated_config` | `protocol`, `infra`; **never duplicates the transition graph** — it delegates to `app.state_machine` |
| `app.result_core_runtime` | approval-core assembly, contribution merge by declared slot, derived `total_tokens` | `app.artifact_values`, `app.declaration_values`, `app.protocol_errors`, `app.result_core_values`, `app.result_identity_values`, `app.result_values`, `domain.terminal` | `protocol`, `infra` |
| `app.result_agreement_runtime` | the deterministic timestamp proposer and the two-request cadence | `app.artifact_values`, `app.peer_final_messages`, `app.ports`, `app.protocol_errors`, `app.protocol_values`, `app.result_identity_values`, `app.result_values` | `protocol`, `infra`; reads **no clock** — the instant arrives through `TimestampPort` |
| `app.result_agreement_gates` | `MutualAgreementGate`, the asymmetric local completion verdict | `app.protocol_values` | everything else; `mutual_agreement` is **local state, never a peer field** |

### Protocol layer — adapters

| Module | Owns | Depends on | Must not import |
|---|---|---|---|
| `protocol.canonical` *(row above; scope amended 4E-R16)* | canonical text and canonical JSON bytes. The v1 domain `str`/`int`/`list`/`dict` **gained `bool` and `Decimal`** when the Step-0 and config cores first needed them; `float` and `None` remain refused | stdlib | domain mutation; **no second canonical policy anywhere** |
| `protocol.keyed_auth` *(row above; deps amended 4E-R16)* | `auth_input`, the `AuthProvider` Protocol, `HmacSha256Provider`, `KeyedAuthenticator` | `protocol.canonical`, `app.auth_values`, `app.protocol_errors` *(runtime use of the value contracts it produces and consumes)* | transport; **never logs, stores, serializes or `repr`s key bytes** |
| `protocol.declaration` *(row above; deps amended 4E-R16)* | the 19-member Step-0 core projection and the `Step0AuthPort` adapter | `protocol.keyed_auth`, `app.auth_values`, `app.declaration_values`, `app.protocol_errors`, `app.team_declaration_values` | transport; maps every member **explicitly** — no reflection, no generic encoder |
| `protocol.config_projection` | the 35-member binding config core and the eleven-profile projection | `app.interop_profiles`, `domain.board`, `domain.negotiated_config` | `protocol.canonical` and hashing — it is **mapping only** |
| `protocol.config_lock` *(row above; deps amended 4E-R16)* | `config_sha256`, the lock-context projection, the `ConfigDigestPort`/`ConfigLockAuthPort` adapter | `protocol.canonical`, `protocol.config_projection`, `protocol.keyed_auth`, `app.auth_values`, `app.peer_pregame_messages`, `app.protocol_values`, `domain.negotiated_config` | strategy, transport |
| `protocol.result_core` | the result approval-core projection, the explicit outcome vocabulary table, and `result_sha256` | `protocol.canonical`, `app.protocol_errors`, `app.protocol_values`, `app.result_core_values`, `app.result_identity_values`, `app.result_values`, `domain.terminal` | transport; introduces **no keyed proof** — result approval is a mutual acknowledgement, not producer authentication |

### Implemented import DAG (read from the committed imports)

```
domain.*  ─┐
app semantic values ─→ app.ports ─→ app.<family>_runtime
                                        (application layer ends here)
protocol.canonical ─→ protocol.keyed_auth ─→ protocol.declaration
                   ├─→ protocol.config_projection ─→ protocol.config_lock
                   └─→ protocol.result_core
protocol adapters ─→ app semantic values + app.protocol_errors   (inward only)
```

Acyclic, and asserted per module from the AST by
`tests/app/test_runtime_layering.py`: **no `app` module imports `protocol`**, and
no runtime performs I/O, reads a clock or computes a digest itself.

**Transport was absent at R16; it exists as of R17.** The sentence that stood
here - "no FastMCP adapter, socket, HTTP client or server exists" - was true when
R16 closed and is false now. A **local** FastMCP Streamable HTTP server and client
are implemented and verified across independent OS processes; the section below
records them. `infra.mcp_server` / `infra.mcp_client` remain **superseded rows**:
the shipped transport lives in `mars777_police.transport`, not under `infra`, and no tunnel,
Gmail or GUI module exists.

## Stage 4E-R17 — implemented FastMCP peer transport (LOCAL only)

The rows below describe what Stage 4E-R17 (with R17-R1, RESUME, FIX, FIX2 and
FIX3) **actually implemented and tested**. Dependency directions were read from
the committed imports and are asserted from the AST, not asserted in prose.

**Scope honesty, stated once and not softened.** What is implemented and verified
is **local** Streamable HTTP between two peer processes on `127.0.0.1`. A public
tunnel, an externally reachable endpoint, external reachability evidence, a real
opponent and a counted match are **none of them implemented and none of them
tested**. Nothing in this section may be read as readiness for any of those.

### Application layer — the four R17 application modules

`app` still may not import `protocol`, and it may not import `transport` either.
Every peer call the application makes leaves through a Protocol it owns; the
FastMCP adapter satisfies that Protocol structurally, from the outside.

| Module | Owns | Depends on | Must not import |
|---|---|---|---|
| `app.peer_transport` | **`PeerTransportPort`** - the outbound application-facing port: the nine semantic `send_*` operations, plus the `AuditDocument` alias. Ordinary completion returns `None`; exactly two operations carry a result (`send_reveal` → the peer's game-legality `bool`, `send_result_agreement` → the peer's `Sha256Digest`) | `app` peer-message families and `app.protocol_values` (type references), `typing.Protocol` | `protocol`, `infra`, `transport`, `fastmcp`, `pydantic`, any HTTP library, any wire DTO, any URL handling |
| `app.peer_supervision` | **`TimeoutPolicy`** (the bootstrap window and `for_config` → the locked `network_and_league.response_timeout_sec`) and **`Watchdog`** (injected clock, `check` / `is_expired`), plus `WatchdogTimeoutError` / `E-TIMEOUT-WATCHDOG` | `domain.negotiated_config` (read-only), stdlib | `protocol`, `transport`, `fastmcp`; **assigns no sanction, no technical loss and no score**, and its error is deliberately **not** a `PeerProtocolError` |
| `app.result_agreement_gates` | **`MutualAgreementGate`** (the asymmetric local completion verdict) and **`require_matching_digest`** (refuses a peer digest that differs from ours, raising the already-frozen `E-REPORT-DISAGREE`). As of R17-FIX3 both are called from production, by `app.result_exchange` - previously they had no production caller | `app.protocol_values`, `app.protocol_errors` | everything else; `mutual_agreement` is **local state, never a peer field**, and this module owns **no new error identity** |
| `app.result_exchange` | **`ResultExchange`** - the application owner of one result agreement end to end: it drives the two-request cadence through `ResultAgreementRuntime`, computes the local digest through `result_core_runtime.assemble()` + `ResultDigestPort`, compares with `require_matching_digest`, and reports the verdict through `MutualAgreementGate`. It handles the frozen proposer/non-proposer asymmetry in one `_verify` | `app.peer_transport` (the port), `app.ports` (`ResultDigestPort`), `app.result_agreement_runtime`, `app.result_core_runtime`, `app` result and artifact values, `app.result_agreement_gates` | `protocol`, `infra`, `transport`, `fastmcp`, `pydantic`, any wire DTO; it **never learns how the digest travelled** and computes **no second digest algorithm** |

### Transport layer — the nineteen `mars777_police.transport` modules

Everything below may import **inward** (`app`, `domain`) and is the **only** place
`fastmcp` and `pydantic` appear. Nothing here owns game truth, decides legality,
assigns a sanction or holds a score.

| Module | Owns | Depends on | Must not import |
|---|---|---|---|
| `transport.__init__` | the package's public surface - `build_server`, `PeerClient`, `PEER_TOOLS`, `FastMcpPeerTransport` | the modules below | anything that would make importing the package do I/O |
| `transport.wire_scalars` | the constrained wire spellings of the project's scalar semantic values, including the **canonical-text** spelling of every semantic `Decimal` | `pydantic` | `app` runtime modules; **no `float` ever represents a semantic decimal** |
| `transport.wire_config_sections` | wire DTOs for the seven Appendix-B config sections | `transport.wire_scalars`, `pydantic` | `app` runtime, `domain` services |
| `transport.wire_config` | wire DTOs for the binding config core, the profile set and the lock evidence | `transport.wire_config_sections`, `transport.wire_scalars` | as above |
| `transport.wire_declaration` | wire DTOs for the declaration subtree and the Step-0 exchange, including the **conditional** `vram_gb` (omitted, never `null`) | `transport.wire_scalars` | as above |
| `transport.wire_turn` | wire DTOs for the three turn families and the two end-of-series families | `transport.wire_scalars` | as above |
| `transport.envelopes` | the **four tool-level request envelopes** and their **closed** `kind` vocabularies. Each tool declares its own kind set - there is deliberately no single union of all nine - and `extra="forbid"` applies at every level | the wire DTO modules, `pydantic` | routing logic, application logic |
| `transport.codec_auth` | codec for the keyed-auth envelope and the eleven series-wide profiles | `app.auth_values`, `app.interop_profiles`, `transport.wire_*` | key material of any kind - **only `key_id` crosses, never key bytes** |
| `transport.codec_declaration` | codec for the declaration subtree and the Step-0 exchange | `app.declaration_values`, `app.team_declaration_values`, `transport.codec_auth`, `transport.wire_declaration` | `protocol` canonicalization - it maps, it does not hash |
| `transport.codec_config` | codec between the config wire DTO and the frozen 35-member semantic core | `domain.negotiated_config`, `domain.config_sections`, `transport.wire_config` | re-implementing an Appendix-F status check the sections already own |
| `transport.codec_pregame` | codec for the config proposal and the config lock evidence | `app.peer_pregame_messages`, `transport.codec_auth`, `transport.codec_config` | as above |
| `transport.codec_turn` | codec for the three per-turn peer families | `app.peer_turn_messages`, `domain.actions`, `transport.wire_turn` | movement-legality logic - legality is `domain.rules`, never a codec |
| `transport.codec_final` | codec for the two end-of-series families (`FinalNonceReveal`, `ResultAgreement`) | `app.peer_final_messages`, `app.result_values`, `transport.wire_turn` | digest computation |
| `transport.wire_errors` | translating project failures onto the framework error channel, **both ways**: the seven peer identities through `ToolError`, `E-TRANSPORT` for a delivery failure, and an unknown server exception collapsed to `E-LOCAL-DEFECT` | `app.protocol_errors`, `fastmcp` | leaking a traceback, an internal `repr` or any secret onto the wire |
| `transport.handlers` | **`PeerOperations`** - the **inbound**, server-side application contract the transport calls: the nine `on_*` operations over semantic values | `app` peer-message families | `fastmcp`, `pydantic`; it is **not** an alias of `PeerTransportPort` and the two share no operation name |
| `transport.router` | dispatching a **validated** envelope to `PeerOperations`, and nothing else | `transport.envelopes`, `transport.handlers`, the codecs | guessing a payload shape - the `kind` discriminator is the only router input |
| `transport.server` | the FastMCP server adapter: **one stable ingress per peer process**, exposing exactly `PEER_TOOLS` | `transport.router`, `transport.wire_errors`, `fastmcp` | a fifth tool, a heartbeat, an alias |
| `transport.client` | the FastMCP client adapter: connection, envelope, **per-call deadline** (`for_locked_config` reads the agreed `response_timeout_sec` through `TimeoutPolicy`; `for_bootstrap` uses the frozen negotiation window), response decoding, framework-error translation | `app.peer_supervision`, `transport.wire_errors`, `fastmcp` | a hardcoded timeout; knowing which **family** it is carrying |
| `transport.peer_transport` | **`FastMcpPeerTransport`** - the concrete adapter that structurally satisfies `PeerTransportPort`, encoding each semantic value with the codec that owns its family | `transport.client`, the codecs, `app` semantic values | importing `app.peer_transport` - conformance is **structural**, proven with no `cast` and no `type: ignore` |

### The two directions, which are never conflated

```
inbound   peer ─→ FastMCP server ─→ transport.router ─→ PeerOperations ─→ application
outbound  application ─→ PeerTransportPort ─→ FastMcpPeerTransport ─→ PeerClient ─→ peer
```

`PeerOperations` is what a peer asks **of us**. `PeerTransportPort` is what we ask
**of a peer**. Same nine frozen operations, opposite directions, disjoint method
names (`on_*` vs `send_*`), no alias and no shared base. Conflating them would
hide which side of the wire a failure came from.

### Implemented import DAG (read from the committed imports)

```
domain.* ─→ app semantic values ─→ app.ports / app.peer_transport
                                        ─→ app.*_runtime, app.result_exchange
                                        (application layer ends here)
transport.wire_scalars ─→ transport.wire_* ─→ transport.envelopes ─→ transport.router
transport.codec_* ─→ app semantic values                       (inward only)
transport.client ─→ app.peer_supervision                       (inward only)
transport.peer_transport ─→ transport.client + transport.codec_*
transport.server ─→ transport.router + transport.wire_errors
```

Acyclic. `domain`, `protocol` and `app` import **nothing** from `transport`;
`transport` imports inward only. `fastmcp` and `pydantic` appear **only** under
`transport` - the sole exception being that `pydantic` is a *directly owned*
project dependency rather than a transitive one, which is a packaging fact, not a
layering one. Asserted from the AST by `tests/transport/test_peer_transport_port.py`
alongside the R16 guard in `tests/app/test_runtime_layering.py`.

### The public tool surface, frozen

Exactly four tools - `negotiate`, `receive_turn`, `submit_audit`,
`receive_control` - carrying exactly nine kinds: `step0`, `config_proposal`,
`config_lock`, `commitment`, `acknowledgement`, `reveal`, `final_nonce_reveal`,
`audit_disclosure`, `result_agreement`. One tool argument, `request = {kind,
payload}`, both members required, `additionalProperties: false` at both levels.
No heartbeat, no fifth tool, no alias.

### What R17 did NOT implement

- **Public transport**: no tunnel, no externally reachable endpoint, no external
  reachability validation, no reconnect evidence, no real opponent.
- **A game orchestrator over `ResultExchange`**: R17 ships the executable
  application exchange service and proves it across independent peer processes.
  Wiring it into a complete counted game is a later integration concern.
- **Token-accounting cryptographic evidence**, which remains
  `TOKEN-ACCOUNTING-CRYPTO-EVIDENCE: BLOCKED-BY-CONSTRUCTION`.
