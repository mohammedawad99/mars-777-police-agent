# JSON Source Map — group MaRs-777

**Status: REVIEWED — Stage 1B supervising review PASS. This is a SOURCE MAP, NOT a schema.**
No JSON Schema is produced here. No fields are invented. The actual contracts
were constructed in **Stage 1C/1D/1D.1** (now reviewed and LOCKED), using this
approved map as input. Approval does NOT authorize invented JSON fields or schemas;
this map deliberately leaves field-level items open and the **now-locked JSON
contracts** (`docs/spec/json/`) resolve them.

Four mandatory JSON document types are attached to the book as examples and
described in Chapter 9 (PDF p.94–95 / book 78–79), named via Appendix F Table 20
(PDF p.157). Names derive from `game_id` and sub-game `<NN>`; the four share a
common `game_uid` (PDF p.95). Below, each type lists purpose, naming rule, every
contributing book section, cryptographic/replay/reporting relevance, whether the
source is binding or illustrative, and unresolved questions.

---

## 1. `declaration_<game_id>.json` — pre-game declaration

- **Purpose:** Fix, cryptographically, everything that does **not** change during the whole game (all sub-games): identity of both teams and members, police & thief repo addresses, MCP server addresses, hardware specs, LLM model, agreed token cap, game start/end times. Includes the **Step-0** hardware declaration and the per-game GitHub commit hash. (PDF p.94,55–56 / book 78,39–40)
- **Naming rule:** `declaration_<game_id>.json` — one per game (not per sub-game). Reference-only table, not negotiated. (PDF p.157 / book 141)
- **Contributing sections:**
  - Ch 9 §9.3.3 — content list (teams, members, repos, MCP addresses, hardware, model, token cap, times). PDF p.94.
  - Ch 5 §5.5 — Step-0 hardware fields: OS, CPU cores+freq, RAM, GPU/VRAM presence, LLM model name, code version, group name, sub-game number; cryptographically signed; **`github_commit`** per game. PDF p.55–56.
  - App F Table 20 — variable name & role. PDF p.157.
  - App F Table 18 #4 — token cap (`token_budget_per_series`). PDF p.154.
- **Cryptographic relevance:** signed with a pre-supplied key; Step-0 hardware+tokens locked to prevent later denial (CRYPTO-006, CRYPTO-011, PERF-002).
- **Replay relevance:** anchors the fairness/repro context (commit hash → exact code) for audit.
- **Reporting relevance:** identity & commit hash surface again in the result report and per-game email.
- **Binding vs illustrative:** the **content requirements** (identity, repos, hardware, commit hash, tokens) are binding (E-24, E-53, E-54); the **exact JSON layout** shown is illustrative.
- **Open questions:** exact field names/keys for Step-0 hardware; signature scheme/key provenance ("pre-supplied key", PDF p.55) not fully specified — **REVIEW REQUIRED** at Stage 1C.

## 2. `config_<game_id>_g<NN>.json` — the signed shared config ("constitution")

- **Purpose:** Define the agreed physics/scoring rules for a sub-game — every quantitative parameter (Appendix F), cryptographically locked and byte-identical between the two sides. (PDF p.94,128 / book 78,112)
- **Naming rule:** `config_<game_id>_g<NN>.json`; **a different name per game** to allow replay of each game's config (App F §2.3). PDF p.156–157.
- **Contributing sections:**
  - App B §B.3 — full structure & sections: `schema_version`, `agreed_between`, `board_and_agents`, `world`, `movement_and_barriers`, `scoring`, `pheromones`, `network_and_league`, `rate_limiter_gatekeeper`. PDF p.128–130.
  - App F Tables 13–19 — the binding values behind every key (one-to-one mapping stated PDF p.130).
  - App F §2 — mandatory config rules (identical, crypto-locked, attached to repo). PDF p.156.
  - Ch 3 §3.2 — config as the game "contract" enforced by agents. PDF p.34.
- **Cryptographic relevance:** canonically serializable (sorted keys) → consistent `config_sha256`; byte-identical load + pre-game signature exchange refuses to play on mismatch (GAME-001, JSON-004). PDF p.127–128.
- **Replay relevance:** the physics context every log step is verified against.
- **Reporting relevance:** the agreed terms underpinning the result.
- **Binding vs illustrative:** **field names are fixed and binding** (PDF p.130); **values** are the Appendix F floors/defaults and may move only in the allowed direction. The shown numbers are the binding defaults.
- **Open questions:** `schema_version` value governance ("1.2" shown) — illustrative or pinned? Where exactly the signature/`config_sha256` lives (inside the file vs a sidecar) — **REVIEW REQUIRED**. (`num_games` is **resolved**: counted series = **6, FIXED**; App B `1` is an illustrative demo — see `CONFLICT_REGISTER.md` C-05, closed.)
- **Field classification (Stage 1B):** all `config/game.json` section+field keys are **EXPLICIT KEYS** (App B §B.3 prints them, PDF p.129–130); `agreed_between` example values `["group-a","group-b"]` are example-only; `config_sha256`/signature location is **REVIEW REQUIRED**. Full per-file classification (EXPLICIT KEY / EXPLICIT SEMANTIC-FIELD-KEY-UNKNOWN / EXAMPLE-ONLY / REVIEW REQUIRED) is in `STAGE_1B_CROSS_AUDIT.md` §J.

