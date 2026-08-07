# Requirement Catalog — group MaRs-777

**Status: REVIEWED — Stage 1B supervising review PASS. Approved specification
baseline (input to Stage 1C). Implementation remains prohibited (NOT STARTED); the
four JSON contracts were reviewed and LOCKED (Stage 1C/1D/1D.1). Modality counts
were approved: MUST 76, MUST NOT 9, SHOULD 4, MAY 2 = 91.**

Source-grounded requirements extracted from the **entire** book v3.0.0 (not only
Appendices E/F). One independently-testable requirement per ID. Modality per
`AUTHORITY_RULES.md` (MUST/MUST NOT/SHOULD/MAY/INFORMATIONAL). Scope: BOTH /
POLICE / THIEF / LEAGUE / SUBMISSION. Sanctions are recorded **only** where the
book states one. Verification describes how we can later prove compliance and
does not change the requirement. Citation format: `PDF p.X / book p.Y`. This
repo is **POLICE**; POLICE-scoped rows are primary, BOTH rows apply equally.

Column key: **Mod** = modality · **E** = Appendix E entry · **F** = Appendix F
ref · **Conf** = conflict id in `CONFLICT_REGISTER.md` (— = none). "Verify" and
"Evidence" are planned (Stage 1A does not implement).

---

## ARCH — architecture / peer isolation / P2P

