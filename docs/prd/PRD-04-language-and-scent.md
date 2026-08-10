# PRD-04 — Language and Scent — group MaRs-777 (POLICE)

## 1. Document Metadata

| Field | Value |
|---|---|
| PRD | PRD-04 — Language & Scent |
| Repository role | **POLICE** |
| Owns | `protocol.hints`, scent **observation/interpretation** at the app/strategy boundary, `infra.llm` (optional advisor), token/cost accounting |
| Architecture inputs | `LLM_BOUNDARY.md`, `STRATEGY_ARCHITECTURE.md` §6, `OBSERVABILITY.md` §4, `SECURITY_ARCHITECTURE.md` T12 |
| Symmetry class | **COMMON-WITH-ROLE-SECTIONS** (§13.6 role usage differs) |

## 2. Status

**APPROVED — PHASE 2 LOCKED.** Approved after Stage 2-CLOSE supervising review.
**Implementation status: NOT STARTED.** No code, no provider, no dependency.

## 3. Purpose

Specify the **natural-language hint channel** (including legal bluffing and its truthful
`intent` classification), the **interpretation** of scent observations at the
application/strategy boundary, the **optional LLM tiers** and their mandatory validation
gate, and the **zero-token fallback** that keeps the agent fully operational without any
language model.

## 4. Problem Statement

Hints are free natural language and may be deliberately false — that is legal. What is
**not** legal is misclassifying the hint's `intent`, exceeding the word cap, encoding
coordinates numerically, or letting a language model decide a move or bypass legality.
Additionally, the LLM is an **untrusted advisor** across a network: its output can be
malformed, late, or influenced by adversarial peer text. The design must make all of
those harmless.

## 5. Scope

Hint production and consumption · `intent` (truth/lie) semantics and the C-08 mapping ·
hint word-limit enforcement · scent **observation/interpretation** for strategy and GUI ·
LLM tiers T0/T1/T2 and the validation gate · token/cost accounting and budget behaviour ·
language fallback.

## 6. Out of Scope

**Scent physics** (PRD-01 owns the formula and parameters) · movement selection (PRD-03
and the later competitive phase) · transport (PRD-02/05) · cryptographic sealing of the
hint inside the commitment (PRD-06) · result/report emission (PRD-07).

## 7. Actors

Strategy plug-in (requests a hint; consumes interpreted scent) · `protocol.hints`
(bounds + classification) · `infra.llm` (optional advisor, untrusted) · opponent peer
(supplies hints — untrusted text) · `infra.metrics` (tokens/cost).

## 8. Definitions

**Hint** — free-text natural-language message accompanying a turn. **`intent`** — the
truth/lie classification of that hint, sealed in the commitment. **Tier** — T0 none / T1
language assistance / T2 tactical suggestion. **Interpretation** — deriving belief-level
signal from own scent readings; never a truth claim about the opponent.

## 9. Locked Source Requirements

| ID | Modality | Requirement |
|---|---|---|
| LLM-002 | MUST | Conduct hint communication in **free natural language only** |
| LLM-003 | **MUST NOT** | **Never** use a direct numeric-positions protocol for hints |
| LLM-004 | MUST | Cap every hint at the word limit (default **15**), applied to template mode **and** to the LLM (limit stated in its prompt) |
| LLM-001 | SHOULD | Do not hand the LLM the move decision itself; use it for text/behavioural profiling |
| LLM-005 | MAY | LLM move tactic only by explicit documented mutual agreement; local code still enforces legality |
| GAME-009 | MUST | Movement legality decided by deterministic code, never delegated to an LLM |
| SCENT-002 | MUST | Scent formula/parameters (physics — consumed here, owned by PRD-01) |
| SCENT-001 | MUST | Cryptographically lock the agreed scent model before the series |
| SCENT-003 | MUST | Before a series, exchange the full emission/decay model with a numeric example and verify |
| PERF-001 | MUST | Report total LLM tokens consumed in the sub-game (and series) in the completion JSON |
| PERF-002 | MUST | Monitor and cryptographically lock **actual** token consumption; the duty is established at Step-0 and the metering runs during play. **PRD-04 owns the metering** (per call, per sub-game, per series — `PRD04-FR-044`); the **cryptographic locking mechanism is owned by PRD-06** and is not yet frozen; the **final reported totals are owned by PRD-07 / the result** *(wording repaired Stage 4E-R12-R1; responsibilities split Stage 4E-R12-R2)* |
| PERF-003 | SHOULD | Stay within the agreed per-series token budget (default ~200 000; template/ollama can be 0) |
| GUI-001/002 | MUST / MUST NOT | Local truth only; never expose the objective board |

