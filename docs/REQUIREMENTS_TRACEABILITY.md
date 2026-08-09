# Requirements Traceability Matrix - group MaRs-777

> **Status: REVIEWED — Stage-1 baseline LOCKED (supervising review PASS); rows extend in later stages.** Seeded foundation rows (F-0xx)
> retained; catalog requirements (Stage 1A extraction) added with catalog IDs.
> Stage 1A statuses are one of: **EXTRACTED**, **REVIEW REQUIRED**, **CONFLICT**,
> **NOT APPLICABLE**. Nothing is IMPLEMENTED or VERIFIED. Full details and
> citations live in `docs/spec/REQUIREMENT_CATALOG.md`; conflicts in
> `docs/CONFLICT_REGISTER.md` (**C-01…C-10**; C-10 added post-lock in
> Stage 3B-FIX2 — scent state bound vs additive update). "Component" = planned PRD/area.

| Requirement ID | Requirement | Source | Mandatory/Optional | Repository | Planned component | Planned verification | Planned evidence | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|
| F-001 | Two separate police & thief repositories | Stage 0B directive | Mandatory | Both | Repo structure | `git rev-parse`; separate `.git` | Stage 0C report | EXTRACTED | Done in Stage 0C |
| F-002 | Cross-link between the two repositories | Stage 0B directive | Mandatory | Both | README | README paired-repo section | README.md | EXTRACTED | Reinforced by SUB-004 |
| F-003 | No secrets in Git history | App E / SECURITY.md | Mandatory | Both | .gitignore, policy | history secret-scan | .gitignore | EXTRACTED | = SEC-003/004 |
| F-004 | Separate runtime state and processes | Stage 0B directive | Mandatory | Both | runtime/, process model | isolation report | runtime/README | EXTRACTED | = ARCH-001..003 |
| F-005 | Exact competition commit reproducible | Stage 0B directive | Mandatory | Both | VCS, uv.lock, tag | commit-hash checks | tag, JSON | EXTRACTED | = GIT-001/003 |
| F-006 | Full requirements extraction from book v3.0.0 | Book v3.0.0 | Mandatory | Both | docs/spec | Stage 1A/1B | Stage 1A/1B docs | EXTRACTED | Stage 1A+1B complete; supervising review PASS (approved baseline) |
| ARCH-001 | Two completely separate processes | PDF p.31,142 (E-1) | Mandatory | Both | Architecture / PRD-02 | process isolation test | launch logs | EXTRACTED | H-01 |
| ARCH-002 | No shared memory/variables/live-state module | PDF p.31,143 (E-2) | Mandatory | Both | Architecture | import-graph audit | isolation report | EXTRACTED | H-01 |
| ARCH-003 | Separate config dirs (police/thief) | PDF p.31 (E-1) | Mandatory | Both | config/ | filesystem check | repo tree | EXTRACTED | — |
| ARCH-004 | Each agent is FastMCP server + client (symmetric) | PDF p.25–28 | Mandatory | Both | PRD-02 | protocol test | MCP handshake | EXTRACTED | — |
| ARCH-005 | JSON config overlays/overrides private TOML | PDF p.126,132 | Mandatory | Both | config loader | overlay unit test | config evidence | EXTRACTED | — |
| NET-001 | Public tunnel exposure (ngrok/Localtonet) | PDF p.29,144 (E-10) | Mandatory | Both | PRD-05 | reachability test | tunnel URL | EXTRACTED | H-09 |
| NET-002 | Token-bucket rate limiter for Gmail | PDF p.89–91,146 (E-28) | Mandatory | Both | PRD-07 gatekeeper | burst test | limiter logs | EXTRACTED | H-09 |
| NET-003 | Public (non-localhost) league transport | PDF p.88,113 | Mandatory | Both | PRD-05 | public-round test | transcript | EXTRACTED | — |
| NET-004 | MCP via FastMCP, not replaceable | PDF p.26 | Mandatory | Both | PRD-02 | protocol inspection | tool schema | EXTRACTED | — |
| GAME-001 | Byte-identical signed config both sides | PDF p.34,128,144 (E-11) | Mandatory | Both | PRD-01/06 | `config_sha256` equality | signature exchange | EXTRACTED | H-02 |
| GAME-002 | Raise MINIMUMs only, never lower | PDF p.144,155 (E-12) | Mandatory | Both | config validator | vs App F floors | validation report | EXTRACTED | H-02 |
| GAME-003 | Orthogonal moves only | PDF p.37,144 (E-13) | Mandatory | Both | PRD-01 | move-legality tests | validator | EXTRACTED | H-12 |
| GAME-004 | No diagonal moves | PDF p.37,144 (E-14) | Mandatory | Both | PRD-01 | reject-diagonal test | validator | EXTRACTED | H-12 |
| GAME-005 | Trapped thief (no legal move) = captured | PDF p.37,149 (E-47) | Mandatory | Both | PRD-01 | trap-state test | end log | EXTRACTED | — |
| GAME-006 | Score per scoring table | PDF p.38,154,149 (E-48) | Mandatory | Both | PRD-01 | scoring tests | result scores | EXTRACTED | C-06 label order (resolved); C-07 technical_loss 0/0 binding via Ch3/E-48, **not** App F |
| GAME-007 | Board dimensions from config (≥7×7) | PDF p.35,152 | Mandatory | Both | PRD-01 | grid-bound tests | config | CONFLICT | C-01 (resolved by App F) |
| GAME-008 | Step ceiling / survival threshold from config | PDF p.38,153 | Mandatory | Both | PRD-01 | end-of-game tests | log | EXTRACTED | — |
| GAME-009 | Movement legality is deterministic code (never LLM) | PDF p.58,66 | Mandatory | Both | PRD-03 | code path review | strategy module | EXTRACTED | H-12 |
| BAR-001 | Declare every barrier placement | PDF p.37,144 (E-15) | Mandatory | Police | PRD-01 | audit vs declared | log audit | EXTRACTED | H-06 |
| BAR-002 | No lying about barrier location | PDF p.37,144 (E-16) | Mandatory | Police | PRD-01 | log-audit cross-check | log | EXTRACTED | H-06 |
| BAR-003 | Barrier on thief's cell = capture | PDF p.37,149 (E-46) | Mandatory | Police | PRD-01 | capture-by-barrier test | end log | EXTRACTED | — |
| BAR-004 | Barrier placement rules (forgo move; own/adjacent; irreversible) | PDF p.37 | Mandatory | Police | PRD-01 | placement tests | validator | EXTRACTED | — |
| BAR-005 | Barrier quota (≥14 default) | PDF p.37,153 | Mandatory | Police | PRD-01 | quota test | config | EXTRACTED | — |
| SCENT-001 | Crypto-lock scent model before series | PDF p.47,145 (E-23) | Mandatory | Both | PRD-04/06 | model-hash exchange | signed hash | EXTRACTED | H-13 |
| SCENT-002 | Scent emission/decay per formula | PDF p.43,153 | Mandatory | Both | PRD-04 | formula unit tests | snapshots | EXTRACTED | H-13 |
| SCENT-003 | Exchange full model + numeric example, verify, lock | PDF p.47 | Mandatory | Both | PRD-04 | pre-series exchange | model hash | EXTRACTED | — |
| CRYPTO-001 | SHA-256 commit-reveal | PDF p.50,145 (E-17) | Mandatory | Both | PRD-06 | conformance test | commit hashes | EXTRACTED | H-03 |
| CRYPTO-002 | Nonce secret until game end | PDF p.51,145 (E-18) | Mandatory | Both | PRD-06 | reveal-timing test | reveal order | EXTRACTED | H-03 |
| CRYPTO-003 | DQ on hash mismatch (score 0) | PDF p.55,145 (E-19) | Mandatory | Both | PRD-06/07 | tamper-injection | replay verdict | EXTRACTED | H-03 |
| CRYPTO-004 | Truthful capture declaration | PDF p.38,145 (E-21) | Mandatory | Both | PRD-06 | capture audit | log | EXTRACTED | H-06 |
| CRYPTO-005 | No false capture claim | PDF p.145 (E-22) | Mandatory | Police | PRD-06 | false-claim audit | log | EXTRACTED | H-06 |
| CRYPTO-006 | Signed Step-0 hardware declaration | PDF p.55,145 (E-24) | Mandatory | Both | PRD-06 | Step-0 signature check | declaration JSON | EXTRACTED | H-08 |
| CRYPTO-007 | Mutual log audit at game end | PDF p.55,147 (E-36) | Mandatory | Both | PRD-06/07 | audit-flow test | audit record | EXTRACTED | — |
| CRYPTO-008 | 4-step order; nonce hidden until final audit | PDF p.50–52 | Mandatory | Both | PRD-06 | sequence test | protocol log | EXTRACTED | H-03 |
| CRYPTO-009 | Canonical JSON hashing; full sealed record | PDF p.50,53 | Mandatory | Both | PRD-06 | byte-identity test | canonical bytes | REVIEW REQUIRED | exact log fields → Stage 1C |
| CRYPTO-010 | Cryptographic RNG for nonce | PDF p.52,53 | Optional (SHOULD) | Both | PRD-06 | code review | source | EXTRACTED | — |
| CRYPTO-011 | Lock LLM token record at Step-0 | PDF p.56 | Mandatory | Both | PRD-06 | field signature | declaration JSON | EXTRACTED | — |
| STATE-001 | Orchestrator single gateway | PDF p.78,143 (E-3) | Mandatory | Both | Architecture | review | module graph | EXTRACTED | H-10 |
| STATE-002 | Strict state machine | PDF p.78,143 (E-4) | Mandatory | Both | Architecture | FSM tests | transition table | EXTRACTED | H-10 |
| STATE-003 | Reject illegal transitions | PDF p.79–80,143 (E-5) | Mandatory | Both | Architecture | illegal-transition test | FSM logs | EXTRACTED | H-10 |
| STATE-004 | Deadline Tracker (expiry → retry/technical-loss) | PDF p.81,143 (E-6) | Mandatory | Both | Architecture | timeout-injection | deadline logs | CONFLICT | C-02 (App F 30/60s) |
| STATE-005 | Watchdog (heartbeat → shutdown + persist) | PDF p.81–83,143 (E-7) | Mandatory | Both | Architecture | heartbeat-loss test | watchdog logs | CONFLICT | C-02 |
| STRAT-001 | Separate strategy module in PeerRuntime | PDF p.58,59 | Mandatory | Both | PRD-03 | integration test | boundary | EXTRACTED | — |
| STRAT-002 | Spatial decision fully algorithmic | PDF p.57,66,68 | Mandatory | Both | PRD-03 | code review | source | EXTRACTED | — |
| STRAT-003 | Policy = heuristics/own/RL (equal) | PDF p.60–61 | Optional (MAY) | Both | PRD-03 | n/a | README §3 | EXTRACTED | — |
| LLM-001 | Don't delegate move to LLM | PDF p.65–66,146 (E-25) | Optional (SHOULD) | Both | PRD-04 | code review | source | EXTRACTED | only SHOULD in App E |
| LLM-002 | Free natural-language hints only | PDF p.146 (E-26) | Mandatory | Both | PRD-04 | format audit | transcript | EXTRACTED | H-15 |
| LLM-003 | No numeric-position protocol | PDF p.146 (E-27) | Mandatory | Both | PRD-04 | content audit | transcript | EXTRACTED | H-15 |
| LLM-004 | Hint word limit (15) | PDF p.67,152 | Mandatory | Both | PRD-04 | word-count test | transcript | EXTRACTED | H-15 |
| LLM-005 | LLM-move tactic only by mutual agreement | PDF p.66 | Optional (MAY) | Both | PRD-04 | agreement + legality guard | negotiation log | EXTRACTED | C-03 (resolved) |
| GUI-001 | Local truth only in live UI | PDF p.70–71,143 (E-8) | Mandatory | Both | PRD-07 | content audit | screenshot | EXTRACTED | — |
| GUI-002 | No full objective board in UI | PDF p.71,143 (E-9) | Mandatory | Both | PRD-07 | UI audit | screenshot | EXTRACTED | — |
| GUI-003 | Belief heatmap + turn banner; screenshots | PDF p.71–72,97,136 | Mandatory | Both | PRD-07 | screenshot presence | README image | EXTRACTED | H-14 |
| REPLAY-001 | Build Replay Viewer | PDF p.72,145 (E-20) | Mandatory | Both | PRD-07 | presence + run | Replay app | EXTRACTED | H-07 |
| REPLAY-002 | Per-step SHA-256 verify (Verified OK / TAMPERED→DQ) | PDF p.72–75 | Mandatory | Both | PRD-07 | tamper e2e test | screenshot | EXTRACTED | H-03/H-07 |
| LEAGUE-001 | Min games vs different teams (≥2) | PDF p.86,147,154 (E-31) | Mandatory | League | PRD-05 | game-count check | result JSONs | EXTRACTED | H-11 |
| LEAGUE-002 | Agree result + separate reports (else 0 both) | PDF p.94,147 (E-35) | Mandatory | League | PRD-07 | reconciliation | two result JSONs | EXTRACTED | H-04 |
| LEAGUE-003 | Declare games-played at start | PDF p.86,147 (E-37) | Mandatory | League | PRD-05 | declaration audit | declaration JSON | EXTRACTED | H-11 |
| LEAGUE-004 | No false game-count | PDF p.86,148 (E-38) | Mandatory | League | PRD-05 | cross-check | declarations | EXTRACTED | H-11 |
| LEAGUE-005 | One counted game/opponent; warm-ups ok | PDF p.86,149 (E-52) | Mandatory | League | PRD-05 | uniqueness check | result set | EXTRACTED | H-11 |
| LEAGUE-006 | Tie rule → tie score each | PDF p.87,154 | Mandatory | League | PRD-05 | tie test | result JSON | EXTRACTED | — |
| LEAGUE-007 | Max games/team (≤10) | PDF p.86,154 | Mandatory | League | PRD-05 | cap check | result set | EXTRACTED | — |
| JSON-001 | Report as standard JSON | PDF p.94,147 (E-33) | Mandatory | Both | PRD-07 / Stage 1C | schema validation | result JSON | EXTRACTED | — |
| JSON-002 | JSON attachment only (no free text) | PDF p.95,147 (E-34) | Mandatory | Both | PRD-07 | attachment check | email evidence | EXTRACTED | H-04 |
| JSON-003 | Four mandatory JSON docs, naming rule | PDF p.94–95,157 | Mandatory | Both | Stage 1C | naming test | four files | REVIEW REQUIRED | C-05 closed (num_games=6 FIXED); exact JSON field names → Stage 1C |
| JSON-004 | Signed shared config constitution (canonical/hashed) | PDF p.127–128 | Mandatory | Both | PRD-06 | canonical-hash test | config + hash | EXTRACTED | — |
| REPORT-001 | Auto-report each game via Gmail | PDF p.87,147 (E-32) | Mandatory | Both | PRD-07 | send-flow test | sent-mail log | EXTRACTED | H-04 |
| REPORT-002 | Send to fixed lecturer reports address | PDF p.87,149,157 (E-51) | Mandatory | Both | PRD-07 | recipient check | headers | EXTRACTED | — |
| REPORT-003 | Respect 429, back off | PDF p.95 | Mandatory | Both | PRD-07 | 429 test | limiter logs | EXTRACTED | H-09 |
| GIT-001 | Annotated submission tag | PDF p.134,148 (E-41) | Mandatory | Submission | Submission | tag check | tag object | EXTRACTED | H-14 |
| GIT-002 | Repo contents (README/config/PRD/PLAN/TODO) | PDF p.96,149 (E-50) | Mandatory | Submission | Repo | contents check | repo tree | EXTRACTED | — |
| GIT-003 | Per-game commit hash (Step-0 + result JSON) | PDF p.56,150,157 (E-53) | Mandatory | Both | PRD-06 | field + rev check | JSON `github_commit` | EXTRACTED | H-08 |
| GIT-004 | Attach each game's config to repo | PDF p.156 | Mandatory | Submission | Repo | config presence | committed configs | EXTRACTED | — |
| GIT-005 | Repos accessible to lecturer | PDF p.95,133 | Mandatory | Submission | Repo | access check | share settings | EXTRACTED | — |
| SEC-001 | DOS detector (circuit breaker) | PDF p.89,146 (E-29) | Mandatory | Both | PRD-07 | anomaly test | gatekeeper logs | EXTRACTED | H-05/H-09 |
| SEC-002 | Send-only Gmail permission | PDF p.146,123 (E-30) | Mandatory | Both | PRD-07 | scope check | OAuth config | EXTRACTED | H-05 |
| SEC-003 | Never push secrets to repo | PDF p.135,148 (E-39) | Mandatory | Both | Repo/CI | secret-scan | clean history | EXTRACTED | H-05 |
| SEC-004 | Secret files in `.gitignore` | PDF p.135,148,121 (E-40) | Mandatory | Both | Repo | ignore + scan | .gitignore | EXTRACTED | H-05 |
| SEC-005 | Rotate credentials if leaked | PDF p.122,135 | Mandatory | Both | Ops | rotation proc | incident record | EXTRACTED | — |
| SEC-006 | Least-privilege `gmail.send` scope | PDF p.121,123 | Mandatory | Both | PRD-07 | scope inspection | OAuth config | EXTRACTED | H-05 |
| PERF-001 | Report total tokens in result JSON | PDF p.150,95 (E-54) | Mandatory | Both | PRD-07 | field check | result JSON | EXTRACTED | — |
| PERF-002 | Monitor/lock tokens at Step-0 | PDF p.56 | Mandatory | Both | PRD-06 | field signature | declaration JSON | EXTRACTED | — |
| PERF-003 | Stay within series token budget | PDF p.154,158 | Optional (SHOULD) | Both | PRD-04 | accounting | token ledger | EXTRACTED | — |
| DOC-001 | Academic README (6 mandatory components) | PDF p.97,134,148 (E-42) | Mandatory | Submission | README | component checklist | README+images | EXTRACTED | H-14 |
| DOC-002 | Self-score code quality only | PDF p.114,150 (E-55) | Mandatory | Submission | Submission | form review | self-score | EXTRACTED | — |
| DOC-003 | Seven-PRD layered build | PDF p.99–106 | Optional (SHOULD) | Both | Process | milestone checklist | 7 PRD files | EXTRACTED | — |
| SUB-001 | Moodle form PDF, unaltered fields | PDF p.114,148 (E-43) | Mandatory | Submission | Submission | form-integrity check | PDF | EXTRACTED | H-14 |
| SUB-002 | Per-member Moodle submission | PDF p.114,148 (E-44) | Mandatory | Submission | Submission | per-member check | receipts | EXTRACTED | H-14 |
| SUB-003 | 8-char group id, no spaces | PDF p.114,148 (E-45) | Mandatory | Submission | Submission | id-format check | group id | EXTRACTED | `MaRs-777` = 8 chars ✓ |
| SUB-004 | Two repos: cross-link + 2 + 4 links | PDF p.96,149 (E-49) | Mandatory | Submission | README/JSON | link-count checks | links | EXTRACTED | H-14 |
| SUB-005 | Appendix C Table 6 checklist complete | PDF p.136 | Mandatory | Submission | Submission | checklist gate | checklist | EXTRACTED | H-14 |

