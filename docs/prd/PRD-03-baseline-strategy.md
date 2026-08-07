# PRD-03 — Baseline Strategy — group MaRs-777 (POLICE)

## 1. Document Metadata

| Field | Value |
|---|---|
| PRD | PRD-03 — Baseline Strategy (**POLICE**) |
| Owns | The strategy plug-in behind `StrategyPort`; `app.strategy_api` contract usage |
| Architecture inputs | `STRATEGY_ARCHITECTURE.md`, `API_BOUNDARIES.md`, `DATA_FLOW.md` §3, `DEPENDENCY_RULES.md` §2 |
| Symmetry class | **ROLE-SPECIFIC** — the Thief PRD-03 differs materially by design |

## 2. Status

**APPROVED — PHASE 2 LOCKED.** Approved after Stage 2-CLOSE supervising review.
**Implementation status: NOT STARTED.** No code. No dependency.

## 3. Purpose

Define (a) the **StrategyPort contract**, (b) a **legal deterministic zero-token police
baseline**, (c) a **benchmarkable fallback**, and (d) the **extension seam** for the
later competitive-strategy phase. This PRD does **not** design our final league strategy.

## 4. Problem Statement

The agent must always produce a legal action inside the step deadline, without ever
seeing the thief's true position, without touching transport or crypto, and identically
on Linux and Windows. A baseline that is merely random wastes the pursuit; a baseline
that is entangled with networking or crypto cannot be replaced later. Both failure modes
must be designed out now.

## 5. Scope

Strategy plug-in decision policy · seeding and tie-breaking · time-boxing and fallback ·
diagnostics it emits · the plug-in selection mechanism.

## 6. Out of Scope

Movement **legality** (PRD-01 — the validator remains authoritative) · transport,
crypto, artifacts (structurally forbidden to strategy) · hint text generation and LLM
(PRD-04) · advanced competitive strategy (later phase, §13.6).

## 7. Actors

`app.turn_service` (calls the port) · `domain.observation` (builds the input) ·
`domain.rules` (validates the output) · `infra.metrics` (records decision diagnostics).

## 8. Definitions

**Observation** — the role-legal input record. **ProposedAction** — a *proposal*, not an
effect. **Candidate set** — legal actions at this step. **Belief** — labelled estimate of
thief location. **Fallback** — the deterministic legal action used when the primary
policy cannot decide in budget.

## 9. Locked Source Requirements

| ID | Modality | Requirement |
|---|---|---|
| STRAT-001 | MUST | Separate strategy module connected between incoming hint-decode and outgoing commit-pack; holds belief update, legal move choice, deception text |
| STRAT-002 | MUST | Keep the spatial/movement decision **fully algorithmic** in all policy modes |
| STRAT-003 | MAY | Movement policy may be heuristics (Bayes + Manhattan), own algorithm, or optionally RL |
| GAME-009 | MUST | Movement legality decided by deterministic code, never delegated to an LLM |
| LLM-001 | SHOULD | Do not hand the LLM the move decision itself |
| LLM-005 | MAY | LLM move tactic only by explicit documented mutual agreement; local code still enforces legality |
| GUI-001 | MUST | Local truth only (own position, sensed scent, received hints, belief heatmap) |
| GUI-002 | **MUST NOT** | Never display/expose the full objective board state |
| BAR-001…005 | MUST (POLICE) | Barrier declaration/quota/placement rules the strategy must respect |

## 10. Project / Architecture Decisions

| Decision | Type |
|---|---|
| Strategy receives `Observation`, returns `ProposedAction` | ARCHITECTURE-CONSTRAINT |
| Strategy imports only `app.strategy_api` + `domain` value types | ARCHITECTURE-CONSTRAINT (D3) |
| Deterministic **given a seed**; seed recorded as replay evidence | PROJECT-CONTRACT |
| Plug-in selected by dotted path in local settings | **REFERENCE-COMPATIBILITY** pattern (D-13) |
| Baseline is intentionally simple and **must not** be our competitive strategy | PROJECT-CONTRACT |

