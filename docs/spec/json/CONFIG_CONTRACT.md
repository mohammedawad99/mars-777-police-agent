# Config Contract — `config_<game_id>_g<NN>.json` — group MaRs-777

**Status: REVIEWED — Stage-1 supervising review PASS; baseline LOCKED. Contract
specification only — no JSON file, no schema, no code.**

The signed shared "constitution" for one sub-game: the agreed physics/scoring,
**byte-identical** on both peers, cryptographically locked. **Appendix B (PDF
p.128–132) is the structural authority** (it prints the exact keys) and **Appendix
F (PDF p.151–155) is the sole numeric authority** (values + status). Per PDF p.130:
"field names are fixed and binding; values may move only in the allowed direction."

Provenance for every config key is **SOURCE-EXPLICIT** (App B §B.3 prints it).
Values carry an Appendix F **status**: FIXED / MINIMUM / NEGOTIABLE (`AUTHORITY_RULES.md`).

## Top-level fields

| Field | Key | Provenance | Required | Type | App F row / status | Source | Notes |
|---|---|---|---|---|---|---|---|
| schema version | `schema_version` | SOURCE-EXPLICIT (key); value EXAMPLE-ONLY | Required | string | — | App B p.129 | value `"1.2"` not binding — see VERSIONING (JDEC-003) |
| agreed parties | `agreed_between` | SOURCE-EXPLICIT | Required | array[string] (2) | — | App B p.129 | the two group ids; example `["group-a","group-b"]` EXAMPLE-ONLY |
| board & agents | `board_and_agents` | SOURCE-EXPLICIT | Required | object | T13 | App B p.129 | 6 sub-keys |
| world | `world` | SOURCE-EXPLICIT | Required | object | T14 | App B p.129 | 2 sub-keys |
| movement & barriers | `movement_and_barriers` | SOURCE-EXPLICIT | Required | object | T15 | App B p.129 | 4 sub-keys |
| scoring | `scoring` | SOURCE-EXPLICIT | Required | object | T17 | App B p.129 | 5 App F rows + `technical_loss` (C-07) |
| pheromones | `pheromones` | SOURCE-EXPLICIT | Required | object | T16 | App B p.129 | 3 sub-keys |
| network & league | `network_and_league` | SOURCE-EXPLICIT | Required | object | T18 + 2 from T19 | App B p.129–130 | 7 sub-keys |
| rate-limiter gatekeeper | `rate_limiter_gatekeeper` | SOURCE-EXPLICIT | Required | object | T19 (5) | App B p.130 | 5 sub-keys |
| config hash | `config_sha256` | SOURCE-SEMANTIC (named p.127); **stored OUTSIDE the hashed config** | Conditional | string (hex) | — | Ch 5 p.127 | **Stage 1D: non-self-referential** — see below (JDEC-010, NDEC-004) |

## Sub-key detail (key → App F row, value, status)

**`board_and_agents`** (App F Table 13):

| Key | Value | Status | Type |
|---|---|---|---|
| `grid_size` | 7 | **MINIMUM** (≥7) | int |
| `num_agents` | 2 | **FIXED** | int |
| `thief_start` | `[3,3]` | NEGOTIABLE | array[int,int] |
| `cop_start` | `[0,0]` | NEGOTIABLE | array[int,int] |
| `axis_origin_corner` | `"top-left"` | NEGOTIABLE | string |
| `axis_start_index` | 0 | NEGOTIABLE | int |

**`world`** (Table 14): `map_area` (string, NEGOTIABLE, `"New York"`; `""`=generic) · `hint_max_words` (int, NEGOTIABLE, 15).

**`movement_and_barriers`** (Table 15): `move_set` (`["N","S","E","W","STAY"]`, FIXED) · `max_barriers` (14, MINIMUM) · `max_moves` (35, MINIMUM) · `survival_threshold` (35, MINIMUM).

