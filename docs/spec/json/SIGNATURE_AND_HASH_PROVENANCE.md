# Signature & Hash Provenance Audit — group MaRs-777

**Status: REVIEWED — Stage-1 supervising review PASS; baseline LOCKED. Specification only — no crypto implementation.**

Every signature/hash the book requires, resolved as far as the source permits.
Where the book does not state a JSON key, scheme, or storage location, that aspect
stays **REVIEW-REQUIRED** or becomes a clearly-labelled **PROJECT-CONTRACT** — never
an invented lecturer requirement. Sources: Ch 5 §5.3–5.5 (PDF p.50–56), App B
§B.3 (p.127–128), Ch 9 §9.3.3 (p.94), App E #17–19, #24, #35–36.

| Requirement | What is signed/hashed | By whom | When | Verified by | Storage explicit? | JSON key explicit? | Sidecar vs embedded? | Status |
|---|---|---|---|---|---|---|---|---|
| `config_sha256` | canonical `config/game.json` bytes | both teams | pre-game (before play) | both peers (equality) | **No** | key name appears in prose ("`config_sha256`", p.127) | **not specified** | SOURCE-SEMANTIC (value/mechanism); storage **REVIEW-REQUIRED** → JDEC-010 |
| Commit hash `H_commit` | canonical sealed per-turn record (SHA-256) | each agent | each turn (commit) | opponent + Replay (audit) | Yes — in the log | no printed JSON key | embedded per log entry | SOURCE-SEMANTIC; key = PROJECT-CONTRACT (JDEC-007) |
| Step-0 **keyed authentication** (K1) | canonical Step-0 hardware/model/commit/tokens declaration, `context="step0"` | each team (holder of pre-supplied key) | pre-game (Step-0) | opponent/grader (verify tag) | key: **out-of-band**; envelope in declaration | envelope `step0_auth {auth_alg,key_id,auth_tag}` (PC) | envelope in declaration; **key never stored** | **SOURCE-REQUIRED** (keyed auth, Ch 5 p.55–56); primitive HMAC-SHA256 = PROJECT-CONTRACT (JDEC-013; NDEC-005) |
| Config **signature exchange** (K2) | canonical config core, `context="config"` | both teams (pre-supplied key) | pre-game (before play) | both peers (verify tag + hash) | key: **out-of-band**; envelope in sidecar | envelope `config_auth {auth_alg,key_id,auth_tag}` (PC) | sidecar; **key never stored** | **SOURCE-REQUIRED** (App B p.128); primitive HMAC-SHA256 = PROJECT-CONTRACT (JDEC-013; NDEC-007) |
| Scent-model lock | agreed emission/decay model (+ numeric example) hash | both teams | before series | both peers | No | no key given | not specified | SOURCE-SEMANTIC (SCENT-001); representation REVIEW-REQUIRED |
| Token-usage lock | LLM token consumption record | each team | Step-0 / per game | grader | No | no key given | not specified | SOURCE-SEMANTIC (PERF-002); representation REVIEW-REQUIRED |
| Result mutual approval | SHA-256 over the agreed result core (`result_sha256`) + mutual-agreement flag | both teams | end of game | both teams + grader (equal hash) | No | `result_sha256` (PC) | stored **outside** the hashed core (non-self-ref) | SOURCE-SEMANTIC (SHA-256-backed acknowledgement, Ch 9 p.94; E-35/36); both reports must match or **0 to both** (C-09; NDEC-006) |
| `github_commit` (hash reference, not a signature) | the played commit id | each team | per game | grader (reproduce) | Yes (declaration + result) | **`github_commit` SOURCE-EXPLICIT** (p.56) | embedded | LOCKED (identity reference) |

## What the book states vs leaves open