## 11. Inputs — the legal `Observation`

Own true position · own step / remaining steps · own barrier budget remaining · locked
config values (grid, `move_set`, `max_barriers`, `max_moves`, `survival_threshold`,
scent parameters) · public barrier set · own scent readings · **belief** over thief
location (explicitly typed, with uncertainty) · current scores · remaining decision
budget · validated opponent-public data (revealed move, revealed hint + its `intent`).

**Forbidden inputs (the type has no field for them):** thief true position · thief nonce
· thief pre-reveal move · any network/transport object · FastMCP client or server ·
hashing/auth objects or key material · artifact writer · Gmail · GUI state ·
unrestricted filesystem access.

## 12. Outputs — `ProposedAction`

`move ∈ {N,S,E,W,STAY}` **or** a barrier placement (police-only) · optional hint request
(text produced by PRD-04) with its `intent` classification · optional confidence and
diagnostics. **Every output is a proposal**; `domain.rules` validates before any effect.

## 13. Functional Requirements

### 13.1 Contract

| ID | Requirement | Traces to |
|---|---|---|
| **PRD03-FR-001** | The strategy is a replaceable plug-in satisfying `StrategyPort`; replacing it requires **no change** to networking, cryptography, persistence, GUI, or reporting. | STRAT-001; `STRATEGY_ARCHITECTURE.md` |
| **PRD03-FR-002** | It accepts only an `Observation` and returns only a `ProposedAction`. | `API_BOUNDARIES.md` P1 |
| **PRD03-FR-003** | It MUST NOT send network messages, write artifacts, touch nonce/hash material, mutate authoritative state, or bypass validation. | `DEPENDENCY_RULES.md` §3 |
| **PRD03-FR-004** | The spatial/movement decision is **fully algorithmic** in all modes. | **STRAT-002**, GAME-009 |
| **PRD03-FR-005** | The plug-in is selected by configuration (dotted path); an unknown/unloadable plug-in fails start-up rather than silently falling back. | REFERENCE-COMPATIBILITY (D-13) |

### 13.2 Police baseline policy

| ID | Requirement | Traces to |
|---|---|---|
| **PRD03-FR-010** | Build the **candidate set** = all legal actions at this step, obtained from the same deterministic rules the validator uses (no private legality logic). | GAME-003/004; PRD-01 |
| **PRD03-FR-011** | Maintain a **belief** over candidate thief cells, updated from legally available evidence only: own scent readings, revealed thief moves, revealed hints (as *unreliable* text — `intent` may be a lie), and barrier-induced reachability constraints. | STRAT-001; GUI-001 |
| **PRD03-FR-012** | Belief update MUST NOT use the thief's true position; it is a distribution over cells, never a certainty unless the position was legitimately revealed. | GUI-002; PRD01-FR-021/022 |
| **PRD03-FR-013** | **Pursuit rule:** when belief has a clear mode (a single highest-weight cell, or a set whose members share a first step), take the legal move minimising **barrier-aware shortest-path distance** to that target. | STRAT-003 (Manhattan/heuristic permitted) |
| **PRD03-FR-014** | Distance MUST be barrier-aware (BFS over passable cells), not plain Manhattan, so a barrier wall does not attract the police into a dead end. Plain Manhattan MAY be used only as a tie-break heuristic. | BAR-004 (impassable); STRAT-003 |
| **PRD03-FR-015** | **Ambiguity rule:** when belief is flat or multi-modal (no dominant mode within a defined margin), choose the legal move maximising a simple, deterministic **information-gain proxy** — the move that most reduces the number of belief-consistent cells reachable by the thief next step (a counting heuristic, not a probabilistic search). | STRAT-003 |
| **PRD03-FR-016** | **STAY is never chosen when a strictly-improving legal move exists.** STAY is permitted only when it is the sole legal action, when it is required to place a barrier, or when every move strictly worsens the objective. | quality requirement (anti-passivity) |
| **PRD03-FR-017** | **Barrier rule (baseline):** place a barrier only when (a) quota remains, (b) placement is legal under BAR-004, and (c) it either captures the thief immediately (BAR-003) or strictly reduces the thief's legal-move count in the belief-supported region by at least a configured threshold. Otherwise prefer moving. | BAR-003/004/005 |
| **PRD03-FR-018** | The baseline MUST respect `max_barriers` and never propose a placement that would exceed it. | **BAR-005** |
| **PRD03-FR-019** | Every barrier the baseline proposes is reported for open, truthful declaration; the strategy never conceals or misreports a placement. | **BAR-001/002** |
| **PRD03-FR-020** | The baseline never proposes a capture claim; capture is **detected** by the domain, not asserted by the strategy. | CRYPTO-004/005; PRD01-FR-055 |