## Stage 1C — JSON contract references (specification-level, not implemented)

The JSON / crypto / reporting requirement families are now **CONTRACT-DEFINED** in
`docs/spec/json/` (no code). Statuses here remain specification-level
(CONTRACT-DEFINED / PROJECT-DECISION / REVIEW-REQUIRED) — **none is IMPLEMENTED or
runtime-VERIFIED**.

| Requirement family | Contract document(s) | Status |
|---|---|---|
| JSON-001..004 (four JSON docs, structure) | `json/{README,CONFIG,DECLARATION,LOG,RESULT}_CONTRACT.md`, `json/FIELD_MATRIX.md` | CONTRACT-DEFINED |
| JSON-003 exact field names | `json/*_CONTRACT.md` + `json/PROJECT_CONTRACT_DECISIONS.md` | PROJECT-DECISION (some fields REVIEW-REQUIRED) |
| CRYPTO-001/002/003/008/009 (commit-reveal, canonical hash) | `json/LOG_CONTRACT.md`, `json/CANONICALIZATION_CONTRACT.md` | CONTRACT-DEFINED |
| CRYPTO-006 / PERF-002 (Step-0, token lock) | `json/DECLARATION_CONTRACT.md`, `json/SIGNATURE_AND_HASH_PROVENANCE.md` | CONTRACT-DEFINED (Stage 1D.1 K1: **keyed authentication** `step0_auth`, HMAC-SHA256 default JDEC-013; primitive negotiable, requirement SOURCE) |
| REPLAY-002 (per-step verify) | `json/LOG_CONTRACT.md` §E | CONTRACT-DEFINED |
| REPORT-001/002, LEAGUE-002 (result report, mutual approval) | `json/RESULT_CONTRACT.md` | CONTRACT-DEFINED; `result_sha256` = SHA-256-backed mutual acknowledgement (NDEC-006); missing/contradictory ⇒ 0 both (C-09); FastMCP + signed hardware mandatory (K3) |
| GIT-003 (`github_commit`) | `json/DECLARATION_CONTRACT.md`, `json/RESULT_CONTRACT.md` | CONTRACT-DEFINED (SOURCE-EXPLICIT key) |
| GAME-006 scoring incl. technical_loss | `json/CONFIG_CONTRACT.md`, `json/RESULT_CONTRACT.md` | CONTRACT-DEFINED (technical_loss provenance C-07 preserved) |

