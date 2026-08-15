# Requirements Traceability Matrix - group MaRs-777

> **Status: REVIEWED — Stage-1 baseline LOCKED (supervising review PASS); rows extend in later stages.** Seeded foundation rows (F-0xx)
> retained; catalog requirements (Stage 1A extraction) added with catalog IDs.
> Stage 1A statuses are one of: **EXTRACTED**, **REVIEW REQUIRED**, **CONFLICT**,
> **NOT APPLICABLE**. Nothing is IMPLEMENTED or VERIFIED. Full details and
> citations live in `docs/spec/REQUIREMENT_CATALOG.md`; conflicts in
> `docs/CONFLICT_REGISTER.md` (**C-01…C-14** currently; C-10 added post-lock in
> Stage 3B-FIX2 — scent state bound vs additive update; C-14 added at Stage 5-R8 —
> full scent-model agreement vs the three-scalar config). "Component" = planned PRD/area.

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
| GAME-003 | Orthogonal moves only | PDF p.37,144 (E-13) | Mandatory | Both | PRD-01 | move-legality tests | validator | EXTRACTED | H-12; 5-R8 semantic audit replays the disclosed move: illegal → `ILLEGAL_ACTION` + `TECHNICAL_LOSS` 0/0, never a hash-tamper DQ |
| GAME-004 | No diagonal moves | PDF p.37,144 (E-14) | Mandatory | Both | PRD-01 | reject-diagonal test | validator | EXTRACTED | H-12 |
| GAME-005 | Trapped thief (no legal move) = captured | PDF p.37,149 (E-47) | Mandatory | Both | PRD-01 | trap-state test | end log | EXTRACTED | Live answer `app.capture_rules`; recomputed at the semantic audit (5-R8) |
| GAME-006 | Score per scoring table | PDF p.38,154,149 (E-48) | Mandatory | Both | PRD-01 | scoring tests | result scores | EXTRACTED | C-06 label order (resolved); C-07 technical_loss 0/0 binding via Ch3/E-48, **not** App F |
| GAME-007 | Board dimensions from config (≥7×7) | PDF p.35,152 | Mandatory | Both | PRD-01 | grid-bound tests | config | CONFLICT | C-01 (resolved by App F) |
| GAME-008 | Step ceiling / survival threshold from config | PDF p.38,153 | Mandatory | Both | PRD-01 | end-of-game tests | log | EXTRACTED | — |
| GAME-009 | Movement legality is deterministic code (never LLM) | PDF p.58,66 | Mandatory | Both | PRD-03 | code path review | strategy module | EXTRACTED | H-12 |
| BAR-001 | Declare every barrier placement | PDF p.37,144 (E-15) | Mandatory | Police | PRD-01 | audit vs declared | log audit | EXTRACTED | H-06 |
| BAR-002 | No lying about barrier location | PDF p.37,144 (E-16) | Mandatory | Police | PRD-01 | log-audit cross-check | log | EXTRACTED | H-06 |
| BAR-003 | Barrier on thief's cell = capture | PDF p.37,149 (E-46) | Mandatory | Police | PRD-01 | capture-by-barrier test | end log | EXTRACTED | Live answer `app.capture_rules`; recomputed at the semantic audit (5-R8) |
| BAR-004 | Barrier placement rules (forgo move; own/adjacent; irreversible) | PDF p.37 | Mandatory | Police | PRD-01 | placement tests | validator | EXTRACTED | 5-R8 semantic audit also enforces the police-only half, which the domain cannot see: illegal placement → `ILLEGAL_ACTION` + `TECHNICAL_LOSS` 0/0 |
| BAR-005 | Barrier quota (≥14 default) | PDF p.37,153 | Mandatory | Police | PRD-01 | quota test | config | EXTRACTED | — |
| SCENT-001 | Crypto-lock scent model before series | PDF p.47,145 (E-23) | Mandatory | Both | PRD-04/06 | model-hash exchange | signed hash | EXTRACTED | H-13; **pre-game contract implemented at Stage 5-R8** — model exchanged in full, agreed by three independent comparisons, `scent_model_sha256` bound into the authenticated `ConfigLockContext`, frozen for `g01…g06` and persisted in the config artifact. See the Stage 5-R8 section, C-14 and JDEC-017. Live emission/consumption is SCENT-002 / Reveal V2, not this row. |
| SCENT-002 | Scent emission/decay per formula | PDF p.43,153 | Mandatory | Both | PRD-04 | formula unit tests | snapshots | EXTRACTED | H-13 |
| SCENT-003 | Exchange full model + numeric example, verify, lock | PDF p.47 | Mandatory | Both | PRD-04 | pre-series exchange | model hash | EXTRACTED | **Pre-series exchange, worked examples and verification implemented at Stage 5-R8**: the complete model plus both numeric examples travels on the existing `ConfigProposal`, is compared by values, canonical rendering and independently derived digest, and is then locked. Evidence: config artifact `scent_model_evidence` + `config_lock`. See C-14, JDEC-017. |
| CRYPTO-001 | SHA-256 commit-reveal | PDF p.50,145 (E-17) | Mandatory | Both | PRD-06 | conformance test | commit hashes | EXTRACTED | H-03 |
| CRYPTO-002 | Nonce secret until game end | PDF p.51,145 (E-18) | Mandatory | Both | PRD-06 | reveal-timing test | reveal order | EXTRACTED | H-03 |
| CRYPTO-003 | DQ on hash mismatch (score 0) | PDF p.55,145 (E-19) | Mandatory | Both | PRD-06/07 | tamper-injection | replay verdict | EXTRACTED | H-03 |
| CRYPTO-004 | Truthful capture declaration | PDF p.38,145 (E-21) | Mandatory | Both | PRD-06 | capture audit | log | EXTRACTED | H-06; 5-R8 semantic audit: a dishonest answer is TAMPERED / DQ (`audit.semantic`), including as the answerer's half of `FALSE_CLAIM_AFFIRMED` |
| CRYPTO-005 | No false capture claim | PDF p.145 (E-22) | Mandatory | Police | PRD-06 | false-claim audit | log | EXTRACTED | H-06; 5-R8 semantic audit: technical loss 0/0, `at_fault` recorded; if the peer affirmed it, `also_at_fault` names the claimant |
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
Project decisions: `json/PROJECT_CONTRACT_DECISIONS.md` (**JDEC-001…JDEC-018**;
JDEC-015 added in Stage 3B-FIX1 — terminal threshold admissibility).

**Baseline after Stage 2A-R2** *(superseded — see the note below)***:** field matrix **75** rows — declaration 16,
config 39, log 9, **result 11**. *(Stage 1 originally locked at 77 rows with result 13;
Stage-2A-R2 **JDEC-014** superseded the project-defined duplication of declaration-owned
static metadata in the result, so the current matrix is 75.)* Requirements remain **91**.

