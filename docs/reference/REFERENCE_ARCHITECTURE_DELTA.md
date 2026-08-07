# Reference ↔ Architecture Delta — group MaRs-777

**Status: STAGE 2A-R — analysis only. No implementation. No Stage-1 fact changed.**

Authority order applied throughout: **book → Appendix E → Appendix F → locked Stage-1
decisions → reference repository → chatbot → our engineering choices.**

Outcomes: `KEEP-OUR-DESIGN` · `ADOPT-REFERENCE-PATTERN` · `DEFER-TO-PRD` ·
`ASK-CHATBOT` · `SPECIFICATION-CONFLICT`.

| ID | Topic | Book position | Locked Stage-1 position | Reference behaviour | Stage-2A behaviour | Risk | Recommendation |
|---|---|---|---|---|---|---|---|
| **D-01** | Commitment construction | Canonical sealed record hashed with SHA-256; nonce is part of the commitment (Ch 5 p.50–53) | `H_commit = SHA256(canonical(sealed_record))`, nonce **inside** the 8-field record; composition + canonicalization are **NEGOTIATED-PRE-MATCH** (NDEC-001/002/003) | `SHA256(canonical_json(payload) + "\|" + nonce)` — nonce **outside**, appended after a `\|` separator | nonce inside canonical record | **High** — if the two peers frame the commitment differently, neither can recompute the other's hash and every turn reads as TAMPERED | **ASK-CHATBOT (Q3)** + **KEEP-OUR-DESIGN** as our default. Our Stage-1 already classifies this as negotiated, so either framing can be agreed pre-match without a spec change |
| **D-02** | Sealed payload fields | Prose lists state, move, intent-classification, hint, step, role, sub_game, nonce | Locked 8-field set `{state, move, intent, hint, step, role, sub_game, nonce}` | 13+ keys incl. `position`, `prompt_discussion`, `model`, `tokens_step/total`, `response_seconds`, `random_move`; **omits `role` and `sub_game`** (sub-game index lives in the step-0 record) | locked 8-field set | **Medium** — richer payloads are fine locally but must match for cross-recompute | **ASK-CHATBOT (Q3)** + **KEEP-OUR-DESIGN**; exact field list is NDEC-001 (negotiated) |
| **D-03** | Canonical JSON parameters | "canonical, sorted keys, fixed separators, UTF-8, byte-identical" | JDEC-002: `sort_keys=True`, `separators=(",",":")`, UTF-8, NFC, LF, no trailing newline; **`ensure_ascii` fixed and agreed** | `sort_keys=True`, `separators=(",",":")`, **`ensure_ascii=False`** | same, with `ensure_ascii` agreed pre-match | **Medium** — Hebrew/non-ASCII hints make this decisive for byte-identity | **ADOPT-REFERENCE-PATTERN** as our *default proposal* (`ensure_ascii=False`) while keeping it NEGOTIATED (NDEC-003). Also **KEEP** our NFC + LF rules, which the reference does not specify |
| **D-04** | Step-0 / config authentication | **Keyed**: "cryptographically signed using a **pre-supplied key**… cannot be forged retroactively" (Ch 5 p.55–56); pre-game **signature exchange** (App B p.128) | K1/K2: keyed authentication is **SOURCE-REQUIRED**; HMAC-SHA256 is a labelled **PROJECT-CONTRACT** default (JDEC-013); tags non-self-referential, domain-separated | **Unkeyed** `SHA256(terms \| nonce)` with the nonce in the clear; **no HMAC, no key, no asymmetric crypto anywhere**; still called "signature" | keyed `step0_auth` / `config_auth` envelopes | **High** — adopting the reference would drop a book-required property (producer authentication) and import wrong terminology | **KEEP-OUR-DESIGN** (book wins) + **ASK-CHATBOT (Q4, Q5)** to confirm the acceptable primitive. **Not** a specification conflict: the *book* is clear; the *reference* is simply weaker |
| **D-05** | Role alternation across sub-games | **Silent** — exhaustive Hebrew/English search found no requirement (see audit §5) | Silent; our two-repo split assigns one fixed role per repository | `role_for()`: natural role on odd sub-games, opposite on even | each repository keeps its natural role | **High** — affects series orchestration and possibly which repo is "active" per sub-game | **ASK-CHATBOT (Q1)**. **No architecture change made.** Note our two-repo team model can express alternation *without* changing role architecture (our police repo plays their thief; our thief repo plays their police) |
| **D-06** | FastMCP tool surface | FastMCP is required; **no tool names printed** | Not fixed; transport representation is negotiable | Tools `negotiate`, `receive_turn`, `submit_audit`, `receive_control`; poll-based inboxes | ports only; **concrete signatures deliberately deferred** (R-24) | **High for interop** — a mismatch means no match can be played at all | **ASK-CHATBOT (Q2)** + **DEFER-TO-PRD** (PRD-02/05). If the answer is "teams may agree", we propose reference-compatible names to reduce integration risk |
| **D-07** | `pheromone_min_center_intensity` | Appendix F Table 16 has **3** pheromone rows (0.9 / 0.10 / 5) | Config contract = App B keys only; no such row | Ships a 4th key `0.5` **inside the signed config** | 3 pheromone keys | **Medium** — an extra key inside a byte-identical config breaks equality unless both sides carry it | **ASK-CHATBOT (Q9)** + **DEFER-TO-PRD**. Do **not** add it unilaterally; it is not an Appendix F row |
| **D-08** | `_note` comment keys in the signed config | Not mentioned | D4 minimalism: signed config = App B SOURCE-EXPLICIT keys only | `_note`, `_axis_note`, `_hint_max_words_note` inside `game.json` | no project keys inside the signed config | **Medium** — comment keys change the canonical bytes | **KEEP-OUR-DESIGN**; if the opponent insists on the reference file verbatim, the exact byte set becomes a pre-match negotiation item (NDEC-004) |
| **D-09** | `num_games` for a counted series | App F Table 18 `[games per series]`; App B example shows `1` | **6, FIXED** for a counted series (C-05, closed) | ships `1` | 6 FIXED | Low | **KEEP-OUR-DESIGN** — reference default is illustrative, exactly as C-05 concluded |
| **D-10** | `verdict` vs `intent` | Prose says "intent classification"; code comment says `verdict` | **C-08**: same object; sealed record carries `intent` only | Sets **both** keys to the *same* value, for consumer compatibility | single `intent` field | Low | **KEEP-OUR-DESIGN** — the reference independently corroborates C-08 |
| **D-11** | Explicit state machine | Describes a protocol flow | Protocol timeline locked (events 1–15) | No explicit state machine; flow is implicit in `runtime.py` | Explicit states + transition table + forbidden transitions | Low | **KEEP-OUR-DESIGN** (stronger, testable) |
| **D-12** | Replay independence | Replay Viewer is a mandatory deliverable; TAMPERED voids the match | REPLAY-001/002; replay from artifacts | Replay reads sibling logs from disk (post-audit) | `infra.replay` = **files-only, offline**, cannot import live state | Low | **KEEP-OUR-DESIGN**; reference confirms post-game both-path reconstruction is legitimate |
| **D-13** | Strategy plug-in seam | Academic freedom on strategy | STRAT-*; strategy replaceable | `thief_class`/`police_class` dotted-path injection | `StrategyPort` + typed `Observation`/`ProposedAction` | Low | **ADOPT-REFERENCE-PATTERN** for the *configuration mechanism* (dotted-path selection) in PRD-03; **KEEP-OUR-DESIGN** for the typed privacy wall |
| **D-14** | Zero-token operation | LLM optional; movement algorithmic (LLM-001) | T0 must always be viable | `template` provider = no LLM, no tokens, no network (default) | T0/T1/T2 tiers, T0 always viable | Low | **KEEP-OUR-DESIGN**; reference confirms the pattern is real and expected |
| **D-15** | Runtime dependency | FastMCP required | none added at Stage 2A | `fastmcp>=3.4.3` (single runtime dep) | none yet | Low | **DEFER-TO-PRD** (PRD-02/05) — add `fastmcp` with written justification at implementation time |
| **D-16** | Python version / coverage floor | Not bound by the book | ours: 3.12, coverage ≥90 | 3.13, coverage ≥85 | 3.12 / ≥90 | Low | **KEEP-OUR-DESIGN** (stricter). Re-evaluate only if `fastmcp` requires 3.13 |
| **D-17** | Version-sync tooling | Book requires code/version identity for submission | GIT-001…005 | `scripts/sync_versions.py` keeps code and book versions aligned | none | Low | **ADOPT-REFERENCE-PATTERN** — useful for the Submission Gate; **DEFER-TO-PRD** (PRD-07) |
| **D-18** | Restart/drain semantics | Not specified | not specified | `RestartSeries` + `drain_inboxes()` clears stale turn messages | not modelled | Medium | **DEFER-TO-PRD** (PRD-02) — adopt as an edge case; it also strengthens our `E-PROTO-STALE` handling |