Cross-artifact invariants: `json/CROSS_ARTIFACT_INVARIANTS.md` (INV-01…INV-15).
Project decisions: `json/PROJECT_CONTRACT_DECISIONS.md` (**JDEC-001…JDEC-015**;
JDEC-015 added in Stage 3B-FIX1 — terminal threshold admissibility).

**Current baseline (after Stage 2A-R2):** field matrix **75** rows — declaration 16,
config 39, log 9, **result 11**. *(Stage 1 originally locked at 77 rows with result 13;
Stage-2A-R2 **JDEC-014** superseded the project-defined duplication of declaration-owned
static metadata in the result, so the current matrix is 75.)* Requirements remain **91**.

**Stage 1D (interoperability lock):** the contracts were independently audited and
locked for interoperable implementation. `json/STAGE_1D_AUDIT.md` (D1–D5),
`json/PROTOCOL_TIMELINE.md`, `json/INTEROPERABILITY_NEGOTIATION.md` (NDEC-001…007),
`json/INTEROPERABILITY_BLOCKERS.md` (**0 blocking**). Key resolutions: `verdict` =
`intent` (C-08); `state` PROJECT-LOCKED (JDEC-012); `config_sha256` non-self-referential;
`game_uid` SOURCE-EXPLICIT (kept).

