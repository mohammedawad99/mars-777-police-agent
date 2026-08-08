# PRD-07 — Reporting, GUI and Replay — group MaRs-777 (POLICE)

## 1. Document Metadata

| Field | Value |
|---|---|
| PRD | PRD-07 — Reporting, GUI & Replay |
| Repository role | **POLICE** |
| Owns | `infra.gui`, `infra.replay`, `infra.artifacts`, `infra.reporter`, series/league scoring record, Gmail delivery, submission evidence |
| Architecture inputs | `ARTIFACT_LIFECYCLE.md`, `DATA_FLOW.md` §8–§11, `OBSERVABILITY.md`, `QUALITY_GATES.md`, `SECURITY_ARCHITECTURE.md` T10/T11 |
| Symmetry class | **COMMON-WITH-ROLE-SECTIONS** (role identity only) |

## 2. Status

**APPROVED — PHASE 2 LOCKED.** Approved after Stage 2-CLOSE supervising review.
**Implementation status: NOT STARTED.** No code, no dependency, no credentials.

## 3. Purpose

Specify the three **evidence surfaces** — the privacy-safe **live GUI**, the offline
**replay verifier**, and the **official artifact/reporting** chain — so that a grader can
independently verify the match, and so that a reporting failure can never rewrite history.

## 4. Problem Statement

These three surfaces share persisted evidence but have very different privileges. A live
GUI that shows opponent truth breaks the game's information model; a replay that reads
live state proves nothing; a reporter that mutates state destroys auditability; and a
report that is missing, malformed, or contradictory costs **both teams** their credit
(C-09). Each hazard must be designed out separately.

## 5. Scope

Live GUI projection · offline replay/verifier · the four official artifacts and their
joins · result contract and `result_sha256` usage · exact played-commit evidence · log
semantics and atomic persistence · Gmail delivery (send-only, least privilege) · delivery
state vs game result · C-09 agreement rule · league/series scoring record · submission
evidence.

## 6. Out of Scope

Game rules/scoring computation (**PRD-01** computes; this PRD records/serializes) ·
orchestration and state machine (**PRD-02**) · strategy (**PRD-03**) · hint/LLM production
(**PRD-04**) · tunnel lifecycle (**PRD-05**) · cryptographic primitives (**PRD-06** — this
PRD **calls** them and never re-implements them).

## 7. Actors

Local operator (views GUI, runs replay) · the **lecturer/grader** (receives the report,
accesses the repos, runs replay) · the opponent peer (agrees the result) · Gmail API
(external, send-only) · GitHub (source identity).

## 8. Definitions

**Projection** — read-only view built from emitted events. **Replay** — offline
re-verification from artifacts only. **Artifact set** — the four official JSON documents.
**Delivery status** — the state of *sending the report*, distinct from the game result.

## 9. Locked Source Requirements

| ID | Modality | Scope | Requirement |
|---|---|---|---|
| **GUI-001** | MUST | BOTH | Live GUI shows **local truth only** (own position, sensed scent, received hints; a belief heatmap) |
| **GUI-002** | **MUST NOT** | BOTH | **Never display the full objective board state** in the live UI |
| **GUI-003** | MUST | BOTH | Provide a **belief-map heatmap and turn-state banner**; belief-map screenshots are a submission requirement |
| **REPLAY-001** | MUST | BOTH | Build a **Replay Viewer** that replays and **cryptographically verifies** the game log |
| **REPLAY-002** | MUST | BOTH | For each log step recompute SHA-256 over revealed data and compare to the stored commitment; show **"Verified OK"** / **"TAMPERED"** |
| **JSON-001** | MUST | BOTH | Format the game report as **standard, machine-readable JSON** |
| **JSON-002** | **MUST NOT** | BOTH | Send the completion report **only as an attached JSON file — never free text** |
| **JSON-003** | MUST | BOTH | Produce the **four mandatory JSON documents**, names derived from `game_id` + `<NN>` |
| **JSON-004** | MUST | BOTH | `config/game.json` is the signed shared constitution, canonically serializable and hashable |
| **REPORT-001** | MUST | BOTH | **Automatically report each game's results via the Gmail API** (each team sends its own) |
| **REPORT-002** | MUST | BOTH | Send to the fixed address **`rmisegal+uoh26finalgame@gmail.com`** |
| **REPORT-003** | MUST | BOTH | Respect **HTTP 429**: back off and wait for the next window |
| **NET-002** | MUST | BOTH | **Token-bucket rate-limiter on outgoing Gmail reports** (`tokens←min(C,tokens+r·Δt)`, allow iff `tokens ≥ 1`) |
| **SEC-001** | MUST | BOTH | **DOS detector** that hard-locks API access on anomalous send patterns (circuit-breaker / backpressure) |
| **SEC-002** | MUST | BOTH | Grant the Gmail integration **send-only** permission |
| **SEC-006** | MUST | BOTH | Request only the least-privilege scope **`https://www.googleapis.com/auth/gmail.send`** |
| **GIT-003** | MUST | BOTH | Record the **exact GitHub commit hash played each game** in the Step-0 declaration |
| **LEAGUE-001…007** | MUST / MUST NOT | LEAGUE | Min counted games (2) vs **different** teams; agree result + separate reports; truthful game count; never falsely declare it; **one counted game per opponent**; tie rule (2); max counted games (10) |
| CRYPTO-007 | MUST | BOTH | Mutual log audit before agreeing the shared result *(PRD-06 owns the mechanism)* |