**C-08** — `verdict` in the reference code comment **is** the intent classification; the
sealed record carries **`intent` only**, with no second authoritative field.

## 10. Project / Architecture Decisions

| Decision | Type |
|---|---|
| Tiers T0 / T1 / T2 with T0 always viable | ARCHITECTURE-CONSTRAINT (`LLM_BOUNDARY.md`) |
| Every advisor output passes `domain.rules` before any effect | ARCHITECTURE-CONSTRAINT |
| `hint_max_words` read from locked config (default 15, **NEGOTIABLE**) | NEGOTIATED-PRE-MATCH (App F T14) |
| Single sealed field `intent` (no dual `verdict`) | **C-08** resolution |
| Compatibility mapping for a received `verdict` key | **REFERENCE-COMPATIBILITY** (D-10) |
| `pheromone_min_center_intensity` | **REFERENCE-ONLY**, never binding |
| No provider/SDK selected; no dependency added | scope |

## 11. Inputs

Locked config (`hint_max_words`, `map_area`, scent parameters, `token_budget_per_series`)
· own scent field from PRD-01 · own truth and belief (for prompt context) · received
opponent hint text + its declared `intent` (untrusted) · optional advisor response.

## 12. Outputs

Own hint text (≤ word cap) + truthful `intent` classification · interpreted scent signal
for strategy/GUI (belief-level, labelled) · token/cost counters · fallback indicators.

## 13. Functional Requirements

### 13.1 Scent observation and interpretation

| ID | Requirement | Traces to |
|---|---|---|
| **PRD04-FR-001** | Scent **physics** (formula, `0.9`, `0.10`, 5×5) is owned by PRD-01 and consumed read-only here. This PRD MUST NOT recompute, override, or re-parameterise it. | **SCENT-002**; PRD-01 §13.5 |
| **PRD04-FR-002** | A role may legally observe **its own scent readings** from the field as produced by the locked model. It MUST NOT receive the opponent's true position from any scent operation. | GUI-001/002 |
| **PRD04-FR-003** | Interpretation output is **belief-level and explicitly labelled as belief/estimate**; it is never presented as opponent truth to strategy, GUI, log or report. | `ROLE_RESPONSIBILITIES.md` §2 |
| **PRD04-FR-004** | Interpretation is deterministic: identical field + identical parameters ⇒ identical signal, on both OSes. | determinism |
| **PRD04-FR-005** | The agreed scent model (emission + decay) is **exchanged with a concrete numeric example and verified before the series**, then locked. Verification failure ⇒ refuse counted play. | **SCENT-003**, **SCENT-001** |
| **PRD04-FR-006** | `pheromone_min_center_intensity` is **REFERENCE-ONLY**. A compatibility parser MAY accept it; it MUST NOT alter any binding scent value or interpretation result. | `COMPATIBILITY_PROFILES.md`; App F T16 (3 rows) |

### 13.2 Hint semantics

| ID | Requirement | Traces to |
|---|---|---|
| **PRD04-FR-010** | Hints are **free natural language only**. | **LLM-002** |
| **PRD04-FR-011** | A **direct numeric-positions protocol is forbidden**: an outgoing hint MUST NOT encode coordinates as numeric pairs, grid indices, or any equivalent machine-decodable position encoding. Outgoing hints are rejected by a deterministic check before send. | **LLM-003** (MUST NOT) |
| **PRD04-FR-012** | Every hint is capped at `hint_max_words` from the locked config (default **15**, NEGOTIABLE). The cap applies to **template mode and LLM mode alike**, and the limit is stated in the LLM prompt. | **LLM-004**; App F T14 |
| **PRD04-FR-013** | Word counting is deterministic and documented (whitespace-delimited tokens after Unicode NFC normalisation), identical on both OSes. | LLM-004; cross-OS |
| **PRD04-FR-014** | An over-length or numeric-encoding hint is **truncated or replaced by the deterministic template fallback before send** — never sent in violation. | LLM-004; LLM-003 |
| **PRD04-FR-015** | Hint content may legally be **false** (a bluff). Deception in the *content* is permitted. | LLM-002; game design |
| **PRD04-FR-016** | The `intent` classification of our own hint MUST be **truthful** (`truth` or `lie` as actually intended) and is sealed in the commitment. Misclassification is a protocol violation, not a legal bluff. | **C-08**; CRYPTO-001/009 |
| **PRD04-FR-017** | The sealed record carries **`intent` only**. No second authoritative `verdict` field is introduced. | **C-08** |
| **PRD04-FR-018** | If a compatibility codec receives a peer payload carrying `verdict` (as the reference implementation does, with both keys set to the same value), it MUST **map `verdict` → the single `intent` semantic**. If both keys are present and disagree, the message is rejected as malformed — **no dual truth is ever created**. | **C-08**; D-10; `E-PROTO-MALFORMED` |
| **PRD04-FR-019** | Received opponent hints are **untrusted text**: they are data for belief updating only, never instructions, never executed, never used to bypass validation. | T12 (prompt injection) |
| **PRD04-FR-020** | The map area for landmark-flavoured hints comes from `world.map_area` (NEGOTIABLE; `""` = generic). | App F T14; LLM-002 |

