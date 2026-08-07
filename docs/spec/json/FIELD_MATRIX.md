# Master Field Matrix — group MaRs-777

**Status: REVIEWED — Stage-1 supervising review PASS; baseline LOCKED. Specification only; no code/schema/JSON artifact.**

Every candidate field across all four artifacts, exactly once. Status ∈ {LOCKED,
LOCKED-PROJECT, NEGOTIATED-PRE-MATCH, PROJECT-DECISION, REVIEW-REQUIRED,
EXAMPLE-ONLY}. **No field is LOCKED if its provenance is ambiguous.** Artifact
codes: **C**=config, **D**=declaration, **L**=log, **R**=result. Relevance flags:
Hash/Sig, Replay, Report (Y/—). **Stage 1D.1:** the Step-0/config keyed-auth and
result FastMCP/hardware fields were added; the interop status column already carries
the final Stage-1D/1D.1 status for those rows.

| Art | Semantic field | Proposed key | Provenance | Req/Opt | Type | Card. | Binding constraint | Req IDs | Primary source | Conflict | Hash/Sig | Replay | Report | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C | schema version | `schema_version` | SRC-EXPLICIT key / EXAMPLE-ONLY value | Opt | string | 1 | value not binding | JSON-004 | App B p.129 | — | — | — | — | EXAMPLE-ONLY (value) |
| C | agreed parties | `agreed_between` | SRC-EXPLICIT | Req | array | 2 | 2 group ids | GAME-001 | App B p.129 | — | Y | — | — | LOCKED |
| C | grid size | `board_and_agents.grid_size` | SRC-EXPLICIT | Req | int | 1 | **MIN ≥7** | GAME-007 | App F T13 | C-01 | Y | Y | — | LOCKED |
| C | num agents | `board_and_agents.num_agents` | SRC-EXPLICIT | Req | int | 1 | **FIXED 2** | GAME-007 | App F T13 | — | Y | Y | — | LOCKED |
| C | thief start | `board_and_agents.thief_start` | SRC-EXPLICIT | Req | array[2] | 1 | NEGOTIABLE | GAME-007 | App F T13 | — | Y | Y | — | LOCKED |
| C | cop start | `board_and_agents.cop_start` | SRC-EXPLICIT | Req | array[2] | 1 | NEGOTIABLE | GAME-007 | App F T13 | — | Y | Y | — | LOCKED |
| C | origin corner | `board_and_agents.axis_origin_corner` | SRC-EXPLICIT | Req | string | 1 | NEGOTIABLE; identical both sides | GAME-001 | App F T13 | — | Y | Y | — | LOCKED |
| C | axis start index | `board_and_agents.axis_start_index` | SRC-EXPLICIT | Req | int | 1 | NEGOTIABLE; identical | GAME-001 | App F T13 | — | Y | Y | — | LOCKED |
| C | map area | `world.map_area` | SRC-EXPLICIT | Req | string | 1 | NEGOTIABLE | LLM-002 | App F T14 | — | Y | — | — | LOCKED |
| C | hint word limit | `world.hint_max_words` | SRC-EXPLICIT | Req | int | 1 | NEGOTIABLE (15) | LLM-004 | App F T14 | — | Y | — | — | LOCKED |
| C | move set | `movement_and_barriers.move_set` | SRC-EXPLICIT | Req | array | 1 | **FIXED** 4+STAY | GAME-003 | App F T15 | — | Y | Y | — | LOCKED |
| C | barrier quota | `movement_and_barriers.max_barriers` | SRC-EXPLICIT | Req | int | 1 | **MIN 14** | BAR-005 | App F T15 | — | Y | Y | — | LOCKED |
| C | step ceiling | `movement_and_barriers.max_moves` | SRC-EXPLICIT | Req | int | 1 | **MIN 35** | GAME-008 | App F T15 | — | Y | Y | — | LOCKED |
| C | survival threshold | `movement_and_barriers.survival_threshold` | SRC-EXPLICIT | Req | int | 1 | **MIN 35** | GAME-008 | App F T15 | — | Y | Y | — | LOCKED |
| C | capture cop | `scoring.capture_cop` | SRC-EXPLICIT | Req | int | 1 | **FIXED 20** | GAME-006 | App F T17 | C-06 | Y | Y | Y | LOCKED |
| C | capture thief | `scoring.capture_thief` | SRC-EXPLICIT | Req | int | 1 | **FIXED 5** | GAME-006 | App F T17 | — | Y | Y | Y | LOCKED |
| C | survival cop | `scoring.survival_cop` | SRC-EXPLICIT | Req | int | 1 | **FIXED 5** | GAME-006 | App F T17 | — | Y | Y | Y | LOCKED |
| C | survival thief | `scoring.survival_thief` | SRC-EXPLICIT | Req | int | 1 | **FIXED 10** | GAME-006 | App F T17 | — | Y | Y | Y | LOCKED |
| C | tie score | `scoring.tie_score` | SRC-EXPLICIT | Req | int | 1 | **FIXED 2** | LEAGUE-006 | App F T17 | — | Y | — | Y | LOCKED |
| C | technical loss | `scoring.technical_loss` | SRC-EXPLICIT key; value via Ch3/E-48 | Req | int | 1 | **0/0; NOT an App F row** | GAME-006 | App B p.129; Ch3; E-48 | **C-07** | Y | Y | Y | LOCKED (key); value provenance C-07 |
| C | scent centre | `pheromones.pheromone_center_intensity` | SRC-EXPLICIT | Req | float | 1 | **FIXED 0.9** | SCENT-002 | App F T16 | — | Y | Y | — | LOCKED |
| C | scent decay | `pheromones.pheromone_decay` | SRC-EXPLICIT | Req | float | 1 | **FIXED 0.10** | SCENT-002 | App F T16 | — | Y | Y | — | LOCKED |
| C | scent field | `pheromones.pheromone_grid_size` | SRC-EXPLICIT | Req | int | 1 | **FIXED 5** | SCENT-002 | App F T16 | — | Y | Y | — | LOCKED |
| C | response timeout | `network_and_league.response_timeout_sec` | SRC-EXPLICIT | Req | int | 1 | NEGOTIABLE (30) | STATE-004 | App F T19 | C-02 | Y | — | — | LOCKED |
| C | watchdog timeout | `network_and_league.watchdog_timeout_sec` | SRC-EXPLICIT | Req | int | 1 | NEGOTIABLE (60) | STATE-005 | App F T19 | C-02 | Y | — | — | LOCKED |
| C | games in series | `network_and_league.num_games` | SRC-EXPLICIT | Req | int | 1 | **FIXED 6** (counted) | LEAGUE-005 | App F T18 | C-05 | Y | — | Y | LOCKED |
| C | diversity reward | `network_and_league.diversity_reward` | SRC-EXPLICIT | Req | int | 1 | **FIXED 10** | LEAGUE-001 | App F T18 | — | Y | — | Y | LOCKED |
| C | min games to pass | `network_and_league.min_games_to_pass` | SRC-EXPLICIT | Req | int | 1 | **FIXED 2** | LEAGUE-001 | App F T18 | — | Y | — | Y | LOCKED |
| C | max games/team | `network_and_league.max_games_per_team` | SRC-EXPLICIT | Req | int | 1 | **FIXED 10** | LEAGUE-007 | App F T18 | — | Y | — | Y | LOCKED |
| C | token budget | `network_and_league.token_budget_per_series` | SRC-EXPLICIT | Req | int | 1 | NEGOTIABLE (~200000) | PERF-003 | App F T18 | — | Y | — | Y | LOCKED |
| C | requests/min | `rate_limiter_gatekeeper.requests_per_minute` | SRC-EXPLICIT | Req | int | 1 | **MIN 30** | NET-002 | App F T19 | — | Y | — | — | LOCKED |
| C | concurrent req | `rate_limiter_gatekeeper.concurrent_requests` | SRC-EXPLICIT | Req | int | 1 | **MIN 2** | NET-002 | App F T19 | — | Y | — | — | LOCKED |
| C | retry backoff | `rate_limiter_gatekeeper.retry_backoff_sec` | SRC-EXPLICIT | Req | int | 1 | **MIN 5** | NET-002 | App F T19 | — | Y | — | — | LOCKED |
| C | max retries | `rate_limiter_gatekeeper.max_retries` | SRC-EXPLICIT | Req | int | 1 | **MIN 3** | NET-002 | App F T19 | — | Y | — | — | LOCKED |
| C | queue depth | `rate_limiter_gatekeeper.queue_depth` | SRC-EXPLICIT | Req | int | 1 | **MIN 100** | NET-002 | App F T19 | — | Y | — | — | LOCKED |
| C | config hash | `config_sha256` | SRC-SEMANTIC; stored **outside** core | Cond | string | 1 | canonical hash; non-self-ref | GAME-001,JSON-004 | Ch5 p.127 | — | Y | Y | — | LOCKED-PROJECT (JDEC-010) |
| C | config auth alg | `config_auth.auth_alg` (sidecar) | SRC-SEMANTIC (signature exchange REQ, K2); algo PC | Req | string | 1 | e.g. HMAC-SHA256 | GAME-001 | App B p.128 | — | Y | Y | — | PROJECT-DECISION (JDEC-013) |
| C | config key id | `config_auth.key_id` (sidecar) | SRC-SEMANTIC (pre-supplied key, K2) | Req | string | 1 | **non-secret id only; key never stored** | GAME-001 | App B p.128 | — | Y | Y | — | LOCKED (id ref) |
| C | config auth tag | `config_auth.auth_tag` (sidecar) | SRC-SEMANTIC (signed config, K2); primitive PC | Req | string(hex) | 1 | keyed MAC over `"config"‖core`; **non-self-ref** | GAME-001 | App B p.128 | — | Y | Y | — | NEGOTIATED-PRE-MATCH (JDEC-013; NDEC-007) |
| D | game id | `game_id` | **SRC-EXPLICIT** (source-named, D3); format PC | Req | string | 1 | unique/game | JSON-003 | Ch9 p.94 | — | — | Y | Y | LOCKED-SOURCE (name); format LP (JDEC-005) |
| D | shared uid | `game_uid` | **SRC-EXPLICIT** (source-named, D3); format PC | Req | string | 1 | shared×4 | JSON-003 | Ch9 p.95 | — | — | Y | Y | LOCKED-SOURCE (name); format LP (JDEC-005) |
| D | team identity | `teams.<g>.group_id/name` | SRC-SEMANTIC + PC | Req | object | 2 | 8-char id | SUB-003 | Ch9 p.94 | — | — | — | Y | PROJECT-DECISION (JDEC-006) |
| D | members | `teams.<g>.members` | SRC-SEMANTIC + PC | Req | array | ≥1 | — | SUB-002 | Ch9 p.94 | — | — | — | Y | PROJECT-DECISION |
| D | repos (police/thief) | `teams.<g>.repos.{police,thief}` | SRC-SEMANTIC + PC | Req | url | 2/team | 4 links total | SUB-004 | Ch9 p.94,96 | — | — | — | Y | PROJECT-DECISION (JDEC-009) |
| D | mcp endpoint | `teams.<g>.mcp_endpoint` | SRC-SEMANTIC + PC | Req | url | 1/team | public tunnel; no secret | NET-001 | Ch9 p.94 | — | — | — | Y | PROJECT-DECISION |
| D | hardware | `teams.<g>.hardware.{os,cpu_cores,cpu_freq_ghz,ram_gb,gpu,vram_gb}` | SRC-SEMANTIC + PC | Req | object | 1/team | Step-0 | CRYPTO-006 | Ch5 p.55 | — | Y | — | Y | PROJECT-DECISION (JDEC-006) |
| D | llm model | `teams.<g>.llm_model` | SRC-SEMANTIC + PC | Req | string | 1/team | — | CRYPTO-006 | Ch5 p.55 | — | Y | — | Y | PROJECT-DECISION |
| D | code version | `teams.<g>.code_version` | SRC-SEMANTIC + PC | Req | string | 1/team | — | CRYPTO-006 | Ch5 p.55 | — | Y | — | — | PROJECT-DECISION |
| D | played commit | `teams.<g>.github_commit` | **SRC-EXPLICIT** | Req | string(sha) | 1/team | 40-hex; per game | GIT-003 | Ch5 p.56 | — | Y | Y | Y | LOCKED |
| D | token cap | `token_budget_per_series` | SRC-SEMANTIC | Req | int | 1 | mirrors config | PERF-003 | Ch9 p.94 | — | Y | — | Y | PROJECT-DECISION |
| D | times | `times.{game_start,game_end}` | SRC-SEMANTIC + PC | Req/Opt | string(ISO) | 1 | ISO-8601 UTC | — | Ch9 p.94 | — | — | — | Y | PROJECT-DECISION (JDEC-011) |
| D | step0 auth alg | `step0_auth.auth_alg` | SRC-SEMANTIC (keyed auth REQ, K1); algo PC | Req | string | 1 | e.g. HMAC-SHA256 | CRYPTO-006 | Ch5 p.55–56 | — | Y | — | Y | PROJECT-DECISION (JDEC-013) |
| D | step0 key id | `step0_auth.key_id` | SRC-SEMANTIC (pre-supplied key, K1) | Req | string | 1 | **non-secret id only; key never stored** | CRYPTO-006 | Ch5 p.55–56 | — | Y | — | Y | LOCKED (id ref) |
| D | step0 auth tag | `step0_auth.auth_tag` | SRC-SEMANTIC (signed w/ pre-supplied key, K1); primitive PC | Req | string(hex) | 1 | keyed MAC over `"step0"‖core`; **non-self-ref** | CRYPTO-006 | Ch5 p.55–56 | — | Y | — | Y | NEGOTIATED-PRE-MATCH (JDEC-013; NDEC-005) |
| D | token-usage lock | `token_usage_locked` | SRC-SEMANTIC | Opt | int | 1 | crypto-locked | PERF-002 | Ch5 p.56 | — | Y | — | Y | LOCKED-PROJECT (own reported datum; authenticated within Step-0, NDEC-005) |
| L | game/uid/sub-game | `game_id`/`game_uid`/`sub_game` | SRC-SEMANTIC + PC | Req | mixed | 1 | INV-01/02 | JSON-003 | Ch5 p.50; Ch9 p.95 | — | — | Y | — | PROJECT-DECISION (JDEC-004/05) |
| L | config hash ref | `config_sha256` | SRC-SEMANTIC | Req | string | 1 | INV-03 | GAME-001 | Ch5 p.127 | — | Y | Y | — | LOCAL-ONLY (log copy of the interop `config_sha256`; JDEC-010) |
| L | turn entries | `entries[]` | SRC-SEMANTIC + PC | Req | array[obj] | ≥1 | Commit→Ack→Reveal | CRYPTO-008 | Ch5 §5.3 | — | Y | Y | — | PROJECT-DECISION (JDEC-007) |
| L | commit hash | `entries[].commit` (`H_commit`) | SRC-SEMANTIC | Req | string(hex) | 1/turn | SHA-256 sealed record | CRYPTO-001 | Ch5 p.50 | — | Y | Y | — | PROJECT-DECISION (key; JDEC-007) |
| L | sealed record | `{state,move,intent,hint,step,role,sub_game,nonce}` | SRC-SEMANTIC | Req | object | 1/turn | canonical hashed payload | CRYPTO-009 | Ch5 p.50–53 | C-04 | Y | Y | — | PROJECT-DECISION (JDEC-002/07) |
| L | ack | `entries[].{ack_of_step,ack_commit,by_role}` | SRC-SEMANTIC + PC | Req | object | 1/turn | Ack step | CRYPTO-008 | Ch5 p.51 | — | Y | Y | — | PROJECT-DECISION |
| L | reveal | `entries[].{move,hint}` (nonce at audit) | SRC-SEMANTIC | Req | object | 1/turn | nonce hidden till audit | CRYPTO-002 | Ch5 p.51 | — | Y | Y | — | PROJECT-DECISION |
| L | nonce | `audit.final_reveal[].nonce` | SRC-SEMANTIC | Req@audit | string | 1/turn | fresh CSPRNG; secret till end | CRYPTO-002,010 | Ch5 p.51,55 | — | Y | Y | — | PROJECT-DECISION (JDEC-007) |
| L | verification | `entries[].verified` / `audit.result` | SRC-SEMANTIC + PC | Req | bool/enum | 1 | Verified OK/TAMPERED | REPLAY-002 | Ch7 p.72–74 | — | Y | Y | — | PROJECT-DECISION |
| R | game/uid | `game_id`/`game_uid` | **SRC-EXPLICIT** (source-named, D3) | Req | string | 1 | INV-01 | JSON-003 | Ch9 p.94 | — | — | Y | Y | LOCKED-SOURCE (identity) |
| R | teams | `teams.<g>.*` | SRC-SEMANTIC + PC | Req | object | 2 | identities | SUB-003 | Ch9 p.94 | — | — | — | Y | PROJECT-DECISION |
| R | four links | `github_links` (4) | SRC-SEMANTIC + PC | Req | object/arr | 4 | four links | SUB-004 | Ch9 p.96; E-49 | — | — | — | Y | PROJECT-DECISION (JDEC-009) |
| R | fastmcp endpoint | `teams.<g>.mcp_endpoint` | SRC-SEMANTIC (MANDATORY, K3) + PC | Req | url | 1/team | self-contained; matches decl (INV-12); no secret | NET-001 | Ch9 p.94 | — | — | — | Y | PROJECT-DECISION (K3) |
| R | hardware decl | `teams.<g>.hardware` | SRC-SEMANTIC (MANDATORY, K3) + PC | Req | object | 1/team | matches Step-0 decl (INV-13) | CRYPTO-006 | Ch9 p.94; Ch5 p.55 | — | Y | — | Y | PROJECT-DECISION (K3) |
| R | hardware auth | `teams.<g>.hardware_auth` `{auth_alg,key_id,auth_tag}` | SRC-SEMANTIC (MANDATORY, K3: "cryptographically-signed hardware declarations") + PC primitive | Req | object | 1/team | keyed-auth evidence = Step-0 `step0_auth`; **key never stored** | CRYPTO-006 | Ch9 p.94; Ch5 p.55–56 | — | Y | — | Y | NEGOTIATED-PRE-MATCH (JDEC-013; INV-13) |
| R | per-sub-game | `sub_games[].{sub_game,cop_score,thief_score,outcome,github_commit,tokens}` | SRC-SEMANTIC (+ SRC-EXPLICIT `github_commit`) | Req | array[obj] | ≥1 | scores per App F; outcome incl technical_loss | GAME-006,GIT-003,PERF-001 | Ch9 p.95; E-48/54 | C-07 | Y | Y | Y | PROJECT-DECISION (JDEC-008); commit LOCKED |
| R | cumulative | `cumulative.{cop_total,thief_total,series_outcome}` | SRC-SEMANTIC + PC | Req | object | 1 | tie rule | LEAGUE-006 | Ch9 p.95,87 | — | — | — | Y | PROJECT-DECISION (JDEC-008) |
| R | total tokens | `total_tokens` | SRC-SEMANTIC | Req | int | 1 | series tokens | PERF-001 | E-54 | — | Y | — | Y | PROJECT-DECISION |
| R | timestamp | `timestamp` | SRC-SEMANTIC + PC | Req | string(ISO) | 1 | ISO-8601 UTC | — | Ch9 p.94 | — | — | — | Y | PROJECT-DECISION (JDEC-011) |
| R | mutual agreement | `mutual_agreement` | SRC-SEMANTIC + PC | Req | bool | 1 | both agree | LEAGUE-002 | Ch9 p.94; E-35 | — | — | — | Y | PROJECT-DECISION |
| R | approval hash | `result_sha256` | SRC-SEMANTIC; over agreed result core; stored outside core | Req | string(hex) | 1 | SHA-256-backed approval; both reports equal; non-self-ref | LEAGUE-002 | Ch9 p.94; E-35/36 | **C-09** | Y | — | Y | NEGOTIATED-PRE-MATCH (NDEC-006) |
| R | reporting team | `reported_by` | SRC-SEMANTIC + PC | Req | string | 1 | each sends own | REPORT-001 | Ch9 p.94 | — | — | — | Y | PROJECT-DECISION |

