# PRD-01…07 Full Crosswalk — group MaRs-777 (POLICE)

**Status: STAGE 2C — complete ownership and coverage audit. Documentation only.**

Guarantees: **every one of the 91 locked requirements has exactly one PRIMARY owner**,
**every architectural concern has exactly one primary PRD**, and no requirement is lost.
Secondary/cross-cutting references may be many; primary ownership is always one.

## 1. Requirement ownership — all 91, one primary owner each

| Owner | Count | Requirement IDs |
|---|---|---|
| **PRD-01** Game Logic | **15** | GAME-001…009, BAR-001…005, SCENT-002 |
| **PRD-02** Local FastMCP & Orchestration | **11** | ARCH-001…005, STATE-001…005, NET-004 |
| **PRD-03** Baseline Strategy | **3** | STRAT-001, STRAT-002, STRAT-003 |
| **PRD-04** Language & Scent | **10** | LLM-001…005, SCENT-001, SCENT-003, PERF-001, PERF-002, PERF-003 |
| **PRD-05** Public Network & Tunnel | **2** | NET-001, NET-003 |
| **PRD-06** Security & Cryptography | **14** | CRYPTO-001…011, SEC-003, SEC-004, SEC-005 |
| **PRD-07** Reporting, GUI & Replay | **24** | GUI-001…003, REPLAY-001/002, REPORT-001…003, JSON-001…004, LEAGUE-001…007, **NET-002**, **SEC-001**, **SEC-002**, **SEC-006**, **GIT-003** |
| **EXTERNAL / SUBMISSION** | **12** | GIT-001, GIT-002, GIT-004, GIT-005, DOC-001…003, SUB-001…005 |
| **TOTAL** | **91** | — |
| **Unmapped** | **0** | — |
| **Duplicate primary owner** | **0** | — |

### 1.1 Reassignments vs the Stage-2B provisional split (each justified from the catalog text)

Stage 2B provisionally expected PRD-05 = 3, PRD-06 = 17, PRD-07 = 19, SUBMISSION = 13.
Reading the **actual locked requirement text** proved four assignments more correct
elsewhere. The 01–04 counts are **unchanged** (15 / 11 / 3 / 10 = 39).

| ID | Stage-2B | **Stage-2C** | Justification (verbatim intent of the catalog row) |
|---|---|---|---|
| **NET-002** | PRD-05 | **PRD-07** | The requirement is a token-bucket rate-limiter *"on outgoing **Gmail** reports"* — it governs the reporting egress, which PRD-07 owns. PRD-05/PRD-02 remain secondary. |
| **SEC-001** | PRD-06 | **PRD-07** | *"DOS detector that hard-locks **API** access on anomalous **send** patterns"* — an outgoing Gmail-API control, not a game-crypto control. |
| **SEC-002** | PRD-06 | **PRD-07** | *"Grant the **Gmail** integration send-only permission"* — Gmail integration is PRD-07. |
| **SEC-006** | PRD-06 | **PRD-07** | *"Request only the least-privilege scope `gmail.send`"* — same Gmail integration. |
| **GIT-003** | SUBMISSION | **PRD-07** | Scope is **BOTH**, not SUBMISSION: *"Record in the Step-0 declaration the exact GitHub commit hash played each game"* — per-game reporting/declaration evidence produced during play. |

Net effect: PRD-05 3→**2**, PRD-06 17→**14**, PRD-07 19→**24**, SUBMISSION 13→**12**.
Total remains **91**. SEC-003/004/005 (secret handling, `.gitignore`, rotation) stay in
**PRD-06** because they govern key/secret lifecycle generally, not the Gmail integration.

## 2. Concern ownership — one primary PRD each

