# Project-Contract Decision Register (JDEC) — group MaRs-777

**Status: REVIEWED — Stage-1 supervising review PASS; baseline LOCKED. Specification only; no code/schema/JSON artifact.**

Every PROJECT-CONTRACT choice, made **only** where the book leaves the
representation open (academic-freedom basis, PDF p.5 / book v). None overrides a
binding source requirement; none is claimed lecturer-specified. Conservative,
simple, reversible representations are preferred.

| JDEC | Decision | Source freedom (why allowed) | Options considered | Selected | Why | Interop impact | Security impact | Future test | Reversal cost |
|---|---|---|---|---|---|---|---|---|---|
| **JDEC-001** | Key spelling = `snake_case` for all SOURCE-SEMANTIC keys | book names meanings, not keys | camelCase / snake_case | snake_case | matches the App B SOURCE-EXPLICIT keys (`grid_size`, `capture_cop`) | must be agreed with opponent for shared files | none | schema lint | low (rename) |
| **JDEC-002** | Canonical serialization params: `sort_keys=True`, `separators=(",",":")`, UTF-8, LF, no trailing newline in hashed payload; `ensure_ascii` fixed & agreed; locale-independent number formatting | Ch 5 requires "canonical, sorted keys, fixed separators, UTF-8, byte-identical"; exact params/`ensure_ascii`/line-endings unspecified | reference params vs custom | **reference-code params** + explicit `ensure_ascii`/LF rule | reproduces the book's reference hash behavior; deterministic cross-OS | **critical**: both peers must use identical params or hashes differ | correct hashing prevents false TAMPERED | cross-impl byte-identity test | medium (affects all hashes) |
| **JDEC-003** | `schema_version` optional, informational (`"mars777-N"`); no version handshake | book prints the key but binds no value/compat rule | mandatory 1.2 / optional project value / omit | optional project value | `1.2` is illustrative; no handshake mandated | none (informational) | none | presence check | trivial |
| **JDEC-004** | `<NN>` = 2-digit zero-padded (`g01`…`g06`) | book writes `g<NN>` without a width | 1-digit / 2-digit / 3-digit | 2-digit | lexical=numeric order; ≤10 fits 2 | filenames must match opponent's expectation | none | filename regex | low |
| **JDEC-005** | `game_id` = opaque `[a-z0-9-]` string (e.g., `<a>-vs-<b>-<yyyyww>-<uid>`); `game_uid` short shared token | book requires uniqueness + filename derivation, not a format | freeform / structured | structured, filesystem-safe | uniqueness, no file mixing (App F §2.3) | agreed at declaration | none | uniqueness test | low |
| **JDEC-006** | Declaration key names (hardware `os/cpu_cores/cpu_freq_ghz/ram_gb/gpu/vram_gb`, `teams.<g>.*`) | Ch 5/9 require the info, not keys | flat / nested-by-team | nested-by-team | groups per-team data cleanly | shared file → agree keys | none | schema lint | low |
| **JDEC-007** | Log entry nesting: `entries[]` with `phase` ∈ {commit, ack, reveal}; hashed `sealed_record` is a separate object | Ch 5 names the fields/flow, not JSON layout | one-object-per-turn / event-list | event-list (`entries[]`) | maps Commit→Ack→Reveal→Audit; auditable | replay must parse same shape | must not leak nonce early | replay round-trip test | medium |
| **JDEC-008** | Result scores: `sub_games[]` array + `cumulative{}` | Ch 9 requires per-sub-game + cumulative, not keys | flat / array+cumulative | array+cumulative | clear per-game + totals | grader parses | none | scoring test | low |
| **JDEC-009** | Four GitHub links = object with 4 explicit keys (`group_a_police`, …) | E-49 requires four links; no key given | array(4) / 4-key object | 4-key object | unambiguous role/team mapping | grader parses 4 links | none | link-count test | low |
| **JDEC-010** | Internal hash storage: `config_sha256`/`result_sha256` stored **outside** the bytes they cover (non-self-referential). **[MODIFIED — Stage 1D non-self-ref; Stage 1D.1 K1/K2]** Step-0/config authentication is **no longer REVIEW-REQUIRED**: it is **keyed authentication** (JDEC-013, NDEC-005/007), envelope `{auth_alg,key_id,auth_tag}` stored outside the authenticated core; **key out-of-band**. | book states hashes/keyed signing exist, not exact primitive/storage | embedded / sidecar | **outside** the hashed/authenticated bytes (declaration/config sidecar) | conservative; non-self-referential; primitive negotiated | **no secret material stored** (only `key_id`) | hash/tag-presence test | low | supersedes the old "defer interop signatures" note |
| **JDEC-011** | Timestamps = ISO-8601 UTC (`Z`) strings | Ch 9 requires times, not a format | epoch / ISO-8601 | ISO-8601 UTC | human+machine readable, unambiguous TZ | agree with opponent | none | format test | trivial |

