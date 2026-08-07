# Stage 1D — Final JSON Contract Audit & Interoperability Lock — group MaRs-777

**Status: DRAFT (Stage 1D). Independent audit + corrections of the Stage 1C
contracts against the PDF. Specification only. Pending review.**

Source: book v3.0.0, SHA-256 `7c9e1d…dd02e`, 160 pages (re-verified). Baseline
HEAD `2113e68`. This audit locks the four contracts for interoperable
implementation and reclassifies every representation dependency.

## Supervising findings D1–D5

| Finding | Verdict | Evidence | Action |
|---|---|---|---|
| **D1 — verdict / sealed record** | **CONFIRMED (with source-ambiguity note)** | Ch 5 p.50 Hebrew prose: the sealed record adds "the verbal hint, **the intent classification (סיווג הכוונה)**, the step number and the role". Ch 5 p.53 English code comment: seals "(hint, **verdict**, step, role, sub_game)". The two lists align position-for-position ⇒ **`verdict` = intent classification = the truth/lie tag = the core `intent`**. The classification is chosen **at commit** (p.50 l.23: agent picks move + hint + Intent flag, then nonce, then hash). | `verdict` is **not** a post-move validation and **not** a separate field: it is the self-declared hint classification (`intent`). It **belongs in the pre-commit payload** (as `intent`). Stage 1C's payload already carried `intent`; the literal `verdict` token is a synonym — **no separate `verdict` field is added** (would double-count and diverge the hash). Source terminology ambiguity recorded (**C-08**). |
| **D2 — interop blockers** | **CONFIRMED (reclassification required)** | Stage 1C labelled several items "not blocking because the opponent can agree later" — which the D2 rule forbids. Mutual audit requires the opponent to **recompute** our commitment hashes and compare result hashes ⇒ those representations are interoperability dependencies. | Every such item reclassified as **SOURCE-LOCKED / PROJECT-LOCKED / NEGOTIATED-PRE-MATCH**; none stays "not blocking". See §Interop dependencies + `INTEROPERABILITY_NEGOTIATION.md` (NDEC) + `INTEROPERABILITY_BLOCKERS.md`. |
| **D3 — game_id vs game_uid** | **REFUTED (premise wrong)** | Ch 9 p.95: "the four files carry a **shared identifier (`game_uid`)**, and each filename derives from the **game identifier (`game_id`)** — so files from different games never mix." **Both are source-named.** | `game_uid` is **KEPT** and reclassified **SOURCE-EXPLICIT** (Stage 1C wrongly called it PROJECT-CONTRACT). Only the **format** of `game_id`/`game_uid` remains project (JDEC-005 MODIFIED). INV-01 keeps both (same `game_id` **and** `game_uid` across all four). |
| **D4 — external minimalism** | **CONFIRMED (corrections applied)** | Any field inside a hashed/mutually-verified object must be SOURCE-LOCKED or NEGOTIATED — a unilateral "optional" field in a hashed object is not harmless. Stage 1C left `schema_version` inside the signed config value-unspecified, and marked project fields "optional". | The **signed config** carries only the App B SOURCE-EXPLICIT keys; `schema_version` **value** is NEGOTIATED (it is in the App B structure and affects the hash). Declaration `schema_version` = **REMOVE-REDUNDANT**. Persistent **log** structure = **LOCAL-ONLY**; the **sealed commitment payload** (interop) = NEGOTIATED. Result presentation = LOCAL; result-**approval core** = NEGOTIATED. |
| **D5 — exact counts** | **CONFIRMED** | Stage 1C used "~19". | All counts below are exact and reconciled with FIELD_MATRIX. |

## Commitment-record reconstruction (Section D)