> **Current FIELD_MATRIX baseline (Stage 4E-R12-R1):** **74 = 15 / 39 / 9 / 11.**
> Stage 4E-R12-R1 removed the declaration `token_usage_locked` row — Appendix E #54
> and Ch 9 §9.3.3 place **actual** consumed tokens in the **result**, while the
> declaration's source-defined role is "everything that does not change during the
> game". Declaration 16 → 15; grand total 75 → 74; provenance SS 13 → 12; status
> LP 9 → 8. **Every "75 = 16/39/9/11" below is a per-stage historical record and is
> correct as of the stage it describes** — those lines are deliberately left
> unrewritten. The **91**-requirement, **55**-Appendix-E and **32 = 14/9/9**
> Appendix-F inventories are **unchanged**: FIELD_MATRIX is a project-derived row
> model, and 74 is not a source count.

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
**pending**); **PRD-03 is BASELINE-IMPLEMENTED (Stage 6B) and WIRED INTO PRODUCTION (Stage 6C-B)** - `app.sub_game_driver` calls `StrategyPort` for one whole natural sub-game, so `STRAT-001`'s separate module is now not merely present but *used*, and `GAME-009` holds in a running game rather than only in principle. — `STRAT-001` (separate strategy module) and `STRAT-002` (fully algorithmic spatial decision) are **SATISFIED** by `app.strategy_api` + `app.baseline_strategy`, and `STRAT-003` is satisfied by exercising the *own-algorithm* track, which Ch 6 §6.3.1 makes one of three equals; `GAME-009` holds absolutely, no LLM being reachable from the strategy at all. Belief, scent consumption, hints and barrier tactics remain **DEFERRED — BELIEF / COMPETITIVE STRATEGY STAGE**, and the strategy is not yet wired into a game owner. PRD-04…07 remain **NOT STARTED**. `FIELD_MATRIX` is unchanged at
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
INV **15**; C-01…C-10; ports **20**; error identities **22**; `ProtocolPhase` **1**; PRD-02 IDs
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
**15**; C-01…C-10; ports **20**; error identities **22**; `ProtocolPhase` **1**; PRD-02
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
JDEC **15**; NDEC **7**; INV **15**; C-01…C-10; ports **20**; error identities **22**;
`ProtocolPhase` **1**; PRD-02 IDs **87**; result fields **11**; PRD-06 IDs
**129**; PRD-07 IDs **140**; timeline events **15**; `num_games` **6 FIXED**.

**Stage 4E-R10 (final audit + move validation readiness).** Attempted and
**stopped `INVENTORY-CONTRADICTION` before any documentation change; 0 files
changed**, with the stop accepted by supervising review. Neither peer-visible
payload could be frozen. No requirement was added, removed, reclassified or
re-owned.

**Stage 4E-R10-R1 (final-audit inventory + audit-material exchange
reconciliation).** Documentation / architecture only; **CLOSED / COMMITTED /
CI-GREEN** at Stage 4E-R10-R1-CLOSE with **0 Python and 0 tests**. Separates
three previously-conflated things: the implemented `FinalNonceReveal` family; the
**SOURCE-REQUIRED** end-of-game audit-material / full-log disclosure (Ch 5 §5.4,
**PRD06-FR-100/101**) that lets each side reconstruct and verify the opponent's
commitments; and `FinalAuditVerdict`, which remains the **local** audit / log /
replay vocabulary owned by `infra.replay` and `LOG_CONTRACT.md` §E
(**PRD-07 REPLAY-001/002**). There is **no peer-visible `FinalAudit` verdict
family** — the source does not require one (Figure 6 draws no such arrow) and the
project declines to invent it; the source is **not** claimed to forbid it.
`ProtocolPhase.FINAL_AUDIT`, timeline event 12 and the **15**-event count all
survive, as does the TAMPERED sanction (**PRD06-FR-085/103/104**). The exact
interchange shape of the audit material is newly recorded as
**`AUDIT-EXCHANGE-PAYLOAD: BLOCKED-BY-INTEROPERABILITY-SHAPE`**, an
artifact/transport integration blocker and **not** a peer-message-family blocker.
A completed mutual audit is a **precondition to** `ResultAgreement`, which is not
the transport of a verdict and remains `BLOCKED-BY-PAYLOAD-SHAPE`.
`MoveValidation` remains `BLOCKED-BY-PAYLOAD-SHAPE`. **The derived peer-visible
family inventory is corrected 10 → 9** — **4 implemented, 0 ready, 5 blocked** —
and the official Conflict Register grows **10 → 11** with **C-11**, distinct from
the unrelated review-local label in `docs/prd/PRD_05_07_REVIEW.md`, which was not
edited. **No requirement was added, removed, reclassified or re-owned; no
JDEC-016, NDEC-008, INV-16 or C-12 was created.** Requirements remain **91**
(76/9/4/2); Appendix E **55**; Appendix F **32 = 14/9/9**; FIELD_MATRIX
**75 = 16/39/9/11**; JDEC **15**; NDEC **7**; INV **15**; **C-01…C-11**; ports
**20**; error identities **22**; `ProtocolPhase` **1**; PRD-02 IDs **87**; result fields
**11**; PRD-06 IDs **129**; PRD-07 IDs **140**; timeline events **15**;
`num_games` **6 FIXED**. **Stage 4E as a whole is NOT COMPLETE.**

**Stage 4E-R10-R2 (MoveValidation existence + payload).** Attempted and
**stopped `BLOCKED-BY-EXISTENCE-EVIDENCE` at the existence gate; 0 files
changed**, with the stop accepted by supervising review. Opponent rejection of an
illegal move is SOURCE-ENTAILED (App E #14) but the mechanism is
SOURCE-UNSPECIFIED. No requirement was added, removed, reclassified or re-owned.

**Stage 4E-R10-R3 (move-rejection inventory + transport-response
reconciliation).** Documentation / architecture only; **CLOSED / COMMITTED /
CI-GREEN** at Stage 4E-R10-R3-CLOSE with **0 Python and 0 tests** — and
**PARTIAL**: the inventory correction is complete while the transport response
shape remains blocked. By supervising **PROJECT-CONTRACT** decision the
peer-facing rejection required by **App E #14** is placed at the transport/port
response boundary rather than modelled as a standalone `app.peer_messages`
family; the source is not claimed to forbid such a message. Game legality remains
owned by `domain.rules` / `LocalTurnService` through the existing
**`GameRulesPort`** (**PRD01-FR-003/004/005**, GAME-003), and the rejection
outcome by the existing **`E-PROTO-ILLEGAL-MOVE`**, so **no new port, semantic
concept or error ID** was created. Four acceptances are now explicitly distinct —
delivery/parsing, authentication (**PRD06** keyed-auth path), protocol
phase/cursor/order, and **game legality** — and the FastMCP `receive_move`
example's `accepted` is the second, not the fourth (**PRD02-FR-034/035**,
REFERENCE-COMPATIBILITY, not book-mandated). Timeline events 8 and 9 survive with
the count still **15**. The derived peer-visible family inventory is corrected
**9 → 8** — **4 implemented, 0 ready, 4 blocked** — and the official Conflict
Register grows **11 → 12** with **C-12**, distinct from the unrelated
review-local label in `docs/prd/PRD_05_07_REVIEW.md`, which was not edited. The
exact response shape remains **`MOVE-REJECTION-TRANSPORT-SHAPE:
BLOCKED-BY-TRANSPORT-SHAPE`**, since `API_BOUNDARIES.md` and **PRD02-FR-035**
defer concrete operation signatures to Stage 2B-2C and both peer ports are async;
`AUDIT-EXCHANGE-PAYLOAD` remains blocked in its own right. **No requirement was
added, removed, reclassified or re-owned; no JDEC-016, NDEC-008, INV-16 or C-13
was created.** Requirements remain **91** (76/9/4/2); Appendix E **55**; Appendix
F **32 = 14/9/9**; FIELD_MATRIX **75 = 16/39/9/11**; JDEC **15**; NDEC **7**; INV
**15**; **C-01…C-12**; ports **20**; error identities **22**; `ProtocolPhase` **1**;
PRD-02 IDs **87**; result fields **11**; PRD-06 IDs **129**; PRD-07 IDs **140**;
timeline events **15**; `num_games` **6 FIXED**. **Stage 4E as a whole is NOT
COMPLETE.**