## 3. `log_<game_id>_g<NN>.json` — sub-game log

- **Purpose:** Step-by-step record enabling full cryptographic verification in the Replay simulator: Commit-Reveal commitments, moves, hints and LLM-discussion fields, plus the Nonce and hash. (PDF p.94–95 / book 78–79)
- **Naming rule:** `log_<game_id>_g<NN>.json` — one per sub-game. PDF p.157.
- **Contributing sections:**
  - Ch 5 §5.3 — sealed record fields: `State`, `Move`, `Intent`, `Nonce`, plus (per PDF p.50,74) hint, verdict/intent classification, step number, role, sub_game; `Hcommit` computed via canonical JSON. PDF p.50–53.
  - Ch 5 §5.4 — final audit: all nonces revealed at game end; recompute & compare. PDF p.55.
  - Ch 7 §7.4–7.5 — Replay Viewer reads `(nonce, move, commit)` per entry and recomputes SHA-256. PDF p.72–74.
  - Ch 9 §9.3.3 — the log is one of the four attached JSON files. PDF p.94.
- **Cryptographic relevance:** the primary integrity artifact — each entry's commitment must match the recomputed hash (CRYPTO-003, CRYPTO-008, REPLAY-002).
- **Replay relevance:** **the** replay input; a single mismatch → TAMPERED → match void.
- **Reporting relevance:** basis for the mutual audit that precedes the agreed result.
- **Binding vs illustrative:** the **need** to log every step's commit-reveal data and to verify it is binding (E-17..E-20); the reference code's simplified `f"{nonce}|{move}"` payload (PDF p.74) is explicitly a **simplification** — the real signature covers State/Move/Intent/Nonce (+more). The exact JSON layout is illustrative.
- **Open questions:** canonical field ordering & exact key names of a log entry; how the hint/LLM-discussion fields are represented; whether `game_uid` and roles are per-entry or header — **REVIEW REQUIRED** at Stage 1C.

## 4. `result_<game_id>.json` — final results report (the emailed binding report)

- **Purpose:** Summarize all sub-games — each team's score per sub-game and the cumulative result — for league scoring by the lecturer. This is the **binding report emailed** to `[ agent reports address ]`. (PDF p.95,94 / book 79,78)
- **Naming rule:** `result_<game_id>.json` — one per game. PDF p.157.
- **Contributing sections:**
  - Ch 9 §9.3.3 — mandatory fields include: both teams' identity, both teams' **GitHub links** (four total), FastMCP server addresses, signed hardware declarations, game timestamp, SHA-256-backed mutual-agreement approvals, **per-sub-game commit hash** (`github_commit`), and **total tokens consumed**. PDF p.94,95.
  - Ch 9 §9.4 — four GitHub links appear in the emailed JSON (2 of team A + 2 of team B). PDF p.96.
  - App E #49, #54 — four links; total tokens. PDF p.149–150.
  - App F Table 20 — variable name & role; recipient address. PDF p.157.
  - Ch 5 §5.5 — `github_commit` field origin. PDF p.56.
- **Cryptographic relevance:** carries SHA-256-backed mutual-agreement approvals & signed hardware declarations (E-35, E-36).
- **Replay relevance:** references the logs/commits that the Replay Viewer verifies.
- **Reporting relevance:** **the** report — must be JSON, sent as an attachment by **each** team separately to the fixed reports address; non-JSON or one-sided → rejected / 0 (E-32,E-33,E-34,E-35, JSON-001/002, REPORT-001/002).
- **Binding vs illustrative:** the **required fields** (identities, four links, commit hashes, tokens, mutual approval, scores) are binding; the exact JSON layout is illustrative.
- **Open questions:** exact key names & nesting for scores per sub-game and cumulative; representation of the four links and the mutual-approval signatures; whether declaration/config are embedded or referenced — **REVIEW REQUIRED** at Stage 1C.

---

## Cross-cutting notes

- **Shared identifiers:** all four files carry a common `game_uid`; names derive from `game_id` (+ `g<NN>` for config/log). (PDF p.95,157)
- **Canonical serialization** (sorted keys, fixed separators, UTF-8) governs anything hashed (config, commit payloads) so both peers produce byte-identical bytes (Ch 5, App B). This is the **same** canonicalization the Stage 0 `.gitattributes` LF/UTF-8 policy protects.
- **Format family (App B §B.2):** JSON for anything shared/signed/exchanged (the four files + `config/game.json` + `rate_limits.json`); TOML only for the private, unsigned per-peer `config/game.toml`. (PDF p.127)
- **Do not** invent fields or write schemas here. Stage 1C builds the contracts from this map after review.
