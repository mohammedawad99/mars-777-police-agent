# Lecturer Reference Repository Audit — group MaRs-777

**Status: STAGE 2A-R — read-only reference research. No reference code was copied.**

> **REFERENCE STATUS: NON-BINDING IMPLEMENTATION EXAMPLE**
> **BOOK STATUS: AUTHORITATIVE**
>
> A behaviour is **never** treated as lecturer-mandatory merely because the reference
> repository implements it. Where reference and book disagree, **the book wins**.

## 1. Snapshot (independently discovered)

| Item | Value |
|---|---|
| URL | `https://github.com/rmisegal/Game-P2P-Cop-Chase` |
| Default branch | `master` |
| HEAD SHA | `960499fd5e8777b4929625f5d8fdcf2ab4677b54` |
| HEAD date | 2026-07-12T21:08:33+03:00 |
| HEAD subject | `Release v3.0.0 — align code and guidelines-book versions to 3.0.0` |
| Commits / tags | 38 commits · 8 tags (latest `v3.0.0`) |
| Declared version | `3.0.0` (pyproject `version = "3.0.0"`) |
| Python requirement | **`>=3.13`** (`.python-version` = 3.13) |
| Runtime dependency | **`fastmcp>=3.4.3`** (single runtime dep) |
| Dev dependencies | `pillow>=12.3.0`, `pytest>=9.1.1`, `pytest-cov>=7.1.0`, `ruff>=0.15.20` |
| Coverage floor | `fail_under = 85` (GUI + MCP server/client omitted from coverage) |
| Source size | 101 `.py`, ~4 414 LOC; largest file 167 lines |
| Tests | 39 test files, **254 test functions** |
| License | Educational-Use EULA (GTAI / Dr. Yoram Segal) |

**Book copy inside the reference:** `docs/police_thief_p2p.pdf`, SHA-256
`7c9e1d7527582c3aef9afd71709981cea50ea60b8fabefe85efccab0a5fdd02e` — **byte-identical
to our authoritative copy**. This independently confirms our Stage-1 baseline read the
correct v3.0.0 book.

## 2. Feature classification

