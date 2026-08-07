# Appendix F Numeric Inventory — group MaRs-777

**Status: REVIEWED — Stage 1B supervising review PASS. Inventory only — no constants
implemented. Approved: 32 parameter rows (FIXED 14 / MINIMUM 9 / NEGOTIABLE 9);
§2=5 rules, Table 20=7, Table 21=4, Table 22=2; `technical_loss` is NOT an App F row
(C-07). Approved baseline (input to Stage 1C).**

Every quantitative entry from **Appendix F** (PDF p.151–160 / book 135–143),
the **only** binding authority for numeric values. Values shown throughout the
book are Hebrew code-names in square brackets; the actual number lives **only**
here. **Do not** replace an Appendix F value with any earlier-chapter value.
Status meanings (PDF p.155 / book 139):

- **FIXED (קבוע):** binding, unchangeable; deviation disqualifies.
- **MINIMUM (מינימום):** negotiable **only in the harder direction** (usually higher), never below the example; default = example value if no agreement.
- **NEGOTIABLE (משא ומתן):** any agreed value; default = example value if no agreement.

`config/game.json` key names (Appendix B, PDF p.129–130) are given for
one-to-one traceability; **field names are fixed and binding**, values may move
only in the allowed direction.

## Table 13 — Board, coordinate system, start positions (PDF p.152)

| # | Code-name (He / En) | Meaning | Value (example) | Unit | Status | config key | Notes |
|---|---|---|---|---|---|---|---|
| 1 | `[ גודל הלוח ]` board size | square grid side | **7×7** | cells | **MINIMUM** | `board_and_agents.grid_size` | may increase by agreement, never below 7 |
| 2 | `[ מספר הסוכנים ]` number of agents | players in the race | **2** | agents | **FIXED** | `board_and_agents.num_agents` | — |
| 3 | `[ ראשית מערכת הצירים ]` coordinate origin | corner where (0,0) sits | **top-left** | — | **NEGOTIABLE** | `board_and_agents.axis_origin_corner` | must be identical both sides |
| 4 | `[ אינדקס התחלת הצירים ]` axis start index | first count of each axis | **0** | — | **NEGOTIABLE** | `board_and_agents.axis_start_index` | 0- vs 1-indexing must match |
| 5 | `[ עמדת פתיחה – גנב ]` thief start | thief start cell | **centre (3,3)** | coord | **NEGOTIABLE** | `board_and_agents.thief_start` | example on 7×7 |
| 6 | `[ עמדת פתיחה – שוטר ]` police start | police start cell | **corner (0,0)** | coord | **NEGOTIABLE** | `board_and_agents.cop_start` | example |

## Table 14 — Game arena & verbal cues (PDF p.152)

| # | Code-name | Meaning | Value | Unit | Status | config key | Notes |
|---|---|---|---|---|---|---|---|
| 1 | `[ זירת המשחק ]` game arena | real-world area feeding landmarks into hints; `""` = generic | **New York** | — | **NEGOTIABLE** | `world.map_area` | affects hint content only |
| 2 | `[ מגבלת מילים ברמז ]` word limit per cue | max words per verbal hint on the wire | **15** | words | **NEGOTIABLE** | `world.hint_max_words` | applies to template mode **and** LLM (in system prompt) |

## Table 15 — Movement & barriers (PDF p.153)

| # | Code-name | Meaning | Value | Unit | Status | config key | Notes |
|---|---|---|---|---|---|---|---|
| 1 | `[ מערך התנועה ]` movement set | single orthogonal move + stay; no diagonals | **4 + STAY** (`["N","S","E","W","STAY"]`) | — | **FIXED** | `movement_and_barriers.move_set` | — |
| 2 | `[ מכסת המחסומים ]` barrier quota | max barriers the police may place | **14** | barriers | **MINIMUM** | `movement_and_barriers.max_barriers` | may increase, never below 14 |
| 3 | `[ תקרת הצעדים ]` step ceiling | max moves per sub-game | **35** | moves | **MINIMUM** | `movement_and_barriers.max_moves` | — |
| 4 | `[ סף ההישרדות ]` survival threshold | valid steps thief must survive to win | **35** | steps | **MINIMUM** | `movement_and_barriers.survival_threshold` | — |