| Candidate field | Exists before commit? | Source says sealed? | Needed for verification? | Final classification |
|---|---|---|---|---|
| `state` | Yes (own-known board context) | Yes (core) | Yes (binds commitment to a situation) | **in sealed payload** (repr PROJECT-LOCKED, JDEC-012 / NDEC-002) |
| `move` | Yes | Yes (core) | Yes | in sealed payload |
| `intent` | Yes (agent's truth/lie choice) | Yes (core) | Yes | in sealed payload |
| `nonce` | Yes (drawn at commit) | Yes (core) | Yes (freshness/dictionary) | in sealed payload; revealed only at final audit |
| `hint` | Yes | Yes (richer record) | Yes | in sealed payload |
| `verdict` | Yes (**= intent classification**) | Yes (richer record) — **synonym of intent** | — | **NOT a separate field**; = `intent` (C-08) |
| `step` | Yes | Yes (richer record) | Yes | in sealed payload |
| `role` | Yes | Yes (richer record) | Yes | in sealed payload |
| `sub_game` | Yes | Yes (richer record, code comment) | Yes | in sealed payload |

**Seven distinct objects (not collapsed):** (1) **COMMITMENT PAYLOAD** (the hashed
`sealed_record`), (2) **COMMIT MESSAGE** (`H_commit` on the wire), (3) **ACK
MESSAGE**, (4) **REVEAL MESSAGE** (move+hint; nonce withheld), (5)
**VERDICT/VALIDATION RECORD** (post-reveal move-legality/capture-truth result — a
*different* object, produced later), (6) **FINAL-AUDIT RECORD** (all nonces +
recompute verdicts), (7) **PERSISTENT LOG ENTRY** (LOCAL-ONLY container). The
**VALIDATION verdict (5)** is the post-move legality/capture check — distinct from
the commit-time `intent`/`verdict` classification; it exists only after reveal and
is **not** in the pre-commit payload.

## Final sealed commitment payload (locked)

`H_commit = SHA256( canonical( { state, move, intent, hint, step, role, sub_game, nonce } ) )`
— **8 fields**, all known at commit; `intent` carries the truth/lie classification
(the "verdict"); no separate `verdict` key. The exact field list + key order +
canonicalization + `state` representation are **NEGOTIATED-PRE-MATCH** (NDEC-001/002/003)
with the PROJECT-LOCKED defaults defined here, because the opponent must recompute
identical bytes.

## Interoperability dependencies (Section D2)

| Dependency | What must match | When agreed | Made immutable by | Recorded in | Mismatch detected by | Failure behaviour | Class |
|---|---|---|---|---|---|---|---|
| Appendix F FIXED values | exact values | — (fixed) | the book | config | config hash / audit | disqualify | **SOURCE-LOCKED** |
| Config structure (App B keys) | key set/names | — (fixed) | App B | config | byte-identity | refuse to play | **SOURCE-LOCKED** |
| MINIMUM/NEGOTIABLE values | agreed values ≥ floor | pre-match | signed config | config | config hash | refuse to play | **NEGOTIATED-PRE-MATCH** (NDEC-004) |
| `schema_version` value | identical value | pre-match | signed config | config | byte-identity | refuse to play | **NEGOTIATED-PRE-MATCH** (NDEC-004) |
| Canonical serialization params | identical serializer behaviour | pre-match | agreement | negotiation record | recompute mismatch | false TAMPERED | **NEGOTIATED-PRE-MATCH** (NDEC-003; PROJECT default JDEC-002) |
| Sealed-record composition | exact field set + order | pre-match | agreement | negotiation record | recompute mismatch | false TAMPERED | **NEGOTIATED-PRE-MATCH** (NDEC-001) |
| `state` representation | exact structure/coords/barrier order | pre-match | agreement | negotiation record | recompute mismatch | false TAMPERED | **NEGOTIATED-PRE-MATCH** (NDEC-002; PROJECT default JDEC-012) |
| `config_sha256` equality | both compute same hash of config | pre-match | mutual exchange+compare | declaration / sidecar | hash inequality | refuse to play | **PROJECT-LOCKED** procedure + NDEC-004 |
| Step-0 keyed authentication (K1) | **keyed auth** (HMAC-SHA256 default) over `"step0"‖core`, pre-supplied key; exchange+verify tag | pre-match | mutual exchange + shared key | declaration (`step0_auth`) | tag/`key_id` verify fail | **refuse counted play** if no compatible key/mechanism | **NEGOTIATED-PRE-MATCH** (NDEC-005; keyed-auth **requirement** SOURCE, primitive PROJECT) |
| Config signature exchange (K2) | **keyed auth** over `"config"‖core` **plus** `config_sha256` equality | pre-match | mutual exchange + shared key | config (+ sidecar `config_auth`) | tag verify fail **or** hash mismatch | **refuse counted play** | **NEGOTIATED-PRE-MATCH** (NDEC-007; requirement SOURCE, primitive PROJECT) |
| Result-approval hashing | SHA-256 over agreed result core; both identical | end of game | dual reports agree | result | `result_sha256` mismatch **or** report missing from either side | **0 to both** (C-09) | **NEGOTIATED-PRE-MATCH** (NDEC-006; SHA-256 SOURCE) |
| Result self-containment (K3) | FastMCP endpoints + signed hardware decl (`hardware_auth`) present + match declaration | end of game | reporting rule | result | missing/omitted field | not credited / dispute | **SOURCE-REQUIRED** content + **PROJECT** keys (INV-10/12/13) |
| Commit-Reveal / replay verify | recompute-and-compare procedure | — | the book | log | mismatch | disqualify | **SOURCE-LOCKED** |
| Persistent log file structure | — (each side its own) | — | — | log | n/a | n/a | **LOCAL-ONLY** |

**No dependency remains "BLOCKING-UNRESOLVED"** — each is SOURCE-LOCKED,
PROJECT-LOCKED, or NEGOTIATED-PRE-MATCH with a defined default, exchange, lock,
detection, and failure behaviour (see `INTEROPERABILITY_BLOCKERS.md`).

## State representation (Section E) — PROJECT-LOCKED (JDEC-012)

Minimum sealed state (binds the commitment to a specific situation; **no opponent
private truth**): the agent's **own known** context —

```json
{ "config_sha256": "<hex>", "self_pos": [row, col], "barriers": [[r,c],...], "step": <int>, "role": "police|thief" }
```

- Coordinates: `[row, col]` integer arrays, per App B convention.
- `barriers`: **lexicographically sorted** list of `[row,col]` (barriers are publicly
  declared, BAR-001) → deterministic order.
- Includes only public/own-known info (own position, declared barriers, step, role,
  config identity); **excludes** the opponent's true position (unknown under partial
  observation — GUI-001/002).