| # | Observed reference feature | Classification |
|---|---|---|
| 1 | Shared `game.json` uses the exact Appendix B key structure and Appendix F values (grid 7, agents 2, move set, 14/35/35, 20/5/5/10/2/0, 0.9/0.10/5, 30/60, 10/2/10/200000, 30/2/5/3/100) | **REFERENCE-MATCHES-BOOK** |
| 2 | `_note` explicitly states "the pre-game **signature exchange** refuses to play on any mismatch" | **REFERENCE-MATCHES-BOOK** (confirms our K2 reading of App B p.128) |
| 3 | Commit-reveal per step, SHA-256, fresh CSPRNG nonce, nonce revealed at end-of-game audit, both peers re-verify | **REFERENCE-MATCHES-BOOK** |
| 4 | Commit construction `SHA256(canonical_json(payload) + "\|" + nonce)` — **nonce concatenated outside** the canonical payload | **REFERENCE-EXAMPLE-ONLY** (book requires a canonical sealed record + SHA-256; this exact framing is one representation) → interop-critical, see delta D-01 |
| 5 | Sealed payload keys: `step, state(string), position, move, intent, verdict, hint, prompt_discussion{...}, model, tokens_step, tokens_total, response_seconds, random_move`; **no `role`, no `sub_game`** | **REFERENCE-EXAMPLE-ONLY** → delta D-02 |
| 6 | Payload carries **both** `intent` and `verdict` set to the *same* value (`decision.verdict`), commented "kept for existing consumers" | **REFERENCE-MATCHES-BOOK** — independently corroborates our **C-08** finding that verdict ≡ intent |
| 7 | `VERDICT_TRUTH = "truth"`, `VERDICT_LIE = "lie"` enum values | **REFERENCE-ENGINEERING-PATTERN** |
| 8 | `_canonical()` = `json.dumps(sort_keys=True, ensure_ascii=False, separators=(",",":"))` | **REFERENCE-ENGINEERING-PATTERN** (matches our JDEC-002 except it fixes `ensure_ascii=False`) → delta D-03 |
| 9 | Negotiation "signature" = `SHA256(canonical(terms) \| nonce)` with the **nonce transmitted in the clear**; **no key of any kind** | **REFERENCE-CONFLICTS-WITH-BOOK** → delta D-04 (see §4) |
| 10 | **No HMAC, no pre-shared key, no asymmetric crypto anywhere** (verified: only `hashlib.sha256` + `secrets.token_hex` in the whole tree) | **REFERENCE-CONFLICTS-WITH-BOOK** → delta D-04 |
| 11 | Identity is deliberately **not** covered by the negotiation signature | **REFERENCE-EXAMPLE-ONLY** |
| 12 | **Role alternation across sub-games** (`role_for()`: natural role on odd, opposite on even) | **REFERENCE-ONLY** — book is silent → delta D-05, chatbot Q1 |
| 13 | FastMCP tools: `negotiate`, `receive_turn`, `submit_audit`, `receive_control`; server name `police-thief-{role}` | **REFERENCE-ONLY** (book mandates FastMCP, not these names) → delta D-06, chatbot Q2 |
| 14 | Transport is poll-based inboxes (`poll_turn`, `poll_control`, `drain_inboxes`) with retry wrapper | **REFERENCE-ENGINEERING-PATTERN** |
| 15 | `num_games` default **1** in the shipped `game.json` | **REFERENCE-MATCHES-BOOK** as an *illustrative default* — confirms our **C-05** (counted series = 6) |
| 16 | Extra pheromone key `pheromone_min_center_intensity: 0.5` **inside the signed config** | **REFERENCE-ONLY** — not an Appendix F row → delta D-07 |
| 17 | Comment keys `_note`, `_axis_note`, `_hint_max_words_note` **inside the signed config** | **REFERENCE-ONLY** → delta D-08 (byte-identity risk) |
| 18 | Private `game.toml`: ports 8801/8802, `127.0.0.1`, `turn_timeout_seconds = 180`, `step_deadline_seconds = 30`, `seed = 1234` | **REFERENCE-ONLY** local settings — confirms our **C-02** (180 s is private, not the negotiated 30/60) |
| 19 | Strategy plug-in seam: `thief_class` / `police_class` = `"my_team.strategy:MyThiefBrain"` | **REFERENCE-ENGINEERING-PATTERN** — independently validates our `StrategyPort` design |
| 20 | LLM providers: `template` (no LLM, no tokens, no network — **default**), `claude_api`, `ollama`, `claude_cli`; `every_n_steps` throttle | **REFERENCE-MATCHES-BOOK** — confirms a real **zero-token** default path |
| 21 | LLM used for *trash-talk / hints only*; deadline miss ⇒ **random legal move** | **REFERENCE-MATCHES-BOOK** (LLM-001: movement algorithmic) |
| 22 | Replay loads the **opponent's sibling log** to draw both true paths | **REFERENCE-MATCHES-BOOK** — legitimate *post-game* use of revealed evidence (see §6) |
| 23 | Sliding-window rate limiter with FIFO wait queue, `max_depth`, `drain_interval`, `timeout` | **REFERENCE-ENGINEERING-PATTERN** |
| 24 | `derive_game_ids()` produces `game_id`/`game_uid` by hashing terms + both group ids | **REFERENCE-ENGINEERING-PATTERN** — corroborates `game_uid` being source-named (our D3) |
| 25 | Python `>=3.13`, coverage floor 85 | **REFERENCE-ONLY** environment choice (ours: 3.12, floor 90 — stricter) |

## 3. Component comparison vs Stage-2A architecture

