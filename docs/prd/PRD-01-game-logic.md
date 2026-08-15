# PRD-01 — Game Logic — group MaRs-777 (POLICE)

## 1. Document Metadata

| Field | Value |
|---|---|
| PRD | PRD-01 — Game Logic |
| Repository role | **POLICE** |
| Owns | The deterministic game domain (`domain.*`) |
| Authoritative source | book v3.0.0 + locked Stage-1 specification (`../spec/`) |
| Architecture inputs | `../architecture/MODULE_BOUNDARIES.md` (domain layer), `STATE_OWNERSHIP.md`, `STATE_MACHINE.md`, `ERROR_MODEL.md`, `DEPENDENCY_RULES.md` |
| Symmetry class | **COMMON-WITH-ROLE-SECTIONS** (§5.3 is the only role-differentiated part) |

## 2. Status

**APPROVED — PHASE 2 LOCKED.** Approved after Stage 2-CLOSE supervising review.
The requirements below are unchanged by implementation progress.

**Implementation status: GAME MECHANICS IMPLEMENTED-INTEGRATED; PRODUCTION
AUTONOMOUS GAME LOOP NOT YET IMPLEMENTED.** The deterministic mechanics this PRD
owns — board geometry, orthogonal movement and `STAY`, barriers and quota,
capture, scoring and the terminal conditions — are implemented in `domain/` and
covered by tests. What does **not** exist is a production driver that selects
actions and plays a sub-game: no strategy chooses a move, and the executable
serves without playing. Terminal outcomes are supplied by test harnesses today,
not reached by play.

**Completed implementation slice:** Stage 3A — deterministic domain foundation:
`GridConfig` (grid geometry policy), `Position`, policy-free `Board` geometry with
blocked cells, the `N/S/E/W/STAY` move vocabulary and stable `MOVE_ORDER`,
deterministic movement legality, legal-move enumeration, and safe `apply_move`.

**Still pending within PRD-01:** barrier placement semantics · capture ·
survival / terminal semantics · scoring · scent physics · the remaining
deterministic game semantics.

**PRD-01 is NOT implemented, NOT done and NOT complete.**

## 3. Purpose

Specify the **deterministic, side-effect-free game domain**: board and coordinates,
movement legality, barrier legality, scent physics, capture, terminal conditions,
scoring, and per-sub-game/series aggregation — such that two independently written
peers reach identical conclusions from identical inputs, with **no central referee**.

## 4. Problem Statement

Both peers must independently compute the same game truth from the same signed
config and the same public exchanges. Any divergence in legality, scent, capture or
scoring produces an unresolvable dispute (and, via commit-reveal, a TAMPERED verdict).
The domain must therefore be **fully deterministic, pure, and independently testable**,
with every numeric value coming from the signed configuration rather than from code.

## 5. Scope

**In scope:** `domain.board`, `domain.rules`, `domain.scoring`, `domain.barriers`,
`domain.scent`, `domain.truth`, `domain.config_model`, `domain.observation`
(construction of the role-legal view).

**5.3 Role-differentiated content:** only the *action space* (barrier placement is
police-only), the *scoring perspective*, and *own-truth ownership*. **The rulebook is
otherwise semantically identical in both repositories.**

## 6. Out of Scope

Networking / FastMCP (PRD-02, PRD-05) · cryptography, commit-reveal, canonical bytes
(PRD-06) · movement *choice* (PRD-03) · hint text, LLM, scent *interpretation*
(PRD-04) · GUI, replay, reporting (PRD-07). **Movement legality belongs here;
movement selection does not.**

## 7. Actors

| Actor | Interaction |
|---|---|
| `app.turn_service` | Submits a proposed action for validation; applies the returned transition |
| `domain.observation` | Builds the role-legal `Observation` from domain state |
| Strategy plug-in (PRD-03) | **Read-only consumer** of `Observation`; never mutates domain |
| `infra.replay` (PRD-07) | Re-executes recorded transitions from artifacts |
| Opponent peer | Supplies *claims* which the domain validates; never a source of our truth |

## 8. Definitions