- Absent/optional values: `barriers` = `[]` when none.
- **PROJECT-LOCKED** default; confirmed pre-match via **NDEC-002** (both peers must
  agree the exact representation to recompute identical hashes).

## Signature/hash terminology (Section G/H) — precise — **CORRECTED Stage 1D.1 (K1/K2)**

> **Correction of the original Stage-1D wording**, which wrongly reduced Step-0 to an
> unkeyed SHA-256 "digest" and said "MAC: none specified … not adopted". **The book
> requires KEYED authentication with a pre-supplied key** — Ch 5 p.55–56 ("the whole
> spec is packed into JSON and **cryptographically signed using a pre-supplied key
> (מפתח המסופק מראש), so it cannot be forged retroactively**") and App B p.128 (a
> pre-game **signature exchange (חילופי החתימה)** that "refuses to play on any
> mismatch"). Full taxonomy in `SIGNATURE_AND_HASH_PROVENANCE.md`.

Four categories — **never interchangeable**:

- **Unkeyed HASH (SHA-256):** content integrity only; does **not** authenticate the
  producer. Used for `H_commit`, `config_sha256`, `result_sha256`.
- **Keyed MAC (e.g. HMAC-SHA256):** integrity **+** proof the holder of a pre-supplied
  shared key produced it. **This — not a bare hash — is what Step-0 and the config
  signature exchange require (SOURCE-REQUIRED, K1/K2).** Exact primitive is
  source-unspecified → **project default HMAC-SHA256 (JDEC-013, PROJECT-CONTRACT, not
  lecturer-specified)**; asymmetric signature allowed if both peers agree.
- **Asymmetric DIGITAL SIGNATURE (PKI):** producer authentication via public-key. The
  book does **not** mandate PKI; we invent none. **SHA-256 is never called a signature;
  HMAC is never called asymmetric.**
- **MUTUAL ACKNOWLEDGEMENT:** two parties compare and agree the same digest (result
  approval). Backs `result_sha256` (both equal ⇒ agreed).

**Key handling:** the pre-supplied key is **out-of-band**; only a non-secret `key_id`
is ever stored. **No key material** in Git, JSON, logs, docs, email, runtime, or
errors (JDEC-013 security block). Envelope `{auth_alg,key_id,auth_tag}` is
**non-self-referential** and **domain-separated** (`context ∈ {"step0","config"}`).

## Config hash procedure (Section I) — non-self-referential

`config_sha256 = SHA256( canonical_bytes( config/game.json ) )` where the hashed
bytes are the App B config **without** any embedded hash field (no self-reference).
`config_sha256` is stored **outside** the signed config — carried in the
`declaration` (and/or a `config_<…>.json.sha256` sidecar) — and both peers compute
it independently and compare for equality before play (NDEC-004). **A hash field
inside the bytes it hashes is explicitly ruled out** (the book defines no such
construction).

## Identity decision (Section J)

`game_uid` = **KEPT**, reclassified **SOURCE-EXPLICIT** (Ch 9 p.95). `game_id` =
SOURCE-EXPLICIT (filename derivation). Their **formats** remain PROJECT-CONTRACT
(JDEC-005 MODIFIED). Filename identity and JSON identity are bound by INV-01
(all four files carry the same `game_id` **and** `game_uid`; filenames derive from
`game_id`) so they cannot drift silently.

## Exact artifact counts (Section D5) — reconciled with FIELD_MATRIX

Interop statuses: **LS**=LOCKED-SOURCE, **LP**=LOCKED-PROJECT, **NPM**=NEGOTIATED-PRE-MATCH,
**LO**=LOCAL-ONLY, **EX**=EXAMPLE-ONLY, **BU**=BLOCKING-UNRESOLVED. **Counting unit =
one semantic-field row** in `FIELD_MATRIX.md` (aggregate rows counted once). These
totals are the authoritative row-exact reconciliation; the earlier JSON-leaf-key
"config 40 / log 20 / result 24 / +9" prose is **superseded** (it double-counted
sub-keys and tagged `game_uid` two ways). No approximation.

| Artifact | Total | SE | SS | PC | EX | LS | LP | NPM | LO | EX-STATUS | BU |
|---|---|---|---|---|---|---|---|---|---|---|---|
| declaration | 16 | 3 | 13 | 0 | 0 | 3 | 9 | 4 | 0 | 0 | 0 |
| config | 39 | 35 | 4 | 0 | 0 | 16 | 1 | 22 | 0 | 0 | 0 |
| log | 9 | 0 | 9 | 0 | 0 | 0 | 0 | 3 | 6 | 0 | 0 |
| result | 13 | 2 | 11 | 0 | 0 | 1 | 2 | 10 | 0 | 0 | 0 |
| **GRAND** | **77** | **40** | **37** | **0** | **0** | **20** | **12** | **39** | **6** | **0** | **0** |

Provenance total = status total = row total for every artifact; all sum to **77**.
**No BLOCKING-UNRESOLVED field in any artifact.** Full per-row derivation in
`FIELD_MATRIX.md` (§Exact reconciliation).

## JDEC audit (Section O)

| JDEC | Action | Note |
|---|---|---|
| JDEC-001 snake_case | **KEEP** | matches App B |
| JDEC-002 canonical params | **KEEP** (as PROJECT default) | now the default for NDEC-003 (both peers confirm) |
| JDEC-003 schema_version | **MODIFY** | config value = NEGOTIATED (NDEC-004); declaration `schema_version` REMOVED |
| JDEC-004 `<NN>` 2-digit | **KEEP** | — |
| JDEC-005 id formats | **MODIFY** | `game_uid`/`game_id` are **source-named**; only their format is project |
| JDEC-006 declaration keys | **KEEP** | declaration presentation keys are ours; Step-0 **keyed-auth** envelope `step0_auth` → NDEC-005 (K1) |
| JDEC-007 log nesting | **MODIFY** | persistent log = LOCAL-ONLY; sealed payload → NDEC-001 |
| JDEC-008 result score shape | **KEEP** | presentation; approval core → NDEC-006 |
| JDEC-009 four-links | **KEEP** | — |
| JDEC-010 hash storage | **MODIFY** | `config_sha256` stored **outside** hashed config (non-self-ref); Step-0/result → NDEC-005/006 |
| JDEC-011 ISO-8601 UTC | **KEEP** | — |
| **JDEC-012** `state` sealed representation | **NEW / KEEP** | PROJECT-LOCKED default; confirmed via NDEC-002 |
| **JDEC-013** keyed-auth default (Stage 1D.1) | **NEW / KEEP** | HMAC-SHA256 over `context‖core`, `context ∈ {"step0","config"}`, `key_id` only, key out-of-band; **source requirement = keyed authentication (K1/K2), primitive is PROJECT-CONTRACT**; no compatible key ⇒ refuse counted play |

No JDEC retired; all remain active (some MODIFIED). NDEC register is separate
(`INTEROPERABILITY_NEGOTIATION.md`, now NDEC-001…007).

## Reporting-failure audit (Section Q)

- Emailed artifact: **`result_<game_id>.json`** only, as a **JSON attachment** (JSON-001/002); each team sends its own (REPORT-001), to `rmisegal+uoh26finalgame@gmail.com` (REPORT-002).
- **Sanction — stricter composite (C-09, corrected Stage 1D.1):** Ch 9 p.94 says a
  **missing** report from one side ⇒ **that side** is not credited; App E #35 p.147 says
  a **contradictory** report ⇒ **game void, 0 to both**. These are **different**
  sanctions (a genuine non-numeric conflict — C-09). We adopt the **strictest**: a
  required report **missing from either team** **or** **contradictory** reports ⇒
  **game invalid, 0 to both**. We never rely on the milder per-side rule where E-35
  can apply.
- **Self-contained report (K3):** the result MUST be verifiable **from itself** — it
  carries identities, four links, **FastMCP endpoints**, **cryptographically-signed
  hardware declarations** (`hardware` + `hardware_auth`), per-sub-game
  scores+outcome+commit+tokens, cumulative, total tokens, timestamp, mutual-agreement,
  and `result_sha256`. **No key material** appears in the report.
- The book supplies **no exact schema** — only "standard, machine-readable JSON". A
  grader/parser may reject unexpected fields ⇒ prefer the **minimum source-complete**
  result above. Optional presentation metadata is LOCAL-ONLY and, if present, must not
  be inside the approval-hashed core (which stays non-self-referential).

## Cross-artifact invariants (Section P) — provenance-tagged

INV-01 (same `game_id` **and** `game_uid` ×4) — **SOURCE**; INV-02 (same sub-game
`NN`) — SOURCE; INV-03 (`config_sha256` = played config hash) — SOURCE(mechanism)+PROJECT(storage);
INV-04 (four links match declaration) — SOURCE; INV-05 (declared commit = reported commit) — SOURCE;
INV-06 (commitments recompute) — SOURCE; INV-07 (scores from App F + C-07 technical_loss) — SOURCE;
INV-08 (both results agree) — SOURCE; INV-09 (`num_games`=6) — SOURCE.
**Stage 1D.1 additions:** INV-10 (result self-contained, K3) — SOURCE; INV-11
(reports present+matching or 0-both, C-09) — SOURCE; INV-12 (result FastMCP endpoints)
— SOURCE; INV-13 (result signed hardware `hardware_auth`) — SOURCE + PROJECT primitive;
INV-14 (Step-0 keyed-auth verifies, K1) — SOURCE-REQUIRED + PROJECT primitive; INV-15
(config keyed-auth + hash both verify, K2) — SOURCE-REQUIRED + PROJECT primitive.

## Preserved facts

- **technical_loss C-07** preserved (0/0 binding via Ch 3/E-48; not an App F row).
- **num_games = 6, FIXED** (App B `1` illustrative).
- Simplified Ch-5 4-field and Ch-7 `nonce|move` examples remain **EXAMPLE-ONLY**.

## Stage 1D.1 corrections (applied)

- **K1 — Step-0 is KEYED authentication, not a bare hash.** Section G/H rewritten;
  `step0_signature` → `step0_auth {auth_alg,key_id,auth_tag}` (HMAC-SHA256 default,
  JDEC-013); NDEC-005 rewritten. INV-14 added.
- **K2 — config signature exchange** (App B p.128) added as a distinct keyed-auth
  layer beyond `config_sha256` equality; NDEC-007 + INV-15 added.
- **K3 — result must be self-contained:** FastMCP endpoints + cryptographically-signed
  hardware declarations (`hardware_auth`) are MANDATORY; INV-10/12/13 added.
- **K4/C-09 — reporting-sanction conflict** (Ch 9 per-side non-credit vs E-35
  game-void/0-both) documented; strictest composite adopted; INV-11 added.
- **K5 — `game_uid`** remains SOURCE-EXPLICIT (kept).
- **K6 — `verdict` = `intent`** remains a documented terminology interpretation
  (C-08), not a literal source alias; no separate field.
- **Counts recalculated** row-exact (77 semantic-field rows: declaration 16, config 39,
  log 9, result 13; provenance total = status total = 77; BU 0); **no key material** in
  any artifact. No code, no schema, no commit.