| Component | Reference | Stage-2A | Verdict |
|---|---|---|---|
| Packages | `domain, peer, infra, shared, strategy, report, sdk, gui` | `domain, app, protocol, infra` | **SAME-CONCEPT**, different grouping |
| CLI | `cli.py` + `__main__.py` | deferred to 2C | NOT-APPLICABLE yet |
| FastMCP server / client | `infra/mcp_server.py`, `infra/mcp_client.py` | `infra.mcp_server`, `infra.mcp_client` | **SAME-CONCEPT** |
| Orchestrator | `peer/runtime.py` + `sdk/series.py` | `app.orchestrator` + `app.turn_service` | **SAME-CONCEPT** |
| State machine | implicit in `runtime.py` / `turn_handler.py` | **explicit** `app.state_machine` with a documented transition table | **OUR-DESIGN-STRONGER** |
| Strategy | `domain/brains.py` + plug-in seam | `StrategyPort` + `Observation`/`ProposedAction` wall | **OUR-DESIGN-STRONGER** (privacy typed into the seam) |
| Belief map | `domain/belief.py` | `domain.belief` | **SAME-CONCEPT** |
| Scent | `domain/smell.py` | `domain.scent` | **SAME-CONCEPT** |
| Barriers | inside `domain/rules.py` | `domain.barriers` + `domain.rules` | **REFERENCE-DIFFERENT** (we separate) |
| Config | `shared/config.py` (JSON + TOML overlay) | `CONFIG_ARCHITECTURE.md` 4 kinds + precedence | **OUR-DESIGN-STRONGER** (explicit no-override rule for binding config) |
| Commit-reveal | `domain/crypto.py`, `peer/sealing.py` | `protocol.commitment` + `protocol.canonical` | **SAME-CONCEPT** |
| Step-0 | `sealed_spec_record()` (SHA-256 seal only) | `protocol.declaration` + **keyed** `step0_auth` | **OUR-DESIGN-STRONGER** (book-required keyed auth) |
| Logs | `report/artifacts.py`, `report/emit.py` | `infra.logger` + `infra.artifacts` | **SAME-CONCEPT** |
| Replay | `gui/replay*.py` | `infra.replay` (**files-only, offline**) | **OUR-DESIGN-STRONGER** (replay cannot touch live state) |
| GUI | `gui/` (Tkinter) | `infra.gui` projection consumer | **SAME-CONCEPT** |
| Reporting | `report/report_writer.py`, `infra/email_sender.py` | `infra.reporter` | **SAME-CONCEPT** |
| Gatekeeper / limiter | `shared/gatekeeper.py`, `shared/rate_limiter.py` | `infra.gatekeeper` | **SAME-CONCEPT** |
| Tests | 254 functions, 39 files | 12 layers + 20 mandatory negative tests | **USEFUL-PATTERN** (see §7) |
| Scripts | `sync_versions.py`, `render_docs_images.py` | none | **USEFUL-PATTERN** (version sync) |

## 4. Cryptographic finding (highest-severity)

The reference calls its handshake value a **"signature"** 18 times, but it is computed as:

```
signature = SHA256( canonical_json(terms) + "|" + nonce )     # nonce sent in the clear
```

Precisely classified:

| Primitive | Present in reference? |
|---|---|
| **HASH** (unkeyed SHA-256) | **Yes** — this is what it actually uses |
| **HMAC / MAC** (keyed) | **No** — no `hmac` import, no key anywhere |
| **DIGITAL SIGNATURE** (asymmetric) | **No** |
| **ACKNOWLEDGEMENT** (both compare equal digests) | **Yes** — this is the real mechanism |

Because the nonce is disclosed with the message, **any party can recompute the value**;
it proves message integrity and mutual agreement on terms, **but not producer
identity**. It is therefore an *acknowledgement*, not authentication.

The book requires Step-0 to be **"cryptographically signed using a pre-supplied key
(מפתח המסופק מראש) so it cannot be forged retroactively"** (Ch 5 p.55–56) and App B
p.128 requires a pre-game **signature exchange**. The reference does not implement a
keyed mechanism.

**Resolution: BOOK WINS.** Our locked Stage-1D.1 decision (keyed authentication;
HMAC-SHA256 as a labelled PROJECT-CONTRACT default, JDEC-013) **stands unchanged**. We
do **not** inherit the reference's terminology, and we do not downgrade to an unkeyed
digest. Chatbot questions **Q4/Q5** ask the lecturer to confirm the acceptable primitive.

## 5. Series / role semantics

`sdk/series.py` implements alternation explicitly:

```
role_for(natural, sub_game_number) -> natural if odd else opposite
```

with the docstring: *"Roles alternate: a peer plays its config-natural role on odd
sub-games and the opposite on even ones, so the two peers always stay consistent."*
`peer/sealing.py` reinforces it: *"Roles alternate across sub-games, so identity is
per-GROUP (not per-role)."*

**Independent book search found no supporting or contradicting requirement.** Searched
(UTF-8 extraction of all 160 pages): `החלפת תפקידים`, `מתחלפים`, `לסירוגין`,
`מחליפים תפקיד`, `החלפת התפקידים`, `תפקידים מתחלפים` → **0 hits each**;
`alternat` → 1 hit (unrelated: "Two Equal Alternatives" about RL, p.~63);
`rotate` → 1 hit (unrelated: rotating leaked credentials, p.~121). The 15 occurrences of
`תפקיד` are all unrelated (tuple elements, model roles, file roles).

**Classification: SOURCE-AMBIGUOUS → CHATBOT-CLARIFICATION-REQUIRED (Q1).**

**Important architectural observation (no change made).** The reference is a **single
repository containing both roles**, so it must switch role *inside one codebase*. Our
project has **two repositories, one per role, and a team owns both**. Series-level
alternation is therefore naturally expressible without changing our architecture: in
sub-game 1 our **police** repo plays their thief; in sub-game 2 our **thief** repo plays
their police. Each repository keeps its fixed, natural role. This is a *match
orchestration* question, not a role-architecture question — but it must be confirmed
before Stage 2B fixes the series driver. **No role-architecture change was made.**