**Conflicts:** **C-07** (technical_loss 0/0 provenance), **C-09** (reporting sanction —
missing from either side **or** contradictory ⇒ 0 to both). **Invariants:** INV-01…05,
INV-10…13.

## 10. Project / Architecture Decisions

| Decision | Provenance |
|---|---|
| Four-artifact-set self-containment; result **references** the declaration | **PROJECT-CONTRACT** (JDEC-014) |
| `declaration_ref == "declaration_<game_id>.json"` | **PROJECT-CONTRACT** (JDEC-014) |
| `<NN>` = `g01`…`g06` | **PROJECT-CONTRACT** (JDEC-004) |
| Four GitHub links as a 4-key object | **PROJECT-CONTRACT** (JDEC-009) |
| `sub_games[]` + `cumulative` shape | **PROJECT-CONTRACT** (JDEC-008) |
| ISO-8601 UTC timestamps | **PROJECT-CONTRACT** (JDEC-011) |
| Replay calls PRD-06 interfaces; **no second crypto implementation** | **ARCHITECTURE-CONSTRAINT** (PRD06-NFR-005) |
| `ResultProfile ∈ {STRICT_PROJECT_RESULT, LECTURER_ATTACHMENT_COMPATIBILITY}` | **ATTACHMENT-COMPATIBILITY** |
| The attachment example is **not** a verified parser schema | **ATTACHMENT-COMPATIBILITY** (AE-03) |

## 11. Inputs

Emitted app events (for GUI) · sealed artifacts (for replay/report) · domain scores and
outcomes (PRD-01) · commitment/audit verdicts and `result_sha256` (PRD-06) · token totals
(PRD-04) · played commit and endpoints (PRD-05/PRD-06 declaration) · Gmail credentials
(environment only).

## 12. Outputs

GUI view models · replay verification report (**Verified OK** / **TAMPERED**) · the four
artifacts · the emailed result attachment · delivery status records · submission evidence.

## 13. Functional Requirements

### 13.1 Live GUI

| ID | Requirement | Provenance |
|---|---|---|
| **PRD07-FR-001** | The live GUI is a **projection only**, built from emitted events; it never holds or reads the live domain aggregate. | **ARCHITECTURE-CONSTRAINT** (D3) |
| **PRD07-FR-002** | It MAY show: own true position, public barriers, own scent observations, **labelled** belief heatmap, turn/sub-game, score, state-machine status, deadlines, protocol/health indicators. | **SOURCE-MANDATORY** (GUI-001, GUI-003) |
| **PRD07-FR-003** | It MUST NOT show: opponent **true** position, opponent private state, any nonce before its permitted reveal, secret/key material, or private protocol internals. | **SOURCE-PROHIBITED** (GUI-002); CRYPTO-002 |
| **PRD07-FR-004** | **The full objective board state is never displayed live.** | **SOURCE-PROHIBITED** (GUI-002) |
| **PRD07-FR-005** | Belief is **visually and semantically labelled as belief/estimate** (heatmap + explicit label), never rendered as a confirmed opponent position. | **SOURCE-MANDATORY** (GUI-001/003) |
| **PRD07-FR-006** | A **turn-state banner** shows the current phase/turn; belief-map screenshots are a submission deliverable. | **SOURCE-MANDATORY** (GUI-003) |
| **PRD07-FR-007** | The GUI **cannot mutate authoritative game state**: it has no write path and no command channel into the domain. | **ARCHITECTURE-CONSTRAINT** |
| **PRD07-FR-008** | GUI failure, slowness or disconnection **MUST NOT stop or alter the game**; the event channel is lossy by design. | `CONCURRENCY_MODEL.md` R-22 |
| **PRD07-FR-009** | The GUI event schema is a **whitelist**; adding a forbidden field is a build/test failure, not a runtime judgement. | GUI-002 enforcement |

### 13.2 Post-game replay