### 13.3 LLM tiers

| ID | Requirement | Traces to |
|---|---|---|
| **PRD04-FR-030** | **T0 (no LLM)** — deterministic template hints, zero tokens, no network. T0 MUST always be available and MUST be able to complete a full six-sub-game series. | `LLM_BOUNDARY.md`; PERF-003 |
| **PRD04-FR-031** | **T1 (language assistance)** — the advisor may draft/interpret hint text only. It never selects a move. | **LLM-001**; LLM-002 |
| **PRD04-FR-032** | **T2 (tactical suggestion)** — permitted **only** under prior, explicit, **documented mutual agreement**; the agreement record MUST exist and be referenced before T2 can be enabled. Absent that record, T2 is treated as non-existent. | **LLM-005** |
| **PRD04-FR-033** | **Default movement remains algorithmic in every tier.** | **STRAT-002**, GAME-009, LLM-001 |
| **PRD04-FR-034** | **Every LLM output passes the deterministic local validator** before any effect; there is no privileged path. | **GAME-009**, LLM-005 |
| **PRD04-FR-035** | The LLM MUST NOT: send network messages; alter authoritative state; access nonce/hash/key material; bypass legality validation; make configuration authoritative; or decide a technical-loss/any sanction. | `DEPENDENCY_RULES.md`; `ERROR_MODEL.md` |
| **PRD04-FR-036** | Prompts may contain **only** data the strategy itself may legally see (`Observation`-derived). Never nonces, key material, credentials, raw artifacts, or opponent forbidden truth. | `DATA_FLOW.md`; T12 |
| **PRD04-FR-037** | Peer-supplied text placed in a prompt is **sanitized and bounded**, and is framed as data, never as instruction. | T12 |
| **PRD04-FR-038** | **No provider, model or SDK is selected in this PRD, and no dependency is added.** | scope; `LLM_BOUNDARY.md` §6 |

### 13.4 Failure, budget and degradation