| Concern | Primary | Secondary | Source IDs |
|---|---|---|---|
| Game rules / turn semantics | **PRD-01** | PRD-02 | GAME-003/005/008 |
| Movement legality | **PRD-01** | PRD-03 | GAME-003/004/009 |
| Barriers | **PRD-01** | PRD-03 | BAR-001…005 |
| **Scent physics** | **PRD-01** | PRD-04 | SCENT-002 |
| **Scent interpretation** | **PRD-04** | PRD-03 | SCENT-001/003 |
| Belief | **PRD-01** (type/owner) | PRD-03, PRD-04 | GUI-001/002 |
| Strategy decision | **PRD-03** | PRD-01 (validates) | STRAT-001…003 |
| Language / hints / `intent` | **PRD-04** | PRD-06 (seals) | LLM-002/003/004, C-08 |
| LLM tiers | **PRD-04** | PRD-03 | LLM-001/005 |
| Local orchestration | **PRD-02** | — | STATE-001 |
| State machine | **PRD-02** | PRD-06 (crypto correctness) | STATE-002/003 |
| FastMCP semantics | **PRD-02** | PRD-05 | ARCH-004, NET-004 |
| **Public tunnel** | **PRD-05** | PRD-02 | NET-001, NET-003 |
| **Endpoint identity** | **PRD-05** | PRD-07 (declaration) | NET-001; INV-01 — **stable group-level ingress, 1/team, static whole-series (CLOSE-F2)** |
| **Series convention** | **PRD-05** | PRD-02 (execution), PRD-06 (authenticated evidence) | **NEGOTIATED-PRE-MATCH** — negotiation record, **not** a declaration field (CLOSE-F1) |
| Timeouts / watchdog | **PRD-02** | PRD-05 | STATE-004/005 |
| Rate limiting (peer) | **PRD-02** | PRD-05 | App F T19 |
| Rate limiting (Gmail) | **PRD-07** | PRD-02 | **NET-002** |
| **Canonicalization** | **PRD-06** | PRD-07 (artifacts) | CRYPTO-009, JSON-004 |
| **Step-0 auth** | **PRD-06** | PRD-05 (readiness), PRD-07 (declaration) | CRYPTO-006, CRYPTO-011 |
| **Config lock** | **PRD-06** | PRD-01/02 | GAME-001/002, JSON-004 |
| **Commit-reveal** | **PRD-06** | PRD-02 (sequencing) | CRYPTO-001/008/009 |
| **Nonce** | **PRD-06** | PRD-07 (log timing) | CRYPTO-002/010 |
| **Final audit** | **PRD-06** | PRD-07 (replay surface) | CRYPTO-003/007 |
| Artifact persistence | **PRD-07** | PRD-06 (bytes) | JSON-003 |
| **Live GUI** | **PRD-07** | PRD-01 (privacy source) | GUI-001/002/003 |
| **Replay** | **PRD-07** | PRD-06 (verification) | REPLAY-001/002 |
| **Result** | **PRD-07** | PRD-01 (scores), PRD-06 (digest) | JSON-001…004, LEAGUE-002/006 |
| **Gmail** | **PRD-07** | PRD-06 (secret rules) | REPORT-001/002/003, SEC-001/002/006 |
| **Git commit evidence** | **PRD-07** | — | **GIT-003** |
| Compatibility profiles | **PRD-02** (select/freeze) | PRD-05, PRD-06, PRD-07 | JDEC-013/014 |
| Privacy | **PRD-01** (structural) | PRD-03/04/07 | GUI-001/002 |
| Security | **PRD-06** | PRD-02, PRD-05, PRD-07 | SEC-003/004/005 |
| Observability | **PRD-02** (emit) | PRD-07 (persist), PRD-04 (tokens) | REPLAY-001 |
| External delivery | **EXTERNAL/SUBMISSION** | PRD-07 | SUB-*, GIT-001/002/004/005, DOC-* |

## 3. Cross-PRD boundary audit