**Stage 1D.1 (crypto & reporting corrections):** **K1** Step-0 and **K2** the config
signature exchange are **keyed authentication with a pre-supplied key** (SOURCE-
REQUIRED — Ch 5 p.55–56, App B p.128), **not** unkeyed SHA-256 digests and **not**
invented PKI; project default HMAC-SHA256 (JDEC-013, PROJECT-CONTRACT); envelopes
`step0_auth`/`config_auth` `{auth_alg,key_id,auth_tag}`, non-self-referential,
domain-separated (NDEC-005/007; INV-14/15). **K3** the emailed result is
**self-contained** — FastMCP endpoints + cryptographically-signed hardware
declarations (`hardware_auth`) are mandatory (INV-10/12/13). **K4** the
reporting-sanction conflict (Ch 9 per-side non-credit vs App E #35 game-void/0-both)
is recorded as **C-09** with the strictest 0-both rule (INV-11). `result_sha256`
mutual approval is SHA-256-backed acknowledgement (NDEC-006). **No key material** in
any artifact. Statuses remain specification-level; **nothing IMPLEMENTED**. Maps to
CRYPTO-006 (signed Step-0), CRYPTO-001/002 (commit-reveal), LEAGUE-002/REPORT-001/002
(reporting), PERF-002 (token lock).

**Completeness (updated Stage 1B):** every MUST / MUST NOT catalog requirement
appears above (exact modality of the full catalog: MUST 76, MUST NOT 9, SHOULD 4,
MAY 2 = 91). SHOULD/MAY rows are marked "Optional". **CONFLICT rows:** GAME-007
(C-01), STATE-004, STATE-005 (C-02). **REVIEW REQUIRED rows:** CRYPTO-009 (log
fields), JSON-003 (JSON field names). GAME-006 no longer CONFLICT (C-06 resolved;
C-07 technical_loss provenance noted). JSON-003 reclassified from CONFLICT (C-05
now closed) to REVIEW REQUIRED (field names → Stage 1C). All others **EXTRACTED**.
No row is IMPLEMENTED or VERIFIED.

**Phase-2 ownership (Stage 2-CLOSE):** all **91** requirements have exactly one primary
PRD owner — PRD-01 15 · PRD-02 11 · PRD-03 3 · PRD-04 10 · PRD-05 2 · PRD-06 14 ·
PRD-07 24 · EXTERNAL/SUBMISSION 12. Unmapped 0; duplicate primary 0. See
`prd/PRD_01_07_CROSSWALK.md`. **PRD-01…07 are APPROVED — PHASE 2 LOCKED; nothing is
IMPLEMENTED or VERIFIED.**

**Phase-3/4 progress (current):** PRD-01 and PRD-02 are **IN PROGRESS** — the
deterministic domain (Stages 3A/3B) and the local turn foundation (Stage 3C) are
implemented and tested, together with the local protocol phase machine
(Stage 4A, `STATE_MACHINE.md` graph enforcement only) and its transition evidence
(Stage 4B, R7 as scoped by `PROTOCOL_TIMELINE.md` event 10 — `source_phase` +
`target_phase` only, valid by construction, phase-path replay, **no** authenticity,
persistence or artifact claim) and the local series orchestrator (Stage 4C — the
current sub-game cursor and the one cursor-owned branch; `num_games` enforced as
exactly **6, FIXED** per App F T18 #1 and C-05, with score recording still
**pending**); PRD-03…07 remain **NOT STARTED**. `FIELD_MATRIX` is unchanged at
**75** — transition evidence and the orchestrator cursor are internal application
values and define no artifact field. The **20** architecture-level ports of `API_BOUNDARIES.md` remain
**design-level only**: none is implemented, `app.ports` does not exist yet, and any
future Python port signature is a **PROJECT-CONTRACT** decision rather than a
source-mandated API (Stage 4D-R1). Port count is an architecture count and does not
affect the 91 requirements or any register. The peer-visible protocol-timeline
family inventory is **10** (Stage-4E audit restored Event 8, "Move validation";
earlier planning said 9), and PRD02-FR-044's turn cursor is **`(sub_game, step)`**
for turn-scoped messages, with the phase check receiver-side under FR-062/STATE-003
(Stage 4E-R1). Both are architecture/PRD-consistency counts and change no
requirement, modality, Appendix-E/F value or register entry. Stage 4F-R1 adds `app.protocol_values` as the
shared home for protocol semantic primitives and records the internal digest
representation (lowercase 64-hex PROJECT-CONTRACT), the closed `Verified OK`/`TAMPERED`
audit verdict, and the `mutual_agreement` bool correction — all internal contract
consistency, changing no requirement, register or FIELD_MATRIX count. Stage-4F value-blocker readiness accounts at
category level as **2 ready / 6 deferred / 1 reconciled = 9**; the six deferred
categories expand to nine unresolved sub-items. Stage 4F implemented exactly the
two ready ones in `app.protocol_values` — `Sha256Digest` (lowercase 64-hex
PROJECT-CONTRACT, no hashing) and `FinalAuditVerdict` (`Verified OK`/`TAMPERED`) —
with `InvalidDigestError(ValueError)` as a supporting error, not a third value.
No requirement, register or FIELD_MATRIX count is affected.

**Stage 4E-R2 (peer message runtime contract readiness).** Documentation/design
only. The `app.peer_messages` module row now permits the pure stdlib
value-definition primitives (`typing`, `dataclasses`), immutable `domain` value
types and `app.protocol_values` at runtime use; `enum` is withheld because no
peer message defines a vocabulary of its own. All **10** peer-visible families
were re-audited against ten readiness criteria: **1 READY** (Commitment =
turn cursor + `Sha256Digest`, per PROTOCOL_TIMELINE event 5's "`H_commit` only"
plus the cursor independently required by **PRD02-FR-044** and **PRD06-FR-086**)
and **9 blocked**. `TurnCursor` is ready with `app.peer_messages` as its home and
remains a projection, not an owner. Requirements consulted and **unchanged**:
PRD02-FR-021/043/044/062/063, PRD01-FR-010/011/012/033/034/035/037,
PRD06-FR-060/061/063/064/065/066/067/080/081/082/083/084/086, BAR-001…005,
CRYPTO-002/008. Blockers recorded against existing contracts only —
`LOG_CONTRACT.md` §C `by_role` (Family 6), the absent barrier-placement reveal
path (Family 7), `INTEROPERABILITY_NEGOTIATION.md` NDEC-006's residual
`mutual_agreement.confirmed` object form and the post-exchange timing of the bool
(Family 14), and unfrozen association shapes (Families 11, 12). `docs/spec/**`
was not edited. Requirements remain **91** (76/9/4/2); Appendix E **55**;
Appendix F **32 = 14/9/9**; FIELD_MATRIX **75 = 16/39/9/11**; JDEC **15**; NDEC
**7**; INV **15**; C-01…C-10; architecture ports **20**; `ProtocolPhase`
definitions **1**; peer-visible families **10**; PRD-02 requirement IDs **87**;
result fields **11**. No new source-level requirement.

**Stage 4E-R2-FIX1 (current result-agreement contract + construction errors).**
Documentation only. **NDEC-006** was corrected from the withdrawn
`mutual_agreement.sha256` / `mutual_agreement.confirmed` nested object form to
the live model — a separate top-level `result_sha256` and a separate
`mutual_agreement` bool set only after the two digests compare equal — with an
explicit scope limit recording that NDEC-006 freezes a **record** shape, not the
Event-14 **message** shape. **NDEC IDs remain NDEC-001…NDEC-007 (7)**; no
NDEC-008, JDEC-016, INV-16 or C-11 was created. `RESULT_CONTRACT.md`,
`FIELD_MATRIX.md`, `CROSS_ARTIFACT_INVARIANTS.md` (INV-11) and
`CONFLICT_REGISTER.md` (C-09) are unchanged; result artifact fields remain
**11**. A mechanical sweep found the same object form still asserted by three
**current** PRD requirements — **PRD06-FR-142**, **PRD07-FR-085** and
**PRD07-FR-190**, with FR-085 contradicting **PRD07-FR-080** in its own table —
which this stage was not authorized to edit; they are reported and tracked, and
the stage therefore closes PARTIAL. No requirement text, modality or ownership
changes: the affected IDs are recorded as **needing a future consistency
correction**, not as new or reclassified requirements. The future static
construction contract for `TurnCursor` and `Commitment` (built-in `ValueError`,
zero supporting error types, no coercion) introduces no requirement and no
register entry. Requirements remain **91** (76/9/4/2); Appendix E **55**;
Appendix F **32 = 14/9/9**; FIELD_MATRIX **75 = 16/39/9/11**; JDEC **15**; NDEC
**7**; INV **15**; C-01…C-10; architecture ports **20**; `ProtocolPhase`
definitions **1**; peer-visible families **10** (**1 READY / 9 BLOCKED**);
PRD-02 requirement IDs **87**; result fields **11**.

**Stage 4E-R2-FIX2 (PRD propagation + constant dependency).** Documentation
only. Three active requirements were corrected **in place** to the already-approved
separate-field result-agreement model: **PRD06-FR-142** (core exclusion list),
**PRD07-FR-085** (digest stored as a separate top-level field, resolving its
contradiction with **PRD07-FR-080**) and **PRD07-FR-190** (both reports carry the
same `result_sha256` and record `mutual_agreement = true` separately once the
comparison establishes equality). **PRD-06 and PRD-07 requirement-ID counts, IDs,
ordering, modality, ownership and provenance are unchanged**; nothing was added,
deleted, renumbered or reclassified, and no acceptance criterion was created to
carry the correction. PRD status is unchanged (**APPROVED — PHASE 2 LOCKED**).
Each corrected row is explicitly a **record** requirement and freezes no Event-14
message multiplicity, so **Family 14 remains BLOCKED-BY-PAYLOAD-SHAPE**. The
`app.peer_messages` module row was narrowly widened to permit read-only use of the
globally-FIXED `domain` constants `FIRST_SUB_GAME` and `FIXED_NUM_GAMES`; this adds
no layer edge (`app.orchestrator` already imports `FIRST_SUB_GAME` at runtime) and
creates no second numeric authority (`FIXED_NUM_GAMES: Final[int] = 6` is the only
`= 6` series length in the source tree). `RESULT_CONTRACT.md`, `FIELD_MATRIX.md`,
`PROJECT_CONTRACT_DECISIONS.md`, `CROSS_ARTIFACT_INVARIANTS.md` (INV-11),
`CONFLICT_REGISTER.md` (C-09) and the FIX1 change to
`INTEROPERABILITY_NEGOTIATION.md` are all unchanged. Requirements remain **91**
(76/9/4/2); Appendix E **55**; Appendix F **32 = 14/9/9**; FIELD_MATRIX
**75 = 16/39/9/11**; JDEC **15**; NDEC **7**; INV **15**; C-01…C-10; architecture
ports **20**; `ProtocolPhase` definitions **1**; peer-visible families **10**
(**1 READY / 9 BLOCKED**); PRD-02 requirement IDs **87**; result fields **11**.

**Stage 4E — RESUME (TurnCursor + Commitment).** The one peer-visible family
Stage 4E-R2 proved ready is now implemented in `app.peer_messages`, together with
its supporting `TurnCursor` contract: exactly two classes, **0** supporting error
types, and 73 targeted tests per repository. `TurnCursor` implements the PRD-02 §8
turn identity `(sub_game, step)` traced to **PRD02-FR-044/FR-063**, with phase
admissibility left to **PRD02-FR-021/FR-062** (STATE-003) and no phase field;
its sub-game bound reads the App-F-FIXED `num_games` contract through
`domain.config_model`, and `step` carries no ceiling because `max_moves` is
per-sub-game locked configuration. `Commitment` implements the Event-5 payload
(`PROTOCOL_TIMELINE.md`: "`H_commit` only") plus that independently-required
cursor, consistent with **PRD06-FR-061/FR-067/FR-081/FR-086** — it stores an
already-validated `Sha256Digest`, performs no hashing, and carries none of the
sealed-record fields of **PRD06-FR-060**. **No requirement was added, removed,
reclassified or re-owned**, and no register entry was created. Nine peer-visible
families remain BLOCKED and **Stage 4E as a whole is not complete**. Requirements
remain **91** (76/9/4/2); Appendix E **55**; Appendix F **32 = 14/9/9**;
FIELD_MATRIX **75 = 16/39/9/11**; JDEC **15**; NDEC **7**; INV **15**;
C-01…C-10; architecture ports **20**; `ProtocolPhase` definitions **1**;
peer-visible families **10**; PRD-02 requirement IDs **87**; result fields **11**;
PRD-06 IDs **129**; PRD-07 IDs **140**.

**Stage 4E-R3 (Acknowledgement + Reveal reconciliation).** Documentation/contract
only. Re-derived from the authoritative book: Ch 5 §5.3.2 (p.51) for the
acknowledgement, Ch 5 §5.3.1 (p.51) for the sealed `Move`, Figure 6 (p.52) for the
exchange, and Ch 3 §3.4 (p.37) + Iron Rules (p.38) for the barrier action and its
truthful exact-location declaration. **Acknowledgement is READY-TO-IMPLEMENT** as
`cursor` + `h_commit`, consistent with **PRD06-FR-082/FR-083** and
**PRD02-FR-044/FR-063**; `LOG_CONTRACT.md` §C `by_role` is reclassified as **local
log attribution**, proved from **ARCH-001/002** (one opponent process) and
**PRD06-FR-048** (role immutable from `CONFIG_LOCKED`). **Reveal remains BLOCKED**,
reclassified to **BLOCKED-BY-VALUE-REPRESENTATION**: the source resolves that a
police barrier placement travels in the ordinary `move` action slot bound by the
same `H_commit` — consistent with **BAR-001/BAR-002**, **PRD01-FR-010/FR-035** and
**PRD06-FR-060/FR-084** — but no shared action semantic type has a reachable home
and the sealed `move` representation is unfrozen. Contracts corrected in place:
`LOG_CONTRACT.md` (§B/§C/§D rows + REVIEW-REQUIRED totals), `NDEC-001` (narrow
amendment, **NDEC count still 7**) and one `PROTOCOL_TIMELINE.md` conclusion line.
**No requirement was added, removed, reclassified or re-owned; no JDEC-016,
NDEC-008, INV-16 or C-11 was created.** Peer-visible families remain **10** — no
eleventh barrier family. Requirements remain **91** (76/9/4/2); Appendix E **55**;
Appendix F **32 = 14/9/9**; FIELD_MATRIX **75 = 16/39/9/11**; JDEC **15**; NDEC
**7**; INV **15**; C-01…C-10; ports **20**; `ProtocolPhase` **1**; PRD-02 IDs
**87**; result fields **11**; PRD-06 IDs **129**; PRD-07 IDs **140**.

**Stage 4E — RESUME 2 (Acknowledgement foundation).** Implementation of the
contract D27 had already frozen; **no contract was re-derived and none changed**.
`Acknowledgement` implements **PRD06-FR-082** (binding receipt of a *specific*
`H_commit` for a *specific* `(sub_game, step)`) over the cursor required by
**PRD02-FR-044/FR-063**, reusing the `Sha256Digest` value from Stage 4F and the
`TurnCursor` from the previous slice — so **0** new supporting error classes and
**0** new dependencies. `LOG_CONTRACT.md` §C `by_role` stays **local log
attribution**, derived from the emitted/received direction plus the role frozen at
`CONFIG_LOCKED` (**ARCH-001/002**, **PRD06-FR-048**) and never transmitted;
`ack_of_step` stays the *persisted* name of `cursor.step`, not a second message
field; and no `accepted`/`ok` status exists, the reference FastMCP `{"accepted": …}`
snippet remaining **NON-BINDING**. `Commitment` and `TurnCursor` are byte-unchanged.
**Reveal remains BLOCKED-BY-VALUE-REPRESENTATION** — its two blockers are carried
forward to Stage 4E-R4. Peer-visible families remain **10**, now **2 implemented**
(Commitment, Acknowledgement) and **8 blocked**; **Stage 4E as a whole is NOT
COMPLETE**. One authorized regression-maintenance line in
`tests/app/test_peer_messages.py` replaced the now-implemented `Acknowledgement`
with the still-blocked `ResultAgreement` in a blocked-family absence assertion,
preserving the assertion count and all coverage. **No requirement was added,
removed, reclassified or re-owned; no JDEC-016, NDEC-008, INV-16 or C-11 was
created.** Requirements remain **91** (76/9/4/2); Appendix E **55**; Appendix F
**32 = 14/9/9**; FIELD_MATRIX **75 = 16/39/9/11**; JDEC **15**; NDEC **7**; INV
**15**; C-01…C-10; ports **20**; `ProtocolPhase` **1**; PRD-02 IDs **87**; result
fields **11**; PRD-06 IDs **129**; PRD-07 IDs **140**; timeline events **15**;
`num_games` **6 FIXED**.

**Stage 4E-R4 (shared physical action + canonical `move` representation).**
Documentation / architecture / contract only; **0 Python**; **CLOSED / COMMITTED /
CI-GREEN** at Stage 4E-R4-CLOSE. Re-derived from the authoritative book: Ch 5 §5.3.1/§5.3.2 (p.51), Ch 5 p.50, Ch 3 §3.4 + Iron Rules
(p.37–38). Freezes the action's **home** (a new domain-owned `domain.actions`,
reachable by `app.turn_service`, `app.peer_messages` and the future
`protocol.commitment`, none of which `domain` imports) and its **canonical
encoding** under the unchanged sealed key `move`: a tagged, structurally-exclusive
`{kind,value}` object, consistent with **PRD01-FR-002/FR-003/FR-010** (cells as
`[row,col]`, the FIXED `move_set`, one action per turn), **PRD01-FR-035** and
**PRD06-FR-060/FR-084** (barrier placement and its exact declared cell), and
**PRD06-FR-007** (canonically sorted arrays). Contracts corrected in place:
`INTEROPERABILITY_NEGOTIATION.md` (**NDEC-001** amended — **NDEC count still 7**),
`CANONICALIZATION_CONTRACT.md` (Layer 2 note + three byte-affecting rows),
`LOG_CONTRACT.md` (§B/§D `[RR]` resolved, the Stage-4E-R3 note updated, one
illustrative reveal entry), `PROTOCOL_TIMELINE.md` (one conclusion line) and
`MODULE_BOUNDARIES.md` (a `domain.actions` row + an `app.turn_service` migration
note). The sealed set stays **exactly eight fields** — no `action`,
`barrier_target` or `action_kind` was added — and `domain.rules.Move` stays the
five-token movement vocabulary. **Reveal is reclassified
BLOCKED-BY-VALUE-REPRESENTATION → BLOCKED-BY-FUTURE-SEMANTIC-TYPE**; the other
nine families are unchanged, implemented families remain **2**, and **Stage 4E as
a whole is NOT COMPLETE**. **No requirement was added, removed, reclassified or
re-owned; no JDEC-016, NDEC-008, INV-16 or C-11 was created.** Peer-visible
families remain **10**. Requirements remain **91** (76/9/4/2); Appendix E **55**;
Appendix F **32 = 14/9/9**; FIELD_MATRIX **75 = 16/39/9/11**; JDEC **15**; NDEC
**7**; INV **15**; C-01…C-10; ports **20**; `ProtocolPhase` **1**; PRD-02 IDs
**87**; result fields **11**; PRD-06 IDs **129**; PRD-07 IDs **140**; timeline
events **15**; `num_games` **6 FIXED**.