## 6. GUI / replay privacy

- **Live GUI (reference):** shows own truth + belief; no opponent-truth channel.
- **Post-game replay (reference):** `gui/replay_data.py::opponent_positions()` locates
  the opponent's sibling log so *both true paths can be drawn*.

This is legitimate: after the final audit all nonces and sealed records are disclosed,
so replay operates on **revealed evidence**, not live private state. It is **not**
permission for a live GUI to know opponent truth.

**Our architecture is unaffected and remains safe:** `DATA_FLOW.md` §9 keeps the live
GUI on projection events (belief labelled as belief), while `infra.replay` reads sealed
artifacts only, offline. The distinction the reference demonstrates is already ours.

## 7. Strategy findings

`domain/brains.py` + `strategy/` ship an intentionally basic heuristic with a documented
plug-in seam (`thief_class` / `police_class`). Deterministic via a private `seed`; on LLM
deadline miss it falls back to a **random legal move**.

**Use as:** BASELINE-OPPONENT (benchmark target), INTERFACE-REFERENCE (the plug-in seam
validates our `StrategyPort`), SIMULATION-REFERENCE (self-play harness).
**Do NOT copy it as our competitive strategy** — it is explicitly basic, and copying
would forfeit the competitive dimension of the grade. Our benchmark plan: run our
strategy against a reference-equivalent baseline in the SIMULATION test layer and track
capture rate / survival length / decision latency over seeded series.

## 8. Environment / numeric drift

| Item | Reference | Appendix F / ours | Verdict |
|---|---|---|---|
| grid_size | 7 | 7 (MINIMUM) | match |
| num_agents | 2 | 2 (FIXED) | match |
| max_barriers / max_moves / survival_threshold | 14 / 35 / 35 | same (MINIMUM) | match |
| scoring 20/5/5/10/2 + technical_loss 0 | same | same (FIXED; technical_loss via C-07) | match |
| pheromones 0.9 / 0.10 / 5 | same | same (FIXED) | match |
| **`pheromone_min_center_intensity`** | **0.5 (extra key)** | **not an Appendix F row** | **REFERENCE-ONLY** (D-07) |
| response / watchdog | 30 / 60 | 30 / 60 (**NEGOTIABLE**) | match (defaults) |
| num_games | **1** | **6 FIXED** for a counted series | reference default is illustrative (C-05) |
| diversity/min_games/max_games/token budget | 10 / 2 / 10 / 200000 | same | match |
| rate limiter 30 / 2 / 5 / 3 / 100 | same | same (MINIMUM) | match |
| `hint_max_words` | 15 | 15 (NEGOTIABLE) | match |
| `schema_version` | "1.3" | value EXAMPLE-ONLY (JDEC-003) | reference confirms it drifts |
| Python | **>=3.13** | ours 3.12 | **REFERENCE-ONLY** — book does not bind a Python version |
| Ports | 8801 / 8802, `127.0.0.1` | local settings | **REFERENCE-ONLY** |
| `turn_timeout_seconds` | 180 (private TOML) | private, not the negotiated 30/60 | confirms **C-02** |
| Coverage floor | 85 | ours **90** | ours stricter — keep |
| Runtime dependency | `fastmcp>=3.4.3` | none yet | adopt in PRD-02/05 with justification |

**No Appendix-F value is contradicted by the reference.** The only in-config extras are
`pheromone_min_center_intensity` and the `_note` comment keys.

## 9. Reference test suite (idea extraction — no test copied)