**Stage 4E-R11 (peer operation + transport contract reconciliation).**
Documentation / architecture only; **CLOSED / COMMITTED / CI-GREEN** at Stage
4E-R11-CLOSE with **0 Python and 0 tests** — and **PARTIAL**: the operation
contract is complete, one integration blocker resolved and the other narrowed.
Freezes `API_BOUNDARIES.md` **O1-O7** over the already-committed port set
(**PRD02-FR-032**), the semantic operation inventory (**PRD02-FR-033**), the
reference tool names as compatibility aliases (**PRD02-FR-034**, not
book-mandated) and the deferral of concrete signatures (**PRD02-FR-035**).
**O1** resolves the async/message-shape conflation using the committed
`CONCURRENCY_MODEL.md` rule that peer calls are *"per request… never
fire-and-forget for state-changing calls"*. **O2** separates a success result
from transport, parse, authentication and protocol failures, each retaining its
`ERROR_MODEL.md` identity. **O5** closes
**`MOVE-REJECTION-TRANSPORT-SHAPE` as RESOLVED-PROJECT / READY-TO-IMPLEMENT**: an
exact `bool` game-legality result on the turn operation, satisfying **App E #14**
and **PRD01-FR-003/004/005** while legality stays with `domain.rules` /
`LocalTurnService` through `GameRulesPort`, and `E-PROTO-ILLEGAL-MOVE` keeps
ownership of the rejection outcome. **O6** fixes the audit submission operation
(f) with per-sub-game cadence matching the `log_<game_id>_g<NN>.json` artifact
(**PRD06-FR-100/101**), transmits no verdict or digest (**PRD06-FR-104**), and
forbids a second audit schema. **`AUDIT-EXCHANGE-PAYLOAD`** is narrowed to
**`BLOCKED-BY-LOG-ARTIFACT-SHAPE`**: the finalized log document is classified
**LOCAL-ONLY** (D4/JDEC-007) and `LOG_CONTRACT.md` retains a REVIEW-REQUIRED item
on ack/reveal nesting, so promoting it to an interoperability payload is a
reviewed decision — `LOG_CONTRACT.md` was deliberately **not** edited. No
peer-message family, port or error ID was created; operation results and audit
material are **not** families. Peer-visible families remain **8** — **4
implemented, 0 ready, 4 blocked** — and **Stage 4E as a whole is NOT COMPLETE.**
**No requirement was added, removed, reclassified or re-owned; no JDEC-016,
NDEC-008, INV-16 or C-13 was created.** Requirements remain **91** (76/9/4/2);
Appendix E **55**; Appendix F **32 = 14/9/9**; FIELD_MATRIX **75 = 16/39/9/11**;
JDEC **15**; NDEC **7**; INV **15**; **C-01…C-12**; ports **20**; error IDs
**20**; `ProtocolPhase` **1**; PRD-02 IDs **87**; result fields **11**; PRD-06
IDs **129**; PRD-07 IDs **140**; timeline events **15**; `num_games` **6 FIXED**.

**Stage 4E-R11-R1 (log artifact interoperability + audit exchange
reconciliation).** Documentation / contract only; **CLOSED / COMMITTED /
CI-GREEN** at Stage 4E-R11-R1-CLOSE with **0 Python and 0 tests**. Resolves the
last integration blocker by reconciling the **SOURCE-REQUIRED** full-log
disclosure of Ch 5 §5.4 (**PRD06-FR-100/101**) with the historical LOCAL-ONLY log
classification. **JDEC-007 is amended in place**: logger mechanics, artifact
metadata and locally-derived verification annotations stay LOCAL, while the
finalized per-sub-game log's audit-disclosure core is SHARED/INTEROPERABLE at
final audit; key spelling and the separate-event `entries[]` nesting remain
PROJECT-CONTRACT. Audit completeness is proved against the frozen Stage 4E-R9
canonical mapping — the seven non-secret sealed members from the per-turn sealed
record, `nonce` from `audit.final_reveal[]` (CRYPTO-002 secrecy preserved), and
`H_commit` from `entries[].commit` — with **no tenth log field**, so
`FIELD_MATRIX.md` is unchanged at **75 = 16/39/9/11** with **9** log rows. The
remaining `LOG_CONTRACT.md` REVIEW-REQUIRED item (ack/reveal nesting) is
**closed**. `submit_audit` carries the exact JSON-native audit-disclosure core;
semantic equality is required and **whole-log byte identity is not**, with no
log-level hash added (**PRD06-FR-104**: evidence preserved, not transmitted).
Locally-derived verdicts — `entries[].verified`, `audit.result`,
`audit.tampered_step`, `FinalAuditVerdict` — are neither transmitted nor trusted
(**PRD-07 REPLAY-001/002** keep the verdict in the local replay path). A
CLOSE-time payload-core guard made the payload boundary deterministic: both
LOCAL-DERIVED-AUDIT and LOCAL-ARTIFACT-METADATA (`by_role`, `schema_version`) are
outside the `submit_audit` payload and create no optional wire semantics. **No
second audit schema** exists. Both integration blockers are now RESOLVED-PROJECT
and `INTEROPERABILITY_BLOCKERS.md` reads **Blocking items: None**; this changed
no family readiness. Peer-visible families remain **8** — **4 implemented, 0
ready, 4 blocked** — and **Stage 4E as a whole is NOT COMPLETE.** **No
requirement was added, removed, reclassified or re-owned; no JDEC-016, NDEC-008,
INV-16 or C-13 was created.** Requirements remain **91** (76/9/4/2); Appendix E
**55**; Appendix F **32 = 14/9/9**; FIELD_MATRIX **75 = 16/39/9/11**; JDEC
**15**; NDEC **7**; INV **15**; **C-01…C-12**; ports **20**; error identities **22**;
`ProtocolPhase` **1**; PRD-02 IDs **87**; result fields **11**; PRD-06 IDs
**129**; PRD-07 IDs **140**; timeline events **15**; `num_games` **6 FIXED**.

**Stage 4E-R12 family (Step-0 + config negotiation + config lock readiness).**
Documentation / semantic-contract only; **0 Python, 0 tests, 0 schema, 0 runtime**;
**CLOSED / COMMITTED / CI-GREEN** at Stage 4E-R12-CLOSE over **20 paths per repo**.
Six stages, recorded as they actually happened rather than as the final answer:

- **Stage 4E-R12** froze the auth vocabulary (`AuthProfile` / `KeyId` / `AuthProof`),
  resolved the **bootstrap profile paradox** (`PRD02-FR-022` verifies the Step-0
  proof in `STEP0_NEGOTIATION`, two states before `PRD02-FR-080` froze
  `AuthProfile` at `CONFIG_LOCKED`, while `PRD06-FR-122` required that profile to be
  authenticated by evidence that did not yet exist), closed the live
  `HMAC-SHA256`/`HMAC_SHA256` spelling divergence in favour of the serialized
  identifiers, defined the previously undefined `step0_core`, and derived the
  `NegotiatedConfig` model. **It also wrongly marked Step-0 READY before the proof
  was complete, and edited four tracking documents it was not authorized to touch.**
- **Stage 4E-R12-FIX** restored those four paths byte-exactly from HEAD, produced the
  implementation-level readiness proof, amended `PRD06-FR-043`/NDEC-007 so the config
  `AuthProof` covers a **`ConfigLockContext`** rather than the App-B core alone (that
  core is byte-identical across every sub-game, so it bound no sub-game and none of
  the `PRD06-FR-048` lock-frozen values), and **withdrew the Step-0 READY claim**:
  `token_usage_locked` was simultaneously Optional and, per `PRD06-FR-029`, a
  mandatory member of the authenticated core, with cardinality **1** at top level in
  a two-team document.
