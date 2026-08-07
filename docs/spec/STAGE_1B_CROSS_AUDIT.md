# Stage 1B — Independent Specification Cross-Audit — group MaRs-777

**Status: REVIEWED — Stage 1B supervising review PASS. Independent re-derivation
from the PDF, with corrections applied to the Stage 1A artifacts. This corrected
baseline is the approved input to Stage 1C (now reviewed and LOCKED).**

Source: `.project-spec/police_thief_p2p.pdf` v3.0.0, SHA-256 `7c9e1d…dd02e`, 160
pages (re-verified). This audit re-derived Appendices E and F directly, **without
relying on the Stage 1A crosswalk while counting**, then corrected discrepancies.

## Review findings R1–R5

| Finding | Verdict | Source evidence | Correction |
|---|---|---|---|
| **R1 — App F parameter-row count** | **CONFIRMED (Stage 1A wrong)** | Tables 13–19 (PDF p.152–155): 6+2+4+3+5+5+7 = **32** rows. Stage 1A summary said 26 (an arithmetic error; the inventory tables themselves already listed all 32 rows). | Inventory summary corrected 26 → **32**. |
| **R2 — App F status distribution** | **CONFIRMED** | Row-by-row status: **FIXED 14, MINIMUM 9, NEGOTIABLE 9 = 32** (independently re-derived; see §Appendix-F below). Token cross-count reconciles once the code-name "מינימום משחקים למעבר" false-positive (status FIXED) and the line-split "משא\nומתן" cells are accounted for. | Inventory status totals corrected to 14/9/9. |
| **R3 — technical_loss provenance** | **CONFIRMED (Stage 1A wrong)** | Whole-book search: `הפסד טכני` on p.38,55,56,79,81,142–145,149; `technical_loss` key only on **p.129 (App B config)**; `0/0` on p.149 (App E #48). **Appendix F (p.151–160) has NO technical-loss row** (Table 17 = 5 scoring rows only). Stage 1A wrongly listed it as an App F FIXED row. | Removed from App F Table 17; new omission record **C-07**; 0/0 scoring rule retained (binding via Ch 3 + E-48), provenance = Ch 3 / App B / App E, **not** App F. |
| **R4 — num_games** | **CONFIRMED** | App B example `num_games:1` (p.129–130) with text "single demo sub-game; the full league series requires `[games per series]`"; App F Table 18 #1 `[מספר המשחקונים]` = **6**, status **קבוע/FIXED** (p.154). App F is the sole numeric authority. | Closed: counted-series = **6, FIXED**; App B `1` = illustrative example. Removed from Open Questions; C-05 marked resolved. |
| **R5 — App F structure** | **CONFIRMED** | Distinct categories: parameter rows Tables 13–19 = **32**; §2 mandatory config rules = **5** (p.156); Table 20 references = **7** (p.157); Table 21 LLM modes = **4** (p.158); Table 22 strategy keys = **2** (p.159). | Inventory restructured to never conflate these into one "numeric entry" count. |

## Appendix E — independent audit (re-counted from tables, not the crosswalk)

Enumerated E-01…E-55 across Tables 7–12 and classified each action word
(חובה = MUST, איסור = MUST NOT, המלצה = SHOULD):

| Table | Entries | MUST | MUST NOT | SHOULD |
|---|---|---|---|---|
| 7 (arch, p.142–144) | 1–10 | 8 (1,3,4,5,6,7,8,10) | 2 (2,9) | 0 |
| 8 (spatial, p.144) | 11–16 | 4 (11,12,13,15) | 2 (14,16) | 0 |
| 9 (crypto, p.145) | 17–24 | 7 (17,18,19,20,21,23,24) | 1 (22) | 0 |
| 10 (strategy/net, p.146) | 25–30 | 4 (26,28,29,30) | 1 (27) | 1 (25) |
| 11 (league/admin, p.147–148) | 31–45 | 12 (31,32,33,35,36,37,40,41,42,43,44,45) | 3 (34,38,39) | 0 |
| 12 (additions, p.149–150) | 46–55 | 10 (46–55) | 0 | 0 |
| **Total** | **55** | **45** | **9** | **1** |

- **Continuity:** E-01 … E-55, no gaps, no duplicates.
- **E-25 is the only recommendation (SHOULD).** All other 54 are MUST/MUST NOT.
- **Modality preservation:** the Stage 1A crosswalk preserved every source modality (E-25 kept as SHOULD; no MUST weakened; no recommendation promoted). Confirmed against `APPENDIX_E_CROSSWALK.md` — 55/55 mapped, consistent.

## Appendix F — row-by-row parameter audit (Tables 13–19)

All 32 rows, with independently re-read status. Config keys are given only where
the book explicitly maps them (App B §B.3, PDF p.129–130); otherwise "—".

| T | # | Code-name (He) | English id | Meaning | Default | Unit | Status | Source | config key | Req IDs |
|---|---|---|---|---|---|---|---|---|---|---|
| 13 | 1 | גודל הלוח | board_size | grid side | 7×7 | cells | **MIN** | p.152 | `board_and_agents.grid_size` | GAME-007 |
| 13 | 2 | מספר הסוכנים | num_agents | players | 2 | agents | **FIXED** | p.152 | `board_and_agents.num_agents` | GAME-007 |
| 13 | 3 | ראשית מערכת הצירים | axis_origin_corner | (0,0) corner | top-left | — | **NEG** | p.152 | `board_and_agents.axis_origin_corner` | GAME-001/007 |
| 13 | 4 | אינדקס התחלת הצירים | axis_start_index | axis start | 0 | — | **NEG** | p.152 | `board_and_agents.axis_start_index` | GAME-001/007 |
| 13 | 5 | עמדת פתיחה – גנב | thief_start | thief start | (3,3) | coord | **NEG** | p.152 | `board_and_agents.thief_start` | GAME-007 |
| 13 | 6 | עמדת פתיחה – שוטר | cop_start | police start | (0,0) | coord | **NEG** | p.152 | `board_and_agents.cop_start` | GAME-007 |
| 14 | 1 | זירת המשחק | map_area | real-world arena for hints | New York | — | **NEG** | p.152 | `world.map_area` | LLM-002 |
| 14 | 2 | מגבלת מילים ברמז | hint_max_words | max words/hint | 15 | words | **NEG** | p.152 | `world.hint_max_words` | LLM-004 |
| 15 | 1 | מערך התנועה | move_set | 4 orthogonal + STAY | 4+STAY | — | **FIXED** | p.153 | `movement_and_barriers.move_set` | GAME-003 |
| 15 | 2 | מכסת המחסומים | max_barriers | max barriers | 14 | barriers | **MIN** | p.153 | `movement_and_barriers.max_barriers` | BAR-005 |
| 15 | 3 | תקרת הצעדים | max_moves | max moves | 35 | moves | **MIN** | p.153 | `movement_and_barriers.max_moves` | GAME-008 |
| 15 | 4 | סף ההישרדות | survival_threshold | steps to survive | 35 | steps | **MIN** | p.153 | `movement_and_barriers.survival_threshold` | GAME-008 |
| 16 | 1 | עוצמת הריח במוקד | pheromone_center_intensity | centre τ | 0.9 | τ | **FIXED** | p.153 | `pheromones.pheromone_center_intensity` | SCENT-002 |
| 16 | 2 | קצב דעיכת הריח | pheromone_decay | decay ρ/turn | 0.10 | rate | **FIXED** | p.153 | `pheromones.pheromone_decay` | SCENT-002 |
| 16 | 3 | גודל שדה הריח | pheromone_grid_size | emission window | 5×5 | cells | **FIXED** | p.153 | `pheromones.pheromone_grid_size` | SCENT-002 |
| 17 | 1 | ניקוד לכידה – שוטר | capture_cop | police capture pts | 20 | pts | **FIXED** | p.154 | `scoring.capture_cop` | GAME-006 |
| 17 | 2 | ניקוד לכידה – גנב | capture_thief | thief capture pts | 5 | pts | **FIXED** | p.154 | `scoring.capture_thief` | GAME-006 |
| 17 | 3 | ניקוד הישרדות – שוטר | survival_cop | police survival pts | 5 | pts | **FIXED** | p.154 | `scoring.survival_cop` | GAME-006 |
| 17 | 4 | ניקוד הישרדות – גנב | survival_thief | thief survival pts | 10 | pts | **FIXED** | p.154 | `scoring.survival_thief` | GAME-006 |
| 17 | 5 | ציון תיקו | tie_score | tie pts each | 2 | pts | **FIXED** | p.154 | `scoring.tie_score` | LEAGUE-006 |
| 18 | 1 | מספר המשחקונים | num_games | sub-games/series | 6 | games | **FIXED** | p.154 | `network_and_league.num_games` | LEAGUE-005, JSON-003 |
| 18 | 2 | תגמול גיוון | diversity_reward | new-opponent bonus | 10 | pts | **FIXED** | p.154 | `network_and_league.diversity_reward` | LEAGUE-001 |
| 18 | 3 | מינימום משחקים למעבר | min_games_to_pass | min to pass | 2 | games | **FIXED** | p.154 | `network_and_league.min_games_to_pass` | LEAGUE-001 |
| 18 | 4 | אומדן טוקנים לסדרה | token_budget_per_series | LLM token cap | ~200000 | tokens | **NEG** | p.154 | `network_and_league.token_budget_per_series` | PERF-003 |
| 18 | 5 | מספר המשחקים המרבי לכל קבוצה | max_games_per_team | max games/team | 10 | games | **FIXED** | p.154 | `network_and_league.max_games_per_team` | LEAGUE-007 |
| 19 | 1 | בקשות לדקה | requests_per_minute | out API rate | 30 | req/min | **MIN** | p.155 | `rate_limiter_gatekeeper.requests_per_minute` | NET-002 |
| 19 | 2 | בקשות מקבילות | concurrent_requests | concurrency | 2 | req | **MIN** | p.155 | `rate_limiter_gatekeeper.concurrent_requests` | NET-002 |
| 19 | 3 | השהיה לאחר שגיאה | retry_backoff_sec | retry wait | 5 | sec | **MIN** | p.155 | `rate_limiter_gatekeeper.retry_backoff_sec` | NET-002 |
| 19 | 4 | ניסיונות חוזרים | max_retries | retries | 3 | tries | **MIN** | p.155 | `rate_limiter_gatekeeper.max_retries` | NET-002 |
| 19 | 5 | עומק התור | queue_depth | queue size | 100 | items | **MIN** | p.155 | `rate_limiter_gatekeeper.queue_depth` | NET-002 |
| 19 | 6 | מגבלת זמן התגובה | response_timeout_sec | request timeout | 30 | sec | **NEG** | p.155 | `network_and_league.response_timeout_sec` | STATE-004 |
| 19 | 7 | סף כלב השמירה | watchdog_timeout_sec | watchdog freeze | 60 | sec | **NEG** | p.155 | `network_and_league.watchdog_timeout_sec` | STATE-005 |

**Row counts:** T13=6, T14=2, T15=4, T16=3, T17=5, T18=5, T19=7 → **grand total 32.**
**Status totals:** FIXED = 14, MINIMUM = 9, NEGOTIABLE = 9 → **32.** Arithmetic reconciles (14+9+9 = 32; 6+2+4+3+5+5+7 = 32).

Every parameter row maps to ≥1 requirement (column "Req IDs"); none is orphaned.

## Appendix F — non-parameter sections (must NOT be counted as parameter rows)

| Category | Location | Independent count |
|---|---|---|
| §2 Mandatory config rules | p.156 | **5** |
| Table 20 attached-file/repo/address references | p.157 | **7** |
| Table 21 LLM modes (verbal game) | p.158 | **4** |
| Table 22 strategy-module keys | p.159 | **2** |

## Technical-loss source audit (E)

| Source | Exact semantic claim | Binding/Illustrative | Numeric authority |
|---|---|---|---|
| Ch 3 Table 2 (PDF p.38) | Technical loss (crash / timeout / forgery) → cop 0, thief 0 | **Binding** (scoring table) | Not App F (chapter text) |
| App B config example (PDF p.129) | `"scoring": { … "technical_loss": 0 }` — a real config field | **Illustrative example** (App B is a sample), but the field name is real | Not App F |
| App E #48 (PDF p.149) | "score every end scenario per the scoring table (… technical loss 0/0)" | **Binding** (MUST) | Cross-refers to "the parameter table" but no F row exists |
| App F Tables 13–19 (PDF p.151–155) | Table 17 scoring has **5 rows** (capture cop/thief, survival cop/thief, tie). **No technical-loss row.** | — | **App F has NO technical-loss parameter** |

**Final provenance classification:** the **0/0 technical-loss scoring rule is
binding** (Ch 3 + App E #48) and the config carries a real `technical_loss` field
(App B), but its **numeric value has no Appendix F row** — a book-internal
omission (App E #48 says "per the parameter table", yet Appendix F omits it).
Conflict-register action: **new record C-07** (provenance omission). We do **not**
delete the 0/0 rule; we correct its provenance to Ch 3 / App B / App E, not App F.

## num_games resolution (F)

- **Example value (App B):** `num_games = 1` (single demo sub-game). PDF p.129–130.
- **Binding value (App F Table 18 #1):** **6**.
- **Binding status:** **FIXED (קבוע).** PDF p.154.
- **Authority reason:** Appendix F is the sole numeric authority (AUTHORITY_RULES); App B text itself defers the series length to `[games per series]`.
- **Open Question closed:** yes. The App B `1` is retained only as an illustrative example (C-05, resolved). Counted league series = **6, FIXED**.

## LLM-movement wording cross-audit (G)

- **Ch 6 §6.5 (PDF p.65–66):** default is algorithmic; "never delegate the move to the LLM." An **explicit exception** allows LLM-based tactical movement **only by prior explicit, documented mutual agreement**, and even then local code must enforce legality.
- **App E #25 (PDF p.146):** a **recommendation** (המלצה), explicitly "no mandatory sanction" — not a prohibition.
- **App F Table 21 (PDF p.158):** the four modes are **verbal-game** modes; move decision "is always algorithmic Python (see Ch 6)"; reference/default policy is algorithmic.
- **Final interpretation:** **no genuine conflict** — a recommendation (E-25) + a bounded, mutually-agreed exception (Ch 6) + a reference note (Table 21) are consistent. Captured as **LLM-001 (SHOULD)** and **LLM-005 (MAY, by mutual documented agreement, legality still code-enforced)**. The Chapter-6 exception is preserved verbatim in nuance; nothing in the book invalidates it. Recorded as C-03 (NOT CONFIRMED as a conflict).

## Citation validation (H)

- **All Appendix E (55) and Appendix F (32 + non-parameter) citations** re-checked against the PDF pages — consistent.
- **26-requirement sample** across all 18 domains (ARCH, NET, GAME, BAR, SCENT, CRYPTO, STATE, STRAT, LLM, GUI, REPLAY, LEAGUE, JSON, REPORT, GIT, SEC, PERF, SUB, DOC): **all 26 primary citations verified present on the cited page.** Four initial script "misses" were **harness artifacts** (non-zero-padded page filename `p43` vs `p043`, and a line-split "שמונה תווים"), not documentation errors — the cited pages do contain the content. **Zero citation mismatches; zero corrections needed.**

## Requirement-modality audit (I)

Exact counts over all **91** requirement rows (`REQUIREMENT_CATALOG.md`):

| Modality | Exact count |
|---|---|
| MUST | **76** |
| MUST NOT | **9** |
| SHOULD | **4** (LLM-001, CRYPTO-010, PERF-003, DOC-003) |
| MAY | **2** (STRAT-003, LLM-005) |
| **Total** | **91** |

- Count 91 unchanged after audit; no IDs added/removed/merged.
- No duplicated semantic requirement; no bundled unrelated requirements found.
- No MUST weakened to SHOULD; no recommendation promoted to MUST; no example promoted to a requirement; no sanction invented or altered.
- Note: JSON-002's modality cell was normalized from "MUST NOT (free text)" to **MUST NOT** for a clean count (its prohibition on free-text reports is unchanged).

## JSON source-map field classification (J)

Field classes: **EK** = explicit key (book prints the key), **ES** = explicit
semantic field, key unknown, **EX** = example-only key (appears only in a sample),
**RR** = REVIEW REQUIRED.

- **declaration:** `schema_version` — **EX** (App B config sample only); Step-0 hardware set (OS/CPU/RAM/GPU/model) — **ES**; `github_commit` — **EK** (named PDF p.56); token cap — **ES**; team/member/repo/MCP identities — **ES**; times — **ES**. Signature/key provenance — **RR**.
- **config (`config/game.json`):** all section+field keys **EK** (App B §B.3 prints them: `schema_version`, `agreed_between`, `board_and_agents.*`, `world.*`, `movement_and_barriers.*`, `scoring.*`, `pheromones.*`, `network_and_league.*`, `rate_limiter_gatekeeper.*`). `config_sha256`/signature location — **RR**. `agreed_between` — **EK** (example values `["group-a","group-b"]` are **EX**).
- **log:** nonce/reveal record fields (State, Move, Intent, Nonce + hint, verdict, step, role, sub_game) — **ES** (named in prose, no JSON keys); the sample `f"{nonce}|{move}"` payload — **EX** (explicitly simplified). Exact entry layout — **RR**.
- **result:** four repository links — **ES**; per-sub-game score + cumulative — **ES**; `github_commit` — **EK**; total tokens — **ES**; SHA-256-backed mutual approval (`result_sha256`; not a signature — see the corrected taxonomy in `json/SIGNATURE_AND_HASH_PROVENANCE.md`) — **ES**. Exact nesting — **RR**.

No schema constructed. No nesting invented.

## Consistency checks (L)

| # | Check | Result |
|---|---|---|
| 1 | Tables 13–19 row total reconciles | ✅ 6+2+4+3+5+5+7 = **32** |
| 2 | Status counts sum to total | ✅ 14+9+9 = **32** |
| 3 | Appendix E IDs E-01…E-55, no gaps/dupes | ✅ 55, continuous |
| 4 | Requirement IDs unique | ✅ 91, no duplicates |
| 5 | Every MUST/MUST NOT in traceability | ✅ all present |
| 6 | Every App E entry maps to ≥1 requirement | ✅ 55/55 |
| 7 | Every App F parameter row maps to a requirement / justified | ✅ all 32 mapped (see §Appendix-F table) |
| 8 | No false App F technical_loss row | ✅ removed; provenance corrected; C-07 added |
| 9 | num_games not marked unresolved | ✅ closed (6, FIXED); C-05 resolved |
| 10 | No page citation outside its section | ✅ sample + E/F citations verified |
| 11 | `git diff --check` | ✅ clean |
| 12 | No implementation file changed | ✅ src/tests/pyproject/uv.lock unchanged |

## Corrections applied

See `## 12 Files Modified` in the Stage 1B report. In summary: App F inventory
(32 rows; 14/9/9; technical_loss removed as an F row; structure clarified);
catalog (GAME-006 provenance; exact modality counts; JSON-002 label); crosswalk
(exact 45/9/1 tally); conflict register (C-07 added, C-05 resolved); JSON source
map (num_games closed; field classes added); traceability (provenance/num_games
notes); workflow docs. **No PRD content changed.**
