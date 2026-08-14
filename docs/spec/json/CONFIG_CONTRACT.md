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

## Stage 4E-R12 — negotiation semantics, `NegotiatedConfig`, and the four-layer lock

### R12-E — the four layers (the lock is a layer, not a step)

The Stage-1D.1 section above lists **three** layers and then treats the lock as a
line in a flow. `PRD06-FR-041` already names **four** distinct artefacts that must
never be conflated, so the lock is raised to a layer of its own:

| # | Layer | Kind | Proves | Lives |
|---|---|---|---|---|
| 1 | **CONFIG CORE** | canonical bytes | the agreed physics | `config_<game_id>_g<NN>.json` |
| 2 | **`config_sha256`** | **unkeyed** content digest | *content equality* — never authorship | **outside** the core (declaration/sidecar) |
| 3 | **`config_auth` `AuthProof`** | **keyed** MAC/signature over `"config" ‖ core` | a key-holder produced this core | sidecar; key never stored |
| 4 | **CONFIG LOCK** | a **local state transition**, not bytes | that this peer will not accept another core for this sub-game | `CONFIG_LOCKED` state + evidence |

Layer 4 has **no serialized representation of its own** and must never acquire
one: it is not a digest, not a tag, and not a field. It is the point after which
`PRD06-FR-048`'s set becomes immutable and `PRD06-FR-049` turns any change into
`E-LOCAL-DEFECT` or a rejected message. **Layer 2 is not layer 3** — restating
`PRD06-FR-044`, equal digests alone never authorise counted play. **Layer 3 is not
layer 4** — a verified tag proves authorship, not that either side has committed.

**Verification order before counted play, fixed:** parse → `auth_alg`/`key_id`
compared against the provisioned expectation (R12-A) → **verify the `AuthProof`**
→ **compare `config_sha256` for equality** → lock. The tag is verified **before**
the digest comparison so that an unauthenticated core is never even compared;
either failure refuses counted play (`INV-15`).

### R12-F — `NegotiatedConfig` (design contract; no Python, no schema)

The typed model of what negotiation converges on, derived **only** from the live
rows above and `FIELD_MATRIX.md`. It **adds nothing**: 39 config rows = **35**
core members + **4** outside members, unchanged.

**Core (35 members, all inside the hashed bytes):** `schema_version` ·
`agreed_between` · the **33 Appendix-B value keys** across `board_and_agents` (6),
`world` (2), `movement_and_barriers` (4), `scoring` (6), `pheromones` (3),
`network_and_league` (7), `rate_limiter_gatekeeper` (5).

**Outside the core (4):** `config_sha256` · `config_auth.{auth_alg, key_id,
auth_tag}`.

Every core member carries exactly one Appendix-F **status**, and the status — not
the member's type — determines what negotiation may do to it:

| Status | Count | Admissible proposal | Inadmissible ⇒ |
|---|---|---|---|
| **FIXED** | **15** | only the Appendix-F value | any other value, **above or below** ⇒ refuse counted play (GAME-002) |
| **MINIMUM** | — | the floor or **higher** ("harder direction") | any value below the floor ⇒ refuse |
| **NEGOTIABLE** | — | any mutually agreed value | unilateral value ⇒ not agreed, no lock |
| **NEGOTIABLE, but PRE-STEP0-FROZEN** — `token_budget_per_series` only | 1 (of the 9 above) | **equality only.** It was agreed **before `BOOT`** and authenticated in the Step-0 core at event 1 (`DECLARATION_CONTRACT.md` §R12-R3), so a counted-series proposal may only **restate** it | any value differing from the authenticated declaration cap ⇒ **`E-CONFIG-MISMATCH`**, refuse counted play; **never** silently renegotiated *(Stage 4E-R12-R3)* |
| — (`schema_version` value) | 1 | the agreed string, default `"mars777-1"` | differing values ⇒ bytes differ ⇒ no lock |

FIXED + MINIMUM/NEGOTIABLE = **15 + 18 = 33** value keys, matching
`FIELD_MATRIX.md`. `scoring.technical_loss` is FIXED-valued with Ch 3 / App E #48
provenance rather than an Appendix-F row (**C-07**) and is negotiated by nobody.
Status validation happens **before** lock (`PRD06-FR-046`); an inadmissible
proposal is refused at negotiation and never reaches layer 2.

**A `NegotiatedConfig` is always a complete core, never a delta.** A delta would
require both sides to share prior state whose equality is exactly what has not yet
been established, and byte-identity (`PRD06-FR-040`) is a property of a whole
document. Proposals and counter-proposals each carry a full core.

### R12-G — what the negotiation exchange carries, and how it converges

`PRD02-FR-022` already fixes the shape: **`CONFIG_NEGOTIATION`** is entered only
after "Step-0 verified both ways", takes **proposed values** inbound, emits
**counter-proposals** outbound, is bounded by the local **negotiation window**,
is idempotent, and forbids lowering a MINIMUM or changing a FIXED value. R12 adds
only what that state's messages must carry beyond the core, and how the exchange
ends:

- **Alongside the proposed core, each side echoes the pre-match agreement set**:
  the NDEC-001 sealed-record composition and action encoding, the NDEC-001 nonce
  profile `[0-9a-f]{32}`, the NDEC-002 `state` representation, the NDEC-003
  canonicalization parameters, the `CommitmentCodec`, the `ResultProfile`, the
  tool-name profile, and the **series convention** (`FIXED_ROLE` or
  `REFERENCE_ODD_EVEN_ALTERNATION`). `AuthProfile` and `KeyId` are **not** in this
  set — they were provisioned out of band (R12-A) and are compared, not echoed
  into effect.
- **These echoes are negotiation evidence, never artifact fields.**
  `PRD02-FR-082`, `PRD05-FR-034a` and `PRD06-FR-122` already place them in the
  negotiation record and **forbid** representing them as fields of any official
  artifact. The negotiation record is not one of the four Table-20 artifacts, so
  it contributes **no `FIELD_MATRIX.md` row** and the total stays at its current
  baseline **74** *(updated Stage 4E-R12-R2; this read 75 before Stage 4E-R12-R1
  removed the declaration `token_usage_locked` row)*.
- **Mismatch never resolves by preference.** A differing echo blocks counted play
  with the owning error — `E-NET-CONVENTION-MISMATCH` for the series convention
  (`PRD05-FR-033`), a refusal before `CONFIG_LOCKED` for the nonce profile
  (NDEC-001), `E-AUTH-FAILURE` for an `auth_alg`/`key_id` difference — and neither
  side's value silently wins.
- **Convergence is demonstrated at the lock, not announced in negotiation.**
  There is **no separate "accept" message**: `PRD02-FR-022` gives `CONFIG_LOCKED`
  the inbound **lock ack**, and agreement is proved by both independently computed
  `config_sha256` values being equal with both `AuthProof`s verified. Negotiation
  ends by transition, or by window expiry ⇒ refuse counted play.
- **Negotiation messages are not individually authenticated, and need not be.**
  Integrity is enforced *at the lock*: a proposal altered in flight yields
  differing cores, unequal digests and no lock (`PRD06-FR-044`). No per-message
  tag is introduced for `CONFIG_NEGOTIATION`.
- **Cadence: once per sub-game**, matching `config_<game_id>_g<NN>.json` and App F
  §2.3–2.4's different-name-per-game rule — deliberately unlike Step-0's
  once-per-series cadence.

## Stage 4E-R12-FIX — exact config readiness proof

### R12-FIX-D — the binding core, enumerated (35 members, mechanically confirmed)

Two top-level members plus the **33** Appendix-B value keys, by exact section and
exact field name, in **CONFIG_CONTRACT section order**:

| # | Section | Field | Status | Semantic type |
|---|---|---|---|---|
| 1 | — | `schema_version` | value NEGOTIATED (NDEC-004) | `str` |
| 2 | — | `agreed_between` | structural | `tuple[str, str]` — exactly 2 group ids |
| 3 | `board_and_agents` | `grid_size` | **MINIMUM** ≥ 7 | `int` |
| 4 | `board_and_agents` | `num_agents` | **FIXED** 2 | `int` |
| 5 | `board_and_agents` | `thief_start` | NEGOTIABLE | `tuple[int, int]` |
| 6 | `board_and_agents` | `cop_start` | NEGOTIABLE | `tuple[int, int]` |
| 7 | `board_and_agents` | `axis_origin_corner` | NEGOTIABLE | `str` — vocabulary **not** closed by the source |
| 8 | `board_and_agents` | `axis_start_index` | NEGOTIABLE | `int` |
| 9 | `world` | `map_area` | NEGOTIABLE | `str` — `""` means generic |
| 10 | `world` | `hint_max_words` | NEGOTIABLE | `int` |
| 11 | `movement_and_barriers` | `move_set` | **FIXED** | `tuple[str, ...]` — exactly `("N","S","E","W","STAY")` |
| 12 | `movement_and_barriers` | `max_barriers` | **MINIMUM** ≥ 14 | `int` |
| 13 | `movement_and_barriers` | `max_moves` | **MINIMUM** ≥ 35 | `int` |
| 14 | `movement_and_barriers` | `survival_threshold` | **MINIMUM** ≥ 35 | `int` |
| 15 | `scoring` | `capture_cop` | **FIXED** 20 | `int` |
| 16 | `scoring` | `capture_thief` | **FIXED** 5 | `int` |
| 17 | `scoring` | `survival_cop` | **FIXED** 5 | `int` |
| 18 | `scoring` | `survival_thief` | **FIXED** 10 | `int` |
| 19 | `scoring` | `tie_score` | **FIXED** 2 | `int` |
| 20 | `scoring` | `technical_loss` | **FIXED** 0 — **C-07**, not an App F row | `int` |
| 21 | `pheromones` | `pheromone_center_intensity` | **FIXED** 0.9 | **`Decimal`** |
| 22 | `pheromones` | `pheromone_decay` | **FIXED** 0.10 | **`Decimal`** |
| 23 | `pheromones` | `pheromone_grid_size` | **FIXED** 5 | `int` |
| 24 | `network_and_league` | `response_timeout_sec` | NEGOTIABLE | `int` |
| 25 | `network_and_league` | `watchdog_timeout_sec` | NEGOTIABLE | `int` |
| 26 | `network_and_league` | `num_games` | **FIXED** 6 | `int` |
| 27 | `network_and_league` | `diversity_reward` | **FIXED** 10 | `int` |
| 28 | `network_and_league` | `min_games_to_pass` | **FIXED** 2 | `int` |
| 29 | `network_and_league` | `max_games_per_team` | **FIXED** 10 | `int` |
| 30 | `network_and_league` | `token_budget_per_series` | NEGOTIABLE | `int` |
| 31 | `rate_limiter_gatekeeper` | `requests_per_minute` | **MINIMUM** ≥ 30 | `int` |
| 32 | `rate_limiter_gatekeeper` | `concurrent_requests` | **MINIMUM** ≥ 2 | `int` |
| 33 | `rate_limiter_gatekeeper` | `retry_backoff_sec` | **MINIMUM** ≥ 5 | `int` |
| 34 | `rate_limiter_gatekeeper` | `max_retries` | **MINIMUM** ≥ 3 | `int` |
| 35 | `rate_limiter_gatekeeper` | `queue_depth` | **MINIMUM** ≥ 100 | `int` |