**Stage 4E-R5 (shared physical-action foundation + `LocalTurnService` migration).**
Implementation of the design D29 froze; **CLOSED / COMMITTED / CI-GREEN** at Stage
4E-R5-CLOSE. `domain.actions` now holds the only `ActionKind`, `MoveAction`,
`BarrierAction`, `PhysicalAction` and `InvalidPhysicalActionError`, satisfying
**PRD01-FR-003** (the FIXED `move_set` stays the movement vocabulary and gains no
barrier token), **PRD01-FR-010** (one action per turn, made structural by an
exclusive union), **PRD01-FR-002** (the barrier binds an exact `[row, col]`
`Position`) and **PRD01-FR-011/FR-012** (validate strictly before effect; state
byte-identical on rejection). Legality stays where **PRD-01 §17** and the LIVE
rules put it: bounds, role, the thief prohibition, adjacency, occupancy and quota
are never checked in a value constructor. Malformed *construction* raises
`InvalidPhysicalActionError(DomainError)` while message composition keeps the
built-in `ValueError`, an intentional split by layer ownership that creates no new
error class. `app/peer_messages.py` is **byte-unchanged**; `domain.rules.Move`
remains exactly five tokens. **Reveal is reclassified BLOCKED-BY-FUTURE-SEMANTIC-TYPE
→ READY-TO-IMPLEMENT** (**PRD06-FR-082/FR-083**, **PRD02-FR-044/FR-063** already
satisfied by `TurnCursor`); the other nine families are unchanged, giving **2
implemented, 1 ready, 7 blocked** of **10**, and **Stage 4E as a whole is NOT
COMPLETE**. **No requirement was added, removed, reclassified or re-owned; no
JDEC-016, NDEC-008, INV-16 or C-11 was created.** Requirements remain **91**
(76/9/4/2); Appendix E **55**; Appendix F **32 = 14/9/9**; FIELD_MATRIX **75 =
16/39/9/11**; JDEC **15**; NDEC **7**; INV **15**; C-01…C-10; ports **20**;
`ProtocolPhase` **1**; PRD-02 IDs **87**; result fields **11**; PRD-06 IDs **129**;
PRD-07 IDs **140**; timeline events **15**; `num_games` **6 FIXED**.