- **Stage 4E-R12-R1** returned to the book and proved the field was a **misplaced
  runtime datum** (Outcome B). Ch 5 §5.5 joins the token duty to the Step-0 signing
  with `במקביל` — *in parallel*, not contained; Ch 9 §9.3.3 gives the declaration the
  role of fixing *"everything that does not change during the game"* and names only
  the **agreed ceiling**; **App E #54** (MUST) and **App F Table 18 #4** place actual
  consumption in the **final report**. The field was removed, its obligation already
  carried by `sub_games[].tokens` + `total_tokens`, and **`FIELD_MATRIX.md` was
  recomputed mechanically: declaration 16 → 15, grand total 75 → 74, SS 13 → 12,
  LP 9 → 8.**
- **Stage 4E-R12-R2** corrected an **overclaim in R12-R1's own reasoning**:
  `result_sha256` gives the **finally reported** totals integrity and mutual
  agreement, but proves nothing about whether every LLM call was metered or whether
  the totals match runtime/provider-observed usage. The source's separate
  requirement — actual consumption **monitored** and **cryptographically locked** —
  therefore remains a **mandatory runtime obligation with a SOURCE-UNSPECIFIED,
  not-yet-frozen construction**: **`TOKEN-ACCOUNTING-CRYPTO-EVIDENCE:
  BLOCKED-BY-CONSTRUCTION`**, owned by PRD-06. The stale `INTEROPERABILITY_BLOCKERS`
  row was repaired, and the repository-wide **74** baseline was swept and reconciled.
- **Stage 4E-R12-R3** closed a chronology contradiction R12-R1 had created: the cap
  was authenticated at event 1 while R12's own text said it was agreed at event 2.
  **MODEL A** was adopted — not for convenience, but because `PROTOCOL_TIMELINE.md`
  event 1 had always listed the **token cap** under *Known before*, `DATA_FLOW.md`
  had always placed it **inside** the Step-0 core, and event 2's *Known before* names
  only board/scent/scoring. The sweep also caught **NDEC-005 still excluding
  `token_budget_per_series` from the core** after R12-R1 had moved it in — two live
  contracts disagreeing about core membership, now reconciled.

**Final contracts.** Step-0 core = **19 members**; `Step0DeclarationExchange(declaration,
auth)`; `AuthProfile ∈ {HMAC_SHA256, ED25519}` provisioned out of band before `BOOT`,
with incoming `auth_alg`/`key_id` **compared, never used to select their own verifier**;
plain unkeyed SHA-256 inadmissible. `ConfigProposal(sub_game, config, profiles)` with a
**complete** 35-member core, never a delta. `ConfigLockEvidence(context, auth)` over
`ConfigLockContext{game_id, game_uid, sub_game, config_sha256, profiles}`; the four config
layers stay distinct and the local `CONFIG_LOCKED` transition never acquires a serialized
field. **`token_budget_per_series` is source-NEGOTIABLE with the project lifecycle
PRE-STEP0-AGREED / SERIES-WIDE / IMMUTABLE-AFTER-STEP0** — equality-only at event 2, never
counter-proposable; the locked config's copy MUST equal the authenticated declaration cap
(`E-CONFIG-MISMATCH` ⇒ refuse counted play). **Step-0 never authenticates a value agreed
only later.**

**Peer-visible families remain 8 — 4 implemented, 3 ready, 1 blocked** —
`ResultAgreement` (`BLOCKED-BY-PAYLOAD-SHAPE`) being the sole blocked family.
**No requirement, port, error ID, peer family, Appendix-E/F row or timeline event was
added, removed or reclassified; no C-13, JDEC-016, NDEC-008 or INV-16 was created.**
Requirements remain **91** (76/9/4/2); Appendix E **55**; Appendix F **32 = 14/9/9**;
JDEC **15**; NDEC **7**; INV **15**; **C-01…C-12**; ports **20**; error identities **22**;
PRD-06 IDs **129**; timeline events **15**; `num_games` **6 FIXED**. **FIELD_MATRIX is
now 74 = 15/39/9/11** (SE 40 / SS 34; LS 20 / LP 12 / NPM 36 / LO 6; EX 0, BU 0) — a
**project-derived** row model, never a source inventory; every earlier "75 = 16/39/9/11"
in this document is a stage-stamped historical record and is correct as of its stage.
Two items are carried forward deliberately: the stale **result (13)** derivation prose
(authoritative row table has **11**), deferred to the ResultAgreement stage, and
**`TOKEN-ACCOUNTING-CRYPTO-EVIDENCE: BLOCKED-BY-CONSTRUCTION`**, which must receive its
own design + implementation stage before Stage 4 can close. **Stage 4E as a whole is NOT
COMPLETE.**

**Stage 4E-R13 family (ResultAgreement payload + result artifact).**
Documentation / semantic-contract only; **0 Python, 0 tests, 0 runtime**;
**CLOSED / COMMITTED / CI-GREEN** at Stage 4E-R13-CLOSE over **14 paths per repo**.
Four stages, recorded as they happened:

- **Stage 4E-R13** resolved the external payload-shape questions — mutual-audit
  precondition (`SERIES_COMPLETE → FINAL_AUDIT → REPORT_READY`, `FinalAuditVerdict`
  staying LOCAL), game-final identity, disagreement behaviour, artifact lifecycle,
  non-self-reference, four **named** GitHub link keys, the six-sub-game inventory,
  a deterministic timestamp-proposer rule, and the authorized repair of the stale
  `FIELD_MATRIX` **result (13)** prose to the authoritative **11** rows. **It then
  stopped PARTIAL**, because underneath the shape it found a defect the shape sat
  on: `PRD06-FR-145` requires both peers to compute the core independently, yet
  `sub_games[].tokens`, `total_tokens` and `sub_games[].github_commit` were
  **per-team** values that no frozen contract transmitted before the digest —
  meaning `E-REPORT-DISAGREE ⇒ 0 to both` would have fired on **every conforming
  match**. Recorded as `RESULT-APPROVAL-CORE-JOINT-DERIVABILITY:
  BLOCKED-BY-CORE-COMPOSITION`; the stage deliberately did **not** guess among the
  three possible readings.
- **Stage 4E-R13-R1** applied the supervising ruling: wherever a semantic is
  participant-owned the shared core carries **both** participants' values, so the
  three members became **`{group_a, group_b}` objects**; a scalar whose meaning
  depends on who emitted the report is forbidden inside the core. Per-group rather
  than combined, because the token **cap** is per group. `total_tokens.<g>` is
  **derived** as the sum of that participant's six sub-game values, so one semantic
  fact has one representation. Introduced the supporting values
  **`ResultContribution`** / **`ResultContributionEntry`** / `GitCommitSha`, replaced
  the digest-only request with one carrying the sender's contribution, and made the
  operation's successful response the receiver's locally computed **`Sha256Digest`**.
  INV-05 was refined participant-explicitly after auditing that a participant's
  played commit is **series-fixed** (Ch 5 permits change *between games*, and the
  declaration is per-game).
- **Stage 4E-R13-R2** closed a hole R13-R1 had itself opened: the new request
  carried the contribution but **excluded `timestamp`**, leaving the non-proposer
  with no channel to learn the exact string the hashed core requires. `timestamp`
  now travels in the request — beside the identity, **not** inside
  `ResultContribution`, because a jointly approved core value is not
  participant-owned evidence — with the exact type **`UtcTimestamp`**
  (`YYYY-MM-DDTHH:MM:SSZ`, 20 ASCII characters, second precision, echoed verbatim).
  The two requests were given a **deterministic order**: proposer first, non-proposer
  second. An audit correction was recorded with it — the proposer is the participant
  whose **`group_id` value is byte-wise lower**, which is **not** the `group_a`
  slot: the live example places `"MaRs-777"` in `group_a` and `"GROUP-XY"` in
  `group_b`, and `"GROUP-XY"` is the lower value.