## Table 16 — Dynamic pheromones (PDF p.153)

| # | Code-name | Meaning | Value | Unit | Status | config key | Notes |
|---|---|---|---|---|---|---|---|
| 1 | `[ עוצמת הריח במוקד ]` scent centre intensity | pheromone strength at the emitting cell | **0.9** | intensity τ | **FIXED** | `pheromones.pheromone_center_intensity` | model crypto-locked before series (E-23) |
| 2 | `[ קצב דעיכת הריח ]` scent decay rate | decay per turn (ρ) | **0.10** | rate/turn | **FIXED** | `pheromones.pheromone_decay` | `(1−ρ)` shrinks scent to 90%/turn |
| 3 | `[ גודל שדה הריח ]` scent field size | emission window side around the agent | **5×5** | cells | **FIXED** | `pheromones.pheromone_grid_size` | radial fall-off from 0.9 |

## Table 17 — Scoring (win, survival, tie) (PDF p.154)

| # | Code-name | Meaning | Value | Status | config key | Notes |
|---|---|---|---|---|---|---|
| 1 | `[ ניקוד לכידה – שוטר ]` capture score police | police points on successful capture | **20** | **FIXED** | `scoring.capture_cop` | — |
| 2 | `[ ניקוד לכידה – גנב ]` capture score thief | thief points on capture | **5** | **FIXED** | `scoring.capture_thief` | — |
| 3 | `[ ניקוד הישרדות – שוטר ]` survival score police | police points when thief survives | **5** | **FIXED** | `scoring.survival_cop` | — |
| 4 | `[ ניקוד הישרדות – גנב ]` survival score thief | thief points on successful survival | **10** | **FIXED** | `scoring.survival_thief` | — |
| 5 | `[ ציון תיקו ]` tie score | points to each side when cumulative score vs an opponent ties | **2** | **FIXED** | `scoring.tie_score` | — |

> **Correction (Stage 1B):** Table 17 has **exactly 5 rows**. `technical_loss`
> is **NOT** an Appendix F parameter row. The 0/0 technical-loss scoring rule is
> binding but its provenance is **Ch 3 Table 2 (PDF p.38) + App E #48 (PDF p.149)**,
> and the `scoring.technical_loss: 0` field appears only in the **App B config
> example (PDF p.129)** — Appendix F omits it. See `CONFLICT_REGISTER.md` **C-07**
> and `STAGE_1B_CROSS_AUDIT.md` (Technical-loss source audit). Do not attribute a
> technical-loss numeric row to Appendix F.

## Table 18 — Network & league (PDF p.154)

| # | Code-name | Meaning | Value | Status | config key | Notes |
|---|---|---|---|---|---|---|
| 1 | `[ מספר המשחקונים ]` games per series | sub-games in a series vs an opponent | **6** | **FIXED** | `network_and_league.num_games` | note: config default `num_games`=1 (single demo sub-game); full series needs 6 — see C-05 |
| 2 | `[ תגמול גיוון ]` diversity reward | points for beating a **new** opponent | **10** | **FIXED** | `network_and_league.diversity_reward` | — |
| 3 | `[ מינימום משחקים למעבר ]` min games to pass | min counted games per team to pass | **2** | **FIXED** | `network_and_league.min_games_to_pass` | vs different teams |
| 4 | `[ אומדן טוקנים לסדרה ]` token estimate/series | total LLM tokens each team may consume; actual reported by email | **~200000** | **NEGOTIABLE** | `network_and_league.token_budget_per_series` | template/ollama modes can be 0 tokens |
| 5 | `[ מספר המשחקים המרבי לכל קבוצה ]` max games/team | max counted games a team may play | **10** | **FIXED** | `network_and_league.max_games_per_team` | — |