- **States:** SHA-256 is the hash (App E #17); commit-reveal recompute-and-compare
  (Ch 5); `config_sha256` naming (p.127); Step-0 is **cryptographically signed with a
  pre-supplied key** so it cannot be forged retroactively (p.55–56 — **keyed
  authentication is required**, not merely "a signature exists"); the config has a
  **pre-game signature exchange** (App B p.128); the result carries SHA-256-backed
  mutual approvals (p.94); `github_commit` is the exact played commit (p.56).
- **Leaves open (negotiated pre-match, not blocking):** the **exact keyed primitive**
  (HMAC-SHA256 default vs an asymmetric signature the peers may agree), the **channel**
  for the pre-supplied key (out-of-band; only `key_id` is stored), and the **JSON key
  names** (our PROJECT-CONTRACT envelope `{auth_alg,key_id,auth_tag}`). The
  **requirement** — keyed authentication with a pre-supplied key — is **not** open; it
  is SOURCE-REQUIRED (K1/K2). No compatible key/mechanism ⇒ refuse counted play.

## Stage 1D.1 — CORRECTED cryptographic taxonomy (K1/K2)

> **Correction of Stage 1D:** Step-0 was wrongly reduced to an unkeyed SHA-256
> digest ("MAC — not adopted"). **The book requires KEYED authentication with a
> pre-supplied key** — Ch 5 p.55–56: the Step-0 spec is "packed into JSON and
> **cryptographically signed using a pre-supplied key (מפתח המסופק מראש), so it
> cannot be forged retroactively**"; App B p.128: the config has a "pre-game
> **signature exchange (חילופי החתימה)**" that "refuses to play on any mismatch".

**Four categories — never interchangeable:**
1. **Unkeyed HASH (SHA-256):** proves *content integrity*, **not** producer identity. A bare hash does **not** authenticate who produced it.
2. **Keyed MAC (e.g., HMAC-SHA256):** integrity **+** proof the holder of a shared key produced it. Symmetric.
3. **Asymmetric DIGITAL SIGNATURE (PKI):** producer authentication, public-key verification. Asymmetric.
4. **MUTUAL ACKNOWLEDGEMENT:** two parties compare and agree on the same digest.

**Source classification (K1/K2):**
- Existence of **keyed authentication using a pre-supplied key** — **SOURCE-REQUIRED** (Step-0 Ch 5 p.55–56; config App B p.128).
- Exact primitive/algorithm — **SOURCE-UNSPECIFIED** (HMAC vs asymmetric not stated).
- Key-distribution mechanism — **SOURCE-UNSPECIFIED** (only "pre-supplied"/out-of-band).
- Same key for Step-0 and config — **SOURCE-UNSPECIFIED** (no reuse assumed; domain-separated).

**Project default (PROJECT-CONTRACT — JDEC-013, not lecturer-specified):**
**HMAC-SHA256** over `context ‖ canonical_payload`, `context ∈ {"step0","config"}`,
key referenced by a `key_id` (no key material in any artifact). HMAC faithfully and
minimally meets "signed with a **pre-supplied (shared) key**" between two peers; the
**source requirement is keyed authentication, not HMAC specifically**.

## Object-by-object taxonomy (Section N)

Never: call SHA-256 a digital signature · call HMAC an asymmetric signature · claim
a bare hash authenticates the producer.

| Object | Category | Source requirement | Exact algo source-specified? | Key required? | Canonical payload | Producer | Verifier | Timing | Storage | Secret material? | JDEC/NDEC | Interop failure |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `H_commit` | unkeyed HASH | SOURCE-REQUIRED (App E #17) | SHA-256 yes; serialization no | No | sealed_record (8 fields) | acting agent | opponent + replay | commit; verify at audit | log | No | NDEC-001/002/003 | mismatch → TAMPERED → void |
| `config_sha256` | unkeyed HASH (content digest) | SOURCE-SEMANTIC (byte-equality) | SHA-256 yes | No | config core (App B keys) | both teams | both | pre-game | **outside** config (declaration/sidecar) | No | JDEC-010; NDEC-004 | inequality → refuse play |
| **Step-0 keyed authentication** | **KEYED MAC / signature** | **SOURCE-REQUIRED** (pre-supplied key, Ch 5 p.55–56) | **No** (HMAC = project default) | **Yes (pre-supplied)** | Step-0 core, `context="step0"` | each team | opponent/grader | pre-game | `auth_alg`,`key_id`,`auth_tag` in declaration; **key out-of-band** | **key: never**; tag: yes | JDEC-013; NDEC-005 | wrong key/tag → refuse/dispute |
| **config keyed authentication** | **KEYED MAC / signature** | **SOURCE-REQUIRED** (signature exchange, App B p.128) | **No** (HMAC = project default) | **Yes (pre-supplied; same-or-distinct unspecified)** | config core, `context="config"` | both teams | both | pre-game | `auth_alg`,`key_id`,`auth_tag` in sidecar; **key out-of-band** | **key: never**; tag: yes | JDEC-013; NDEC-007 | bad tag → refuse play |
| `result_sha256` | unkeyed HASH (content digest) | SOURCE-SEMANTIC (SHA-256-backed approval, Ch 9 p.94) | SHA-256 yes | No | result approval core | each team | both + grader | end of game | in result (outside core) | No | NDEC-006 | mismatch → 0 both |
| mutual result acknowledgement | AGREEMENT (equal digests) | SOURCE-REQUIRED (both agree, E-35) | n/a | No | — | both teams | both + grader | end | result | No | NDEC-006 | one-sided/contradictory → 0 both (**C-09**) |
| Git commit SHA (`github_commit`) | version identity (Git hash) | SOURCE-EXPLICIT | Git's | No | — | Git | grader | per game | declaration + result | No | — | wrong → cannot reproduce |

**Domain separation:** a valid `auth_tag` cannot replay across object types because
`context` (`"step0"`/`"config"`) is authenticated with the payload. **Non-self-reference:**
`auth_tag`/`auth_alg`/`key_id` are **not** part of the bytes authenticated (the tag is
computed over `context ‖ core`, not over the envelope that carries the tag).

## Guidance

- **Distinguish the requirement from the primitive.** The book **requires** two
  things: (a) unkeyed SHA-256 hashing for `H_commit`/`config_sha256`/`result_sha256`
  (App E #17), and (b) **keyed authentication with a pre-supplied key** for Step-0 and
  the config signature exchange (Ch 5 p.55–56; App B p.128). Both are SOURCE-REQUIRED.
- **Never invent a lecturer-required *primitive*.** The exact keyed algorithm is
  source-unspecified → project default **HMAC-SHA256 (JDEC-013, PROJECT-CONTRACT)**,
  clearly labelled and reversible to an asymmetric signature if both peers agree.
  **Never call SHA-256 a signature; never call HMAC an asymmetric signature; never
  claim a bare hash authenticates the producer.**
- A conservative **PROJECT-CONTRACT** fixes *where our hashes/tags live* —
  `config_sha256`/`result_sha256`/`auth_tag` are stored **outside** the bytes they
  cover (non-self-referential); envelopes carry only the non-secret `key_id`. **Key
  material is provisioned out-of-band and never appears in Git, JSON, logs, docs,
  email, runtime, or errors** (JDEC-013 security block).
- What remains genuinely open is only *negotiated pre-match* (the peer's exact
  primitive and the key channel), with a labelled default and a **refuse-counted-play**
  fallback — **not** a blocker and **not** the requirement itself.