**Final contracts.** `ResultAgreement(game_id, game_uid, declaration_ref,
timestamp, contribution)` — one game-final peer family, no `result_sha256` in the
request, no `accepted` flag. Exactly **two** semantic requests per series in fixed
order; transport retries re-send the **same immutable** request and are not
additional semantic requests. Both completion gates require **both directions**
and **equal digests** before `mutual_agreement`. `result_sha256` remains an
unkeyed, non-self-referential content-agreement digest stored outside the core.
The approval core is canonically byte-identical across peers while the physical
result files may differ only in explicitly excluded reporter-local metadata such
as `reported_by`. **C-09** is unchanged, and no peer-visible audit verdict exists.

**All eight peer-visible families are now IMPLEMENTED or READY — 4 implemented, 4
ready, 0 blocked.** `ResultContribution`, `ResultContributionEntry`,
`UtcTimestamp` and `GitCommitSha` are supporting values nested inside the family,
and the `Sha256Digest` response is an operation result, so **no ninth family** and
**no `FIELD_MATRIX` row** was created. **No requirement, port, error ID,
Appendix-E/F row or timeline event was added, removed or reclassified; no C-13,
JDEC-016, NDEC-008 or INV-16 was created.** Requirements remain **91** (76/9/4/2);
Appendix E **55**; Appendix F **32 = 14/9/9**; JDEC **15**; NDEC **7**; INV **15**;
**C-01…C-12**; ports **20**; error identities **22**; timeline events **15**;
FIELD_MATRIX **74 = 15/39/9/11** with the repaired **result (11)** prose.
**`TOKEN-ACCOUNTING-CRYPTO-EVIDENCE: BLOCKED-BY-CONSTRUCTION` is carried forward
untouched** — participant token values in the result are what the peers agree was
**reported**, never proof that every actual LLM call was metered. **Stage 4E is NOT
COMPLETE.**

**Stage 4E-R14 family (pregame peer semantic types).** **CLOSED / COMMITTED /
CI-GREEN** at Stage 4E-R14-CLOSE over **35 paths per repo** — the first Stage-4E
family to add production Python since the commitment codec. Five stages, recorded
as they happened:

- **Stage 4E-R14** stopped **BLOCKED-BEFORE-CODE with 0 files written**. Two of
  the stage's own pre-code gates fired: no authoritative `Declaration` semantic
  type existed in `src` (`grep -rn "class Declaration"` → 0 matches), and four of
  the eleven `InteropProfileSet` members — the tool-name, canonicalization,
  sealed-record and `state`-representation profiles — had **no frozen value
  vocabulary or member name**, only cross-references. Together they blocked 5 of
  the 9 target types, so the stage delivered the audit rather than a guess.
- **Stage 4E-R14-R1** closed both. `Declaration` became **one immutable type
  whose instances are the lifecycle moments** — partial producer snapshot, merged
  pre-game snapshot, final snapshot with `game_end` — with no state field, no
  phase and no `sender_id`, and the 15 declaration rows split **12 subject + 3
  `step0_auth` envelope** so the proof stays beside the subject data rather than
  inside it. Every profile vocabulary was frozen, giving **10 closed types / 17
  memberships / 16 unique tokens**, and `ConfigLockEvidence`'s profile/key_id
  equality was ruled **structural**.
- **Stage 4E-R14-R1-FIX** repaired four defects, three of them introduced by R1
  itself: `ram_gb` had been retyped `Decimal`, contradicting the frozen
  §R12-FIX-6 sentence — the faulty reasoning was *"it is inside the hashed core,
  therefore `Decimal`"*, and **hash membership does not determine a semantic
  numeric type**; the profile count read "nine closed types" when `AuthProfile`
  made it ten; `GitCommitSha`/`UtcTimestamp` were relocated to
  **`app.artifact_values`** as cross-artifact primitives; and §R12-FIX-7 still
  placed `Declaration` in `app.peer_pregame_messages`. It then **stopped** on
  `DECLARATION-HARDWARE-VRAM-TYPE`, which was typed nowhere.
- **Stage 4E-R14-R1-FIX2** froze `vram_gb = int | None` with its `gpu`-dependent
  presence rule — **PROJECT-CONTRACT, not source-mandated** — closing the last
  dependency.
- **Stage 4E-R14-R2** implemented the layer: **9 new production modules**, the
  façade extended by re-export only, and **313 new tests per repo** at **100.00%
  statement and branch coverage**, every production file **≤150 LOC**, all ten
  production paths **byte-identical** across repos and all fourteen test files
  identical modulo the package root.

**What is now implemented, stated precisely.** The pregame **semantic value
layer**: `GitCommitSha` and `UtcTimestamp` (`app.artifact_values`);
`AuthProfile`, `KeyId`, `AuthProof` (`app.auth_values`); `RepositoryLinks`,
`HardwareDeclaration`, `TeamDeclaration` (`app.team_declaration_values`);
`DeclarationTimes`, `DeclarationTeams`, `Declaration`
(`app.declaration_values`); nine profile enums plus `InteropProfileSet`
(`app.interop_profiles`); the seven config section values and `NegotiatedConfig`
(`domain.config_sections`, `domain.config_league_sections`,
`domain.negotiated_config`); and `Step0DeclarationExchange`, `ConfigProposal`,
`ConfigLockContext`, `ConfigLockEvidence` (`app.peer_pregame_messages`).

**What is NOT implemented, equally precisely.** No FastMCP, no transport, no
network, no public tunnel, no HMAC or Ed25519 computation or verification, no key
loading, no config-negotiation orchestration, no `CONFIG_LOCKED` transition, no
canonical serializer, no JSON Schema, no `ResultAgreement`, no Gmail and no
token-accounting crypto evidence. **Step-0, config negotiation and config lock
therefore remain READY, not IMPLEMENTED**: their semantic values exist, their
protocol runtime does not. The peer-family matrix is unchanged at **8 = 4
implemented / 4 ready / 0 blocked**.

**No requirement, port, error ID, Appendix-E/F row, timeline event, peer family
or FIELD_MATRIX row was added, removed or reclassified; no C-13, JDEC-016,
NDEC-008 or INV-16 was created.** Requirements remain **91** (76/9/4/2);
Appendix E **55**; Appendix F **32 = 14/9/9**; JDEC **15**; NDEC **7**; INV
**15**; **C-01…C-12**; ports **20**; error identities **22**; timeline events **15**;
FIELD_MATRIX **74 = 15/39/9/11** — every type added here is a Python value, not
an artifact row. **`TOKEN-ACCOUNTING-CRYPTO-EVIDENCE: BLOCKED-BY-CONSTRUCTION`
is carried forward untouched, and Stage 4 must not be called complete merely
because the peer-family semantic values now exist. Stage 4E is NOT COMPLETE.**

**Stage 4E-R15 (ResultAgreement semantic types).** **CLOSED / COMMITTED /
CI-GREEN** at Stage 4E-R15-CLOSE over **18 paths per repo** — a single-pass
implementation stage, the contract having been frozen by R13/R13-R1/R13-R2.

**Implemented — the semantic VALUE layer.** `app.result_values` gains
`ParticipantGitCommits` and `ParticipantTokenUsage` (the frozen two-participant
shapes the shared core holds wherever a semantic is participant-owned),
`ResultContributionEntry` (`sub_game` / `github_commit` / `tokens`) and
`ResultContribution` (`group_id` + exactly six entries).
`app.peer_final_messages` gains **`ResultAgreement`**`(game_id, game_uid,
declaration_ref, timestamp, contribution)` beside the unchanged
`NonceRevealEntry` and `FinalNonceReveal`, and `app.peer_messages` re-exports it
identity-equal. `GitCommitSha`, `UtcTimestamp` and `Sha256Digest` were reused
from their existing defining modules, never redefined. **96 new tests per repo**;
totals **1667 / 1662** at **100.00% statement and branch coverage**; every
production file ≤150 LOC; the three production files **byte-identical** across
repos and all nine touched test files identical modulo the package root.