## Table 19 — Network, rate-limiter & protection (Gatekeeper) (PDF p.155)

| # | Code-name | Meaning | Value | Unit | Status | config key | Notes |
|---|---|---|---|---|---|---|---|
| 1 | `[ בקשות לדקה ]` requests per minute | max outgoing API rate | **30** | req/min | **MINIMUM** | `rate_limiter_gatekeeper.requests_per_minute` | token-bucket average `r` must stay under Google quota |
| 2 | `[ בקשות מקבילות ]` concurrent requests | max concurrent requests | **2** | req | **MINIMUM** | `rate_limiter_gatekeeper.concurrent_requests` | — |
| 3 | `[ השהיה לאחר שגיאה ]` retry backoff | wait before retry | **5** | sec | **MINIMUM** | `rate_limiter_gatekeeper.retry_backoff_sec` | — |
| 4 | `[ ניסיונות חוזרים ]` retries | attempts before failure | **3** | tries | **MINIMUM** | `rate_limiter_gatekeeper.max_retries` | — |
| 5 | `[ עומק התור ]` queue depth | request-queue size under load | **100** | items | **MINIMUM** | `rate_limiter_gatekeeper.queue_depth` | — |
| 6 | `[ מגבלת זמן התגובה ]` response time limit | timeout per network request | **30** | sec | **NEGOTIABLE** | `network_and_league.response_timeout_sec` | Deadline Tracker (Ch 8) |
| 7 | `[ סף כלב השמירה ]` watchdog threshold | freeze time until Watchdog intervenes | **60** | sec | **NEGOTIABLE** | `network_and_league.watchdog_timeout_sec` | Ch 8 code example uses 180s illustratively — see C-02 |

## Appendix F §2 — Mandatory Rules on the config (PDF p.156 / book 140)

1. Each team must define **all** the above values in the config file; the two teams must verify the values are identical and **cryptographically lock** them.
2. In each new game the team may change the settings, as long as they match the agreement with the opposing team.
3. Each config file must be given a **different name per game**, to allow easy replay of each game's config.
4. **Must attach** each game's config file to the GitHub repo.
5. Each team may change code between games; therefore, for each game the team must **email the lecturer the GitHub Commit number** used in that game.

(These reinforce catalog GAME-001/002, CRYPTO-001, GIT-002/003, REPORT-002.)

## Appendix F §3 — Attached-file variables, repo & addresses (Table 20, PDF p.157) — reference only, not negotiable

| Variable (He / En) | Role & content | Value |
|---|---|---|
| `[ קובץ ההצהרה ]` declaration file | pre-game declaration: all constant game data — teams, members, repos, hardware, model, tokens, times | `declaration_<game_id>.json` |
| `[ קובץ התצורה ]` config file | agreed config: cryptographically-locked, identical game parameters | `config_<game_id>_g<NN>.json` |
| `[ קובץ היומן ]` log file | sub-game log for cryptographic verification in the Replay simulator | `log_<game_id>_g<NN>.json` |
| `[ קובץ התוצאות ]` result file | final results report for league scoring by the lecturer | `result_<game_id>.json` |
| `[ מאגר הקוד לדוגמה ]` example repo | reference implementation | `https://github.com/rmisegal/Game-P2P-Cop-Chase` |
| `[ כתובת המרצה ]` lecturer address | general mail & GitHub repo sharing | `rmisegal@gmail.com` |
| `[ כתובת דיווחי הסוכן ]` agent reports address | destination for the JSON reports the agent auto-sends | `rmisegal+uoh26finalgame@gmail.com` |

File names derive from `game_id` and sub-game number `<NN>`; the four files share a common `game_uid` (Ch 9, PDF p.95). This table is **reference only — not part of the negotiated config, not negotiable.**