## Summary

| Outcome | Count | IDs |
|---|---|---|
| KEEP-OUR-DESIGN | 8 | D-04, D-08, D-09, D-10, D-11, D-12, D-14, D-16 |
| ASK-CHATBOT | **0 — all resolved at Stage 2A-R2** | (was D-01, D-02, D-05, D-06, D-07) |
| ADOPT-REFERENCE-PATTERN | 4 | D-03 (default proposal), D-13 (mechanism), D-17, (D-03 partial) |
| DEFER-TO-PRD | 5 | D-06, D-07, D-15, D-17, D-18 |
| **SPECIFICATION-CONFLICT** | **0** | — |

**No SPECIFICATION-CONFLICT was found.** The reference is weaker than the book on
authentication (D-04) and silent-vs-implemented on role alternation (D-05), but neither
reveals an internal contradiction *within the book*. The locked Stage-1 specification
therefore stands entirely unchanged.

## Stage-2A-R2 closure of the ASK-CHATBOT deltas

| ID | Final outcome |
|---|---|
| **D-01** commitment construction | **KEEP-OUR-DESIGN** + future negotiated `CommitmentCodec` (`LECTURER_REFERENCE_COMMITMENT` profile) |
| **D-02** sealed field set | **KEEP-OUR-DESIGN** (8 fields); remains NDEC-001 negotiable |
| **D-05** role alternation | **PROJECT-SUPPORTED-BEHAVIOR** at orchestration level (`SeriesLauncher`); **no new MUST**; repos stay independent |
| **D-06** FastMCP tools | **DEFER-TO-PRD** with reference names as compatibility defaults |
| **D-07** extra pheromone key | **KEEP-OUR-DESIGN** — REFERENCE-ONLY, recognised but never binding |
| **D-08** `_note` keys | **KEEP-OUR-DESIGN** — strict emitter excludes; compatibility parser may accept negotiated metadata keys |
| **NEW D-19** result static metadata | **PROJECT-CONTRACT-CORRECTION applied** — four-artifact-set self-containment (JDEC-014); result 13→11 rows, grand total 77→75 |
| **NEW D-20** Ed25519 | **ADOPT AS PROFILE** — `AuthProfile.ED25519` for attachment compatibility; **not** SOURCE-MANDATORY; no crypto dependency added yet |

**SPECIFICATION-CONFLICT count remains 0.** No unresolved chatbot item remains.