**Three structural invariants are enforced at construction**, each because every
value it compares already sits inside the same immutable object: the six entries
must cover **1…6 exactly once in ascending order** — never sorted, deduplicated
or repaired; all six `github_commit` values must be **equal**, since a
participant's played commit is fixed for the game; and `declaration_ref` must
equal `f"declaration_{game_id}.json"`, the frozen Table-20 join, with no path
prefix, alternate extension or trimming.

**Not implemented, and deliberately so.** No `ResultAgreement` operation runtime,
no deterministic timestamp proposer, no two-request cadence, no
`RESULT_APPROVAL_CORE` construction, no `result_sha256` computation, no
`Sha256Digest` response handling or comparison, no `mutual_agreement` transition,
no FastMCP, transport, reporting, Gmail or token-accounting crypto evidence.
**`ResultAgreement` therefore remains operationally READY, not IMPLEMENTED** —
its semantic value exists, its protocol does not. The peer-family matrix is
unchanged at **8 = 4 implemented / 4 ready / 0 blocked**.

**Four Stage-4E-R7 architecture guards failed on the first run and were right to.**
They asserted that `ResultAgreement` is absent from the façade, that the
finalization module owns exactly two classes, and an exact sibling-import set —
all true only while the family was blocked. The assertions were updated to the
new truth **without being loosened**: the not-a-family list keeps
`MoveValidation`, `FinalAudit` and `Declaration`, the ownership set names the
three families it genuinely owns while still asserting support values stay out,
the import set is stated explicitly, and a new positive guard requires the façade
to expose `ResultAgreement` *and hide* its support values. That edit pushed the
layout file to 162 LOC, so it was split by semantic ownership into module-layout
and façade-surface files.

**No requirement, port, error ID, peer family, Appendix-E/F row, timeline event
or FIELD_MATRIX row was added, removed or reclassified; no C-13, JDEC-016,
NDEC-008 or INV-16 was created.** Requirements remain **91** (76/9/4/2);
Appendix E **55**; Appendix F **32 = 14/9/9**; JDEC **15**; NDEC **7**; INV
**15**; **C-01…C-12**; ports **20**; error identities **22**; timeline events **15**;
FIELD_MATRIX **74 = 15/39/9/11**. **`TOKEN-ACCOUNTING-CRYPTO-EVIDENCE:
BLOCKED-BY-CONSTRUCTION` is carried forward untouched** — contribution token
counts are what a peer *reports*, never independently verified provider
consumption. **Stage 4E is NOT COMPLETE.**

**Stage 4E-R16 (peer application protocol runtime).** **CLOSED / COMMITTED /
CI-GREEN** at Stage 4E-R16-CLOSE over **52 paths per repo** — 16 production, 27
tests, 3 contract reconciliations and 6 tracking. It took **three** stages, and
the middle one is the point: R16 implemented broadly and passed, supervising
review then found that the conditional-VRAM branch was under-proved and one
count assertion was phrased unconditionally, and **R16-FIX proved the production
code had been right all along** while repairing the proof and the wording. The
record says so rather than presenting R16 as a clean first pass.

**What now executes.** The four remaining READY families became local
application behaviour. **Step-0** projects its **19-member semantic inventory**,
constructs and verifies the keyed proof, validates participant ownership and the
equality-only token cap, merges into a **new** immutable `Declaration` and gates
completion on both directions. **Config negotiation** selects the deterministic
initial proposer — the byte-wise lower `group_id` **value**, which in the live
fixture sits in the `group_b` slot — runs the bounded cadence, validates
proposals LIVE and converges on one agreed `NegotiatedConfig` +
`InteropProfileSet`. **Config lock** projects the exact **35 members**, computes
`config_sha256`, builds and verifies authenticated `ConfigLockEvidence`, and
gates `CONFIG_LOCKED` on all four conditions by delegating to the one
authoritative transition graph. **ResultAgreement** assembles the approval core
identically on both sides, merges contributions by declared slot, derives
`total_tokens`, computes `result_sha256`, runs the deterministic
timestamp-proposer and two-request cadence, returns `Sha256Digest` responses and
decides both asymmetric completion gates. **Auth** is concrete stdlib
HMAC-SHA256 with an injected `ED25519` provider path, **no fallback**, and no
persisted or rendered key material.

**The architecture that made it testable.** `MODULE_BOUNDARIES.md` forbids `app`
from importing `protocol`, so every byte, digest and proof arrives through an
`app.ports` Protocol implemented by a `protocol` adapter. The runtimes are
therefore synchronous, deterministic, free of canonicalization and key material,
and exercised with plain fakes — and a guard asserts the rule per module from
the AST.

**The one conditional member, stated exactly.** `hardware.vram_gb` is present
exactly when `gpu` is not `false`. A **CPU-only** core serializes **18** present
leaves and a **GPU** core **19**; the inventory stays 19 either way. The key is
**omitted, never `null`** — and could not be `null`, since the canonical layer
refuses `None`, so emitting one would make a lawful CPU-only declaration
impossible to authenticate.

**The framing gap R16 found and CLOSE froze.** Every live statement wrote the
keyed construction as `context ‖ canonical(core)` and deferred the framing to
"a fixed, unambiguous framing agreed pre-match" that **no document then fixed**.
`CANONICALIZATION_CONTRACT.md` Layer 4 now freezes it byte-exactly as
`b"step0" + canonical_json_bytes(core)` and
`b"config" + canonical_json_bytes(context)` — direct concatenation, prefixes
`b"step0{"` / `b"config{"`, **no separator and no length prefix** — recorded as
**PROJECT-CONTRACT completing JDEC-013**, never as lecturer-mandated.

**Counts.** 293 R16 targeted tests; totals **1959 / 1954** at **100.00%
statement and branch coverage**; every production file ≤150 LOC; all 16
production files **byte-identical** across repos.

**Not implemented, deliberately.** No FastMCP, network transport, public
endpoint or tunnel, wire adapter, Gmail, report delivery, GUI, artifact
persistence or token-accounting crypto evidence. **At the application-runtime
level the peer-family matrix is 8 IMPLEMENTED / 0 READY / 0 BLOCKED / 8**;
**transport integration is OUTSTANDING**, and nothing here is network-,
league- or counted-match-ready.

**No register moved.** Requirements **91**; Appendix E **55**; Appendix F **32 =
14/9/9**; JDEC **15**; NDEC **7**; INV **15**; **C-01…C-12**; ports **20**;
error identities **22**; timeline events **15**; FIELD_MATRIX **74 = 15/39/9/11**. No
ninth family, no new requirement, no new conflict.
**`TOKEN-ACCOUNTING-CRYPTO-EVIDENCE: BLOCKED-BY-CONSTRUCTION`** is carried
forward untouched — R16 aggregates and agrees *reported* token numbers and
proves nothing about provider usage. **Stage 4E is NOT COMPLETE.**

**Stage 4E-R17-R1 (FastMCP transport prerequisites).** **CLOSED / COMMITTED /
CI-GREEN** at Stage 4E-R17-R1-CLOSE over **16 paths per repo** — 2 dependency,
2 current-live contracts, 6 test/probes and 6 tracking. **0 production files.**

