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