## Stage 1D — final interoperability status (each field, exactly one)

Final statuses: **LOCKED-SOURCE (LS)**, **LOCKED-PROJECT (LP)**,
**NEGOTIATED-PRE-MATCH (NPM)**, **LOCAL-ONLY (LO)**, **EXAMPLE-ONLY (EX)**,
**BLOCKING-UNRESOLVED (BU)**. Derived by this deterministic rule from the Provenance
+ object, with explicit overrides below:

- SOURCE-EXPLICIT field in a hashed/shared object → **LS**.
- SOURCE-SEMANTIC value that both peers must agree (in a hashed/exchanged object) → **NPM**.
- PROJECT key/representation inside a hashed/exchanged object → **LP** if we fix a deterministic default; **NPM** if opponent agreement is required.
- PROJECT key in a purely local artifact (persistent log/our presentation) → **LO**.
- EXAMPLE-ONLY value → **EX**.

**Explicit reclassifications (Stage 1D):**

| Field | Old Status | Final interop status | Basis |
|---|---|---|---|
| all 34 config App F value keys | LOCKED | **LS** (FIXED) / **NPM** (MINIMUM,NEGOTIABLE values) | NDEC-004 |
| `schema_version` (config) value | EXAMPLE-ONLY | **NPM** (in signed config; agreed) + value **EX** | D4; NDEC-004 |
| `config_sha256` | REVIEW-REQUIRED | **LP** (non-self-ref; stored outside; both compute) | JDEC-010 |
| `game_uid`, `game_id` | PROJECT-DECISION | **LS** (source-named); format **LP** | D3 |
| sealed commitment payload `{state,move,intent,hint,step,role,sub_game,nonce}` | PROJECT-DECISION | **NPM** (field set/order/canonical) with **LP** defaults | NDEC-001/002/003 |
| `state` representation | REVIEW-REQUIRED | **LP** (default) + **NPM** (confirm) | JDEC-012 |
| persistent log structure (`entries[]` shape, ack/reveal nesting, `phase`) | PROJECT-DECISION | **LO** | D4 |
| `step0_auth` (was `step0_signature`) | REVIEW-REQUIRED | **NPM** — **keyed authentication** (HMAC-SHA256 default, JDEC-013), **not** a plain digest, **not** PKI; envelope `{auth_alg,key_id,auth_tag}`, key out-of-band | **Stage 1D.1 (K1)**; NDEC-005 |
| config authentication `config_auth` | (new) | **NPM** — **keyed authentication / signature exchange** (K2), HMAC-SHA256 default; `config_sha256` equality **plus** verified tag | **Stage 1D.1 (K2)**; NDEC-007 |
| result FastMCP endpoint (`teams.<g>.mcp_endpoint` in result) | (new) | **LP** — MANDATORY report content, matches declaration | **Stage 1D.1 (K3)**; INV-12 |
| result hardware decl + `hardware_auth` | (new) | **NPM** — MANDATORY "cryptographically-signed hardware declarations"; keyed-auth evidence, key never stored | **Stage 1D.1 (K3)**; INV-13 |
| declaration `schema_version` | (present) | **removed** (REMOVE-REDUNDANT) | D4 |
| `result_sha256` (was `approval_sha256`) | REVIEW-REQUIRED | **NPM** — SHA-256 over agreed core; **both reports must be present and equal** or **0 to both** (C-09) | NDEC-006; **C-09** |
| `github_commit` (decl + result) | LOCKED | **LS** | SOURCE-EXPLICIT |
| result presentation keys (`reported_by`, nesting) not in approval core | PROJECT-DECISION | **LO** | D4 |
| `token_usage_locked` | REVIEW-REQUIRED | **NPM** (authenticated within Step-0 keyed auth / result tokens) | NDEC-005; E-54 |