### 13.3 Determinism and tie-breaking

| ID | Requirement | Traces to |
|---|---|---|
| **PRD03-FR-030** | Given identical strategy profile, seed and `Observation`, the returned `ProposedAction` is identical on Linux and Windows. | NFR; cross-OS |
| **PRD03-FR-031** | Randomness, if any, comes **only** from a seeded RNG owned by the strategy. Global/unseeded randomness and wall-clock-derived randomness are forbidden. | determinism |
| **PRD03-FR-032** | The seed is supplied via local settings and **recorded as replay evidence**. | REPLAY-001/002 |
| **PRD03-FR-033** | **Tie-break order (total and deterministic):** (1) lower barrier-aware distance; (2) higher information-gain proxy; (3) fixed action order `N, E, S, W, STAY`; (4) lexicographically smaller destination `[row, col]`. This yields exactly one action for any candidate set. | determinism |
| **PRD03-FR-034** | No decision may depend on Python hash randomization, set iteration order, or dictionary insertion order; all collections are canonically sorted before iteration. | cross-OS determinism |

### 13.4 Time-boxing, fallback and failure

| ID | Requirement | Traces to |
|---|---|---|
| **PRD03-FR-040** | The decision is time-boxed to a budget strictly smaller than the negotiated `response_timeout_sec` (config-sourced; App F default 30 s, NEGOTIABLE). | STATE-004; PRD-02 |
| **PRD03-FR-041** | **Fallback order** on timeout, invalid proposal, empty candidate set, or internal exception: (1) best action found so far if legal; (2) the legal move minimising barrier-aware distance to the belief mode; (3) the first legal action in the fixed order `N, E, S, W`; (4) `STAY` if it is the only legal action. | robustness with measurable order |
| **PRD03-FR-042** | A strategy failure MUST degrade to a deterministic legal fallback and MUST NOT bypass the validator. | S-clause; GAME-009 |
| **PRD03-FR-043** | A strategy failure MUST NOT mutate authoritative domain state (the strategy has no write path). | `DEPENDENCY_RULES.md` |
| **PRD03-FR-044** | If the optional LLM (PRD-04) is unavailable, slow, or returns unusable output, movement is unaffected — movement never depended on it. | LLM-001; T0 viability |
| **PRD03-FR-045** | Every fallback activation is recorded with its reason for observability. | `OBSERVABILITY.md` §3 |

### 13.5 Zero-token operation

| ID | Requirement | Traces to |
|---|---|---|
| **PRD03-FR-050** | The baseline operates fully at **T0** (no LLM, no tokens, no network beyond the peer protocol) and can complete an entire six-sub-game series. | `LLM_BOUNDARY.md`; PERF-003 |

### 13.6 Future competitive extension (explicitly deferred)