| Reference test | Behaviour tested | Book requirement | Our planned test | Gap? |
|---|---|---|---|---|
| `test_crypto.py` | seal/verify/audit, mismatch raises | CRYPTO-001/009, REPLAY-002 | #4 hash mismatch | covered |
| `test_negotiation.py` | terms mismatch + signature verify | GAME-001, App B p.128 | #11 config mismatch | covered (ours adds keyed auth) |
| `test_series.py` | series loop + **role alternation** | *none found* | — | **GAP → depends on Q1** |
| `test_rules.py` / `test_board.py` | movement/barrier legality | GAME-003, BAR-* | #2, #3 | covered |
| `test_scoring.py` | Appendix F scoring | GAME-006 | domain unit | covered |
| `test_smell.py` / `test_belief.py` | scent field + belief update | SCENT-*, GUI-002 | domain unit | covered |
| `test_rate_limiter.py` / `test_gatekeeper.py` | RPM, queue depth, overflow, timeout | NET-002/003 | #9, #10 | covered |
| `test_protocol.py` / `test_turn_handler.py` | turn message shape, sequencing | STATE-* | #7 stale/duplicate | covered |
| `test_transport_drain.py` | draining stale inboxes on restart | — | **new idea** | **adopt as an edge case** |
| `test_artifacts.py` / `test_report_writer.py` | four-artifact emission + fields | JSON-*, REPORT-* | artifact tests | covered |
| `test_replay_data.py` / `test_replay_normalize.py` | replay reconstruction | REPLAY-001/002 | #13, #20 | covered |
| `test_deadline_controls.py` | step deadline → fallback move | STATE-004 | #8 timeout | covered |
| `test_port_check.py` | port already in use | — | **new idea** | **adopt (BOOT failure)** |
| `test_config.py` | config version/validation | GAME-002 | #11 | covered |
| `test_sysinfo.py` | hardware spec collection | CRYPTO-006 | Step-0 test | covered |
| `test_llm_provider.py` | provider fallback | LLM-001 | #19 zero-token | covered |
| `integration/test_mcp_match.py` | two real MCP servers end-to-end | ARCH-001 | CROSS-PROCESS layer | covered |
| — | **cross-OS canonical byte equality** | JDEC-002 | #16 | **reference has no equivalent — ours is stronger** |
| — | **wrong keyed-auth key** | CRYPTO-006 | #5 | **reference cannot test (no keyed auth)** |
| — | **privacy-leak scans** | GUI-001/002 | #17 | **reference has no equivalent** |

**Three new edge cases adopted:** inbox draining after restart, port-in-use at boot,
and version-sync consistency.

## 10. What we deliberately do NOT take

- The unkeyed "signature" and its terminology (§4).
- The `payload | nonce` commitment framing as *our* locked contract (ours keeps the
  nonce inside the canonical sealed record; the exact wire form is NEGOTIATED-PRE-MATCH).
- `_note` comment keys and the extra pheromone key inside a byte-identical signed config.
- `num_games = 1` for a counted series.
- Python `>=3.13` and coverage floor 85.
- The basic shipped strategy as our competitive strategy.

## 11. Stage-2A-R2 resolution of all open items

All previously open (ASK-CHATBOT / CLARIFICATION-CANDIDATE) items are now closed —
see `ATTACHMENT_EVIDENCE.md`, `CHATBOT_ANSWERS.md`, `COMPATIBILITY_PROFILES.md` and
`STAGE1_CLARIFICATION_IMPACT.md`.

| Item | Resolution |
|---|---|
| Role alternation (§5) | **ATTACHED-EXAMPLE-CONVENTION + REFERENCE-CONVENTION + PROJECT-SUPPORTED.** Book silent → **no new MUST**. Architecture supports it via a `SeriesLauncher` that selects the appropriate **independent** role process per sub-game; the two role repositories stay independent and are **not** merged |
| Step-0 auth (§4) | Book requires **keyed producer authentication with a pre-supplied key**; the reference's unkeyed `SHA256(terms\|nonce)` does **not** satisfy it. `AuthProfile` = **HMAC_SHA256** (project default) or **ED25519** (attachment-example compatibility, AE-02). Plain SHA-256 rejected for strict Step-0 |
| Config auth | Byte-identity + auth-exchange semantic **SOURCE-REQUIRED**; **exact primitive SOURCE-UNSPECIFIED**. Step-0's explicit "pre-supplied key" wording is **not** transferred onto the looser config wording |
| Commitment construction/fields | Locked 8-field contract retained; reference framing only through a future negotiated `CommitmentCodec` |
| FastMCP tool surface | Reference names kept as **compatibility defaults**, not book-mandated |
| `pheromone_min_center_intensity` | **REFERENCE-ONLY** — absent from Appendix F *and* from the reported attachment |
| Config `_note` keys | **ATTACHED-EXAMPLE-CONVENTION.** Strict emitter excludes them; the attachment (2 keys) and the reference (3 keys) disagree, which itself shows they are presentational |
| Result static metadata | **Corrected:** four-artifact-set self-containment (JDEC-014). Result references the declaration; it does not duplicate MCP/hardware/member data |
| `<NN>` | Project convention `g01`…`g06` (JDEC-004); not SOURCE-MANDATORY |

**Reference-repo status is unchanged: NON-BINDING IMPLEMENTATION EXAMPLE.**