## Exact reconciliation (counting unit = one semantic-field row above)

**Counting unit.** Each **table row above is exactly one semantic-field entry**; the
count is the number of rows, not JSON leaf-keys (an aggregate row such as `hardware`,
`sub_games[]`, or the 8-field `sealed_record` is **one** entry with its sub-keys noted
in-cell). This is the single, unambiguous unit; every row carries **exactly one**
provenance bucket and **exactly one** final interop status, so the two tallies must
both equal the artifact's row total.

**Provenance bucket (single, per row):** **SE** if the row asserts any source-named
field (App B keys; `github_commit`; `game_id`/`game_uid` are source-named, D3 — so the
`sub_games[]` row, which carries the SOURCE-EXPLICIT `github_commit` sub-field, counts
SE); **SS** if the source requires only the meaning and we chose the key; **PC** if the
field is a project addition the source does not require; **EX** if example-only. This
rule is mechanically checkable against the Provenance column. **Final status:** **LS**
source-locked, **LP** locked-project (deterministic default, we fix it), **NPM**
negotiated-pre-match (opponent agreement and/or keyed-auth verification required),
**LO** local-only (persistent log container / own presentation, never the interop
surface), **EX** example-only value, **BU** blocking-unresolved.

| Artifact | Total | SE | SS | PC | EX | LS | LP | NPM | LO | EX-STATUS | BU |
|---|---|---|---|---|---|---|---|---|---|---|---|
| declaration | 16 | 3 | 13 | 0 | 0 | 3 | 9 | 4 | 0 | 0 | 0 |
| config | 39 | 35 | 4 | 0 | 0 | 16 | 1 | 22 | 0 | 0 | 0 |
| log | 9 | 0 | 9 | 0 | 0 | 0 | 0 | 3 | 6 | 0 | 0 |
| result | 13 | 2 | 11 | 0 | 0 | 1 | 2 | 10 | 0 | 0 | 0 |
| **GRAND** | **77** | **40** | **37** | **0** | **0** | **20** | **12** | **39** | **6** | **0** | **0** |