| ID | Requirement |
|---|---|
| **PRD03-FR-060** | The seam MUST allow a later competitive strategy to add, **without contract change**: Bayesian belief updates, multi-turn lookahead/search, choke-point and barrier-network planning, opponent modelling and adaptation across the series, and learned priors. |
| **PRD03-FR-061** | **None of these is claimed or required for the baseline.** The baseline is explicitly a simple, competent, deterministic policy — not a search engine. |

## 14. Non-Functional Requirements

| ID | Requirement |
|---|---|
| **PRD03-NFR-001** | Decision latency p95 **< 50 ms** at 7×7 with a full barrier set (measurable), leaving ample margin inside the step budget. |
| **PRD03-NFR-002** | Zero imports of transport, crypto, artifact, GUI or LLM modules (dependency test). |
| **PRD03-NFR-003** | Every strategy file ≤ **150 lines**; belief, distance and policy are separate modules. |
| **PRD03-NFR-004** | The baseline beats a uniform-random legal policy on capture rate over ≥ 200 seeded self-play sub-games (measurable benchmark, SIMULATION layer). |

## 15. State / Lifecycle Responsibilities

The strategy owns **only** its internal policy state (belief working copy, seeded RNG,
per-turn scratch). It owns no authoritative state, and its internal belief copy is
derived — `domain.belief` remains the owner.

## 16. Validation Rules

The strategy pre-checks candidate legality using the shared rules, but the **validator
remains authoritative**: any proposal is re-validated by `domain.rules` before effect. A
proposal rejected by the validator triggers `E-LOCAL-VALIDATION` and the fallback ladder.

## 17. Error / Failure Behaviour

Timeout → fallback · invalid proposal → `E-LOCAL-VALIDATION` → fallback · empty candidate
set → (thief-trapped case is a domain terminal; for police an empty set means STAY) ·
internal exception → logged, fallback · LLM unavailable → `E-LLM-UNAVAILABLE`,
non-fatal. No sanction is produced by the strategy.

## 18. Security / Privacy Constraints

Cannot access opponent truth (type has no field) · cannot reach nonce/key material ·
cannot emit network traffic · receives only sanitized, validated opponent-public data ·
its diagnostics MUST NOT contain forbidden data or secrets.

## 19. Determinism / Reproducibility

Same profile + seed + observation ⇒ same action, on both OSes; total tie-break order;
no wall-clock or unseeded randomness; canonical iteration order. Seed recorded for replay.

## 20. Performance / Deadline Constraints

Budget strictly inside `response_timeout_sec` (config-sourced). Anytime behaviour: the
policy must always have a legal "best so far" available when the budget expires.

## 21. Cross-Platform Constraints

Identical decisions on Linux and Windows; integer arithmetic for distances; sorted
collections; no locale or platform-dependent behaviour.

## 22. Observability / Evidence

Decision latency, fallback rate + reason, validator-rejection rate, candidate-set size,
belief entropy/mode margin, action chosen, seed. **Belief quality is measured only
post-hoc at replay time**, never live (that would require opponent truth).

## 23. Acceptance Criteria

**Common**

| ID | Criterion |
|---|---|
| **PRD03-AC-001** | The `Observation` type exposes no opponent true position; a compile/contract test fails if such a field is added. |
| **PRD03-AC-002** | Static check: strategy imports no transport, crypto, artifact, reporting or GUI module. |
| **PRD03-AC-003** | Same seed + same observation ⇒ identical action, verified on Linux and Windows. |
| **PRD03-AC-004** | Decision always returns within the budget, or the fallback ladder produces a legal action. |
| **PRD03-AC-005** | A deliberately illegal proposal is rejected by the validator and the fallback is used; no state change occurs. |
| **PRD03-AC-006** | A complete six-sub-game series runs at **T0** with zero tokens. |

**Police-specific**