**Stage 4E — RESUME 3 (Reveal foundation).** Implementation of the shape R4 froze
over the value type R5 supplied; **CLOSED / COMMITTED / CI-GREEN** at Stage
4E-RESUME3-CLOSE. `Reveal(cursor, action, hint)` satisfies the ordinary-reveal
content of **Ch 5 §5.3.2** (the action plus the verbal sentence, nonce withheld)
over the cursor required by **PRD02-FR-044/FR-063**, carrying the physical action
of **PRD01-FR-010** including a police placement's exact cell
(**PRD01-FR-002/FR-035**, **PRD06-FR-060/FR-084**). Structural validation only:
exact `(MoveAction, BarrierAction)` membership with subclass rejection and no
coercion, exact `TurnCursor`, exact `str`; malformed composition raises the
built-in `ValueError` while malformed *domain* construction stays
`InvalidPhysicalActionError(DomainError)` — an intentional split by layer that
adds no error class. `hint_max_words` (**PRD06**) stays LIVE, so empty,
whitespace and very long hints are structurally accepted. No canonicalization,
hashing or live protocol validation; `domain.actions`, `app.turn_service` and
`domain.rules.Move` are byte-unchanged, and `Commitment`, `Acknowledgement` and
`TurnCursor` are executable-AST identical to the parent after prose-only
compression. `app/peer_messages.py` is at **150/150 LOC** — compliant, but no
further family may be added there until Stage 4E-R6 reconciles module
organization. Peer-visible families remain **10**, now **3 implemented
(Commitment, Acknowledgement, Reveal) and 7 blocked**; no family was reclassified
by this slice, and **Stage 4E as a whole is NOT COMPLETE**. **No requirement was
added, removed, reclassified or re-owned; no JDEC-016, NDEC-008, INV-16 or C-11
was created.** Requirements remain **91** (76/9/4/2); Appendix E **55**; Appendix
F **32 = 14/9/9**; FIELD_MATRIX **75 = 16/39/9/11**; JDEC **15**; NDEC **7**; INV
**15**; C-01…C-10; ports **20**; `ProtocolPhase` **1**; PRD-02 IDs **87**; result
fields **11**; PRD-06 IDs **129**; PRD-07 IDs **140**; timeline events **15**;
`num_games` **6 FIXED**.