| Term | Meaning |
|---|---|
| **Cell** | `[row, col]` integer pair on the grid |
| **Legal action** | A move in `move_set` or a police barrier placement satisfying BAR-004 |
| **Own truth** | This agent's authoritative position/step/budget (`domain.truth`) |
| **Belief** | Estimate of opponent location; never promoted to truth |
| **Sub-game** | One complete game (`config_<game_id>_g<NN>.json`) |
| **Series** | `num_games` sub-games — **6, FIXED** for a counted match |
| **Terminal** | capture · survival · tie · technical_loss |

## 9. Locked Source Requirements

| ID | Modality | Scope | Requirement (verbatim intent) |
|---|---|---|---|
| GAME-001 | MUST | BOTH | Byte-for-byte identical signed config on both sides before play |
| GAME-002 | MUST | BOTH | Negotiate MINIMUM parameters only in the harder direction (raise); never lower |
| GAME-003 | MUST | BOTH | Move only in the four orthogonal directions (or STAY); one cell per turn |
| GAME-004 | **MUST NOT** | BOTH | Never make a diagonal move |
| GAME-005 | MUST | BOTH | A thief with no legal move (all adjacencies blocked by barriers/edges) is **captured** |
| GAME-006 | MUST | BOTH | Score every terminal scenario per the scoring table |
| GAME-007 | MUST | BOTH | Enforce board dimensions from the signed config (default 7×7, MINIMUM ≥7) |
| GAME-008 | MUST | BOTH | Enforce step ceiling and survival threshold from config (defaults 35, MINIMUM) |
| GAME-009 | MUST | BOTH | Movement legality decided by deterministic code, **never** delegated to an LLM |
| BAR-001 | MUST | POLICE | Declare openly and truthfully every barrier placement and exact location |
| BAR-002 | **MUST NOT** | POLICE | Never lie about a barrier placement location |
| BAR-003 | MUST | POLICE | A barrier placed on the thief's current cell counts as a capture |
| BAR-004 | MUST | POLICE | Barrier only on a turn police forgoes movement, on own or orthogonally-adjacent cell; impassable to both, irreversibly, until game end |
| BAR-005 | MUST | POLICE | Do not exceed the barrier quota (default 14, MINIMUM) |
| SCENT-002 | MUST | BOTH | `τij(t+1)=max(0,(1−ρ)·τij(t)+Δτij)`, center 0.9, ρ 0.10, field 5×5, radial fall-off |
| LEAGUE-005 | MUST | LEAGUE | Series length (`num_games`) |