Section arithmetic: 6 + 2 + 4 + 6 + 3 + 7 + 5 = **33**; + `schema_version` +
`agreed_between` = **35**. Matches `FIELD_MATRIX.md`'s 39 config rows as 35 core
+ 4 non-core.

**FIXED (15):** #4, #11, #15, #16, #17, #18, #19, #20, #21, #22, #23, #26, #27,
#28, #29.
**MINIMUM (9):** #3, #12, #13, #14, #31, #32, #33, #34, #35.
**NEGOTIABLE (9):** #5, #6, #7, #8, #9, #10, #24, #25, #30.

15 + 9 + 9 = **33**. **Independent cross-check:** the tracked Appendix-F total is
**32 = 14 / 9 / 9**; our FIXED set is **15** because `technical_loss` is a
FIXED-valued key whose provenance is Ch 3 Table 2 + App E #48 and **not** an
Appendix-F row (**C-07**). 14 + 1 = 15, and the MINIMUM and NEGOTIABLE counts
match Appendix F exactly. **`num_games` = 6 FIXED** is preserved (C-05).

**Type policy.** Every numeric member is an exact `int` except #21 and #22, which
are **`Decimal`** carrying the verbatim Appendix-F textual form (`"0.9"`,
`"0.10"`) under the existing `domain.config_model.require_decimal` policy —
**never `float`**, so no binary rounding can perturb canonical bytes. `bool` is
**never** accepted where `int` is required (exact-type checks, as elsewhere in
this repository). No member is `Any`, `dict[str, object]` or an untyped nested
dict.

### R12-FIX-E — cross-field invariants

- **JDEC-015 (PROJECT-CONTRACT, not a new Appendix-F row):**
  `survival_threshold <= max_moves`; a violating configuration is **refused
  before `CONFIG_LOCKED`**. Both keep their independent MINIMUM-35 floors.
- Structural, already owned by `domain`: `thief_start` and `cop_start` are
  distinct and inside the `grid_size` board; `axis_start_index` is consistent
  with the declared origin corner; `max_barriers` cannot exceed the placeable
  cell count of the board.

These are **structural/local** checks over one config value — they are not peer
equality checks and do not belong to the LIVE layer.

### R12-FIX-F — typed decomposition (no `Any`, no untyped dicts)

One component per live Appendix-B section, reusing what `domain.config_model`
already defines:

| Section | Component | Reuses |
|---|---|---|
| `board_and_agents` | `BoardAndAgentsTerms` | existing `GridConfig` |
| `world` | `WorldTerms` | — |
| `movement_and_barriers` | `MovementAndBarrierTerms` | — |
| `scoring` | `ScoringTerms` | — |
| `pheromones` | `PheromoneTerms` | existing `ScentParams` (`Decimal` policy) |
| `network_and_league` | `NetworkAndLeagueTerms` | existing `SeriesConfig` for `num_games` |
| `rate_limiter_gatekeeper` | `RateLimiterTerms` | — |

The composite is **`NegotiatedConfig(schema_version, agreed_between,
board_and_agents, world, movement_and_barriers, scoring, pheromones,
network_and_league, rate_limiter_gatekeeper)`**.

**`SeriesConfig` remains the narrow `num_games` value and is *not* the full
config** — unchanged from its committed definition.

### R12-FIX-G — field order

**Semantic/declaration order** is exactly the order of R12-FIX-D: `schema_version`,
`agreed_between`, then the seven sections in CONFIG_CONTRACT order, and within
each section the exact field order printed in the sub-key detail above.

**Canonical byte order is independent of it**: `sort_keys=True` (NDEC-003,
`PRD06-FR-002`) fixes serialization, so bytes never depend on declaration order.
**Python dict insertion order is never relied on as a contract.** The commitment
canonicalization contract is **not** re-opened.

### R12-FIX-H — binding config core vs lock context

The App-B core **must not absorb protocol metadata** merely to make locking
easier (**D4 minimalism**: any extra key breaks byte-identity with the opponent).
Everything below is frozen at `CONFIG_LOCKED` (`PRD06-FR-048`, `PRD02-FR-080/082`,
`PRD05-FR-034/034a`) yet is **outside** the config core:

| Lock-context value | Values | Scope |
|---|---|---|
| `series_convention` | `FIXED_ROLE` · `REFERENCE_ODD_EVEN_ALTERNATION` | **SERIES-WIDE** |
| `auth_profile` | `HMAC_SHA256` · `ED25519` | **SERIES-WIDE** (out of band, pre-`BOOT`) |
| `key_id` | a `KeyId` | **SERIES-WIDE** (out of band, pre-`BOOT`) |
| `commitment_codec` | `STRICT_PROJECT_COMMITMENT` · `LECTURER_REFERENCE_COMMITMENT` | **SERIES-WIDE** (`PRD06-FR-087`) |
| `result_profile` | `STRICT_PROJECT_RESULT` · `LECTURER_ATTACHMENT_COMPATIBILITY` | **SERIES-WIDE** |
| `compatibility_profile` | `STRICT_COUNTED_MATCH` · the two compatibility profiles | **SERIES-WIDE** |
| tool-name profile | reference aliases or not | **SERIES-WIDE** (`PRD02-FR-034`) |
| canonicalization profile | NDEC-003 parameters incl. `ensure_ascii=False` | **SERIES-WIDE** |
| sealed-record composition + action encoding | NDEC-001 | **SERIES-WIDE** |
| `state` representation | NDEC-002 | **SERIES-WIDE** |
| nonce representation | NDEC-001 `[0-9a-f]{32}` | **SERIES-WIDE** |
| the binding config core + `config_sha256` | — | **SUB-GAME** |
| `sub_game` association | `int >= 1` | **SUB-GAME** |

**Every profile value above is SERIES-WIDE; only the config core, its digest and
the sub-game association are SUB-GAME.** None of them is an official artifact
field (`PRD05-FR-034a`), so `FIELD_MATRIX.md` gains **no row** and stays at its
current baseline **74 = 15/39/9/11** *(updated Stage 4E-R12-R2; this line read 75 = 16/39/9/11 before Stage 4E-R12-R1 removed the declaration `token_usage_locked` row)*. **No invisible local defaults**: each of these is explicitly
exchanged and compared — a value that must be equal between peers is never
assumed.

Collectively they form **`InteropProfileSet`** (the eleven SERIES-WIDE rows).

### R12-FIX-I — config negotiation: exact shape, cadence, convergence

```
ConfigProposal(
    sub_game: int,
    config: NegotiatedConfig,
    profiles: InteropProfileSet,
)
```

Field order exactly `(sub_game, config, profiles)`. `sub_game` is an exact `int`
`>= 1` (`FIRST_SUB_GAME`) — **not** a `TurnCursor`, and there is **no `step`,
no `phase`, no digest and no proof** in a proposal. `profiles` is **always
present, never optional**: a receiver must be able to detect a convention or codec
mismatch *before* the lock exchange (`PRD05-FR-033`), and in an interoperability
contract optionality is a decision, not a hedge. It is not duplicated *within* a
message, and being SERIES-WIDE it must be **identical in every sub-game's
proposal** of the series.

**Cadence — deterministic, bounded:**

- **Initial proposal:** the peer whose `group_id` sorts **first** under exact
  byte-wise ascending comparison of the two ids in `agreed_between` sends it. A
  deterministic rule, never "first sender wins" and never a race.
- **Counter-proposals:** **both** peers may counter (`PRD02-FR-022` outbound is
  "counter-proposal"), each carrying a **complete** core — never a delta.
  **A counter-proposal may change only those members whose lifecycle still permits
  event-2 negotiation** *(Stage 4E-R12-R3)*. That is every MINIMUM member (upward)
  and **eight** of the nine NEGOTIABLE members. It is **not**
  `token_budget_per_series`: that member was agreed before `BOOT` and is already
  authenticated inside both peers' Step-0 cores, so changing it at event 2 would
  silently contradict a signed value. It stays in every proposal — the proposal
  remains **complete**, and no delta protocol is introduced — but purely for
  **equality checking**. A differing value is `E-CONFIG-MISMATCH` and refuses
  counted play; it is never treated as an offer.
- **Termination:** bounded solely by the **negotiation window** already owned by
  the state (`PRD02-FR-022` timeout source), so the dialogue is never unbounded
  and no new bound is invented.
- **Echo:** a peer's message is an echo when its `config` is member-for-member
  equal to the last received proposal and its `profiles` is equal.
- **Convergence:** both peers hold **member-for-member equal** cores and equal
  `profiles`. It is **not announced** — there is no accept message — it is
  **proved at the lock** by equal `config_sha256` with both proofs verified.
- **Operation completion:** ordinary completion of the negotiation operation
  means the proposal was delivered and structurally accepted, **not** that terms
  were agreed.
- **Mismatch:** never resolved by preference and never silently normalised or
  repaired — an inadmissible FIXED/MINIMUM value or a differing profile blocks
  counted play with the owning error.