**Stage 4E-R6 (remaining turn-protocol readiness + peer-message module
organization).** Documentation / architecture / contract only; **0 Python**;
**CLOSED / COMMITTED / CI-GREEN** at Stage 4E-R6-CLOSE, including corrections
R6-FIX1 and R6-FIX2. Re-derived from the authoritative book: Ch 5 §5.3.2 + Figure 6 (p.51–52), Ch 5
§5.4 (p.55), Ch 2.2.1, Ch 6.5, Ch 7 §7.5 + Figure 10 (p.72–74), App E #14. Freezes
a four-module organization for the peer-message contracts — `app.turn_cursor`,
`app.peer_turn_messages`, `app.peer_final_messages` behind an `app.peer_messages`
façade re-exporting identity-equal classes — chosen by measured LOC and adding no
message hierarchy, enum or registry, consistent with `MODULE_BOUNDARIES.md` and the
inward dependency rule. **#11 Final nonce reveal is reclassified
BLOCKED-BY-VALUE-REPRESENTATION → READY-TO-IMPLEMENT**: it is one batched
per-side message over that side's own steps (**PRD06** commit-reveal integrity,
**PRD02-FR-044/FR-063** for the cursor), and the last gap — the nonce's structural
form — is frozen in **NDEC-001 in place** as the **PROJECT-CONTRACT** profile
`[0-9a-f]{32}` lowercase, `secrets.token_hex(16)` remaining REFERENCE-EXAMPLE.
*(Stage 4E-R6-FIX2: current v1 supports exactly one nonce representation, so
NEGOTIATED-PRE-MATCH means both peers echo that required profile before
`CONFIG_LOCKED`; a differing profile refuses counted play as a LIVE compatibility
check, never an `InvalidNonceError`, tampering verdict or invented sanction.)* *(Stage 4E-R6-FIX1 corrected the rationale: a fixed
case/length is **not** required for recomputation, since the receiver rebuilds the
record from the exact revealed string; it is kept for parser strictness,
NFC-invariance and a 128-bit entropy floor. CSPRNG production (**CRYPTO-010**) and
secrecy-until-reveal are producer/runtime duties, not structural checks.)* FIX1 also
froze the full inventory — `NonceValue` + `InvalidNonceError` in
`app.protocol_values`, `NonceRevealEntry` and `FinalNonceReveal` in
`app.peer_final_messages` — and the **sub-game batch boundary**, matching the locked
per-sub-game log artifact (**INV-02**, **JDEC-004**, **JDEC-007**). **#8 Move validation** (BLOCKED-BY-VALUE-REPRESENTATION →
**BLOCKED-BY-PAYLOAD-SHAPE**) and **#12 Final audit** (BLOCKED-BY-ASSOCIATION-SHAPE →
**BLOCKED-BY-PAYLOAD-SHAPE**) both keep their old labels only in the sense that they
remain blocked: the value-representation and association questions are answered, and
what is unfrozen for each is whether anything is **transmitted** at all — Figure 6
draws no arrow for either, and `LOG_CONTRACT.md` §E already fixes what the audit
records. `TAMPERED` (verdict) stays distinct from technical loss (sanction, p.55) and
from `FAILED` (protocol terminal). Contracts corrected in place:
`MODULE_BOUNDARIES.md` (three future module rows + an organization note),
`PROTOCOL_TIMELINE.md` (events 8 and 12 marked REVIEW-REQUIRED with the Figure-6
evidence), `INTEROPERABILITY_NEGOTIATION.md` (**NDEC-001** amended — **NDEC count
still 7**) and `LOG_CONTRACT.md` (the nonce PC default). Implemented families remain
**3**; peer-visible families remain **10**; **Stage 4E as a whole is NOT COMPLETE**.
**No requirement was added, removed, reclassified or re-owned; no JDEC-016, NDEC-008,
INV-16 or C-11 was created.** Requirements remain **91** (76/9/4/2); Appendix E **55**;
Appendix F **32 = 14/9/9**; FIELD_MATRIX **75 = 16/39/9/11**; JDEC **15**; NDEC **7**;
INV **15**; C-01…C-10; ports **20**; `ProtocolPhase` **1**; PRD-02 IDs **87**; result
fields **11**; PRD-06 IDs **129**; PRD-07 IDs **140**; timeline events **15**;
`num_games` **6 FIXED**.

**Stage 4E-R7 (peer-message module reorganization).** Pure behaviour-preserving
migration of the architecture D32 froze; **CLOSED / COMMITTED / CI-GREEN** at
Stage 4E-R7-CLOSE. No requirement, contract or family semantics changed: the
values `TurnCursor` (**PRD02-FR-044/FR-063**), `Commitment` (**PRD06-FR-086**),
`Acknowledgement` (**PRD06-FR-082**) and `Reveal` (Ch 5 §5.3.2, **PRD01-FR-010**)
were relocated **unchanged**, proved by executable-AST equivalence against the
committed parent for all five moved definitions. `app.peer_messages` is now a
façade re-exporting identity-equal class objects, so every public import path is
preserved and the three committed behaviour test modules passed **with zero
edits**. `app/__init__.py`, `app/protocol_values.py`, `app/turn_service.py`,
`domain/actions.py` and `domain/rules.py` are byte-unchanged, and the import graph
stays acyclic and inward per `DEPENDENCY_RULES.md` and `MODULE_BOUNDARIES.md`. The
former 150/150-LOC capacity blocker is removed with real headroom in every module.
**No new semantic family was implemented** — `NonceValue`, `InvalidNonceError`,
`NonceRevealEntry`, `FinalNonceReveal`, `MoveValidation` and `FinalAudit` all
remain absent from Python, and `FinalNonceReveal` stays **READY-TO-IMPLEMENT** in
contract only. Peer-visible families remain **10** — **3 implemented, 1 ready, 6
blocked** — and **Stage 4E as a whole is NOT COMPLETE**. **No requirement was
added, removed, reclassified or re-owned; no JDEC-016, NDEC-008, INV-16 or C-11
was created.** Requirements remain **91** (76/9/4/2); Appendix E **55**; Appendix F
**32 = 14/9/9**; FIELD_MATRIX **75 = 16/39/9/11**; JDEC **15**; NDEC **7**; INV
**15**; C-01…C-10; ports **20**; `ProtocolPhase` **1**; PRD-02 IDs **87**; result
fields **11**; PRD-06 IDs **129**; PRD-07 IDs **140**; timeline events **15**;
`num_games` **6 FIXED**.

**Stage 4E-R8 (final nonce reveal foundation).** Implementation of the contract
R6/FIX1/FIX2 froze; **CLOSED / COMMITTED / CI-GREEN** at Stage 4E-R8-CLOSE.
Tests-first from the exact clean committed parents, with genuine RED proved while
all four production files were byte-identical to HEAD. `NonceValue` and
`InvalidNonceError(ValueError)` implement the NDEC-001 nonce profile
(**PROJECT-CONTRACT**, exactly `[0-9a-f]{32}`, never normalised);
`NonceRevealEntry` + `FinalNonceReveal` implement `PROTOCOL_TIMELINE.md` event 11
and Figure 6's *Final Reveal: all Nonces* (**PRD06-FR-087**, Ch 5 §5.4 p.55) as
**one batched message per peer per sub-game**, associated by `TurnCursor` alone.
Representation is separated from generation: **CRYPTO-010 stays a producer runtime
obligation** and secrecy-until-final-reveal stays a protocol invariant, so neither
is a structural check and a low-entropy-looking value is valid. Completeness,
uniqueness, ordering and same-sub-game agreement remain **LIVE**. No requirement
was re-owned and no contract text changed: `docs/` diff was **0** at implementation
time. `app/turn_cursor.py`, `app/peer_turn_messages.py`, `app/turn_service.py`,
`domain/actions.py` and `domain/rules.py` are byte-unchanged. **No nonce generator,
hashing, canonicalization, commitment verification or `FinalAudit`** — `FinalAudit`,
`MoveValidation` and the mutual result agreement stay `BLOCKED-BY-PAYLOAD-SHAPE`.
Peer-visible families remain **10** — **4 implemented, 0 ready, 6 blocked** — and
**Stage 4E as a whole is NOT COMPLETE.** **No requirement was added, removed,
reclassified or re-owned; no JDEC-016, NDEC-008, INV-16 or C-11 was created.**
Requirements remain **91** (76/9/4/2); Appendix E **55**; Appendix F
**32 = 14/9/9**; FIELD_MATRIX **75 = 16/39/9/11**; JDEC **15**; NDEC **7**; INV
**15**; C-01…C-10; ports **20**; `ProtocolPhase` **1**; PRD-02 IDs **87**; result
fields **11**; PRD-06 IDs **129**; PRD-07 IDs **140**; timeline events **15**;
`num_games` **6 FIXED**.

**Stage 4E-R9 (canonical commitment codec + recompute foundation).** Attempted and
**stopped `BLOCKED-BEFORE-CODE`** at the mandatory pre-code dependency audit, with the
stop accepted by supervising review. Five of the eight sealed members were exact and
implementation-ready — `move` (**PRD01-FR-003**, NDEC-001), `hint` (**PRD06-FR-003**),
`step`, `sub_game` and `nonce` (NDEC-001) — while `role`, `state` and `intent` had no
implementation-ready representation. **0 Python, 0 tests, 0 documentation** were
produced. No requirement was added, removed, reclassified or re-owned.