**Per-artifact derivation (which rows land in which bucket):**

- **declaration (16):** SE = `game_id`, `game_uid`, `github_commit` (3). SS = the other
  13. Status LS = the 3 SE identity/commit rows; LP (9) = own authenticated declaration
  data with a fixed project schema (`team_identity`, `members`, `repos`, `mcp_endpoint`,
  `hardware`, `llm_model`, `code_version`, `times`, `token_usage_locked`); NPM (4) =
  values/mechanisms both peers must agree/verify (`token_cap` mirrors config;
  `step0_auth.auth_alg`, `step0_auth.key_id`, `step0_auth.auth_tag`).
- **config (39):** SE = `schema_version` (key) + `agreed_between` + 33 App B value keys
  (35). SS = `config_sha256` + `config_auth.{auth_alg,key_id,auth_tag}` (4). Status LS =
  `agreed_between` + the **15 FIXED** value keys (16); NPM = the **18 MINIMUM/NEGOTIABLE**
  value keys + `schema_version` value + 3 `config_auth` (22); LP = `config_sha256` (1).
  (FIXED 15 + MIN/NEG 18 = the 33 App B value keys; `technical_loss` is a FIXED-value
  key whose numeric provenance is Ch 3/E-48, not App F — C-07.)
- **log (9):** all SS. Status LO (6) = persistent-container rows (`game/uid/sub-game`,
  `config_sha256` copy, `entries[]`, `ack`, `reveal`, `verification`); NPM (3) = the
  cryptographic interop surface the opponent recomputes (`H_commit`, `sealed_record`,
  `nonce`).