**The sequence, recorded as it happened.** Stage 4E-R17 was authorized as a broad
transport-implementation stage and **stopped BLOCKED-BEFORE-CODE with 0 files
changed**. Both blockers were real and both were accepted by supervising review.
**`FASTMCP-DEPENDENCY: BLOCKED-BY-MISSING-DECLARED-DEPENDENCY`** — `fastmcp` and
`mcp` were absent from `pyproject.toml`, absent from `uv.lock`, unimportable in
the locked environment and not vendored; the project had **no runtime dependency
at all**. **`TRANSPORT-OPERATION-DISCRIMINATOR: BLOCKED-BY-UNFROZEN-WIRE-SHAPE`**
— three semantic variants share `negotiate`, three share `receive_turn` and two
share `submit_audit`, while `PRD02-FR-035` and `API_BOUNDARIES.md` **O7**
deliberately deferred every signature and JSON schema, so the only way to
dispatch would have been guessing which payload keys happened to be present.

**R17-R1 resolved the prerequisites.** `fastmcp==3.4.6` was provisioned with
`uv add` in both repos (resolving `mcp==1.29.0`, `pydantic==2.13.4`,
`pydantic-core==2.46.4`), the installed 3.4.6 API was audited mechanically rather
than from memory, and the wire contract was frozen in `API_BOUNDARIES.md`: one
tool argument `request` carrying **exactly** `{kind, payload}`, both required, a
**closed nine-token `kind` vocabulary** across the four tools, no heartbeat, no
alias, and `E-PROTO-MALFORMED` for an unknown token **or a valid token sent to
the wrong tool**.

**The Decimal finding is the one that mattered.** Probed against a real
Streamable HTTP server, a `Decimal`-annotated parameter handed the JSON **number**
`0.10` arrives as **`Decimal('0.1')`** — a silent lexical loss that changes
`config_sha256` and would make two honest peers refuse each other. Handed the
JSON **string** `"0.10"` it arrives as `Decimal('0.10')`. The project wire rule is
therefore **canonical decimal TEXT**, reconstructed with `Decimal(text)` directly
and never through a float; JSON floats and integers, scientific notation,
whitespace, a leading `+` and locale separators are all refused. Proved end to
end with the real project code across a real FastMCP call: **canonical config
bytes and `config_sha256` are identical before and after**
(`b9bdf822ecc143a4a283bbf3ae6cd3bcdba9da80b7c470a73dce404f9ce44bd8`). The
semantic type stays `Decimal`, the canonical bytes stay a bare JSON number, and
`FIELD_MATRIX.md` is untouched — **only the transport DTO uses text**.

**Error identity survives exactly.** A `ToolError("E-PROTO-STALE")` is observed
client-side with `str(exception) == "E-PROTO-STALE"`, with no prefix or suffix,
recoverable by three independent routes. Known failures therefore cross carrying
their **existing** identity and **never as `False`** — that value belongs to
`reveal` legality alone. Ordinary completion returns **no semantic value**
(`None`), never `accepted=true`; `result_agreement` returns `Sha256Digest` as 64
lowercase hex.

**R17-R1-FIX promoted Pydantic to direct ownership**, and the justification is
measured rather than stylistic: only a Pydantic model emits
`additionalProperties: false` and refuses an extra envelope member — a
`dataclass` and a `TypedDict` both **accept** one — so the frozen envelope is
unenforceable without it. Direct runtime dependencies are now exactly
**`fastmcp==3.4.6`** and **`pydantic==2.13.4`**; `mcp`, `pydantic-core` and
`pydantic-settings` stay transitive, and adding the direct pin moved **no**
resolved version (82 packages identical before and after; one line of
`uv.lock` changed).

**44 permanent transport probes** run against the real framework. Totals **2003 /
1998** at **100.00% statement and branch coverage**.

**No transport was implemented.** No FastMCP server or client adapter, no
`PeerTransportPort`, no production wire DTOs, no tool registration, no
timeout/watchdog wiring, no two-process harness and no network runtime — a test
asserts no `src` module imports `fastmcp` or `pydantic`. **Transport:
prerequisites CLOSED, implementation NOT STARTED.**

**No register moved.** Requirements **91**; Appendix E **55**; Appendix F **32 =
14/9/9**; JDEC **15**; NDEC **7**; INV **15**; **C-01…C-12**; ports **20**; error
IDs **20**; timeline events **15**; FIELD_MATRIX **74 = 15/39/9/11**. Peer
families remain **8** — the envelope is transport, not semantics, and no
`Step0Ack`, `ConfigAck`, `ConfigLockAck`, `ResultAck` or `AuditAck` exists. The
application-runtime matrix remains **8 IMPLEMENTED / 0 READY / 0 BLOCKED / 8**,
which describes **local application behaviour and not transport**.
**`TOKEN-ACCOUNTING-CRYPTO-EVIDENCE: BLOCKED-BY-CONSTRUCTION`** is carried
forward untouched. **Stage 4E is NOT COMPLETE.**

## Stage 4E-R17 — FastMCP peer transport (implemented, LOCAL only)

Stage 4E-R17 closed across eight passes with **53 paths per repo** (23 production,
23 tests, 1 architecture document, 6 tracking; **0** dependency, **0** CI, **0**
deletion). It created **no register-shaped row of any kind**.

**Registers, re-verified at close and unchanged.** Requirements **91** = 76/9/4/2 ·
Appendix E **55** · Appendix F **32** = 14/9/9 · **C-01…C-12** · JDEC **15** ·
NDEC **7** · INV **15** · error identities **22** · ports **20** · timeline **15** ·
**FIELD_MATRIX 74 = 15 / 39 / 9 / 11**. Peer-visible families remain **8**, and
the application-runtime matrix remains **8 IMPLEMENTED / 0 READY / 0 BLOCKED /
8 TOTAL** — that matrix describes **local application behaviour, not transport**.

**`PeerTransportPort` is not a new register entry.** It is the implementation of
the already-frozen `API_BOUNDARIES.md` architecture: the outbound
application-facing port whose adapter is the FastMCP client. Likewise
`E-REPORT-DISAGREE` covers the digest mismatch introduced in FIX2/FIX3 — a second
check reaching an **existing** identity, not a new one. The seven peer identities
(`E-PROTO-MALFORMED`, `E-PROTO-STALE`, `E-AUTH-FAILURE`, `E-CONFIG-MISMATCH`,
`E-NET-CONVENTION-MISMATCH`, `E-REPORT-DISAGREE`, `E-LOCAL-DEFECT`) are unchanged
and each round-trips through real FastMCP; `E-TRANSPORT` (delivery failure) and
`E-TIMEOUT-WATCHDOG` (local supervision) remain separate categories that are not
members of the peer mapping.

**What became executable.** The peer-visible transport contract that PRD-02
specified is now a running local server and client: four tools, nine kinds, one
`request = {kind, payload}` argument. The result-agreement completion workflow —
previously a set of semantic values and unreached helpers — is owned by
`app.result_exchange.ResultExchange`, so a genuine digest disagreement raises
`E-REPORT-DISAGREE` **in production** and neither direction is recorded complete.

**What is still not discharged.** Public network transport (PRD-05) remains
entirely unimplemented and untested: no tunnel, no external endpoint, no external
reachability evidence, no real opponent, no counted match.
**`TOKEN-ACCOUNTING-CRYPTO-EVIDENCE: BLOCKED-BY-CONSTRUCTION`** is carried forward
untouched and remains a mandatory later Stage-4 security slice. **Stage 4E is NOT
COMPLETE.**

## Stage 4E-R18-R1 — public ingress and public transport (closed at the infrastructure boundary)

Stage 4E-R18-R1 closed across eleven passes with **0 new register rows of any kind**.