Conflicts in force: **C-01** (board ≥7), **C-05** (`num_games` = 6 FIXED, closed),
**C-07** (`technical_loss` 0/0 binding via Ch 3 + App E #48, **not** an Appendix F row).

## 10. Project / Architecture Decisions

| Decision | Type | Reference |
|---|---|---|
| Coordinates are `[row, col]` integer arrays | PROJECT-CONTRACT | App B convention; JDEC-006 |
| Barrier list canonically **sorted** `[[r,c],…]` | PROJECT-CONTRACT | JDEC-012 |
| Sealed `state` = `{config_sha256, self_pos, barriers(sorted), step, role}` | PROJECT-CONTRACT | JDEC-012, NDEC-002 |
| `domain` imports nothing outward; pure functions | ARCHITECTURE-CONSTRAINT | `DEPENDENCY_RULES.md` D1 |
| `pheromone_min_center_intensity` | **REFERENCE-COMPATIBILITY only — never binding** | `../reference/COMPATIBILITY_PROFILES.md` |
| Role alternation across sub-games | **REFERENCE / ATTACHMENT convention — not a game rule** | AE-01; handled in PRD-02 SeriesLauncher |

## 11. Inputs

Locked config (`domain.config_model`) · current own truth · public barrier set ·
current scent field · validated opponent-public data (revealed move/hint after reveal)
· the proposed action under validation.

## 12. Outputs

Legality verdict (+ machine-readable reason) · next domain state on accept ·
scent field update · terminal detection + outcome · per-sub-game and cumulative scores
· the role-legal `Observation`.

## 13. Functional Requirements

### 13.1 Grid / world

| ID | Requirement | Traces to |
|---|---|---|
| **PRD01-FR-001** | The board is a square grid whose size is read from `board_and_agents.grid_size` in the **locked** config. The engine MUST reject a size `< 7`. Size is never hard-coded. | GAME-007; App F T13 (MINIMUM 7); C-01 |
| **PRD01-FR-002** | Cells are addressed as `[row, col]` integers. The origin corner and first index come from `axis_origin_corner` and `axis_start_index` (NEGOTIABLE; defaults `"top-left"`, `0`) and MUST be identical on both peers. | App F T13; GAME-001 |
| **PRD01-FR-003** | The legal action alphabet is exactly `move_set` = `["N","S","E","W","STAY"]` (**FIXED**). Any other token is rejected. | GAME-003; App F T15 (FIXED) |
| **PRD01-FR-004** | A non-STAY move changes exactly one coordinate by exactly ±1. Any diagonal (both coordinates change) MUST be rejected. | GAME-003, **GAME-004** |
| **PRD01-FR-005** | A move whose destination lies outside `[start_index, start_index+grid_size-1]` on either axis MUST be rejected as out-of-bounds. | GAME-007 |
| **PRD01-FR-006** | Start positions come from `thief_start` / `cop_start` (NEGOTIABLE; defaults `[3,3]` / `[0,0]`). `num_agents` is **FIXED 2**. | App F T13 |
| **PRD01-FR-007** | Legality is computed by deterministic code only. No LLM, network call, clock read, or filesystem access may participate in a legality decision. | **GAME-009**; LLM-001; `DEPENDENCY_RULES.md` |

### 13.2 Turn semantics

| ID | Requirement | Traces to |
|---|---|---|
| **PRD01-FR-010** | Exactly **one** proposed action is evaluated per turn per agent. | GAME-003 |
| **PRD01-FR-011** | Validation strictly precedes effect: an action mutates domain state **only** after the validator accepts it. | `STATE_MACHINE.md` R4 |
| **PRD01-FR-012** | An illegal action MUST leave all authoritative state byte-identical (no partial mutation). | `ERROR_MODEL.md` `E-LOCAL-VALIDATION` / `E-PROTO-ILLEGAL-MOVE` |
| **PRD01-FR-013** | The turn/step counter is owned by `domain.truth` and advances only on `VALIDATING → TURN_COMPLETE`. | `STATE_OWNERSHIP.md` |
| **PRD01-FR-014** | At sub-game start the domain resets position, step, barrier set, scent field and belief. Series-level score accumulators are **not** reset. | `STATE_OWNERSHIP.md` (reset boundary) |
| **PRD01-FR-015** | Once a terminal condition is detected, no further action is accepted for that sub-game. | GAME-005/006/008 |

### 13.3 Position and truth

| ID | Requirement | Traces to |
|---|---|---|
| **PRD01-FR-020** | `domain.truth` holds exactly one authoritative copy of **own** position/step/budget. | `STATE_OWNERSHIP.md` |
| **PRD01-FR-021** | The domain MUST NOT contain any field, parameter or return value carrying the **opponent's true position**. | GUI-001/002; `ROLE_RESPONSIBILITIES.md` (FORBIDDEN-TO-KNOW) |
| **PRD01-FR-022** | Opponent location exists only as `domain.belief` (typed as belief, with uncertainty) and MUST NOT be copied into `domain.truth`. | `STATE_OWNERSHIP.md` anti-duplication rule 4 |
| **PRD01-FR-023** | `domain.observation` may compose an `Observation` only from own truth + public data + belief + *validated* opponent-public data. | `DATA_FLOW.md` §3 |

### 13.4 Barriers

| ID | Requirement | Traces to |
|---|---|---|
| **PRD01-FR-030** | Barriers form a set of cells, canonically **sorted** `[[r,c],…]` for hashing determinism. | JDEC-012; NDEC-002 |
| **PRD01-FR-031** | Barrier placement is a **police-only** action, legal only on a turn the police **forgoes movement**. | **BAR-004** |
| **PRD01-FR-032** | The target cell MUST be the police's own cell or one **orthogonally adjacent** cell. | **BAR-004** |
| **PRD01-FR-033** | A placed barrier is **impassable to both agents** and **irreversible until game end**. Removal/relocation MUST be rejected. | **BAR-004** |
| **PRD01-FR-034** | Placement is rejected when the count would exceed `max_barriers` (default 14, **MINIMUM**) from the locked config. | **BAR-005**; App F T15 |
| **PRD01-FR-035** | Every placement is recorded with its exact cell for open, truthful declaration; the domain provides that record to the log. | **BAR-001**, **BAR-002** |
| **PRD01-FR-036** | A barrier placed on the thief's **current** cell is a **capture**. | **BAR-003** |
| **PRD01-FR-037** | The barrier set is PUBLIC/SHARED and may appear in `Observation`, GUI projection, and logs. | `ROLE_RESPONSIBILITIES.md` §3 |

### 13.5 Scent physics (domain only)

| ID | Requirement | Traces to |
|---|---|---|
| **PRD01-FR-040** | Scent evolves as `τij(t+1) = max(0, (1−ρ)·τij(t) + Δτij)`. | **SCENT-002** |
| **PRD01-FR-041** | `ρ = pheromone_decay` = **0.10 (FIXED)**; centre deposit `= pheromone_center_intensity` = **0.9 (FIXED)**; field size `= pheromone_grid_size` = **5 (FIXED)**, i.e. a 5×5 neighbourhood with radial fall-off. All three are read from the locked config, never hard-coded. | **SCENT-002**; App F T16 (all FIXED) |
| **PRD01-FR-042** | The `max(0, …)` clamp MUST be applied so intensities never go negative. | **SCENT-002** |
| **PRD01-FR-043** | Scent update is deterministic and order-independent for a given step: same field + same deposits ⇒ same next field, bit-for-bit. | Determinism (§19) |
| **PRD01-FR-044** | `pheromone_min_center_intensity` is **REFERENCE-ONLY**. A compatibility parser MAY accept it; it MUST NOT alter the three binding parameters or any scent result. | `COMPATIBILITY_PROFILES.md`; App F T16 has 3 rows |
| **PRD01-FR-045** | The domain exposes only the **role-legal** scent view; it never derives opponent position from scent (that inference is belief, §13.3). | GUI-001/002 |

*Scent **interpretation** and any language use of it belong to PRD-04.*

### 13.6 Capture

| ID | Requirement | Traces to |
|---|---|---|
| **PRD01-FR-050** | Capture occurs when the police and thief occupy the same cell, **as evaluated against each side's sealed step-`k` cell** under `JDEC-016` §4: `state.self_pos` is the mover's cell *before* that step's action, both actors of a step are checked from the shared pre-step state, and the step's effects are applied afterwards. *Clarified at Stage 6C-B: the earlier wording, "after a validated transition", was written when one actor moved per step, where a non-mover's pre- and post-action cells coincide. Under lockstep both actors move in step `k`, so the two readings diverge and `JDEC-016` §4 - which is interoperability-binding and which both the live `capture_rules` path and the final `semantic_capture` audit already implement - governs. **This is alignment with an already-locked contract, not a new rule**; no register entry changed.* | GAME-006 (capture scenario); `JDEC-016` §4 |
| **PRD01-FR-051** | Capture also occurs when a barrier is placed on the thief's current cell. | **BAR-003** |
| **PRD01-FR-052** | Capture also occurs when the thief has **no legal move** (all orthogonal neighbours blocked by barriers or edges) — the thief is considered captured. | **GAME-005** |
| **PRD01-FR-053** | Capture is evaluated **after** each validated transition, before the next turn is offered. | `STATE_MACHINE.md` (VALIDATING→TURN_COMPLETE) |
| **PRD01-FR-054** | Capture is a terminal condition for the sub-game and produces the capture score split. | GAME-006 |
| **PRD01-FR-055** | Capture is established by **deterministic evaluation on both peers**, never by one side's assertion; a claim inconsistent with the validated state is rejected. **No central referee exists.** | ARCH-001/002; CRYPTO-004/005 |
| **PRD01-FR-056** | Evidence for a capture (final positions, barrier set, step) is emitted to the log for replay. | REPLAY-001/002 |

### 13.7 Survival and step ceiling

| ID | Requirement | Traces to |
|---|---|---|
| **PRD01-FR-060** | `max_moves` (step ceiling) and `survival_threshold` are read from the locked config; both default **35** with status **MINIMUM**. Values below the floor MUST be rejected at config validation. | **GAME-008**; App F T15; GAME-002 |
| **PRD01-FR-061** | If the thief is not captured by the survival threshold, the sub-game terminates as **survival**. | GAME-006; GAME-008 |
| **PRD01-FR-062** | The engine MUST use the configured values as-is and MUST NOT infer a different threshold from any example, attachment or reference default. | GAME-002; `COMPATIBILITY_PROFILES.md` |

### 13.8 Scoring (explicit ordering)

| ID | Requirement | Traces to |
|---|---|---|
| **PRD01-FR-070** | Scores are returned as an explicitly **role-keyed** structure (`{cop: n, thief: m}`), never as a positional pair, so police/thief values cannot be reversed. | GAME-006; C-06 (label-order hazard) |
| **PRD01-FR-071** | **Capture** ⇒ `cop = capture_cop = 20 (FIXED)`, `thief = capture_thief = 5 (FIXED)`. | GAME-006; App F T17 |
| **PRD01-FR-072** | **Survival** ⇒ `cop = survival_cop = 5 (FIXED)`, `thief = survival_thief = 10 (FIXED)`. | GAME-006; App F T17 |
| **PRD01-FR-073** | **Tie** ⇒ `tie_score = 2 (FIXED)` to each role. | GAME-006; App F T17 |
| **PRD01-FR-074** | **Technical loss** ⇒ **0 / 0**. Its numeric provenance is **Ch 3 Table 2 + App E #48**, **not** an Appendix F row; the engine MUST NOT cite Appendix F for it. | **C-07**; GAME-006 |
| **PRD01-FR-075** | All scoring values are read from the locked config; a value differing from an Appendix-F **FIXED** entry MUST be rejected at config validation. | GAME-002 |
| **PRD01-FR-076** | `diversity_reward` = **10 (FIXED)** is a **league-level** award computed at series/league scope, not a per-sub-game domain score. | App F T18; LEAGUE-001 |

### 13.9 Series (six sub-games)

| ID | Requirement | Traces to |
|---|---|---|
| **PRD01-FR-080** | A counted series is `num_games` sub-games; for a counted league match this is **6, FIXED**. The illustrative `1` MUST NOT be used. | **C-05** (closed); App F T18 |
| **PRD01-FR-081** | The domain computes per-sub-game scores; the series aggregate is the per-role sum across played sub-games. | GAME-006 |
| **PRD01-FR-082** | Aggregation is deterministic and order-independent (integer addition). | Determinism |
| **PRD01-FR-083** | The domain exposes sub-game outcome + scores; **series orchestration and any role alternation are PRD-02 concerns and are NOT game rules.** | AE-01 (attachment convention); PRD-02 SeriesLauncher |

### 13.10 Configuration handling

| ID | Requirement | Traces to |
|---|---|---|
| **PRD01-FR-090** | `domain.config_model` exposes each value with its Appendix-F **status**: FIXED / MINIMUM / NEGOTIABLE. | App F; `AUTHORITY_RULES.md` |
| **PRD01-FR-091** | **FIXED** ⇒ reject any deviation. **MINIMUM** ⇒ accept only ≥ floor. **NEGOTIABLE** ⇒ accept any mutually agreed value. | GAME-002; App F §1 |
| **PRD01-FR-092** | The domain never mutates config after `CONFIG_LOCKED`; a write attempt is a programming defect. | `CONFIG_ARCHITECTURE.md` R8; `ERROR_MODEL.md` `E-LOCAL-DEFECT` |

## 14. Non-Functional Requirements

| ID | Requirement |
|---|---|
| **PRD01-NFR-001** | The domain is **pure**: no I/O, no network, no clock, no filesystem, no global mutable state. |
| **PRD01-NFR-002** | Every domain module is independently unit-testable with no fixtures beyond value objects. |
| **PRD01-NFR-003** | Every Python file in the domain stays **≤ 150 lines**; splits follow the seams named in `MODULE_BOUNDARIES.md`. |
| **PRD01-NFR-004** | A full legality evaluation completes well inside the step budget; target **< 5 ms** on the reference dev machine (measurable, not "fast"). |
| **PRD01-NFR-005** | No domain API accepts or returns opponent-truth data (enforced by contract test). |

## 15. State / Lifecycle Responsibilities

Owned here: own position, step, barrier set, scent field, belief, per-sub-game outcome
and score (computed). Reset at sub-game start: position, step, barriers, scent, belief.
Persist across the series: cumulative scores. **Not owned here:** state-machine phase
(PRD-02), nonce/commitment (PRD-06), artifacts (PRD-07).

## 16. Validation Rules

| Check | Rejection reason |
|---|---|
| token ∉ `move_set` | illegal action |
| both coordinates change | diagonal (GAME-004) |
| |Δ| > 1 on an axis | multi-cell move |
| destination out of bounds | out-of-bounds |
| destination is a barrier | blocked |
| barrier placement by thief | role-illegal |
| barrier placement while moving | BAR-004 violation |
| barrier target not own/adjacent cell | BAR-004 violation |
| barrier count would exceed quota | BAR-005 violation |
| barrier removal/relocation | irreversibility violation |
| action after terminal | sub-game closed |
| config value violating FIXED/MINIMUM | GAME-002 violation |

## 17. Error / Failure Behaviour

Domain functions **return verdicts, they do not raise for legality**. Mapping:
own illegal proposal → `E-LOCAL-VALIDATION` (re-decide, no state change);
opponent illegal move → `E-PROTO-ILLEGAL-MOVE`; invalid/undeclared barrier →
`E-PROTO-BARRIER`; config outside Appendix-F status → `E-CONFIG-MISMATCH` (refuse
counted play); internal invariant violation → `E-LOCAL-DEFECT` (fail fast).
**No sanction is invented beyond the locked set** (`ERROR_MODEL.md`).

## 18. Security / Privacy Constraints

No opponent truth in any domain type (PRD01-FR-021) · no secrets, keys or nonces in the
domain · opponent claims are untrusted input validated before effect · barrier
declarations are truthful by construction (BAR-001/002) · a false capture claim is
detectable by deterministic re-evaluation (CRYPTO-005).

## 19. Determinism / Reproducibility

Given identical **locked config**, identical prior domain state, and an identical legal
action, the transition result is **bit-for-bit reproducible**. There is **no randomness
in the domain** — nonce generation (PRD-06) and strategy seeding (PRD-03) live outside
it. No wall-clock, no iteration over unordered sets without canonical sorting, no
dependence on Python hash randomization (barriers sorted; dict iteration never
semantically significant).

## 20. Performance / Deadline Constraints

The domain performs no waiting. It must be fast enough that the strategy decision fits
inside the negotiated `response_timeout_sec` (App F default **30 s**, **NEGOTIABLE**) —
timeouts themselves are enforced in PRD-02, never hard-coded here.

## 21. Cross-Platform Constraints

Identical results on Linux and Windows. Integer arithmetic for positions/scores; float
use confined to scent with values sourced verbatim from config (`0.9`, `0.10`); no
locale-dependent formatting; canonical ordering for any collection that reaches a hash.

## 22. Observability / Evidence

Per turn the domain supplies: validated action, resulting own position, barrier delta,
scent summary, legality verdict + reason, terminal detection, and score on termination.
**Never emitted:** opponent truth, nonce, secrets.

## 23. Acceptance Criteria

| ID | Criterion |
|---|---|
| **PRD01-AC-001** | All five actions `N/S/E/W/STAY` accepted in an open board; each moves exactly one cell (STAY moves none). |
| **PRD01-AC-002** | Every diagonal proposal is rejected; no state change. |
| **PRD01-AC-003** | Out-of-bounds moves rejected on all four edges for a 7×7 board. |
| **PRD01-AC-004** | A move into a barrier cell is rejected; a barrier blocks both agents. |
| **PRD01-AC-005** | Replaying a recorded action sequence from the same start state reproduces the identical final state. |
| **PRD01-AC-006** | Capture detected for all three routes: same-cell, barrier-on-thief-cell, thief-has-no-legal-move. |
| **PRD01-AC-007** | Survival terminal fires exactly at the configured `survival_threshold`, not at a hard-coded 35 when config says otherwise. |
| **PRD01-AC-008** | Tie yields `{cop: 2, thief: 2}`. |
| **PRD01-AC-009** | Scores are role-keyed: capture ⇒ `{cop: 20, thief: 5}`; survival ⇒ `{cop: 5, thief: 10}`; a reversed mapping fails the test. |
| **PRD01-AC-010** | `technical_loss` ⇒ `{cop: 0, thief: 0}` and its documented provenance is Ch 3 + App E #48, **not** Appendix F. |
| **PRD01-AC-011** | A six-sub-game series aggregates per-role totals correctly; `num_games` = 6 is taken from config. |
| **PRD01-AC-012** | Sub-game reset clears position/step/barriers/scent/belief but preserves cumulative scores. |
| **PRD01-AC-013** | No domain type exposes opponent true position (static/contract test over the public API). |
| **PRD01-AC-014** | Config validation: a FIXED value altered ⇒ rejected; a MINIMUM lowered ⇒ rejected; a MINIMUM raised ⇒ accepted; a NEGOTIABLE change ⇒ accepted. |
| **PRD01-AC-015** | Identical scent evolution and identical final scores on Linux and Windows for the same seeded scenario. |
| **PRD01-AC-016** | `pheromone_min_center_intensity` present in a compatibility config does not change any scent value. |
| **PRD01-AC-017** | Barrier quota enforced at the configured `max_barriers`; the (quota+1)-th placement is rejected. |
| **PRD01-AC-018** | Barrier placement while moving, by the thief, or on a non-adjacent cell is rejected. |

## 24. Planned Tests

| ID | Test | Layer |
|---|---|---|
| **PRD01-T-001** | Movement alphabet + single-cell delta | UNIT |
| **PRD01-T-002** | Diagonal rejection (property: any 2-axis change rejected) | PROPERTY |
| **PRD01-T-003** | Bounds rejection on all edges/corners | UNIT |
| **PRD01-T-004** | Barrier blocking both agents | UNIT |
| **PRD01-T-005** | Barrier legality matrix (role, forgo-move, adjacency, quota, irreversibility) | UNIT |
| **PRD01-T-006** | Capture — three routes | UNIT |
| **PRD01-T-007** | Trapped thief ⇒ captured (GAME-005) | UNIT |
| **PRD01-T-008** | Survival threshold from config | UNIT |
| **PRD01-T-009** | Scoring table incl. role-keying and technical_loss 0/0 | UNIT |
| **PRD01-T-010** | Scent formula incl. `max(0,…)` clamp and 5×5 fall-off | UNIT |
| **PRD01-T-011** | Scent determinism / order-independence | PROPERTY |
| **PRD01-T-012** | Six-sub-game aggregation | UNIT |
| **PRD01-T-013** | Sub-game reset boundary | UNIT |
| **PRD01-T-014** | No-opponent-truth API contract scan | CONTRACT |
| **PRD01-T-015** | Appendix-F status enforcement (FIXED/MINIMUM/NEGOTIABLE) | UNIT |
| **PRD01-T-016** | Cross-OS determinism (Linux + Windows CI) | PROPERTY / CROSS-PROCESS |
| **PRD01-T-017** | Reference-only key ignored | CONTRACT |
| **PRD01-T-018** | Full-sub-game replay reproducibility | REPLAY |

## 25. Requirement Traceability

GAME-001…009 · BAR-001…005 · SCENT-002 · GAME-002 (App F status) · LEAGUE-005
(`num_games`) — **directly owned**. GAME-009/LLM-001 constrain PRD-03/04. SCENT-001/003
(model lock/exchange) are **PRD-06/PRD-04**. GUI-001/002 constrain §13.3 but are owned by
PRD-07. Conflicts honoured: C-01, C-05, C-06, C-07.

## 26. Dependencies on Other PRDs

**Provides to:** PRD-02 (transition + terminal signals), PRD-03 (`Observation`,
validator), PRD-04 (scent field, hint word limit source), PRD-06 (sealed `state`
representation), PRD-07 (scores, evidence).
**Consumes from:** PRD-06 (locked config + `config_sha256` identity), PRD-02 (turn
sequencing).

## 27. Open Design Decisions

Internal board representation (dense array vs sparse set) · exact split of
`rules`/`scoring` to respect ≤150 lines · granularity of legality-rejection reason codes
· belief representation detail (shared with PRD-03) · whether scent stores floats or
fixed-point (must not change results).

## 28. Explicit Non-Goals

Not a referee · not a simulator of the opponent's decisions · no move *selection* · no
transport, crypto, GUI, reporting · no LLM · no persistence.

## 29. Implementation Readiness Checklist

- [x] Every numeric value sourced from the signed config with Appendix-F status
- [x] All legality rules enumerated with rejection reasons
- [x] Capture routes complete (3) and terminal ordering defined
- [x] Scoring role-keyed with explicit anti-reversal requirement
- [x] Determinism and cross-OS constraints stated and testable
- [x] Privacy boundary (no opponent truth) stated and test-enforced
- [x] Supervising review — **PASS** (Stage 2-CLOSE)
- [ ] Implementation — **in progress**: Stage 3A foundation done; barriers, capture,
      terminal/survival, scoring and scent still pending

## 30. Phase-3 Implementation Clarifications (post-lock)

**These are Phase-3 implementation findings recorded after this PRD was locked.
They did not exist during Phase 2, they change no requirement, acceptance
criterion, planned test, numeric value or provenance above, and the counts in
§13/§14/§23/§24 are unchanged.**

| # | Finding | Class | Effect |
|---|---|---|---|
| **JDEC-015** *(Stage 3B-FIX1)* | App F T15 #3/#4 fix only two independent MINIMUM-35 floors, and Ch 3 Table 2 defines **no** end event for a survival threshold the step ceiling can never reach. A counted configuration therefore MUST satisfy `survival_threshold <= max_moves`; a violating configuration is **refused before `CONFIG_LOCKED`**. | **PROJECT-CONTRACT** — implementation-discovered source-gap resolution | Validation only. No new outcome is invented; PRD01-FR-060/061 and both MINIMUM-35 floors are unchanged; **not** an Appendix-F row. |
| Radial kernel contract *(Stage 3B-FIX1)* | Ch 4 p.43 and Figure 4 describe the emission window only as a **radial fall-off**; App F T16 locks solely centre 0.9, ρ 0.10 and 5×5. The 25 weights are therefore **agreed, not locked**, and are validated as: centre exactly 0.9 · finite, non-negative · equal **integer squared radius** ⇒ equal intensity · a farther ring never stronger than a nearer one (non-increasing). | SOURCE description + **PROJECT** formalisation | PRD01-FR-041/044 unchanged. The Figure-4 numbers stay **ILLUSTRATIVE** and appear only in tests, never in production. |
| Scent numeric representation | `Decimal` built from strings in a fixed context, resolving the §27 open "floats vs fixed-point" decision. | **PROJECT** implementation | Results unchanged in value; `0.9 → 0.81` becomes exact and platform-independent. |
| **C-10** *(Stage 3B-FIX2)* | PDF p.43 (book p.27) defines `τij(t)` as *"ערך רציף בתחום [0, 0.9]"* — a continuous value **in [0, 0.9]** — while the written recurrence `τ(t+1)=max(0,(1−ρ)·τ(t)+Δτ)` with centre `Δτ = 0.9` has no upper clamp and can reach 1.71. **Resolved: the explicit state domain wins**, so the implemented evolution saturates: `τ_next = min(0.9, max(0, (1−ρ)·τ + Δτ))`, and every field cell is validated into `[0, 0.9]` at construction. | **SOURCE-CONFLICT** resolved by documented project interpretation (`CONFLICT_REGISTER.md` C-10) | PRD01-FR-040/041/042 unchanged; App F 0.9 / 0.10 / 5×5 unchanged; below the bound the recurrence is exactly additive. Figure 5 is corroborating **illustration** only, Figure 4 stays **ILLUSTRATIVE**, and no config field is introduced. |