**Stage 4E-R9-R1 (sealed commitment semantic prerequisites reconciliation).**
Documentation / contract / architecture only; **CLOSED / COMMITTED / CI-GREEN** at Stage
4E-R9-R1-CLOSE with **0 Python and 0 tests**. Resolves exactly the three R9 blockers and
two directly-related ambiguities, moving the sealed record from **5/8 to 8/8
contract-ready**. `intent` is frozen to the **SOURCE-REQUIRED** `truth`/`lie` vocabulary
(Ch 5 p.51 prints both words) under **PRD04-FR-016/017**; `role` to the
**PROJECT-CONTRACT** `police`/`thief` vocabulary under **NDEC-001**, with the repository
constants mapped explicitly and the PRD-01 score keys `{cop, thief}` (**PRD01-FR-070/071/072**)
recorded as a deliberately separate reporting vocabulary that is **not** edited; `state`
to the existing **JDEC-012 / NDEC-002 / PRD06-FR-068** own-known shape, tightened with
sorted duplicate-free barriers (**PRD06-FR-007**) and the `state.step`/`state.role`
equality invariants the builder must enforce before hashing. Complete future semantic
contracts for `ActorRole`, `Intent` and `SealedState` are frozen in a legal
dependency-safe home, `app.sealed_record_values`, with `DEPENDENCY_RULES.md` unchanged.
Also reconciled: the stale `LOG_CONTRACT.md` REVIEW-REQUIRED text for `state`, the
`[row,col]` coordinate citation (**JDEC-012**, not JDEC-006), **`ensure_ascii=False`**
propagated from **PRD06-FR-005** into the central canonical contract and **NDEC-003**,
and the three-layer separation keeping `E-HASH-MISMATCH` / `FinalAuditVerdict.TAMPERED`
above the pure comparison primitive. `ActorRole`, `Intent` and `SealedState` are **not
peer-message families** and are **not implemented**; peer-visible families remain **10**
— **4 implemented, 0 ready, 6 blocked** — and **Stage 4E as a whole is NOT COMPLETE.**
**No requirement was added, removed, reclassified or re-owned; no JDEC-016, NDEC-008,
INV-16 or C-11 was created.** Requirements remain **91** (76/9/4/2); Appendix E **55**;
Appendix F **32 = 14/9/9**; FIELD_MATRIX **75 = 16/39/9/11**; JDEC **15**; NDEC **7**;
INV **15**; C-01…C-10; ports **20**; error IDs **20**; `ProtocolPhase` **1**; PRD-02 IDs
**87**; result fields **11**; PRD-06 IDs **129**; PRD-07 IDs **140**; timeline events
**15**; `num_games` **6 FIXED**.

**Stage 4E-R9-R2 (sealed record semantic values foundation).** Implementation of
the three semantic prerequisites Stage 4E-R9-R1 froze at contract level;
**CLOSED / COMMITTED / CI-GREEN** at Stage 4E-R9-R2-CLOSE. Tests-first from the
exact clean committed parents, with genuine `ModuleNotFoundError` RED proved
while `app/__init__.py`, `app/protocol_values.py` and `domain/board.py` were all
byte-identical to HEAD. `ActorRole` implements the **PROJECT-CONTRACT**
`police`/`thief` vocabulary (NDEC-001) and `Intent` the **SOURCE-REQUIRED**
`truth`/`lie` vocabulary (Ch 5 p.51, **PRD04-FR-016/017**); `SealedState`
implements the own-known snapshot of **JDEC-012 / NDEC-002 / PRD06-FR-068** with
sorted duplicate-free barriers (**PRD06-FR-007**) that are never silently
repaired. The runtime `ROLE`/`VALID_ROLES` constants and the PRD-01 score keys
`{cop, thief}` (**PRD01-FR-070/071/072**) are unchanged and provably distinct
from the sealed vocabulary. Structural validation only: board bounds, barrier
legality, quotas, capture and the builder's `state.step == cursor.step` /
`state.role == role` invariants all remain with their owners, and **no opponent
truth is representable**. No serialization, canonical JSON, NFC runtime, UTF-8
codec, SHA-256, recomputation, digest comparison, `FinalAudit` or `protocol/`
package was added. `app/protocol_values.py`, `app/turn_cursor.py`,
`app/peer_turn_messages.py`, `app/peer_final_messages.py`, `app/peer_messages.py`,
`app/turn_service.py`, `domain/board.py`, `domain/actions.py` and
`domain/rules.py` are byte-unchanged, and **no committed test required
maintenance**. `ActorRole`, `Intent` and `SealedState` are internal semantic
prerequisites, **not peer-message families**: peer-visible families remain **10**
— **4 implemented, 0 ready, 6 blocked** — the eight sealed members remain
contract-ready, the original R9 codec scope is now implementation-unblocked but
not started, and **Stage 4E as a whole is NOT COMPLETE.** **No requirement was
added, removed, reclassified or re-owned; no JDEC-016, NDEC-008, INV-16 or C-11
was created.** Requirements remain **91** (76/9/4/2); Appendix E **55**; Appendix
F **32 = 14/9/9**; FIELD_MATRIX **75 = 16/39/9/11**; JDEC **15**; NDEC **7**; INV
**15**; C-01…C-10; ports **20**; error IDs **20**; `ProtocolPhase` **1**; PRD-02
IDs **87**; result fields **11**; PRD-06 IDs **129**; PRD-07 IDs **140**;
timeline events **15**; `num_games` **6 FIXED**.

**Stage 4E-R9-RESUME (canonical commitment codec + recompute foundation).** The
scope the original Stage 4E-R9 correctly stopped on, resumed once 4E-R9-R1 and
4E-R9-R2 made all eight sealed members contract-ready and implemented;
**CLOSED / COMMITTED / CI-GREEN** at Stage 4E-R9-RESUME-CLOSE. Implements
**CRYPTO-009** (every operation states exactly which bytes it covers) and
**PRD06-FR-001…FR-009** in the architecture-frozen `protocol.canonical` and
`protocol.commitment`: canonical JSON with `sort_keys=True`,
`separators=(",",":")`, **`ensure_ascii=False`** (**PRD06-FR-002/005**), UTF-8
with NFC-normalised text (**PRD06-FR-003**), LF and no trailing newline
(**PRD06-FR-004**); the eight-field sealed record of **NDEC-001** with the
`state` mapping of **JDEC-012 / NDEC-002 / PRD06-FR-068** and the action mapping
of **NDEC-001 / Stage 4E-R4**; and `H_commit` as unkeyed SHA-256 into the
existing `Sha256Digest`. Barriers are emitted in the order `SealedState` fixed
(**PRD06-FR-007**) — the mapper never sorts. The builder refuses
`state.step != cursor.step` and `state.role != role` **before hashing**, a local
composition defect rather than a `TAMPERED` verdict. One `compute_commitment`
primitive serves both the initial commitment and the later recomputation from the
revealed nonce (**PRD06-FR-065**: the nonce is consumed, never generated), and
digest inequality returns a plain `bool` — `E-HASH-MISMATCH` and
`FinalAuditVerdict.TAMPERED` remain owned above this layer, as Stage 4E-R9-R1
froze. Three supervisor known-answer vectors were verified **independently, before
production existed**, by a stdlib-only one-off script that imported no project
code, and match exactly in both repositories (**PRD06-FR-009**, cross-OS
byte-identity). `app/**` and `domain/**` are byte-unchanged and **no committed
test required maintenance**. `MODULE_BOUNDARIES.md`'s `protocol.commitment`
dependency list was reconciled to include `app.turn_cursor` — documentation
reconciliation of the already-frozen builder input, not a new decision. No
peer-visible family was added: peer-visible families remain **10** — **4
implemented, 0 ready, 6 blocked** — and **Stage 4E as a whole is NOT COMPLETE.**
**No requirement was added, removed, reclassified or re-owned; no JDEC-016,
NDEC-008, INV-16 or C-11 was created.** Requirements remain **91** (76/9/4/2);
Appendix E **55**; Appendix F **32 = 14/9/9**; FIELD_MATRIX **75 = 16/39/9/11**;
JDEC **15**; NDEC **7**; INV **15**; C-01…C-10; ports **20**; error IDs **20**;
`ProtocolPhase` **1**; PRD-02 IDs **87**; result fields **11**; PRD-06 IDs
**129**; PRD-07 IDs **140**; timeline events **15**; `num_games` **6 FIXED**.