- **result (13):** SE = `game/uid` identity **and** `sub_games[]` (which carries the
  SOURCE-EXPLICIT `github_commit`) = 2. SS = the other 11. Status LS = `game/uid` (1);
  the `sub_games[]` container's status is NPM (approval core) even though its
  `github_commit` sub-field is source-locked. LP (2) =
  own-report keys `mutual_agreement`, `reported_by`; NPM (10) = the mutually-agreed,
  byte-identical approval core + crypto (`teams`, `github_links`, `mcp_endpoint`,
  `hardware`, `hardware_auth`, `sub_games[]`, `cumulative`, `total_tokens`, `timestamp`,
  `result_sha256`).

**Invariants (all hold):** provenance total = status total = row total for every
artifact; 16+39+9+13 = **77**; SE+SS+PC+EX = 40+37+0+0 = **77**;
LS+LP+NPM+LO+EX+BU = 20+12+39+6+0+0 = **77**. **BU = 0** in every artifact.
**No approximation signs.** No duplicate `Artifact + Semantic Field` identity; every
field appears exactly once; `verdict` is **not** a separate field — it equals `intent`
(C-08); `step0_auth`/`config_auth`/`hardware_auth` are distinct objects with distinct
`context`. No key material is a field anywhere.

**Note on prior Stage-1D/1D.1 prose counts:** earlier summaries counted JSON leaf-keys
inconsistently (e.g. "config 40", "log 12+8=20", "LS 34") and tagged `game_uid` two
ways. Those approximate totals are **superseded** by this row-exact reconciliation;
the semantic content of the contracts is unchanged.