| Boundary | Rule | Verification |
|---|---|---|
| **PRD-02 vs PRD-05** — local protocol vs public reachability | PRD-02 owns local semantics, the state machine and **retry scheduling**; PRD-05 owns whether the **public path exists and is verified**. PRD-05 emits typed connectivity failures; PRD-02 decides when to retry. | PRD05-FR-060…066; PRD02-FR-050…056 |
| **PRD-02 vs PRD-06** — sequencing vs cryptographic correctness | PRD-02 decides **when** a message is legal in the phase/cursor; PRD-06 decides **whether the bytes are authentic and reproducible**. Neither re-implements the other. | PRD02-FR-020…029; PRD06-FR-080…088 |
| **PRD-05 vs PRD-06** — public transport vs peer authenticity | Reaching an endpoint is **never** evidence of peer identity. The readiness probe **cannot substitute for or bypass Step-0 auth**. | PRD05-FR-024; PRD06-FR-027 |
| **PRD-06 vs PRD-07** — crypto vs persisted/displayed evidence | PRD-06 generates and verifies; PRD-07 persists and displays. **Replay calls PRD-06 interfaces; a second crypto implementation is forbidden.** | PRD06-NFR-005; PRD07-FR-025, PRD07-AC-013 |
| **PRD-01 vs PRD-07** — result calculation vs serialization | PRD-01 **computes** scores/outcomes; PRD-07 **records and serializes** them and never recomputes them differently. | PRD01-FR-070…076; PRD07-FR-080/083 |
| **PRD-03 vs PRD-04** — movement policy vs language/scent interpretation | PRD-03 chooses the action; PRD-04 produces hint text/`intent` and interprets scent. PRD-04 never selects a move; PRD-03 never generates hint text itself. | PRD03-FR-004; PRD04-FR-031/033 |

**No duplicated authoritative ownership found across any boundary.**

## 4. Compatibility discipline (global)

`STRICT_COUNTED_MATCH` is the authoritative acceptance target.
`LECTURER_REFERENCE_COMPATIBILITY` and `LECTURER_ATTACHMENT_COMPATIBILITY` may **add**
accepted encodings/conventions and may **never weaken** a binding requirement.

| Item | Status across all seven PRDs | Ever SOURCE-MUST? |
|---|---|---|
| Role alternation | series convention, explicitly agreed, no silent default (PRD-05) | **No** |
| Reference FastMCP tool names | REFERENCE-COMPATIBILITY DEFAULT (PRD-02) | **No** |
| Ed25519 | ATTACHMENT-COMPATIBILITY `AuthProfile` (PRD-06) | **No** |
| Reference commitment encoding | negotiated `CommitmentCodec` (PRD-06) | **No** |
| `_note` keys | example/compatibility metadata (PRD-06/PRD-01) | **No** |
| `pheromone_min_center_intensity` | REFERENCE-ONLY, cannot alter results (PRD-01/PRD-04) | **No** |
| `g01…g06` padding | PROJECT convention JDEC-004 (PRD-07) | **No** |
| Ports 8801/8802, `127.0.0.1` | REFERENCE-ONLY defaults (PRD-05) | **No** |
| Attachment result shape | ATTACHMENT-COMPATIBILITY; Table-20 filenames always win (PRD-07) | **No** |

**Compatibility cannot downgrade:** the keyed Step-0 requirement (PRD06-FR-021/022/028),
any Appendix-F value (PRD01-FR-091, PRD06-FR-046), game isolation (PRD02-FR-002/003),
privacy (PRD01-FR-021, PRD07-FR-003/004), or reporting obligations (PRD07-FR-140…143, C-09).

## 5. Global numeric audit