- **Timeout / no agreement:** **refuse counted play.** **No technical-loss score
  is invented for a pre-game failure to agree** (technical loss is a
  counted-play sanction; C-07/App E #48 are untouched).

**Structural vs LIVE.** Structural: exact types, all 35 members present, the
R12-FIX-E local invariants, `sub_game >= 1`. LIVE: expected `sub_game`; opponent
equality; FIXED/MINIMUM/NEGOTIABLE admissibility (`PRD06-FR-046`); profile and
convention equality; echo/convergence; the negotiation window; duplicate/stale
detection; lock readiness.

**Error ownership — existing IDs only:** malformed proposal ⇒
**`E-PROTO-MALFORMED`**; core inequality or an inadmissible Appendix-F status ⇒
**`E-CONFIG-MISMATCH`**; series-convention mismatch ⇒
**`E-NET-CONVENTION-MISMATCH`** (`PRD05-FR-033`); wrong phase or stale sub-game ⇒
**`E-PROTO-STALE`**; window expiry ⇒ **`E-TIMEOUT-STEP`**; delivery ⇒
**`E-TRANSPORT`**/**`E-RETRY-EXHAUSTED`**.

**Module:** `ConfigProposal` and `InteropProfileSet` in
**`app.peer_pregame_messages`**, re-exported identity-equal through the
**`app.peer_messages`** façade (**D32**); the typed config components in
`domain.config_model` and its measured-LOC siblings; canonical bytes and the
digest in `protocol.canonical` / `protocol.config_lock`.

### R12-FIX-J — config lock: the four layers, and the peer/local reconciliation

Layer 4 was described as "a local state transition with no serialized
representation", while Config lock is also one of the eight peer-visible
families. Both are true, of **different objects**, and R12-FIX separates them:

- **A — PEER LOCK EVIDENCE** (the family): an exact semantic value, exchanged,
  authenticated, with a frozen shape. This is what the family is.
- **B — LOCAL `CONFIG_LOCKED` TRANSITION** (the consequence): a state-machine
  event with **no serialized artifact field, ever**. This is what layer 4 is.

B is permitted **only** after A has been produced by this peer, received from the
opponent, and verified in both directions. The evidence is **not** hidden inside
"successful operation completion" — it is an explicit semantic value; ordinary
completion covers only the **return** path. **No ninth family and no
`ConfigLockAck` is created.**

### R12-FIX-K — the exact authenticated core for `config_auth`

`PRD06-FR-043` and NDEC-007 authenticate `"config" ‖ canonical(config_core)`.
That construction cannot carry the lock, for a reason that only became visible
once the lock context was enumerated: **the App-B core is byte-identical across
every sub-game of a series**, so a tag over it alone binds **no sub-game, no game
identity, and none of the `PRD06-FR-048` values frozen at the lock** — one tag
would be equally valid evidence for every sub-game, and the series convention and
profile set would be exchanged unauthenticated.

**Decision (PROJECT-CONTRACT).** The authenticated core is **`config_sha256`
plus an explicit lock context** — the third of the constructions this stage was
asked to choose between:

```
ConfigLockContext(
    game_id: str,
    game_uid: str,
    sub_game: int,
    config_sha256: Sha256Digest,
    profiles: InteropProfileSet,
)

AuthProof.value = KEYED_AUTH_key( "config" ‖ canonical(ConfigLockContext) )
```

Every field, and why it is there:

| Field | Binds |
|---|---|
| `game_id`, `game_uid` | game identity — a tag cannot replay into another game |
| `sub_game` | the **sub-game association** — the member that makes per-sub-game locking meaningful |
| `config_sha256` | **all 35 binding core members**, transitively and exactly, via the layer-2 digest — hash-then-authenticate, so the core is canonicalized once |
| `profiles` | the eleven SERIES-WIDE values whose unilateral post-lock change must be detectable: series convention, auth profile, `key_id`, commitment codec, result profile, compatibility profile, tool-name profile, canonicalization, sealed-record composition, `state` representation, nonce representation |

**Excluded, deliberately:** `config_auth` itself — the envelope is **never** inside
its own authenticated bytes (non-self-reference, `PRD06-FR-025`); **all key
material** — only `key_id` appears, and inside `profiles` as a non-secret label;
and any App-B core member **individually** — they enter only through
`config_sha256`, so the binding config core is never polluted with protocol
metadata (**D4**).

**`auth_alg` / `key_id` substitution is impossible in effect**: the envelope
values are **compared** against the locally provisioned expectation (R12-FIX-C),
and the `auth_profile`/`key_id` inside `profiles` are additionally **bound
cryptographically**, so an altered envelope either fails equality or contradicts
the authenticated context.

This **amends `PRD06-FR-043` and NDEC-007 in place**. `context = "config"` is
unchanged, domain separation from `"step0"` is unchanged, `config_sha256` remains
an unkeyed content digest computed exactly as before, and **no requirement, NDEC
or field was added**.

### R12-FIX-L — the four layers, stated separately

1. **Canonical binding config bytes** — Layer 1 canonicalization of the 35 core
   members. Content only.
2. **`config_sha256`** — an **unkeyed** SHA-256 over those bytes. **Content
   identity only**; it authenticates nobody and proves no authorship.
3. **`config_auth` `AuthProof`** — a **keyed** MAC (`HMAC_SHA256`) or **digital
   signature** (`ED25519`) over `"config" ‖ canonical(ConfigLockContext)`.
   **Producer/key-holder authentication**, binding identity, sub-game, content
   digest and profiles.
4. **Local `CONFIG_LOCKED` transition** — a **state-machine consequence** after
   mutual verified evidence. No bytes, no field, no digest.

2 is not 3 (`PRD06-FR-044`: equal digests alone never authorise counted play); 3
is not 4 (a verified proof shows authorship, not commitment). **None of these is
called "the signature" generically** — layer 2 is a digest, layer 3 is an
`AuthProof` whose primitive category depends on its profile, layer 4 is a
transition.

### R12-FIX-M — config lock: exact peer semantic shape

```
ConfigLockEvidence(
    context: ConfigLockContext,
    auth: AuthProof,
)
```

Field order exactly `(context, auth)`. `sub_game`, `config_sha256` and the
profiles live **inside `context`** and are therefore **not duplicated** alongside
it — the same no-duplication discipline O5 applied to the turn operation.
**Deliberately absent:** `accepted`, `ok`, `timestamp`, `phase`, `TurnCursor`,
`step`, score and technical loss.

**Return path:** ordinary **successful operation completion** — stated separately
from the request value above, and carrying no semantic result of its own (O2/O6).

**Structural vs LIVE.** Structural: exact types; `sub_game >= 1`; `config_sha256`
a well-formed `Sha256Digest`; `AuthProof` well-formed for its declared profile;
`profiles` complete. LIVE: `auth_alg`/`key_id` equal to the provisioned
expectation; **proof verification**; **digest equality with the locally computed
`config_sha256`**; `sub_game` equal to the expected sub-game; profile and
convention equality; phase correctness; replay/staleness.

**Error ownership — existing IDs only:** malformed ⇒ **`E-PROTO-MALFORMED`**;
proof or profile/`key_id` failure ⇒ **`E-AUTH-FAILURE`**; digest inequality ⇒
**`E-CONFIG-MISMATCH`**; wrong sub-game or phase ⇒ **`E-PROTO-STALE`**; own-side
fault ⇒ **`E-LOCAL-DEFECT`**. Any of them **refuses counted play** (`INV-15`);
**none produces a technical-loss score before counted play.**

**Module:** `ConfigLockContext` and `ConfigLockEvidence` in
**`app.peer_pregame_messages`**, identity-equal through the **`app.peer_messages`**
façade; keyed computation in `protocol.keyed_auth`; the lock itself in
`protocol.config_lock`; `Sha256Digest` reused unchanged from
`app.protocol_values`; `AuthProfile`/`KeyId`/`AuthProof` from `app.auth_values`.

### R12-FIX-N — lock cadence and symmetry

Per sub-game, both peers independently and symmetrically:

1. derive the same binding config core from the converged negotiation;
2. compute `config_sha256` locally — never accept the opponent's digest as the
   value of their own core;
3. build `ConfigLockContext` and produce their own `AuthProof`;
4. exchange `ConfigLockEvidence`;
5. verify the peer's profile/`key_id` equality, then the peer's proof, then
   digest equality, then `sub_game` and profile equality;
6. **only then** transition locally to `CONFIG_LOCKED`.

**No unilateral first-sender winner** — neither side's evidence alone permits the
transition. **No silent repair** at any step. **No technical loss before counted
play** for failing to agree or lock; the outcome is refusal.

## Stage 4E-R14-R1 — `InteropProfileSet` exact vocabulary (implementation dependency frozen)

§R12-FIX-H enumerated the eleven SERIES-WIDE lock-context members as *concepts*
with cross-references — enough to prove the lock context binds them, not enough to
construct a typed value. Stage 4E-R14 stopped on exactly that. Each member's
**field name**, **type** and **serialized token vocabulary** is frozen here. All
tokens are **PROJECT-CONTRACT**; serialized values equal the identifiers exactly,
with **no alias, no case folding, no normalization**.

### R14-R1-A — the nine profile types

| Type | Members | Note |
|---|---|---|
| `SeriesConvention` | `FIXED_ROLE` · `REFERENCE_ODD_EVEN_ALTERNATION` | already frozen (PRD05-FR-030); **neither is source-mandated** |
| `AuthProfile` | `HMAC_SHA256` · `ED25519` | already frozen (R12-FIX-A); plain SHA-256 is not a member |
| `CommitmentCodec` | `STRICT_PROJECT_COMMITMENT` · `LECTURER_REFERENCE_COMMITMENT` | already frozen; reference codec by explicit agreement only |
| `ResultProfile` | `STRICT_PROJECT_RESULT` · `LECTURER_ATTACHMENT_COMPATIBILITY` | already frozen |
| **`CompatibilityProfile`** | `STRICT_COUNTED_MATCH` · `LECTURER_REFERENCE_COMPATIBILITY` · `LECTURER_ATTACHMENT_COMPATIBILITY` | **newly exact** — the three profile headings `COMPATIBILITY_PROFILES.md` already prints. `STRICT_COUNTED_MATCH` is the default and the only emitter for a counted artifact; no profile may weaken a binding requirement |
| **`ToolNameProfile`** | `PROJECT_LOGICAL_OPERATIONS` · `LECTURER_REFERENCE_ALIASES` | **newly exact.** The first uses the neutral logical operation identities; the second additionally enables the frozen aliases `negotiate` / `receive_turn` / `submit_audit` / `receive_control` (PRD02-FR-034, **not book-mandated**). **It never changes internal operation identity, and there is no enum member per tool name.** |
| **`CanonicalizationProfile`** | `CANONICAL_JSON_V1` | **newly exact.** One token identifying the complete frozen NDEC-003 v1 bundle: `sort_keys=True`, `separators=(",",":")`, UTF-8, NFC where required, `ensure_ascii=False`, LF, no trailing newline in a hashed payload, the existing deterministic numeric rules. **The token identifies the bundle; it does not replace those rules.** No second v1 profile. |
| **`SealedRecordProfile`** | `SEALED_RECORD_V1` | **newly exact.** Identifies the NDEC-001 v1 bundle: the exact eight-member sealed set, the frozen tagged action encoding, and the current `intent`/`role`/action contracts. **Distinct from `CommitmentCodec`** — that selects strict-vs-reference commitment compatibility behaviour, this identifies the sealed-record/action semantic profile inside the lock context. They are **not merged.** |
| **`StateRepresentationProfile`** | `SEALED_STATE_V1` | **newly exact.** Identifies the NDEC-002 / JDEC-012 representation `{config_sha256, self_pos, barriers, step, role}` with its frozen structural rules. No second v1 profile. |
| **`NonceRepresentationProfile`** | `LOWER_HEX_32` | **newly exact.** Identifies the current-v1 `NonceValue` representation `[0-9a-f]{32}` — 32 lowercase ASCII hex characters, no prefix, no whitespace, no normalization, no coercion. **PROJECT-CONTRACT: the source mandates a fresh nonce, not this encoding.** v1 supports exactly one. |

`KeyId` is unchanged from `SIGNATURE_AND_HASH_PROVENANCE.md` R12-FIX-A.

### R14-R1-B — `InteropProfileSet` final exact shape

```
InteropProfileSet(
    series_convention:            SeriesConvention,
    auth_profile:                 AuthProfile,
    key_id:                       KeyId,
    commitment_codec:             CommitmentCodec,
    result_profile:               ResultProfile,
    compatibility_profile:        CompatibilityProfile,
    tool_name_profile:            ToolNameProfile,
    canonicalization_profile:     CanonicalizationProfile,
    sealed_record_profile:        SealedRecordProfile,
    state_representation_profile: StateRepresentationProfile,
    nonce_representation_profile: NonceRepresentationProfile,
)
```

Field order exactly as written. All eleven are **SERIES-WIDE**, all are
**required — no `Optional` member**, none is a raw `str` where a closed type
exists, none is an arbitrary mapping, and **no default is hidden inside the value
object**: a caller must state every profile explicitly, because a silent default
is precisely how two peers end up believing they agreed on different things.

### R14-R1-C — every serialized token

`FIXED_ROLE` · `REFERENCE_ODD_EVEN_ALTERNATION` · `HMAC_SHA256` · `ED25519` ·
`STRICT_PROJECT_COMMITMENT` · `LECTURER_REFERENCE_COMMITMENT` ·
`STRICT_PROJECT_RESULT` · `LECTURER_ATTACHMENT_COMPATIBILITY` ·
`STRICT_COUNTED_MATCH` · `LECTURER_REFERENCE_COMPATIBILITY` ·
`PROJECT_LOGICAL_OPERATIONS` · `LECTURER_REFERENCE_ALIASES` ·
`CANONICAL_JSON_V1` · `SEALED_RECORD_V1` · `SEALED_STATE_V1` · `LOWER_HEX_32`.

**Ten closed profile types · 17 enum-member memberships · 16 unique serialized
token strings** *(corrected Stage 4E-R14-R1-FIX; an earlier draft said "sixteen
tokens across nine closed types", which undercounted the types)*.

Memberships per type: `SeriesConvention` 2 · `AuthProfile` 2 · `CommitmentCodec` 2
· `ResultProfile` 2 · `CompatibilityProfile` 3 · `ToolNameProfile` 2 ·
`CanonicalizationProfile` 1 · `SealedRecordProfile` 1 ·
`StateRepresentationProfile` 1 · `NonceRepresentationProfile` 1 = **17**.

Memberships exceed unique strings by one because
`LECTURER_ATTACHMENT_COMPATIBILITY` is deliberately the serialized token of
**both** `ResultProfile.LECTURER_ATTACHMENT_COMPATIBILITY` **and**
`CompatibilityProfile.LECTURER_ATTACHMENT_COMPATIBILITY`. They are **distinct
typed members** that happen to share a string; **neither is renamed to make token
strings globally unique**, because typed context already disambiguates them and
renaming would break the alignment with `COMPATIBILITY_PROFILES.md`.

**`KeyId` is the eleventh `InteropProfileSet` member but is not one of the ten
closed profile types** — it is a validated value, not a closed vocabulary.

### R14-R1-D — current-v1 single-profile restrictions

`CanonicalizationProfile`, `SealedRecordProfile`, `StateRepresentationProfile` and
`NonceRepresentationProfile` each have **exactly one v1 member**. That is
deliberate and matches NDEC-001/002/003: for current counted play both peers echo
the one required profile, and a differing echo **refuses counted play before
`CONFIG_LOCKED`** rather than being normalised or accommodated. A second member is
a **future-version change** requiring the contract extended, the representation
defined and both repositories implementing it. Single-member enums are kept rather
than elided so the lock context binds an explicit token instead of an implicit
assumption.

### R14-R1-E — `ConfigLockEvidence` cross-object invariant (STRUCTURAL)

Supervising ruling, frozen: inside `ConfigLockEvidence`,

```
auth.profile == context.profiles.auth_profile
auth.key_id  == context.profiles.key_id
```

**both MUST hold at construction.** All four values sit inside one immutable
composite, so a mismatch makes the evidence **self-contradictory before any peer,
network, key or clock is consulted** — that is a structural defect, not a runtime
disagreement. A mismatch raises **`ValueError`** under the existing
structural-validation policy; **`E-AUTH-*` identities are never constructor
exceptions** — they belong to the boundary layers.

This verifies **nothing cryptographic**. The LIVE layer still owns the
pre-provisioned profile/key expectation, actual MAC or signature verification,
peer identity, phase, replay/staleness and config-digest equality.

**No equivalent check exists on `Step0DeclarationExchange`**: `Declaration` is
subject data and deliberately owns **no** `auth_profile`/`key_id` source of truth
(§R14-R1-2), so there is nothing to compare. Bootstrap profile and key equality
stays LIVE against the pre-`BOOT` provisioned expectation, and **no auth member is
inserted into `Declaration` merely to manufacture a structural comparison.**

### R14-R1-F — status

**`INTEROP-PROFILE-VOCABULARY: RESOLVED-PROJECT`.** `NegotiatedConfig` is
untouched — still **35** core members, **15 FIXED / 9 MINIMUM / 9 NEGOTIABLE**,
with `token_budget_per_series` keeping its SOURCE-NEGOTIABLE status and
PRE-STEP0-AGREED / SERIES-WIDE / IMMUTABLE-AFTER-STEP0 project lifecycle.
`FIELD_MATRIX.md` is unchanged at **74 = 15/39/9/11**: every type frozen here is a
Python supporting value, **not an artifact row**.

## Stage 5-R8 — the counted turn contract is named by the posture

`CompatibilityProfile` now has four members:

| Token | Meaning |
|---|---|
| `STRICT_COUNTED_MATCH` | **Legacy.** The pre-R8 turn result: `Reveal` answered with a game-legality `bool`. Parseable, and **not** accepted for current counted play. |
| `STRICT_COUNTED_MATCH_TURN_OUTCOME_V1` | **Current default and sole strict counted emitter.** `Reveal(cursor, action, hint, capture_claim?)` answers with `TurnOutcome(accepted, capture)`; `CaptureAnswer` is `NO_QUESTION` / `NOT_CAUGHT` / `CAUGHT`; the sealed eight-member commitment record is unchanged. It **also** binds the final-audit half of the same contract: the disclosure carries the `capture[]` transcript, the transcript is compared row for row against what was observed live, and `state.self_pos` / `state.barriers` are read as **pre-action** (JDEC-016 §4). |
| `LECTURER_REFERENCE_COMPATIBILITY` | Reference artefact/tool-name compatibility. It does **not** imply the synchronous `TurnOutcome` exchange — the reference answers a capture claim on a later message — and is refused for counted turn play until a real adapter proves the whole exchange. |
| `LECTURER_ATTACHMENT_COMPATIBILITY` | Attachment/artefact compatibility only; it says nothing about the live turn protocol. |

Both peers must echo `STRICT_COUNTED_MATCH_TURN_OUTCOME_V1` **before**
`CONFIG_LOCKED`. The check lives in `app/turn_contract_gate.py` and runs inside
the existing config-negotiation profile comparison — there is no second
negotiation subsystem, no new operation and no new error identity; a mismatch
raises the existing `E-CONFIG-MISMATCH`. Nothing sniffs the response shape at
the first reveal, and there is no fallback from `TurnOutcome` to `bool`.

**The profile fixes the sealed-state timing, not only the live shape.** Two
peers that echo this posture must read every `state` snapshot the same way or
their semantic audits disagree on the same bytes:

* `state.self_pos` — the mover's cell **before** that step's action. A
  post-action reading would put the piece one cell ahead of where the opponent's
  capture question was answered, so the same transcript would recompute to a
  different `CaptureAnswer`.
* `state.barriers` — the public barrier set **before** that step's action:
  everything revealed in steps `1…k-1` by either side, and nothing revealed at
  step `k`, because both commitments for a step are sealed before either reveal.

This is stated once in **JDEC-016 §4/§6** and repeated here because it is part
of what selecting this profile promises. It adds no fifth profile value and no
new decision id.


## Stage 5-R8 — the agreed scent model is locked beside this core, never inside it

Four things must not be conflated, and the lock binds two of them:

| Thing | What it is | Digest |
|---|---|---|
| `NegotiatedConfig` | the **35-member** Appendix-B core, unchanged; `pheromones` carries exactly the three Appendix-F scalars (`center_intensity` 0.9, `decay` 0.10, `field_size` 5) | `config_sha256` — over this core **only** |
| `ScentModelAgreement` | the **complete** agreed emission/decay model: model id, those same three values, all 25 kernel weights and the worked numeric examples | `scent_model_sha256` — over the model **only** |
| `ConfigLockContext` | `game_id`, `game_uid`, `sub_game`, `config_sha256`, `profiles`, `scent_model_sha256` — **six** members | authenticated as a whole by the existing keyed proof |
| `config_auth` | the keyed `AuthProof` over `b"config" + canonical_json_bytes(lock_context_core)` | unchanged framing |

Two statements are therefore false and must never be written anywhere: that the scent
model's fields are part of `NegotiatedConfig`, and that `config_sha256` covers the scent
model. The model is a **separate** agreement with a **separate** identity; the single
authenticated context binds both identities without merging them. The reasoning is
recorded in **C-14** and the representation is frozen by **JDEC-017**; the recurrence
itself remains **C-10**'s resolution and is not restated here.