| ID | Criterion |
|---|---|
| **PRD03-AC-010** | *Simple pursuit:* with belief concentrated on one cell and an open board, each turn strictly reduces barrier-aware distance to that cell. |
| **PRD03-AC-011** | *Scent-guided ambiguity:* with a flat belief and a scent gradient, the chosen move is the deterministic information-gain maximiser, reproducible across runs. |
| **PRD03-AC-012** | *Barrier-aware route:* with a wall between police and target, the policy routes around it and does **not** oscillate against the wall (plain-Manhattan behaviour would fail this test). |
| **PRD03-AC-013** | *Deterministic equal-choice:* with two equally-scored moves, the documented tie-break order selects exactly one, identically every run. |
| **PRD03-AC-014** | *Barrier discipline:* the baseline never proposes a placement exceeding `max_barriers`, never places while moving, and never places on a non-adjacent cell. |
| **PRD03-AC-015** | *Anti-passivity:* STAY is not chosen when a strictly-improving legal move exists. |
| **PRD03-AC-016** | *Benchmark:* capture rate over ≥ 200 seeded sub-games is strictly greater than a uniform-random legal policy. |

## 24. Planned Tests

| ID | Test | Layer |
|---|---|---|
| **PRD03-T-001** | Observation privacy contract | CONTRACT |
| **PRD03-T-002** | Forbidden-import scan | CONTRACT |
| **PRD03-T-003** | Seeded determinism (same in/out) | PROPERTY |
| **PRD03-T-004** | Cross-OS determinism | PROPERTY / CROSS-PROCESS |
| **PRD03-T-005** | Time-box + fallback ladder (each rung) | UNIT |
| **PRD03-T-006** | Validator authority over a bad proposal | INTEGRATION |
| **PRD03-T-007** | Pursuit distance monotonicity | UNIT |
| **PRD03-T-008** | Barrier-aware routing around a wall | UNIT |
| **PRD03-T-009** | Ambiguity/information-gain determinism | UNIT |
| **PRD03-T-010** | Tie-break total order | PROPERTY |
| **PRD03-T-011** | Barrier quota/legality discipline | UNIT |
| **PRD03-T-012** | Anti-passivity (no idle STAY) | UNIT |
| **PRD03-T-013** | Zero-token full series | INTEGRATION |
| **PRD03-T-014** | Baseline vs random benchmark (≥200 seeded runs) | SIMULATION |

## 25. Requirement Traceability

**Directly owned:** STRAT-001, STRAT-002, STRAT-003. **Constrained by:** GAME-009,
LLM-001, LLM-005, GUI-001/002, BAR-001…005, GAME-003/004. **Consumes:** PRD-01
validator + `Observation`; PRD-02 deadline budget; PRD-04 hint production.

## 26. Dependencies on Other PRDs

PRD-01 (legality, distance primitives, belief type) · PRD-02 (invocation, budget,
seed plumbing) · PRD-04 (hint/intent when a hint is requested) · PRD-07 (metrics,
replay-time belief-quality analysis).

## 27. Open Design Decisions

Belief representation (weight map vs candidate set) — shared with PRD-01 · exact
information-gain proxy formula and its ambiguity margin · barrier-benefit threshold ·
whether the baseline uses BFS every turn or caches distances · benchmark harness shape.

## 28. Explicit Non-Goals

Not the competitive league strategy · no Bayesian/Monte-Carlo/RL machinery in the
baseline · no opponent modelling · no multi-turn search · no LLM movement · no
legality logic of its own.

## 29. Implementation Readiness Checklist

- [x] Port contract, legal inputs and forbidden inputs enumerated
- [x] Baseline policy fully specified (pursuit, ambiguity, barriers, anti-passivity)
- [x] Total deterministic tie-break order defined
- [x] Fallback ladder defined with measurable ordering
- [x] Benchmark criterion defined (beats random, ≥200 seeded runs)
- [x] Advanced techniques explicitly deferred, not claimed
- [ ] Supervising review — **pending**
- [ ] Implementation — **not started**