**Registers, re-verified at close and unchanged.** Requirements **91** = 76/9/4/2 · Appendix E
**55** · Appendix F **32** = 14/9/9 · **C-01…C-12** · JDEC **15** · NDEC **7** · INV **15** ·
error identities **22** · ports **20** · timeline **15** · **FIELD_MATRIX 74 = 15 / 39 / 9 / 11** · peer
families **8** · application-runtime matrix **8 IMPLEMENTED / 0 READY / 0 BLOCKED / 8**.

**What became executable.** Our group's public ingress: a provider-neutral `PublicIngressPort`
with ngrok 3.39.10 as the first concrete outer adapter, bounded structured endpoint discovery,
strict publicity validation (`E-NET-NOT-PUBLIC`), three distinct endpoint identities, the exact
ten-check `PRD05-FR-021` readiness gate with a real production caller that refuses counted play,
declaration-before-authentication, `FR-015b` replacement and same-ingress recovery, `infra.settings`
and `infra.clock`, and a persistent FastMCP session on `PeerClient`.

**What is transport-proven versus application-proven.** Public crossings are verified for all nine
semantic kinds through the real ngrok route, the real FastMCP server and the real router. Behind
that boundary, **Step-0**, **ConfigProposal** and **ResultAgreement** reached real production
runtimes; **Commitment**, **Acknowledgement**, **Reveal**, **FinalNonceReveal** and
**AuditDocument** reached a test double, because those five have **no production application
runtime owner**. That distinction replaces the earlier wording, which implied production handling
for all nine.

**What is still not discharged.** The five missing application runtimes, a concrete
`PeerOperations`, the outbound peer runner for eight `send_*` operations, the `infra` composition
root required by D3/D4, BOOT and shutdown, and an executable entrypoint - all carried to **Stage 5
— Production Application Runtime Integration**. Public two-group readiness, an independent external
network and a real opponent remain **DEFERRED, NOT CANCELLED** to Stage 4E-R18-R2, which now
follows Stage 5. **`TOKEN-ACCOUNTING-CRYPTO-EVIDENCE: BLOCKED-BY-CONSTRUCTION`** is carried forward
untouched. Live ten-check readiness remains **NOT_READY**. **Stage 4 is closed at the
infrastructure / public-transport boundary only.**

### Operator runtime inputs (project implementation choice, not a source requirement)

`infra.settings` reads six environment variables - `MARS777_ROLE`, `MARS777_BIND_HOST`,
`MARS777_BIND_PORT`, `MARS777_OPPONENT_ENDPOINT` (optional), `MARS777_KEY_ID`,
`MARS777_AUTH_SECRET`. No document froze an operator vocabulary and none of these values crosses
the wire, enters a declaration or is negotiated, so the names are a project implementation choice.
Deliberately **not** settings: `group_id` (the frozen package `GROUP_CODE`, not operator-
overridable), `game_id`/`game_uid` (no process-global game identity exists in this architecture),
our **own public endpoint** (discovered from the ingress, never trusted from the environment), and
anything `NegotiatedConfig` owns (a post-lock timeout must never be operator-overridable). The
opponent endpoint is optional at BOOT and required for counted readiness. The keyed-auth secret is
**environment-only, required at BOOT, never persisted, never serialized, never logged**; the ngrok
authtoken is operator-only and never enters project settings.

## Stage 5-R8 — the scent pre-game model contract (implemented, evidenced, documented)

**Status: CLOSED / COMMITTED / CI-GREEN for the pre-game half.** Seven checkpoints
implemented what `SCENT-001` and `SCENT-003` ask for, each committed to both repositories
and green on exact-SHA CI (Ubuntu 100.00% statements and branches; Windows ≥ 99.82%).
The gap they close is recorded as **C-14** and the chosen representation is frozen as
**JDEC-017**; the recurrence conflict **C-10** is unchanged and is consumed, not restated.

**The matrix below is the audit trail** — every row is a clause of the two requirements,
its production owner and the evidence that proves it, so the chain can be checked without
reading commit history.

| Pre-game step | Requirement clause | Production owner | Evidence |
|---|---|---|---|
| Full model definition | SCENT-003 "the full emission/decay model" | `domain/scent_model.py`, `domain/scent_kernel.py`, `domain/scent_model_default.py`, `domain/scent_model_examples.py` | `tests/domain/test_scent_model.py`, `tests/protocol/test_scent_model_digest.py` (30) · scent domain suites (88) |
| Model identity | SCENT-001 "the agreed … model" is one identifiable thing | `protocol/scent_model.py` — canonical bytes + unkeyed `scent_model_sha256` | golden rendering **344 bytes**, golden digest `e587d487…7600`, asserted in both repos |
| Full model exchange | SCENT-003 "exchange … before a series" | `transport/wire_scent_model.py`, `transport/codec_scent_model.py` on the existing `ConfigProposal` | `tests/transport/test_scent_model_codec.py` + `tests/app/test_peer_pregame_messages.py` (46) |
| Concrete numeric example | SCENT-003 "with a concrete numeric example" | `ScentExample` rows executed against the real recurrence by `domain/scent_model_examples.py` | `τ=0.9, Δ=0 → 0.81` and `τ=0.9, Δ=0.9 → 0.9`; an untruthful example is refused at the boundary |
| Verify identical interpretation | SCENT-003 "verify identical interpretation" | `app/scent_agreement.py`, `app/scent_model_identity.py`, `app/config_negotiation_runtime.py` via `ConfigDigestPort` | three independent comparisons (values, rendering, derived digest); `tests/session/test_scent_model_agreement.py` group (40) |
| Cryptographic lock | SCENT-001 "cryptographically lock … before the game/series starts" | `scent_model_sha256` inside `ConfigLockContext`; `protocol/config_lock.py` keyed proof unchanged | crypto-lock group (74), including a valid proof over a different model still refused |
| Series freeze | SCENT-001 "before the … series starts" for all six sub-games | `app/series_scent_freeze.py`, `app/pregame_session_runtime.py` | series-freeze group (23) — `g01` establishes, `g02…g06` must match, bilateral mid-series switch refused before play |
| Artifact evidence | SCENT-001 evidence "signed scent-model hash"; SCENT-003 evidence "model+example hash" | `artifact_documents.py`, `transport/wire_artifacts.py`, `transport/codec_artifacts.py`, `artifact_verification.py` | artifact-evidence group (36): `config_<game_id>_g<NN>.json` carries the actual model, its digest, the lock context and the safe auth proof; read-back verifies both chains |

**Not closed by the above, and not claimed:** live `ScentEmission` during gameplay,
delivery or consumption of the opponent's scent, `Reveal` V2 (`Reveal` remains V1), a live
scent transcript, and a semantic audit of emissions. Those belong to **Reveal V2 / live
distributed scent** and to a later scent-audit surface. `SCENT-002` (the emission/decay
computation itself) has its domain implementation and its own tests, and is **not** part of
this closure statement.

**Register effect.** `C-01…C-14` and `JDEC-001…JDEC-017`. Requirements remain **91**
(76/9/4/2) — no requirement id was added, removed, reworded or re-modalised, and the Status
column keeps its Stage-1A vocabulary throughout (see the note below).

**Why no row says IMPLEMENTED.** This matrix has never used an implementation status: its
header freezes the Stage-1A vocabulary (`EXTRACTED` / `REVIEW REQUIRED` / `CONFLICT` /
`NOT APPLICABLE`) and every implemented requirement in this project — `ARCH-001`,
`CRYPTO-001`, `GAME-003` and the rest — still reads `EXTRACTED` with its implementation
recorded in the Notes column and in a stage section such as this one. Introducing a closure
status for two rows alone would make the column mean two different things, so the scent rows
follow the established practice instead.