| ID | Requirement | Provenance |
|---|---|---|
| **PRD07-FR-020** | A **Replay Viewer** MUST exist that replays and **cryptographically verifies** the game log. | **SOURCE-MANDATORY** (REPLAY-001) |
| **PRD07-FR-021** | Replay consumes **persisted artifacts only** (file paths in, verdict out). It MUST NOT import or read live mutable game state, and MUST run in a **fresh process with no network**. | **ARCHITECTURE-CONSTRAINT**; REPLAY-001 |
| **PRD07-FR-022** | Replay reconstructs: ordered turns, public events, role-legal path information, revealed commitment evidence, scores/outcomes, and audit status. | REPLAY-001/002 |
| **PRD07-FR-023** | **After the permitted audit/reveal point**, replay MAY use disclosed evidence to show historical truth that was forbidden to the live GUI (including both agents' true paths). This is **not** permission for the live GUI to do so. | **SOURCE-PERMITTED**; GUI-001/002 boundary |
| **PRD07-FR-024** | For each log step, replay recomputes SHA-256 over the revealed data and compares it to the stored commitment, showing **"Verified OK"** or **"TAMPERED"**. | **SOURCE-MANDATORY** (REPLAY-002) |
| **PRD07-FR-025** | Replay MUST call the **PRD-06** `CommitmentCodec`/`KeyedAuth` interfaces. **A second cryptographic implementation is forbidden.** | PRD06-NFR-005 |
| **PRD07-FR-026** | A deliberately mutated log MUST produce **TAMPERED**. | REPLAY-002; INV-06 |
| **PRD07-FR-027** | Verification status is **evidence-driven, not visual**: a GUI/rendering error MUST NOT change or mask the verdict, and the verdict is available headlessly. | **ARCHITECTURE-CONSTRAINT** |
| **PRD07-FR-028** | Replay verification is **deterministic and identical on Linux and Windows**. | cross-OS |

### 13.3 Four-artifact lifecycle

| ID | Requirement | Provenance |
|---|---|---|
| **PRD07-FR-040** | Exactly these official names are used: `declaration_<game_id>.json`, `config_<game_id>_g<NN>.json`, `log_<game_id>_g<NN>.json`, `result_<game_id>.json`. | **SOURCE-MANDATORY** (JSON-003; App F Tbl 20) |
| **PRD07-FR-041** | `<NN>` is **two-digit zero-padded** `g01`…`g06` — a **PROJECT convention**, not source-mandated. | **PROJECT-CONTRACT** (JDEC-004) |
| **PRD07-FR-042** | Ownership: **declaration** = static whole-series/team data; **config** = binding per-sub-game terms; **log** = per-sub-game replay/audit evidence; **result** = minimal mandatory league semantics + joins. | **SOURCE-MANDATORY** (Ch 9 p.78; App F Tbl 20) |
| **PRD07-FR-043** | The **four-artifact set is self-contained**; the result alone need **not** duplicate declaration-owned static metadata. | **PROJECT-CONTRACT** (JDEC-014); INV-10 |
| **PRD07-FR-044** | Artifacts are **write-once then sealed**; corrections create a new game/sub-game identity, never an edit. | `ARTIFACT_LIFECYCLE.md` |
| **PRD07-FR-045** | Writes are **atomic** (temp file → fsync → rename) so a crash never leaves a half-written artifact that would fail replay. | `ARTIFACT_LIFECYCLE.md` rule 2 |
| **PRD07-FR-046** | All hashed artifact bytes are canonical **via PRD-06** (sorted keys, `(",",":")`, UTF-8, NFC, LF, no trailing newline). | **SOURCE-MANDATORY** (JSON-004, CRYPTO-009) |
| **PRD07-FR-047** | Each counted game's config file is **attached to the GitHub repo** with a distinct name per game. | **SOURCE-MANDATORY** (GIT-004; App F §2.3–2.4) |

### 13.4 Artifact joins

| ID | Requirement | Provenance |
|---|---|---|
| **PRD07-FR-060** | `result.declaration_ref == "declaration_<game_id>.json"`. | **PROJECT-CONTRACT** (JDEC-014) |
| **PRD07-FR-061** | `result.game_id == declaration.game_id` and `result.game_uid == declaration.game_uid`. | **INV-01** |
| **PRD07-FR-062** | Group identities MUST agree across declaration and result. | SUB-003; INV-01 |
| **PRD07-FR-063** | Config and log identity (`game_id`, `game_uid`, `<NN>`/`sub_game`) MUST agree with the declaration. | **INV-01/02** |
| **PRD07-FR-064** | **No orphan artifact is valid counted-match evidence**: an artifact whose identity does not join the set is rejected at validation. | INV-01 |
| **PRD07-FR-065** | The `config_sha256` referenced by a log MUST equal the hash of the config actually used for that sub-game. | **INV-03** |
| **PRD07-FR-066** | The played `github_commit` in the declaration MUST equal the commit reported for that game's sub-games in the result. | **INV-05** |

### 13.5 Result semantics

| ID | Requirement | Provenance |
|---|---|---|
| **PRD07-FR-080** | The official result contains: `game_id`, `game_uid`, `declaration_ref`, team `group_id`(+name), the **four GitHub links**, `sub_games[]` `{sub_game, cop_score, thief_score, outcome, github_commit, tokens}`, `cumulative`, `total_tokens`, `timestamp`, `mutual_agreement`, `result_sha256`, `reported_by`. | **SOURCE-MANDATORY** (Ch 9 p.79 mandatory fields) + **PROJECT-CONTRACT** (JDEC-008/009/014) |
| **PRD07-FR-081** | Full hardware, MCP endpoints, member lists and model metadata are **declaration-owned and NOT duplicated** in the result. | **PROJECT-CONTRACT** (JDEC-014); INV-12/13 |
| **PRD07-FR-082** | The official external result surface is **minimal**: **no debug or presentation fields** unless contract-required. | **PROJECT-CONTRACT**; Q7 |
| **PRD07-FR-083** | Scores use only Appendix-F values plus technical_loss **0/0 whose provenance is Ch 3 + App E #48, not Appendix F**. | **SOURCE-MANDATORY** (GAME-006); **C-07** |
| **PRD07-FR-084** | The **tie rule** applies the configured `tie_score` (default 2, FIXED) when cumulative scores tie against an opponent. | **SOURCE-MANDATORY** (LEAGUE-006) |
| **PRD07-FR-085** | `result_sha256` is computed by **PRD-06** over `RESULT_APPROVAL_CORE` and is **non-self-referential**; it is stored as a **separate top-level result field**, beside the **separate top-level** `mutual_agreement` bool that records agreement state — exactly the two fields **FR-080** already lists. *(Stage 4E-R2-FIX2 propagation: this row previously said the digest "is stored in `mutual_agreement.sha256`, with `confirmed` recording agreement state", which contradicted FR-080 in this same table and the bool defined by `RESULT_CONTRACT.md`, `FIELD_MATRIX.md` and NDEC-006. No third representation is introduced.)* | PRD06-FR-140…144 |
| **PRD07-FR-086** | The result MUST be **standard machine-readable JSON**. | **SOURCE-MANDATORY** (JSON-001) |
| **PRD07-FR-087** | The **attachment example is not a verified 1:1 parser schema**; `LECTURER_ATTACHMENT_COMPATIBILITY` may align naming/nesting where it does not conflict, but **official Table-20 filenames always win**. | **ATTACHMENT-COMPATIBILITY** (AE-03) |
| **PRD07-FR-088** | League bookkeeping is recorded truthfully: counted games played, opponents faced (**one counted game per opponent**), min 2 vs **different** teams, max 10, diversity reward 10. | **SOURCE-MANDATORY** (LEAGUE-001/003/004/005/007) |
| **PRD07-FR-089** | The number of counted games already played is **declared truthfully** at the start of each game and **never falsely declared**. | **SOURCE-MANDATORY** (LEAGUE-003, **LEAGUE-004**) |

### 13.6 Exact played commit

| ID | Requirement | Provenance |
|---|---|---|
| **PRD07-FR-100** | The **exact Git commit actually played** is recorded per counted sub-game in the Step-0 declaration and reported in the result. | **SOURCE-MANDATORY** (GIT-003) |
| **PRD07-FR-101** | The commit MUST be captured from the **running process's checkout at play time**; inferring "latest `main`" or resolving a branch name later is **forbidden**. | GIT-003 |
| **PRD07-FR-102** | Police and Thief **repository identities remain distinct** in the four links and in any per-role commit evidence. | SUB-004; ARCH-001 |
| **PRD07-FR-103** | The Git SHA is **source-code identity evidence only — never authentication**. | taxonomy (PRD-06 §8) |
| **PRD07-FR-104** | The submission version is fixed with a documented **annotated Git tag**, pushed. | **SOURCE-MANDATORY** (GIT-001) |
| **PRD07-FR-105** | Each repo contains at least README.md, `config/`, PRD files, a PLAN file and TODO files; both repos are accessible to the lecturer (public, or private and explicitly shared with `rmisegal@gmail.com`). | **SOURCE-MANDATORY** (GIT-002, GIT-005) |

### 13.7 Log semantics

| ID | Requirement | Provenance |
|---|---|---|
| **PRD07-FR-120** | The log is **append-oriented evidence**, one file per sub-game; it is **not** a mutable game-state authority. | **ARCHITECTURE-CONSTRAINT**; REPLAY-001 |
| **PRD07-FR-121** | It records ordered entries: protocol/phase events, commitment/ack/reveal evidence, validation verdicts, approved timestamps/latencies, token/resource evidence, outcome, and final audit status. | REPLAY-001/002; PERF-001 |
| **PRD07-FR-122** | **Nonces appear only in the final-audit section**, never earlier. | **SOURCE-MANDATORY** (CRYPTO-002/008) |
| **PRD07-FR-123** | **No secrets** (keys, credentials, tokens) are ever logged. | **SOURCE-MANDATORY** (SEC-003) |
| **PRD07-FR-124** | Forbidden opponent truth MUST NOT appear before it becomes legitimate disclosed evidence. | GUI-002; `DATA_FLOW.md` |
| **PRD07-FR-125** | Persistence is **failure-safe**: atomic append/rename, flush before sealing, and a crash mid-write must not corrupt earlier verified entries. | `ARTIFACT_LIFECYCLE.md` |
| **PRD07-FR-126** | A rewritten or reordered log is detectable at audit ⇒ **TAMPERED**. | INV-06; REPLAY-002 |

### 13.8 Gmail reporting

| ID | Requirement | Provenance |
|---|---|---|
| **PRD07-FR-140** | Each team **automatically reports each game's result via the Gmail API**, sending **its own** report. | **SOURCE-MANDATORY** (REPORT-001; LEAGUE-002) |
| **PRD07-FR-141** | The recipient is exactly **`rmisegal+uoh26finalgame@gmail.com`** — validated against a constant; a typo is a build/test failure. | **SOURCE-MANDATORY** (REPORT-002) |
| **PRD07-FR-142** | The report is sent as a **JSON attachment** named exactly **`result_<game_id>.json`**. | **SOURCE-MANDATORY** (JSON-002, JSON-003) |
| **PRD07-FR-143** | **Free-text/plaintext-only reports, prose reformatting, or an arbitrary email-body representation are forbidden**; a non-machine-readable report is rejected and may cost the round's league points. | **SOURCE-PROHIBITED** (JSON-002, JSON-001) |
| **PRD07-FR-144** | Gmail access uses **send-only, least-privilege** scope **`https://www.googleapis.com/auth/gmail.send`** and nothing broader. | **SOURCE-MANDATORY** (SEC-002, SEC-006) |
| **PRD07-FR-145** | OAuth/token material (`credentials.json`, `token.json`) stays **local, git-ignored, never logged, never attached, never in the report**. | **SOURCE-MANDATORY** (SEC-003, SEC-004) |
| **PRD07-FR-146** | Outgoing reports pass a **token-bucket rate limiter** (`tokens ← min(C, tokens + r·Δt)`, send iff `tokens ≥ 1`). | **SOURCE-MANDATORY** (NET-002) |
| **PRD07-FR-147** | A **DOS detector / circuit-breaker** hard-locks API access on anomalous send patterns (backpressure), preventing a mail-send loop. | **SOURCE-MANDATORY** (SEC-001) |
| **PRD07-FR-148** | **HTTP 429 ⇒ back off and wait for the next window**; never retry immediately. | **SOURCE-MANDATORY** (REPORT-003) |
| **PRD07-FR-149** | Delivery attempts are **idempotent-aware**: each attempt is recorded, and a retry must not produce a second contradictory report for the same game. | **PROJECT-CONTRACT** |
| **PRD07-FR-150** | Errors are **sanitized**: no credential, token, or header secret in any message, log or metric. | SEC-003; T18 |
| **PRD07-FR-151** | **Real Gmail credentials are never required for CI.** A fake/adapter reporter is used locally; actual delivery is an **external manual E2E gate**. | **PROJECT-CONTRACT**; `QUALITY_GATES.md` |

### 13.9 Delivery state vs game result

| ID | Requirement | Provenance |
|---|---|---|
| **PRD07-FR-170** | **Delivery status is separate from the game result.** States: `NOT_ATTEMPTED`, `READY`, `SENT`, `DELIVERY_FAILED`. These are **reporting states, not game-domain states**. | **ARCHITECTURE-CONSTRAINT** |
| **PRD07-FR-171** | The reporter reads **finalized evidence** and **MUST NEVER mutate authoritative game history**. | T11; `DEPENDENCY_RULES.md` |
| **PRD07-FR-172** | A Gmail/API failure **cannot rewrite the historical played result**; the artifacts remain as sealed. | T11 |
| **PRD07-FR-173** | However, **official league credit follows the locked reporting rules**: delivery failure that results in a missing required report has the C-09 consequence. | **C-09**; LEAGUE-002 |

### 13.10 Result agreement (C-09)

| ID | Requirement | Provenance |
|---|---|---|
| **PRD07-FR-190** | Before sending, each peer **compares the agreed result-approval digest**; once that comparison establishes equality, both reports MUST carry the **same** `result_sha256` and record `mutual_agreement = true` as a **separate top-level field**. *(Stage 4E-R2-FIX2 propagation: previously written as `mutual_agreement.confirmed = true`. This is a **record** requirement, not a message one — it does not freeze the Event-14 exchange pattern, define an offer/confirm/response/echo, or name any RPC method, wire key or FastMCP method.)* | **SOURCE-MANDATORY** (LEAGUE-002); NDEC-006 |
| **PRD07-FR-191** | **A required report missing from either side, OR contradictory final reports, invalidates official game credit** — the stricter locked resolution. | **SOURCE-MANDATORY** (App E #35) + **C-09** |
| **PRD07-FR-192** | **No softer rule may be applied**, and the milder per-side non-credit reading is not used where C-09 governs. | **C-09** |
| **PRD07-FR-193** | Contradictory result evidence MUST NOT be silently "fixed", adjusted or reconciled by the reporter; it is surfaced as a blocking condition. | **C-09**; T11 |
| **PRD07-FR-194** | The mutual log audit (PRD-06 / CRYPTO-007) MUST complete **before** the shared result is agreed. | **SOURCE-MANDATORY** (CRYPTO-007) |

### 13.11 Submission evidence

| ID | Requirement | Provenance |
|---|---|---|
| **PRD07-FR-210** | Collected evidence: live GUI screenshot(s) incl. the **belief-map heatmap**, replay **"Verified OK"** output, a **TAMPERED negative demonstration**, the four artifacts per counted game, and delivery evidence. | **SOURCE-MANDATORY** (GUI-003, REPLAY-002) |
| **PRD07-FR-211** | **Screenshots are supporting evidence only — never authoritative state.** | **ARCHITECTURE-CONSTRAINT** |
| **PRD07-FR-212** | Submission obligations (Moodle form/PDF, per-member submission, 8-char group ID, two repos + cross-link + two links + four links, Appendix-C checklist) are tracked here as **EXTERNAL/SUBMISSION** deliverables. | **SOURCE-MANDATORY** (SUB-001…005; DOC-001/002) |

## 14. Non-Functional Requirements

| ID | Requirement |
|---|---|
| **PRD07-NFR-001** | Replay of a full six-sub-game series verifies in **< 10 s** on the reference machine, headless, offline. |
| **PRD07-NFR-002** | GUI rendering never blocks the game loop; frame drops are acceptable and observable. |
| **PRD07-NFR-003** | The full PRD-07 suite (GUI projection, replay, artifacts, reporting) runs **offline with fakes**; no Gmail credentials, no internet. |
| **PRD07-NFR-004** | Every file ≤ **150 lines**; gui, replay, artifacts, reporter and league-record are separate modules. |
| **PRD07-NFR-005** | Zero cryptographic primitive is re-implemented here (import/contract check). |

## 15. Lifecycle / State Responsibilities

Owns: artifact files and their sealing, log handle, GUI view model, replay verdict,
delivery status, league bookkeeping record. **Does not own:** game truth/scores computation
(PRD-01), crypto (PRD-06), sequencing (PRD-02), transport (PRD-05).

## 16. Validation Rules

Official filename regex · `<NN>` in `g01…g06` · identity joins (INV-01/02/05) ·
`declaration_ref` exact string · four links present · per-sub-game `github_commit` present
and 40-hex · tokens present · scores from Appendix F (+C-07) · `result_sha256` present and
matching · recipient address exact · attachment name exact · JSON parses as
machine-readable · no forbidden field in GUI events · no secret in any artifact.

## 17. Failure Behaviour

`E-REPORT-DELIVERY` (retryable, paced; missing required report ⇒ C-09 consequence) ·
`E-REPORT-DISAGREE` (contradictory ⇒ **0 to both**, C-09) · `E-RATE-429` (back off to next
window) · `E-REPLAY-MISMATCH` ⇒ **TAMPERED** · artifact I/O error ⇒ fail before sealing ·
GUI error ⇒ non-fatal, never alters verdicts. **No sanction beyond the locked set.**

## 18. Security / Privacy

Live GUI privacy wall (GUI-001/002) enforced by a whitelist schema · nonce never shown
pre-audit · replay uses disclosed evidence only after audit · reporter is write-only w.r.t.
game state · Gmail send-only least privilege · credentials env-only, git-ignored, never
logged/attached · DOS detector + rate limiter prevent send abuse · sanitized errors.

## 19. Determinism / Reproducibility

**Replay verification is fully deterministic** from artifacts alone and must give the same
verdict on any machine, any time, offline. Artifact bytes are canonical. GUI rendering is
explicitly **not** required to be deterministic and never affects verdicts.

## 20. Performance / Deadline Constraints

Replay bounded (NFR-001). Reporting is off the game critical path — a slow send never
delays play. Gmail pacing uses the token bucket (NET-002) and honours 429 windows
(REPORT-003).

## 21. Cross-Platform Constraints

Artifact bytes and replay verdicts identical on Linux and Windows (canonical bytes from
PRD-06; `pathlib` paths; LF; UTF-8). Filenames are case-consistent and contain no
platform-illegal characters.

## 22. Observability / Evidence

Artifact write/seal events, replay verdict + first-mismatch location, GUI event counts and
drops, delivery attempts/status/latency, 429 and circuit-breaker events, league counters
(counted games, opponents, tie applications). **Never:** secrets, nonces pre-audit,
opponent forbidden truth.

## 23. Acceptance Criteria

**Live GUI**

| ID | Criterion |
|---|---|
| **PRD07-AC-001** | Own truth, public barriers, own scent, labelled belief heatmap and turn-state banner are all visible. |
| **PRD07-AC-002** | **Opponent true position is impossible to display** — the GUI event schema has no such field; adding one fails the whitelist test. |
| **PRD07-AC-003** | Belief is rendered with an explicit belief label, never as a confirmed position. |
| **PRD07-AC-004** | The GUI has no write path: an attempted state mutation from the GUI layer fails to compile/contract-test. |
| **PRD07-AC-005** | Killing/stalling the GUI does not halt or alter the game. |

**Replay**

| ID | Criterion |
|---|---|
| **PRD07-AC-010** | Replay runs **offline from files only**, in a fresh process, with no network. |
| **PRD07-AC-011** | A valid log yields **Verified OK** for every step. |
| **PRD07-AC-012** | A **one-byte or one-semantic-field mutation** of the log yields **TAMPERED**, naming the failing step. |
| **PRD07-AC-013** | Replay imports no live app/domain state (dependency test) and no second crypto implementation. |
| **PRD07-AC-014** | Verification verdicts are identical on Linux and Windows for the same artifacts. |
| **PRD07-AC-015** | A GUI/rendering failure during replay does not change the verdict (headless run gives the same result). |

**Artifacts**

| ID | Criterion |
|---|---|
| **PRD07-AC-020** | All four filenames match exactly, with `<NN>` in `g01…g06`. |
| **PRD07-AC-021** | Joins exact: `declaration_ref`, `game_id`, `game_uid`, group ids, config/log identity (INV-01/02/03/05). |
| **PRD07-AC-022** | An orphan artifact (identity not joining) is rejected as counted-match evidence. |
| **PRD07-AC-023** | The result does **not** contain full hardware/MCP/member/model metadata (declaration-owned). |
| **PRD07-AC-024** | Every counted sub-game carries an exact 40-hex `github_commit`; a branch name or "latest main" is rejected. |
| **PRD07-AC-025** | Tokens, scores and outcomes are present for every sub-game; cumulative and `total_tokens` present. |
| **PRD07-AC-026** | `result_sha256` is present and **non-self-referential** (including it in the core changes the value). |
| **PRD07-AC-027** | An interrupted write leaves no half-written artifact (atomic rename test). |

**Reporting**

| ID | Criterion |
|---|---|
| **PRD07-AC-030** | Recipient is exactly `rmisegal+uoh26finalgame@gmail.com` (constant test; a typo fails). |
| **PRD07-AC-031** | The report is sent as a **JSON attachment** named exactly `result_<game_id>.json`. |
| **PRD07-AC-032** | A plaintext-only/prose-body report is rejected by the reporter before sending. |
| **PRD07-AC-033** | The attachment parses as valid machine-readable JSON. |
| **PRD07-AC-034** | Scan: no OAuth credential, token or secret in the message, attachment, logs or metrics. |
| **PRD07-AC-035** | The fake Gmail adapter test passes fully offline; **real delivery is an explicitly deferred external gate**. |
| **PRD07-AC-036** | The requested scope is exactly `gmail.send` (least privilege). |
| **PRD07-AC-037** | A 429 causes back-off to the next window; the rate limiter and circuit-breaker prevent a send loop. |
| **PRD07-AC-038** | A delivery failure does **not** alter any sealed artifact or score. |
| **PRD07-AC-039** | **C-09:** a report missing from either side, or two contradictory reports, blocks official credit; the reporter never silently reconciles them. |
| **PRD07-AC-040** | Sending is refused until the mutual log audit (CRYPTO-007) has completed and the digests match. |

## 24. Planned Tests

| ID | Test | Layer |
|---|---|---|
| **PRD07-T-001** | GUI event whitelist / forbidden-field scan | SECURITY |
| **PRD07-T-002** | GUI no-write-path contract | CONTRACT |
| **PRD07-T-003** | GUI stall/kill does not affect game | INTEGRATION |
| **PRD07-T-004** | Replay offline from files, fresh process | REPLAY |
| **PRD07-T-005** | Valid log ⇒ Verified OK | REPLAY |
| **PRD07-T-006** | Mutated log (byte + semantic) ⇒ TAMPERED | REPLAY / SECURITY |
| **PRD07-T-007** | Replay imports no live state, no duplicate crypto | CONTRACT |
| **PRD07-T-008** | Cross-OS replay verdict equality | PROPERTY |
| **PRD07-T-009** | Filename + `<NN>` regex | UNIT |
| **PRD07-T-010** | Artifact join invariants (INV-01/02/03/05) | UNIT |
| **PRD07-T-011** | Orphan artifact rejection | UNIT |
| **PRD07-T-012** | Result minimality (no declaration-owned duplication) | CONTRACT |
| **PRD07-T-013** | Exact played commit capture (no branch inference) | INTEGRATION |
| **PRD07-T-014** | `result_sha256` non-self-reference regression | UNIT |
| **PRD07-T-015** | Atomic write / crash safety | UNIT |
| **PRD07-T-016** | Recipient + attachment name constants | UNIT |
| **PRD07-T-017** | Plaintext report rejected | UNIT |
| **PRD07-T-018** | Fake Gmail adapter end-to-end | INTEGRATION |
| **PRD07-T-019** | Scope = gmail.send only | CONTRACT |
| **PRD07-T-020** | 429 + rate limiter + circuit breaker | INTEGRATION |
| **PRD07-T-021** | Delivery failure leaves artifacts unchanged | INTEGRATION |
| **PRD07-T-022** | C-09 missing/contradictory report handling | INTEGRATION |
| **PRD07-T-023** | Secret-absence scan (message/attachment/logs/metrics) | SECURITY |
| **PRD07-T-024** | League bookkeeping (min 2 different opponents, one counted per opponent, max 10, tie rule) | UNIT |
| **PRD07-T-025** | Real Gmail delivery | **MANUAL / E2E (deferred gate)** |

## 25. Requirement Traceability

**Primary owner (24):** GUI-001/002/003 (3) · REPLAY-001/002 (2) · REPORT-001/002/003 (3) ·
JSON-001/002/003/004 (4) · LEAGUE-001…007 (7) · **NET-002** (Gmail rate limiter) ·
**SEC-001** (DOS detector), **SEC-002**, **SEC-006** (Gmail scope) · **GIT-003** (exact
played commit).
**Consumes:** PRD-01 (scores/outcomes), PRD-06 (canonical bytes, commitment verification,
`result_sha256`, secret rules SEC-003/004/005), PRD-04 (tokens, PERF-001), PRD-02
(evidence emission), PRD-05 (endpoints/connectivity evidence).
**Tracks as EXTERNAL/SUBMISSION:** GIT-001/002/004/005, DOC-001/002/003, SUB-001…005.
**Conflicts honoured:** C-07, C-09.

## 26. Dependencies on Other PRDs

PRD-06 (all crypto — **called, never duplicated**) · PRD-01 (scores/outcomes) · PRD-02
(events, sequencing) · PRD-04 (token totals) · PRD-05 (endpoint/connectivity evidence).

## 27. Open Design Decisions

GUI toolkit (must not influence the projection contract) · screenshot capture/storage
format · replay report output format (text/JSON/UI) · Gmail client approach and OAuth flow
mechanics · retention policy for evidence · exact league-record file shape · whether
`LECTURER_ATTACHMENT_COMPATIBILITY` is ever enabled for a real match.

## 28. Explicit Non-Goals

No game-rule computation · no crypto implementation · no transport/tunnel · no strategy ·
no LLM · real Gmail delivery is not a CI gate · the attachment example is not adopted as a
binding schema · screenshots are not authoritative.

## 29. Implementation Readiness Checklist

- [x] Live-GUI privacy wall specified with a whitelist enforcement mechanism
- [x] Replay defined as offline, artifact-only, single-crypto-implementation
- [x] Four artifacts, names, ownership, joins and atomic persistence specified
- [x] Result contract minimal, joined, and non-self-referentially hashed
- [x] Exact played commit required, branch inference forbidden
- [x] Gmail contract exact (recipient, attachment, JSON-only, send-only scope, 429, DOS detector)
- [x] Delivery status separated from game result; C-09 preserved strictly
- [x] CI stays offline; real delivery deferred to a manual gate
- [ ] Supervising review — **pending**
- [ ] Implementation — **not started**