| Key | Value / default | Status | Authority | Used in |
|---|---|---|---|---|
| `num_games` | **6** | **FIXED** (counted series) | App F T18; **C-05** | PRD-01, PRD-02, PRD-07 |
| `grid_size` | 7 | **MINIMUM (≥7)** | App F T13; C-01 | PRD-01 |
| `num_agents` | 2 | **FIXED** | App F T13 | PRD-01 |
| `move_set` | N,S,E,W,STAY | **FIXED** | App F T15 | PRD-01 |
| `max_barriers` | 14 | **MINIMUM** | App F T15 | PRD-01, PRD-03 |
| `max_moves` | 35 | **MINIMUM** | App F T15 | PRD-01 |
| `survival_threshold` | 35 | **MINIMUM** | App F T15 | PRD-01, PRD-03 |
| `pheromone_center_intensity` | 0.9 | **FIXED** | App F T16 | PRD-01, PRD-04 |
| `pheromone_decay` | 0.10 | **FIXED** | App F T16 | PRD-01, PRD-04 |
| `pheromone_grid_size` | 5 | **FIXED** | App F T16 | PRD-01, PRD-04 |
| `capture_cop` / `capture_thief` | 20 / 5 | **FIXED** | App F T17 | PRD-01, PRD-07 |
| `survival_cop` / `survival_thief` | 5 / 10 | **FIXED** | App F T17 | PRD-01, PRD-07 |
| `tie_score` | 2 | **FIXED** | App F T17 | PRD-01, PRD-07 |
| `technical_loss` | **0 / 0** | key SOURCE-EXPLICIT; **value via Ch 3 + App E #48 — NOT an App F row** | **C-07** | PRD-01, PRD-07 |
| `diversity_reward` | 10 | **FIXED** | App F T18 | PRD-07 |
| `min_games_to_pass` | 2 | **FIXED** | App F T18 | PRD-07 |
| `max_games_per_team` | 10 | **FIXED** | App F T18 | PRD-07 |
| `token_budget_per_series` | ~200 000 | **NEGOTIABLE** | App F T18 | PRD-04 |
| `hint_max_words` | 15 | **NEGOTIABLE** | App F T14 | PRD-04 |
| `map_area` | "New York" / "" | **NEGOTIABLE** | App F T14 | PRD-04 |
| `response_timeout_sec` | 30 | **NEGOTIABLE** | App F T19 | PRD-02, PRD-03, PRD-04, PRD-05 |
| `watchdog_timeout_sec` | 60 | **NEGOTIABLE** | App F T19 | PRD-02, PRD-05 |
| `requests_per_minute` | 30 | **MINIMUM** | App F T19 | PRD-02, PRD-07 |
| `concurrent_requests` | 2 | **MINIMUM** | App F T19 | PRD-02 |
| `retry_backoff_sec` | 5 | **MINIMUM** | App F T19 | PRD-02, PRD-05 |
| `max_retries` | 3 | **MINIMUM** | App F T19 | PRD-02, PRD-05 |
| `queue_depth` | 100 | **MINIMUM** | App F T19 | PRD-02 |

**Non-binding numerics explicitly excluded:** private `turn_timeout_seconds` **180 s**
(reference/local only — **C-02**, never the negotiated deadline) · ports 8801/8802 ·
nonce length 16 bytes (PROJECT default, not sourced) · readiness window 60 s (local
setting, **not** an Appendix-F value) · `pheromone_min_center_intensity` 0.5 (reference-only).

## 6. Role-symmetry classification (all seven)

| PRD | Classification | Role difference |
|---|---|---|
| PRD-01 | COMMON-WITH-ROLE-SECTIONS | action space (barriers police-only) + scoring perspective |
| PRD-02 | COMMON-WITH-ROLE-SECTIONS | role identity only |
| **PRD-03** | **ROLE-SPECIFIC** | genuinely different pursuit vs escape policies |
| PRD-04 | COMMON-WITH-ROLE-SECTIONS | §13.6 hint usage (profiling vs deception) |
| PRD-05 | COMMON-WITH-ROLE-SECTIONS | role identity only |
| PRD-06 | COMMON-WITH-ROLE-SECTIONS | role identity only; crypto identical |
| PRD-07 | COMMON-WITH-ROLE-SECTIONS | role identity only |
| This crosswalk | COMMON-WITH-ROLE-SECTIONS | header role |
| `PRD_05_07_REVIEW` | COMMON-EXACT | none |

## 7. Stage-2-CLOSE closure findings (F1 / F2)

| Finding | Question | Answer | Artifact-contract impact |
|---|---|---|---|
| **CLOSE-F1** | Does the locked declaration already have a series-convention slot? | **NO** — the declaration fields contain no convention/profile slot *(16 at the time of this review; **15 currently**, after Stage 4E-R12-R1 removed `token_usage_locked` — the answer is unchanged)* | **NONE.** No field added, no JDEC created; matrix stays **75** (16/39/9/11). The convention lives in the **negotiation record / profile evidence**, authenticated pre-series and frozen at `CONFIG_LOCKED` |
| **CLOSE-F2** | Is `mcp_endpoint` per group or per role? | **One per team/group** (`teams.<g>.mcp_endpoint`, cardinality **1/team**) | **NONE.** A stable group ingress routes locally to the active independent role process, so role alternation needs **no new declaration field**. A forced change of the declared ingress requires re-negotiation / a new declaration-game boundary — never silent mutation |