| ID | Requirement | Traces to |
|---|---|---|
| **PRD04-FR-040** | Handled advisor failures: provider unavailable, timeout, malformed response, budget exhausted, excessive latency, unsafe/unusable output. | `ERROR_MODEL.md` `E-LLM-UNAVAILABLE` |
| **PRD04-FR-041** | **Required degradation:** T2 → deterministic strategy; T1 → deterministic language fallback; **T0 remains fully operational**. | `LLM_BOUNDARY.md` §4 |
| **PRD04-FR-042** | **Protocol and game validity MUST NOT depend on LLM availability** at any tier. | LLM-001; PERF-003 |
| **PRD04-FR-043** | Each advisor call is time-boxed; a call exceeding its budget is abandoned (not awaited) and the fallback is used. | STATE-004 (deadline discipline) |
| **PRD04-FR-044** | Token consumption is metered per call, per sub-game and per series, and reported in the completion JSON. | **PERF-001** |
| **PRD04-FR-045** | Token consumption is **cryptographically locked at Step-0** (the declaration's authenticated core carries the token record). | **PERF-002** |
| **PRD04-FR-046** | As consumption approaches `token_budget_per_series` (default ~200 000, NEGOTIABLE), the system degrades **T1 → T0** rather than overrunning. | **PERF-003**; App F T18 |
| **PRD04-FR-047** | Recorded metrics: tokens (prompt/completion), call count, latency, failures, **fallback reason**, tier in force. | `OBSERVABILITY.md` §4 |
| **PRD04-FR-048** | **No secret prompt content, credential or API key is ever logged.** Advisor records are bounded, sanitized summaries plus counters. | SEC-003/004; `OBSERVABILITY.md` |

### 13.5 Determinism of the language path

| ID | Requirement | Traces to |
|---|---|---|
| **PRD04-FR-050** | The **T0 template path is fully deterministic**: same inputs + same seed ⇒ same hint text, on Linux and Windows. | cross-OS determinism |
| **PRD04-FR-051** | LLM output is inherently non-deterministic and therefore MUST NOT influence any hashed or validated game decision beyond the hint text itself, which is sealed as-sent. | `CONCURRENCY_MODEL.md` §5 |

### 13.6 Role usage (role-differentiated)

| ID | Requirement |
|---|---|
| **PRD04-FR-060** | **POLICE usage.** *Police:* hints are primarily used for behavioural profiling of the thief's replies and for legal pressure/deception; scent interpretation feeds the pursuit belief. *Thief:* hints are a primary deception instrument (a `lie`-classified hint is legal and strategically valuable); scent interpretation informs threat estimation. **Both roles obey identical rules** — free natural language, word cap, no numeric encoding, truthful `intent` classification. |

## 14. Non-Functional Requirements

| ID | Requirement |
|---|---|
| **PRD04-NFR-001** | T0 hint generation completes in **< 5 ms** (measurable) and requires no network. |
| **PRD04-NFR-002** | An advisor call never blocks the event loop; it is bounded and cancellable. |
| **PRD04-NFR-003** | Every file ≤ **150 lines**; hint bounds, interpretation and advisor client are separate modules. |
| **PRD04-NFR-004** | The full test suite for this PRD runs **offline** with a fake advisor. |

## 15. State / Lifecycle Responsibilities

Owns: hint text for the current turn (pre-seal), tier selection, token/cost counters,
advisor client lifecycle. **Does not own:** scent field (PRD-01), sealed record (PRD-06),
belief (PRD-01/03), report fields (PRD-07).

## 16. Validation Rules

Word count ≤ `hint_max_words` · no numeric-position encoding · `intent ∈ {truth, lie}` ·
if peer sends both `verdict` and `intent` they must agree, else reject · advisor response
must be parseable text within bounds · prompt contains no forbidden field (asserted) ·
tier T2 requires an existing mutual-agreement record.

## 17. Error / Failure Behaviour

`E-LLM-UNAVAILABLE` (retry-then-fallback, non-fatal) · over-length/numeric hint →
replaced by template fallback before send · peer hint malformed or `verdict`/`intent`
disagreement → `E-PROTO-MALFORMED` (reject) · budget exhausted → tier downgrade, not
failure. **The language path never produces a sanction and never voids a game.**

## 18. Security / Privacy Constraints

Advisor is untrusted (TB-4) · peer text is data, never instruction · prompts carry no
secrets/nonces/forbidden truth · no verbatim logging of prompts/responses that could
contain injected protocol-like content · no credential in any artifact · the hint channel
cannot leak our own true position implicitly through a numeric encoding (LLM-003 check).

## 19. Determinism / Reproducibility

T0 fully deterministic and cross-OS reproducible; word counting normalised (NFC) and
deterministic; LLM non-determinism confined to hint text, which is sealed exactly as
sent so replay verifies the *actual* bytes regardless of how they were produced.

## 20. Performance / Deadline Constraints

Advisor calls are time-boxed strictly inside the strategy's decision budget, which is
itself inside `response_timeout_sec` (config-sourced). Exceeding the budget ⇒ abandon and
fall back; never extend a protocol deadline for the LLM.

## 21. Cross-Platform Constraints

Identical T0 hints and identical word-count decisions on Linux and Windows; NFC
normalisation before counting; UTF-8 throughout; no locale-dependent tokenisation.

## 22. Observability / Evidence

Tokens (prompt/completion/sub-game/series), call count, latency, failure count, fallback
reason, tier in force, hint length distribution, rejected-hint count (over-length /
numeric-encoding), peer `verdict`/`intent` mapping events. Tokens surface in the result
via PRD-07 (PERF-001).

## 23. Acceptance Criteria

| ID | Criterion |
|---|---|
| **PRD04-AC-001** | With the advisor fully disabled, a complete six-sub-game series runs and every turn produces a legal hint — **strict zero-token operation**. |
| **PRD04-AC-002** | A hint exceeding `hint_max_words` is never sent; the deterministic fallback is used. Changing the config cap to a different value changes the enforced limit (proving no hard-coded 15). |
| **PRD04-AC-003** | A hint containing a numeric coordinate encoding is rejected before send (LLM-003). |
| **PRD04-AC-004** | A malformed advisor response is rejected and the template fallback is used; no exception escapes. |
| **PRD04-AC-005** | An advisor timeout falls back within the decision budget; the protocol deadline is never extended. |
| **PRD04-AC-006** | A prompt-construction test asserts that no forbidden field (opponent true position, nonce, key material, credential) appears in the prompt payload. |
| **PRD04-AC-007** | A tactical LLM suggestion that is illegal is **rejected by the validator**; the deterministic action is used. The advisor cannot bypass validation. |
| **PRD04-AC-008** | T2 cannot be activated without a recorded prior mutual-agreement reference; attempting to enable it otherwise fails at start-up. |
| **PRD04-AC-009** | The sealed record contains exactly one classification field, `intent`; no `verdict` field is added. |
| **PRD04-AC-010** | A peer payload carrying both `verdict` and `intent` with the **same** value maps to the single `intent` semantic; with **different** values it is rejected as malformed — no dual truth. |
| **PRD04-AC-011** | Scent interpretation changes no underlying field value: the physics output before and after interpretation is byte-identical. |
| **PRD04-AC-012** | A config containing `pheromone_min_center_intensity` produces identical interpretation results to one without it. |
| **PRD04-AC-013** | T0 hint text and word-count decisions are identical on Linux and Windows for the same seed. |
| **PRD04-AC-014** | Token counters accumulate per call/sub-game/series and are exposed for the completion JSON (PERF-001). |
| **PRD04-AC-015** | Approaching `token_budget_per_series` degrades T1 → T0 instead of overrunning the budget. |
| **PRD04-AC-016** | No log line, metric label or artifact contains prompt secrets, credentials or API keys (scan). |

## 24. Planned Tests

| ID | Test | Layer |
|---|---|---|
| **PRD04-T-001** | Zero-token full series | INTEGRATION |
| **PRD04-T-002** | Word-cap enforcement from config (multiple caps) | UNIT |
| **PRD04-T-003** | Numeric-encoding rejection (LLM-003) | UNIT / SECURITY |
| **PRD04-T-004** | Malformed advisor response handling | UNIT |
| **PRD04-T-005** | Advisor timeout → fallback within budget | INTEGRATION |
| **PRD04-T-006** | Prompt forbidden-field scan | SECURITY |
| **PRD04-T-007** | Illegal LLM suggestion rejected by validator | INTEGRATION |
| **PRD04-T-008** | T2 gating on recorded mutual agreement | CONTRACT |
| **PRD04-T-009** | Single `intent` field in sealed record | CONTRACT |
| **PRD04-T-010** | `verdict`→`intent` mapping; disagreement rejected | PROTOCOL |
| **PRD04-T-011** | Interpretation does not mutate scent physics | UNIT |
| **PRD04-T-012** | Reference-only pheromone key ignored | CONTRACT |
| **PRD04-T-013** | Cross-OS T0 determinism | PROPERTY / CROSS-PROCESS |
| **PRD04-T-014** | Token accounting + budget degradation | INTEGRATION |
| **PRD04-T-015** | Secret-absence scan for prompts/logs | SECURITY |
| **PRD04-T-016** | Prompt-injection resistance (peer text as data) | SECURITY |

## 25. Requirement Traceability

**Directly owned:** LLM-002, LLM-003, LLM-004, LLM-005, PERF-001, PERF-002, PERF-003,
SCENT-003 (exchange/verify), SCENT-001 (lock — jointly with PRD-06). **Constrained by:**
LLM-001, GAME-009, STRAT-002, GUI-001/002. **Consumes:** SCENT-002 physics (PRD-01),
`hint_max_words` and `map_area` (App F T14), `token_budget_per_series` (App F T18).
**Conflict honoured:** C-08.

## 26. Dependencies on Other PRDs

PRD-01 (scent physics, config values) · PRD-02 (deadline budget, transport of the hint) ·
PRD-03 (requests a hint; consumes interpreted signal) · PRD-06 (hint + `intent` sealed in
the commitment; token record locked at Step-0) · PRD-07 (tokens in the result).

## 27. Open Design Decisions

Provider/model/SDK (deferred; none chosen) · prompt templates and phrasing · the exact
numeric-encoding detector heuristic and its false-positive budget · hint quality metric ·
`every_n_steps` style throttling · whether T2 is ever enabled (requires a documented
mutual agreement first).

## 28. Explicit Non-Goals

No scent physics ownership · no movement selection · no transport · no cryptographic
sealing · no provider dependency · no claim that the LLM improves play · T2 is not
enabled by default.

## 29. Implementation Readiness Checklist

- [x] Hint rules complete: free language, no numeric protocol, config-sourced cap
- [x] `intent` single-field semantics and `verdict` compatibility mapping defined
- [x] Tiers, validation gate and forbidden LLM powers enumerated
- [x] Full degradation ladder with T0 always operational
- [x] Token accounting, Step-0 lock and budget degradation specified
- [x] Scent physics/interpretation boundary explicit
- [ ] Supervising review — **pending**
- [ ] Implementation — **not started**