## Stage 1D audit (KEEP / MODIFY / RETIRE) + new JDEC-012

| JDEC | Action | Change |
|---|---|---|
| JDEC-001 | KEEP | — |
| JDEC-002 | KEEP | now the PROJECT-LOCKED **default** confirmed via **NDEC-003** |
| JDEC-003 | **MODIFY** | config `schema_version` **value = NEGOTIATED** (NDEC-004, in the byte-identical config); **declaration `schema_version` REMOVED** (redundant) |
| JDEC-004 | KEEP | — |
| JDEC-005 | **MODIFY** | `game_uid` **and** `game_id` are **SOURCE-EXPLICIT names** (Ch 9 p.95); only their **format** is project (D3) |
| JDEC-006 | KEEP | declaration presentation keys; Step-0 hashed subset → NDEC-005 |
| JDEC-007 | **MODIFY** | persistent log = **LOCAL-ONLY**; sealed commitment payload → **NDEC-001** |
| JDEC-008 | KEEP | result presentation; approval core → NDEC-006 |
| JDEC-009 | KEEP | — |
| JDEC-010 | **MODIFY** | `config_sha256` stored **outside** the hashed config (non-self-referential); Step-0/result hashes → NDEC-005/006 |
| JDEC-011 | KEEP | — |
| **JDEC-012** | **NEW** | `state` sealed representation `{config_sha256, self_pos, barriers(sorted), step, role}` (own-known only); PROJECT-LOCKED default, confirmed via **NDEC-002** |
| **JDEC-013** | **NEW (Stage 1D.1)** | **Keyed authentication default = HMAC-SHA256** over `context ‖ canonical_payload`, `context ∈ {"step0","config"}`, key referenced by `key_id` (no key material anywhere). **Source requirement = keyed authentication with a pre-supplied key (Ch 5 p.55–56; App B p.128); the algorithm is our choice, not lecturer-specified.** Out-of-band key provisioning; `auth_tag`/`auth_alg`/`key_id` envelope is non-self-referential. No compatible key/mechanism pre-match ⇒ **refuse counted play**. |

**No JDEC retired.** JDEC-001…013 active, unique. Negotiated items are tracked as
NDEC-001…007 in `INTEROPERABILITY_NEGOTIATION.md`.

### JDEC-013 key handling (security)

Key material MUST NOT appear in Git, JSON artifacts, logs, docs, email, runtime
evidence, or error messages. Only a non-secret `key_id` reference is stored; the
pre-shared key is provisioned out-of-band ("pre-supplied key"). HMAC-SHA256 is
PROJECT-CONTRACT — the **source requirement is keyed authentication**, not HMAC
specifically; an asymmetric signature is an allowed alternative if both peers agree.

## Rules

- No JDEC changes any Appendix F value, any MUST/MUST NOT, or C-07.
- JDEC-002, JDEC-010, JDEC-012 are the interop/security-relevant ones (hashing
  determinism, non-self-referential hash storage, sealed `state`); each has a
  PROJECT-LOCKED default confirmed via an NDEC.
- IDs are unique JDEC-001…JDEC-013; no duplicates. `game_uid` is **not** invented —
  it is source-named (D3). JDEC-013 (keyed authentication) fixes only the **primitive**;
  the **requirement** (keyed auth with a pre-supplied key) is SOURCE, not a JDEC.