## Appendix F §4 — LLM modes for the verbal game (Table 21, PDF p.158) — private, not negotiated

Move decision is **always** algorithmic Python (Ch 6); these modes touch only deception text. Chosen in the **private** TOML (`[trash_talk] provider`).

| Mode (key) | Where it runs / token cost | Rate limit | Account/setup |
|---|---|---|---|
| `template` `[ ספק תבנית ]` | in-process, pre-written sentences — **0 tokens**; **default** | — | none; offline, free |
| `ollama` `[ ספק אולמה ]` | local model at `localhost:11434` — **0 API tokens** | none | install Ollama + pull model |
| `claude_api` `[ ספק ענן ]` | small cloud model (Haiku) via API — real consumption vs `[token estimate/series]` | per account | Anthropic API key (paid) |
| `claude_cli` `[ ספק שורת הפקודה ]` | `claude -p` via Claude Code CLI — highest cost | per subscription | Claude CLI login (subscription) |

`every_n_steps` invokes the model only once per N turns. In `template`/`ollama` a whole 6-sub-game series can run at **zero tokens**.

## Appendix F §5 — Strategy-module selection (Table 22, PDF p.159) — private, not negotiated

Movement policy (the score core) is chosen in the **private** TOML `[strategy]`. Empty → the shipped heuristic brain runs.

| Key (`[strategy]`) | Role | How to override |
|---|---|---|
| `thief_class` | your thief brain, `package.module:Class` | inherit `ThiefBrain`, override `_pick_move` and/or `_decide_move` |
| `police_class` | your police brain | same; in `_decide_move` the police also chooses the barrier |

## Inventory summary (corrected in Stage 1B)

**Structural counts — five distinct categories, never conflated:**

| Category | Location | Count |
|---|---|---|
| **A. Quantitative parameter rows** | Tables 13–19 (p.152–155) | **32** |
| B. Mandatory config rules | Appendix F §2 (p.156) | 5 |
| C. Attached-file/repo/address references | Table 20 (p.157) | 7 |
| D. LLM mode reference entries | Table 21 (p.158) | 4 |
| E. Strategy-module selection keys | Table 22 (p.159) | 2 |

**Parameter-row breakdown (Tables 13–19):** T13=6, T14=2, T15=4, T16=3, T17=5, T18=5, T19=7 → **grand total 32.**

**By status (reconciles to 32):**

- **FIXED: 14** — num_agents; move_set; pheromone_center_intensity, pheromone_decay, pheromone_grid_size; capture_cop, capture_thief, survival_cop, survival_thief, tie_score; num_games, diversity_reward, min_games_to_pass, max_games_per_team.
- **MINIMUM: 9** — grid_size; max_barriers, max_moves, survival_threshold; requests_per_minute, concurrent_requests, retry_backoff_sec, max_retries, queue_depth.
- **NEGOTIABLE: 9** — axis_origin_corner, axis_start_index, thief_start, cop_start; map_area, hint_max_words; token_budget_per_series; response_timeout_sec, watchdog_timeout_sec.
- **14 + 9 + 9 = 32.** ✅

**Not an Appendix F parameter row:** `technical_loss` (0/0). Binding via Ch 3 + App E #48; config field in App B; **omitted from Appendix F** (see C-07). Do not count it among the 32.

- **Conflicting illustrative values elsewhere in the book:** board `5×5`/`10×10` (Ch 2/3/6 examples) vs FIXED-authority `7×7` MINIMUM (C-01); watchdog `180s` code sample (Ch 8) vs `60s` NEGOTIABLE (C-02); `num_games` config default `1` vs series `6` FIXED — **resolved: 6, FIXED** (C-05). `technical_loss` numeric provenance omission (C-07). All in `CONFLICT_REGISTER.md`; **Appendix F governs numeric values**.

> This document is an **inventory only**. It does **not** implement constants and
> does **not** resolve non-numeric conflicts. Constants are built later, after review.