| ID | Normalized requirement | Mod | Scope | Primary source | E | F | Verify (planned) | Evidence (planned) | Sanction | Conf |
|---|---|---|---|---|---|---|---|---|---|---|
| ARCH-001 | Run police and thief as two completely separate OS processes. | MUST | BOTH | PDF p.31,142 / book 15,126 | E-1 | — | process audit; two PIDs, separate entry points | process/launch logs | Total failure; breaks Zero-Trust | — |
| ARCH-002 | Never share memory, live-state modules, or variables between the two sides. | MUST NOT | BOTH | PDF p.31,143 / book 15,127 | E-2 | — | static import graph; no shared mutable module | isolation report | Immediate DQ for info leakage | — |
| ARCH-003 | Keep police and thief under separate config directories (`config/police/` vs `config/thief/`). | MUST | BOTH | PDF p.31 / book 15 | E-1(supp) | — | filesystem layout check | repo tree | (as E-1/E-2) | — |
| ARCH-004 | Each agent is simultaneously a FastMCP **server** (exposes `@mcp.tool`) and a **client** (calls the opponent's tools); no strong/weak side. | MUST | BOTH | PDF p.25–28 / book 9–12 | — | — | protocol test: both roles active | MCP handshake log | — | — |
| ARCH-005 | When the shared `config/game.json` exists, its values **overlay/override** matching keys in the private `config/game.toml`; the private file can never weaken a signed term. | MUST | BOTH | PDF p.126,132 / book 110,116 | — | F§2 | overlay unit test | config-load evidence | — | — |

## NET — FastMCP / networking / public tunnel

| ID | Requirement | Mod | Scope | Source | E | F | Verify | Evidence | Sanction | Conf |
|---|---|---|---|---|---|---|---|---|---|---|
| NET-001 | Expose the local FastMCP server to the public internet via a tunnelling tool (e.g., ngrok / Localtonet); localhost only for early dev. | MUST | BOTH | PDF p.29,144 / book 13,128 | E-10 | — | public URL reachability test | tunnel URL in declaration JSON | Cannot compete in league | — |
| NET-002 | Implement a token-bucket rate-limiter (`tokens←min(C,tokens+r·Δt)`, allow iff tokens≥1) on outgoing Gmail reports. | MUST | BOTH | PDF p.89–91,146 / book 73–75,130 | E-28 | Tbl 19 | rate test under burst | limiter logs | Prevents 429 that paralyses reporting | — |
| NET-003 | Communicate over the negotiated **public** transport in counted league games (not localhost). | MUST | BOTH | PDF p.88,113 / book 72,97 | E-10(supp) | Tbl 19 timeouts | public-round test | game transcript | — | — |
| NET-004 | Use MCP (via FastMCP) as the agent-to-agent protocol; it may not be replaced. | MUST | BOTH | PDF p.26 / book 10 | — | — | protocol inspection | MCP tool schema | — | — |

## GAME — board / movement / turn mechanics

| ID | Requirement | Mod | Scope | Source | E | F | Verify | Evidence | Sanction | Conf |
|---|---|---|---|---|---|---|---|---|---|---|
| GAME-001 | Load a **byte-for-byte identical** signed `config/game.json` on both sides before play. | MUST | BOTH | PDF p.34,128,144 / book 18,112,128 | E-11 | F§2 | `config_sha256` equality check | pre-game signature exchange | DQ for symmetry break | — |
| GAME-002 | Negotiate MINIMUM-status parameters only in the harder direction (raise); never lower them below the Appendix F example. | MUST | BOTH | PDF p.144,155 / book 128,139 | E-12 | Tbl 13–19 status | config validator vs F floors | validation report | Threshold breach → score DQ | — |
| GAME-003 | Move only in the four orthogonal directions (or STAY); one cell per turn. | MUST | BOTH | PDF p.37,144 / book 21,128 | E-13 | Tbl 15 | move-legality unit tests | move validator | Illegal move → technical loss | — |
| GAME-004 | Never make a diagonal move. | MUST NOT | BOTH | PDF p.37,144 / book 21,128 | E-14 | Tbl 15 | reject-diagonal test | validator | Move rejected → loss | — |
| GAME-005 | A thief with no legal move (all adjacencies blocked by barriers/edges) is considered **captured**. | MUST | BOTH | PDF p.37,149 / book 21,133 | E-47 | — | trap-state unit test | end-condition log | — | — |
| GAME-006 | Score every terminal scenario per the scoring table (capture: cop 20 / thief 5; survival: cop 5 / thief 10; technical loss 0/0). | MUST | BOTH | PDF p.38,154,149 / book 22,138,133 | E-48 | Tbl 17 (capture/survival/tie only) | scoring unit tests | result JSON scores | — | C-06, **C-07**: `technical_loss` 0/0 is **not** an App F row — binding via Ch 3 Table 2 + E-48; config field in App B (p.129) |
| GAME-007 | Enforce board dimensions from the signed config (default 7×7, MINIMUM ≥7). | MUST | BOTH | PDF p.35,152 / book 19,136 | E-11(supp) | Tbl 13 #1 | grid-bound tests | config | — | C-01 (5×5/10×10 examples) |
| GAME-008 | Enforce step ceiling and survival threshold from config (defaults 35, MINIMUM). | MUST | BOTH | PDF p.38,153 / book 22,137 | E-12(supp) | Tbl 15 #3,#4 | end-of-game step tests | log | — | — |
| GAME-009 | Movement legality is decided by deterministic code, never delegated to an LLM. | MUST | BOTH | PDF p.58,66 / book 42,50 | E-25(rel) | — | code path review | strategy module | (LLM misuse → illegal move/loss) | — |

## BAR — barriers

| ID | Requirement | Mod | Scope | Source | E | F | Verify | Evidence | Sanction | Conf |
|---|---|---|---|---|---|---|---|---|---|---|
| BAR-001 | Declare openly and truthfully every barrier placement and its exact location. | MUST | POLICE | PDF p.37,144 / book 21,128 | E-15 | — | audit vs declared placements | log audit | Board forgery → auto-loss in audit | — |
| BAR-002 | Never lie about a barrier placement location. | MUST NOT | POLICE | PDF p.37,144 / book 21,128 | E-16 | — | log-audit cross-check | log | Severe DQ cause | — |
| BAR-003 | A barrier placed on the thief's current cell counts as a capture (police wins). | MUST | POLICE | PDF p.37,149 / book 21,133 | E-46 | — | capture-by-barrier test | end log | — | — |
| BAR-004 | Place a barrier only on a turn the police forgoes movement, on the police's own cell or one orthogonally-adjacent cell; the cell is impassable to both, irreversibly, until game end. | MUST | POLICE | PDF p.37 / book 21 | E-15(supp) | Tbl 15 | placement-rule tests | validator | (illegal placement → audit loss) | — |
| BAR-005 | Do not exceed the barrier quota (default 14, MINIMUM) from config. | MUST | POLICE | PDF p.37,153 / book 21,137 | E-12(supp) | Tbl 15 #2 | quota-limit test | config | — | — |

## SCENT — scent / pheromone mechanics

| ID | Requirement | Mod | Scope | Source | E | F | Verify | Evidence | Sanction | Conf |
|---|---|---|---|---|---|---|---|---|---|---|
| SCENT-001 | Cryptographically lock the agreed scent emission+decay model before the game/series starts. | MUST | BOTH | PDF p.47,145 / book 31,129 | E-23 | Tbl 16 | hash-of-model exchange test | signed scent-model hash | Decay-formula deviation voids game | — |
| SCENT-002 | Compute scent per `τij(t+1)=max(0,(1−ρ)·τij(t)+Δτij)` with center=0.9, ρ=0.10, field 5×5, radial fall-off. | MUST | BOTH | PDF p.43,153 / book 27,137 | E-23(supp) | Tbl 16 | formula unit tests + numeric example | scent snapshots | (deviation voids game) | — |
| SCENT-003 | Before a series, exchange the full emission/decay model with a concrete numeric example and verify identical interpretation, then lock it. | MUST | BOTH | PDF p.47 / book 31 | E-23(supp) | Tbl 16 | pre-series exchange log | model+example hash | — | — |

## CRYPTO — commit-reveal / integrity / hashing

| ID | Requirement | Mod | Scope | Source | E | F | Verify | Evidence | Sanction | Conf |
|---|---|---|---|---|---|---|---|---|---|---|
| CRYPTO-001 | Use a SHA-256-based commit-reveal protocol for every move. | MUST | BOTH | PDF p.50,145 / book 34,129 | E-17 | — | protocol conformance test | commit hashes in log | Missing → solution illegal | — |
| CRYPTO-002 | Keep each nonce secret until the end of the game (final audit). | MUST | BOTH | PDF p.51,145 / book 35,129 | E-18 | — | reveal-timing test | log nonce-reveal order | DQ (dictionary-attack risk) | — |
| CRYPTO-003 | On any hash mismatch at audit, technically disqualify the game (score 0 to the forger). | MUST | BOTH | PDF p.55,145 / book 39,129 | E-19 | — | tamper-injection test | replay verdict | Score 0, iron rule | — |
| CRYPTO-004 | Declare only the truth when a capture is claimed (cryptographic obligation to answer truthfully). | MUST | BOTH | PDF p.38,145 / book 22,129 | E-21 | — | capture-response audit | log | Immediate DQ for denying reality | — |
| CRYPTO-005 | Never falsely declare a capture. | MUST NOT | POLICE | PDF p.145 / book 129 | E-22 | — | false-claim audit | log | Score 0 + technical loss, no appeal | — |
| CRYPTO-006 | Perform a signed Step-0 hardware declaration before the game starts. | MUST | BOTH | PDF p.55,145 / book 39,129 | E-24 | — | Step-0 presence + signature check | declaration JSON | Loss of fairness-bonus eligibility | — |
| CRYPTO-007 | Perform a comprehensive mutual log audit at the end of each game before agreeing the shared result. | MUST | BOTH | PDF p.55,147 / book 39,131 | E-36 | — | audit-flow test | audit record | Precondition for result agreement | — |
| CRYPTO-008 | Follow the 4-step order Commit → Acknowledge → Reveal → (final) Audit; reveal Move+Hint but keep the nonce hidden until the end-of-game audit. | MUST | BOTH | PDF p.50–52 / book 34–36 | E-17(supp) | — | sequence test | protocol log | — | — |
| CRYPTO-009 | Hash over **canonical JSON** (sorted keys, fixed separators) so both peers hash byte-identical input; sealed record includes State, Move, Intent, Nonce (+ hint, verdict, step, role, sub_game). | MUST | BOTH | PDF p.50,53 / book 34,37 | E-17(supp) | — | cross-impl byte-identity test | canonical bytes | — | — |
| CRYPTO-010 | Generate nonces with a cryptographic RNG (`secrets`), not `random`. | SHOULD | BOTH | PDF p.52,53 / book 36,37 | — | — | code review | source | — | — |
| CRYPTO-011 | Cryptographically lock the LLM token-consumption record at Step-0 to prevent later denial. | MUST | BOTH | PDF p.56 / book 40 | E-24(supp) | Tbl 18 #4 | Step-0 token-field signature | declaration JSON | (fairness) | — |

## STATE — orchestrator / state machine / watchdog

| ID | Requirement | Mod | Scope | Source | E | F | Verify | Evidence | Sanction | Conf |
|---|---|---|---|---|---|---|---|---|---|---|
| STATE-001 | Define the orchestrator as the single gateway/entry point to all sub-systems (it coordinates, does not execute). | MUST | BOTH | PDF p.78,143 / book 62,127 | E-3 | — | architecture review | module graph | Technical instability & loss | — |
| STATE-002 | Manage game phases with a strict state machine. | MUST | BOTH | PDF p.78,143 / book 62,127 | E-4 | — | FSM unit tests | transition table | Deadlock → technical loss | — |
| STATE-003 | Reject any illegal state transition immediately (transition table: WAITING_FOR_OPPONENT→COMPUTING_MOVE→COMMITTING→AWAITING_REVEAL→VERIFYING; TECHNICAL_LOSS terminal). | MUST | BOTH | PDF p.79–80,143 / book 63–64,127 | E-5 | — | illegal-transition test | FSM logs | Logic error → loss | — |
| STATE-004 | Implement a Deadline Tracker: every MCP request carries an expiry; on timeout, controlled retry or declare technical loss and close the turn cleanly. | MUST | BOTH | PDF p.81,143 / book 65,127 | E-6 | Tbl 19 #6 | timeout-injection test | deadline logs | Paralysis & loss on timeout | C-02 (180s vs 60s) |
| STATE-005 | Run a Watchdog background process monitoring heartbeat; on prolonged freeze, controlled shutdown + state persistence. | MUST | BOTH | PDF p.81–83,143 / book 65–67,127 | E-7 | Tbl 19 #7 | heartbeat-loss test | watchdog logs | Crash & loss of documentation | C-02 |

## STRAT — strategy-module constraints

| ID | Requirement | Mod | Scope | Source | E | F | Verify | Evidence | Sanction | Conf |
|---|---|---|---|---|---|---|---|---|---|---|
| STRAT-001 | Implement a separate strategy module connected to PeerRuntime between incoming hint-decode and outgoing Commit-pack; it holds all agent intelligence (belief update, legal move choice, deception text). | MUST | BOTH | PDF p.58,59 / book 42,43 | — | Tbl 22 | integration-point test | module boundary | — | — |
| STRAT-002 | Keep the spatial/movement decision fully algorithmic in all policy modes. | MUST | BOTH | PDF p.57,66,68 / book 41,50,52 | E-25(rel) | — | code path review | strategy source | — | — |
| STRAT-003 | Movement policy may be pure heuristics (Bayes+Manhattan), your own algorithm, or (optionally) RL — three equal options. | MAY | BOTH | PDF p.60–61 / book 44–45 | — | Tbl 22 | n/a (choice) | README §3 | — | — |

## LLM — language-model usage

| ID | Requirement | Mod | Scope | Source | E | F | Verify | Evidence | Sanction | Conf |
|---|---|---|---|---|---|---|---|---|---|---|
| LLM-001 | Do not hand the LLM the move decision itself; use it for text/behavioural profiling only. | SHOULD | BOTH | PDF p.65–66,146 / book 49–50,130 | E-25 | Tbl 21 | code review | strategy source | **No mandatory sanction**; blind reliance risks illegal moves/loss | — |
| LLM-002 | Conduct hint communication in free natural language only. | MUST | BOTH | PDF p.146 / book 130 | E-26 | Tbl 14 | message-format audit | hint transcript | Preserves challenge nature | — |
| LLM-003 | Never use a direct numeric-positions protocol for hints. | MUST NOT | BOTH | PDF p.146 / book 130 | E-27 | — | hint-content audit | transcript | DQ of game character | — |
| LLM-004 | Cap every hint at the word limit (default 15), applied to template mode and to the LLM (stated in its system prompt). | MUST | BOTH | PDF p.67,152 / book 51,136 | E-26(supp) | Tbl 14 #2 | word-count test | hint transcript | — | — |
| LLM-005 | An LLM-based move tactic is permitted only by explicit, documented mutual agreement; even then, local code must enforce legality. | MAY | BOTH | PDF p.66 / book 50 | E-25(exc) | — | agreement record + legality guard | negotiation log | — | — |

## GUI — live interface

| ID | Requirement | Mod | Scope | Source | E | F | Verify | Evidence | Sanction | Conf |
|---|---|---|---|---|---|---|---|---|---|---|
| GUI-001 | The live GUI shows **local truth only** (own position, sensed scent, received hints; a belief heatmap) — never a bird's-eye full board. | MUST | BOTH | PDF p.70–71,143 / book 54–55,127 | E-8 | — | GUI content audit | GUI screenshot | DQ (info breach) | — |
| GUI-002 | Never display the full objective board state in the live UI. | MUST NOT | BOTH | PDF p.71,143 / book 55,127 | E-9 | — | GUI audit | screenshot | DQ for illegal advantage | — |
| GUI-003 | Provide a belief-map heatmap and turn-state banner in the live GUI; belief-map screenshots are a submission requirement. | MUST | BOTH | PDF p.71–72,97,136 / book 55–56,81,120 | E-8(supp) | — | screenshot presence | README image | (submission incompleteness) | — |

## REPLAY — replay / verification

| ID | Requirement | Mod | Scope | Source | E | F | Verify | Evidence | Sanction | Conf |
|---|---|---|---|---|---|---|---|---|---|---|
| REPLAY-001 | Build a Replay Viewer that replays and cryptographically verifies the game log. | MUST | BOTH | PDF p.72,145 / book 56,129 | E-20 | — | tool presence + run | Replay app | Threshold for audit & submission | — |
| REPLAY-002 | For each log step, recompute SHA-256 over the revealed data and compare to the stored commitment; show "Verified OK" on match, "TAMPERED" (immediate disqualification, no appeal) on any mismatch. | MUST | BOTH | PDF p.72–75 / book 56–59 | E-19(supp),E-20 | — | tamper-injection e2e test | Replay screenshot (Verified OK) | Match void on first tamper | — |

## LEAGUE — league / fairness / competition

| ID | Requirement | Mod | Scope | Source | E | F | Verify | Evidence | Sanction | Conf |
|---|---|---|---|---|---|---|---|---|---|---|
| LEAGUE-001 | Play at least the minimum counted games (default 2) against **different** teams. | MUST | LEAGUE | PDF p.86,147,154 / book 70,131,138 | E-31 | Tbl 18 #3 | game-count check | result JSONs | Below minimum → no passing grade | — |
| LEAGUE-002 | Agree the result with the opponent; each team sends its own separate report. Non-report by one, or conflicting reports → game disqualified, 0 to both. | MUST | LEAGUE | PDF p.94,147 / book 78,131 | E-35 | — | dual-report reconciliation | two result JSONs | 0 to both on conflict/omission | — |
| LEAGUE-003 | Truthfully declare the number of counted games already played, at the start of each game. | MUST | LEAGUE | PDF p.86,147 / book 70,131 | E-37 | — | declaration audit | declaration JSON | Threshold for diversity weighting | — |
| LEAGUE-004 | Never falsely declare the number of games played. | MUST NOT | LEAGUE | PDF p.86,148 / book 70,132 | E-38 | — | cross-check vs lecturer records | declarations | Total DQ | — |
| LEAGUE-005 | Exactly one counted game per opponent (no score-farming repeats); uncounted warm-ups allowed. | MUST | LEAGUE | PDF p.86,149 / book 70,133 | E-52 | Tbl 18 #1 | opponent-uniqueness check | result set | — | — |
| LEAGUE-006 | Apply the tie rule: if cumulative score vs an opponent ties, each side receives the tie score (default 2). | MUST | LEAGUE | PDF p.87,154 / book 71,138 | E-48(rel) | Tbl 17 #5 | tie-scenario test | result JSON | — | — |
| LEAGUE-007 | Do not exceed the max counted games per team (default 10). | MUST | LEAGUE | PDF p.86,154 / book 70,138 | E-31(supp) | Tbl 18 #5 | cap check | result set | — | — |

## JSON — JSON artifacts and data contracts

| ID | Requirement | Mod | Scope | Source | E | F | Verify | Evidence | Sanction | Conf |
|---|---|---|---|---|---|---|---|---|---|---|
| JSON-001 | Format the game report as a standard, machine-readable JSON data structure. | MUST | BOTH | PDF p.94,147 / book 78,131 | E-33 | Tbl 20 | schema validation (Stage 1C) | result JSON | Rejected report if not JSON | — |
| JSON-002 | Send the completion report only as an attached JSON file — never free text. | MUST NOT | BOTH | PDF p.95,147 / book 79,131 | E-34 | — | email-attachment check | sent email evidence | Non-JSON rejected → 0 | — |
| JSON-003 | Produce the four mandatory JSON documents (declaration / config / log / result), names derived from `game_id`+`<NN>`, sharing a `game_uid`. | MUST | BOTH | PDF p.94–95,157 / book 78–79,141 | E-33(supp) | Tbl 20 | file presence + naming test | four JSON files | — | C-05 (num_games) |
| JSON-004 | Treat `config/game.json` as the signed shared "constitution"; it is canonically serializable (sorted keys) and hashed (`config_sha256`). | MUST | BOTH | PDF p.127–128 / book 111–112 | E-11(supp) | F§2 | canonical-hash test | config + hash | — | — |

## REPORT — Gmail / automatic reporting

| ID | Requirement | Mod | Scope | Source | E | F | Verify | Evidence | Sanction | Conf |
|---|---|---|---|---|---|---|---|---|---|---|
| REPORT-001 | Automatically report each game's results via the Gmail API (each team sends its own). | MUST | BOTH | PDF p.87,147 / book 71,131 | E-32 | — | send-flow test | sent-mail log | No report → points from that game DQ'd | — |
| REPORT-002 | Send the automatic completion reports to the fixed lecturer reports address `rmisegal+uoh26finalgame@gmail.com`. | MUST | BOTH | PDF p.87,149,157 / book 71,133,141 | E-51 | Tbl 20 | recipient config check | email headers | — | — |
| REPORT-003 | Respect HTTP 429 (Too Many Requests): back off and wait for the next window rather than retrying immediately. | MUST | BOTH | PDF p.95 / book 79 | E-28(supp) | Tbl 19 | 429-handling test | limiter logs | Blind retry risks account suspension | — |

## GIT — repository / history / tags / submission

| ID | Requirement | Mod | Scope | Source | E | F | Verify | Evidence | Sanction | Conf |
|---|---|---|---|---|---|---|---|---|---|---|
| GIT-001 | Tag the submission version with a documented **annotated** Git tag (e.g., `v1.0-submission`) and push it. | MUST | SUBMISSION | PDF p.134,148 / book 118,132 | E-41 | — | `git tag`/`git show` check | tag object | Admin condition for grading | — |
| GIT-002 | Each repo contains at least: README.md, `config/`, PRD files, a PLAN file, TODO files. | MUST | SUBMISSION | PDF p.96,149 / book 80,133 | E-50 | — | repo-contents check | repo tree | — | — |
| GIT-003 | Record in the Step-0 declaration the exact GitHub commit hash played each game (code may change between games; hash must be updated per game) and include it in the result JSON (`github_commit`). | MUST | BOTH | PDF p.56,150,157 / book 40,134,141 | E-53 | F§2.5 | declaration/result field check | JSON `github_commit` | Enables exact reproduction | — |
| GIT-004 | Attach each game's config file to the GitHub repo. | MUST | SUBMISSION | PDF p.156 / book 140 | E-50(supp) | F§2.4 | repo config presence | committed configs | — | — |
| GIT-005 | Make both repos accessible to the lecturer — public, or private and explicitly shared with `rmisegal@gmail.com`. | MUST | SUBMISSION | PDF p.95,133 / book 79,117 | E-49(supp) | Tbl 20 | access check | share settings | — | — |

## SEC — secrets / security / quotas / abuse prevention

| ID | Requirement | Mod | Scope | Source | E | F | Verify | Evidence | Sanction | Conf |
|---|---|---|---|---|---|---|---|---|---|---|
| SEC-001 | Implement a DOS detector that hard-locks API access on anomalous send patterns (circuit-breaker / backpressure). | MUST | BOTH | PDF p.89,146 / book 73,130 | E-29 | — | anomaly-injection test | gatekeeper logs | Prevents account suspension | — |
| SEC-002 | Grant the Gmail integration send-only permission. | MUST | BOTH | PDF p.146,123 / book 130,107 | E-30 | — | scope check | OAuth scope config | Security violation → DQ in code | — |
| SEC-003 | Never push secrets/credentials to the repository — even a private one shared only with the lecturer. | MUST NOT | BOTH | PDF p.135,148 / book 119,132 | E-39 | — | history secret-scan | clean history | Severe security failure & project failure | — |
| SEC-004 | Add credential/secret files (`credentials.json`, `token.json`, keys) to `.gitignore`. | MUST | BOTH | PDF p.135,148,121 / book 119,132,105 | E-40 | — | `.gitignore` + tracked-file scan | `.gitignore` | Mandatory leak protection | — |
| SEC-005 | If a secret is ever leaked/committed, rotate the credentials in the console (deletion from current code is insufficient). | MUST | BOTH | PDF p.122,135 / book 106,119 | E-39(supp) | — | rotation procedure | incident record | — | — |
| SEC-006 | Request only the least-privilege scope `https://www.googleapis.com/auth/gmail.send`. | MUST | BOTH | PDF p.121,123 / book 105,107 | E-30(supp) | — | scope inspection | OAuth config | — | — |

## PERF — timing / tokens / resource awareness

| ID | Requirement | Mod | Scope | Source | E | F | Verify | Evidence | Sanction | Conf |
|---|---|---|---|---|---|---|---|---|---|---|
| PERF-001 | Report the total LLM tokens consumed in the sub-game (and series) in the completion JSON. | MUST | BOTH | PDF p.150,95 / book 134,79 | E-54 | Tbl 18 #4 | result-field check | result JSON tokens | Feeds computational-fairness scoring | — |
| PERF-002 | Monitor and cryptographically lock token consumption at Step-0. | MUST | BOTH | PDF p.56 / book 40 | E-24(supp) | — | Step-0 field signature | declaration JSON | — | — |
| PERF-003 | Stay within the agreed per-series token budget (default ~200000; template/ollama can be 0). | SHOULD | BOTH | PDF p.154,158 / book 138,142 | — | Tbl 18 #4 | budget accounting | token ledger | — | — |

## DOC — documentation / academic reporting

| ID | Requirement | Mod | Scope | Source | E | F | Verify | Evidence | Sanction | Conf |
|---|---|---|---|---|---|---|---|---|---|---|
| DOC-001 | Provide a comprehensive academic report in `README.md` with the 6 mandatory components: (1) chosen Dec-POMDP model; (2) FastMCP orchestration dilemmas; (3) implemented strategies; (4) learning curves if RL used; (5) **mandatory** screenshots of Live-GUI belief map and Replay "Verified OK"; (6) link to the companion repo. | MUST | SUBMISSION | PDF p.97,134,148 / book 81,118,132 | E-42 | — | README component checklist | README + images | Academically incomplete without it | — |
| DOC-002 | Give a self-score for **code quality only** — never for the league game result. | MUST | SUBMISSION | PDF p.114,150 / book 98,134 | E-55 | — | submission-form review | self-score field | — | — |
| DOC-003 | Build the system in seven layered PRD stages (Base Logic → MCP → Blind Strategy → Language+Scent → Cloud+Tunnel → Security → Reporting Shell), each running end-to-end before the next. | SHOULD | BOTH | PDF p.99–106 / book 83–90 | — | — | milestone checklist | 7 PRD files | — | — |

## SUB — final submission requirements

| ID | Requirement | Mod | Scope | Source | E | F | Verify | Evidence | Sanction | Conf |
|---|---|---|---|---|---|---|---|---|---|---|
| SUB-001 | Download the Moodle submission form, fill it, save as PDF; do not change or move fields. | MUST | SUBMISSION | PDF p.114,148 / book 98,132 | E-43 | — | form-integrity check | submitted PDF | Bureaucratic condition for grade | — |
| SUB-002 | Submit the assignment in Moodle **separately for each group member**. | MUST | SUBMISSION | PDF p.114,148 / book 98,132 | E-44 | — | per-member submission check | Moodle receipts | No individual submission → no grade | — |
| SUB-003 | Use a unique **8-character group ID with no spaces**. | MUST | SUBMISSION | PDF p.114,148 / book 98,132 | E-45 | — | id-format check (`MaRs-777` = 8 chars) | group id field | Breaks auto report attribution | — |
| SUB-004 | Submit two separate repos (police, thief) with README cross-link, two links in the Moodle submission, and four links in both teams' JSON. | MUST | SUBMISSION | PDF p.96,149 / book 80,133 | E-49 | Tbl 20 | link-count checks | README + JSON links | — | — |
| SUB-005 | Satisfy every Appendix C Table 6 checklist item before tagging: both repos accessible; cross-link + 2 submission links; annotated tag pushed; README components complete in both; belief-map GUI screenshots; Replay "Verified OK" screenshot; ≥2 games vs different teams; game-end email from each team; no secrets uploaded (`.gitignore` verified). | MUST | SUBMISSION | PDF p.136 / book 120 | E-41/42/49(supp) | — | checklist gate | checklist evidence | — | — |

---

## Catalog summary (statistics — not a completeness proof by themselves)

- **Total requirements: 91** across 18 domains (verified by row count; no duplicate IDs).
- **By modality (exact, Stage 1B):** **MUST 76 · MUST NOT 9 · SHOULD 4 (LLM-001, CRYPTO-010, PERF-003, DOC-003) · MAY 2 (STRAT-003, LLM-005)** = 91. INFORMATIONAL captured separately in `PAGE_COVERAGE.md`.
- **By scope:** BOTH dominates; POLICE ≈ 7; LEAGUE ≈ 7; SUBMISSION ≈ 9.
- **Appendix E coverage:** all 55 E-entries referenced by ≥1 catalog ID (see `APPENDIX_E_CROSSWALK.md`).
- **Conflicts flagged:** C-01, C-02, C-05, C-06 (see `CONFLICT_REGISTER.md`).
- Counts are indicative; completeness rests on the page-coverage ledger and the Appendix E/F crosswalks, not on these totals.