**`scoring`** (Table 17 + C-07): `capture_cop` (20, FIXED) · `capture_thief` (5, FIXED) · `survival_cop` (5, FIXED) · `survival_thief` (10, FIXED) · `tie_score` (2, FIXED) · **`technical_loss` (0, key SOURCE-EXPLICIT in App B p.129; value binding via Ch 3 Table 2 + App E #48; NOT an Appendix F row — C-07).**

**`pheromones`** (Table 16): `pheromone_center_intensity` (0.9, FIXED, float) · `pheromone_decay` (0.10, FIXED, float) · `pheromone_grid_size` (5, FIXED, int).

**`network_and_league`** (Table 18 + response/watchdog from Table 19): `response_timeout_sec` (30, NEGOTIABLE) · `watchdog_timeout_sec` (60, NEGOTIABLE) · **`num_games` (6, FIXED for a counted series — see below)** · `diversity_reward` (10, FIXED) · `min_games_to_pass` (2, FIXED) · `max_games_per_team` (10, FIXED) · `token_budget_per_series` (~200000, NEGOTIABLE).

**`rate_limiter_gatekeeper`** (Table 19 rows 1–5): `requests_per_minute` (30, MINIMUM) · `concurrent_requests` (2, MINIMUM) · `retry_backoff_sec` (5, MINIMUM) · `max_retries` (3, MINIMUM) · `queue_depth` (100, MINIMUM).

## num_games — binding resolution (approved Stage 1B)

The App B example shows `"num_games": 1` (single-demo sub-game). **The binding
counted-league series value is `6`, status FIXED** (App F Table 18 #1; PDF p.154,
and App B text p.130 defers to `[games per series]`). **Do not treat the
illustrative `1` as binding.** For a counted league game the config MUST carry
`num_games: 6` exactly — FIXED means "binding, unchangeable; deviation
disqualifies", so a value **above** 6 is refused just like a value below it.
(See `CONFLICT_REGISTER.md` C-05, closed.)

## technical_loss — provenance (C-07)

`scoring.technical_loss` is a **real config key** (App B example prints it) with
binding value **0/0** from **Ch 3 Table 2 + App E #48** — **not** from Appendix F,
which has no technical-loss parameter row. The key is SOURCE-EXPLICIT; the value's
numeric provenance is the chapter/appendix-E rule. **Never fabricate an Appendix F
technical_loss row** (C-07 remains an open book-internal omission).

## Status-enforcement semantics (per value)

- **FIXED** — reject any value ≠ the App F value; deviation disqualifies (GAME-002).
- **MINIMUM** — accept only values ≥ the App F floor (negotiation may raise, "harder direction"); default = the floor if no agreement (App F §1, p.155).
- **NEGOTIABLE** — accept any mutually-agreed value; default = the shown value if no agreement.

Both peers MUST load a byte-identical file and exchange/verify its hash before
play (GAME-001, JSON-004). Config for a **counted** game must be **attached to the
repo** and given a **different name per game** (App F §2.3–2.4).

## Stage 1D locks (config hash, schema_version, minimalism)

- **`config_sha256` is non-self-referential (JDEC-010):** it is computed over the
  canonical bytes of `config/game.json` **containing only the App B keys** (no
  embedded hash field). It is stored **outside** the signed config — in the
  `declaration` and/or a `config_<…>.json.sha256` sidecar — so the bytes it hashes
  never include itself. Both peers compute it independently and compare for
  equality before play (**NDEC-004**). A hash field embedded in the bytes it hashes
  is **ruled out** (the book defines no such construction).
- **`schema_version` value is NEGOTIATED (NDEC-004):** the key is in the App B
  structure and therefore inside the hashed config; its value must be **identical**
  on both peers for byte-identity. It is agreed pre-match (default `"mars777-1"`),
  not a unilateral optional field. The value `"1.2"` remains illustrative.
- **Minimalism (D4):** the signed config contains **only** the App B
  SOURCE-EXPLICIT keys. **No project-added field** may be placed inside the signed
  config — any extra key would break byte-identity with the opponent. All
  project metadata lives outside the hashed config.

## Stage 1D.1 — signed-config authentication (K2)

The config is not only byte-equal-hashed; App B p.128 requires a **pre-game
signature exchange** ("חילופי החתימה … refuses to play on any mismatch"). Three
distinct conceptual layers (no envelope schema implemented):

1. **CONFIG CORE** — the App B keys, canonically serialized (the physics contract).
2. **CONFIG SHA-256** — `config_sha256`, an **unkeyed content digest** over the core
   (equality/integrity); stored **outside** the core (declaration/sidecar); both
   compute + compare (NDEC-004).
3. **CONFIG AUTHENTICATION ENVELOPE** — a **keyed authentication** over
   `"config" ‖ core` proving each side signed the agreed config with the
   **pre-supplied key** (SOURCE-REQUIRED; primitive unspecified). Project default
   **HMAC-SHA256** (JDEC-013), stored in a sidecar as `{auth_alg, key_id, auth_tag}`
   — **key never in any artifact**; the tag is **not** part of the bytes it
   authenticates (non-self-referential). Whether it uses the **same** key as Step-0
   is **source-unspecified** → agreed pre-match; **domain-separated** by the
   `"config"` context so a Step-0 tag cannot be replayed here. See NDEC-007.

**Pre-game flow:** canonical config → `config_sha256` → keyed authentication
(`auth_tag`) → exchange → verify tag → compare hash → **immutable lock** → play
allowed. **Any mismatch or failed authentication stops counted play.**

## Illustrative example (Markdown only — not a real file; values match Appendix F)

Fields marked **[PC]** are PROJECT-CONTRACT; all others are SOURCE-EXPLICIT keys.
`config_sha256` placement is **[PC/REVIEW-REQUIRED]** (JDEC-010).

```json
{
  "schema_version": "mars777-1",
  "agreed_between": ["mars-777", "opponent-group"],
  "board_and_agents": {
    "grid_size": 7,
    "num_agents": 2,
    "thief_start": [3, 3],
    "cop_start": [0, 0],
    "axis_origin_corner": "top-left",
    "axis_start_index": 0
  },
  "world": { "map_area": "New York", "hint_max_words": 15 },
  "movement_and_barriers": {
    "move_set": ["N", "S", "E", "W", "STAY"],
    "max_barriers": 14,
    "max_moves": 35,
    "survival_threshold": 35
  },
  "scoring": {
    "capture_cop": 20, "capture_thief": 5,
    "survival_cop": 5, "survival_thief": 10,
    "tie_score": 2, "technical_loss": 0
  },
  "pheromones": {
    "pheromone_center_intensity": 0.9,
    "pheromone_decay": 0.10,
    "pheromone_grid_size": 5
  },
  "network_and_league": {
    "response_timeout_sec": 30, "watchdog_timeout_sec": 60,
    "num_games": 6, "diversity_reward": 10,
    "min_games_to_pass": 2, "max_games_per_team": 10,
    "token_budget_per_series": 200000
  },
  "rate_limiter_gatekeeper": {
    "requests_per_minute": 30, "concurrent_requests": 2,
    "retry_backoff_sec": 5, "max_retries": 3, "queue_depth": 100
  }
}
```

- `schema_version` value **[PC]** (JDEC-003) — `"1.2"` is illustrative, not binding.
- `agreed_between` values **[PC]** identifiers — 8-char group ids (SUB-003).
- `num_games` set to **6** (FIXED counted-series value), not the illustrative `1`.
- `config_sha256` is intentionally **not** shown embedded — its storage is REVIEW-REQUIRED (JDEC-010).

All example values conform to Appendix F (no FIXED value altered; MINIMUMs at
floor; `num_games` at the binding 6). No comments inside JSON. No secrets.
