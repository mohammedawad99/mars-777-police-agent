# PRD-06 — Security and Cryptography — group MaRs-777 (POLICE)

## 1. Document Metadata

| Field | Value |
|---|---|
| PRD | PRD-06 — Security & Cryptography (**HIGH-RISK**) |
| Repository role | **POLICE** |
| Owns | `protocol.canonical`, `protocol.commitment`, `protocol.keyed_auth`, `protocol.config_lock`, `protocol.declaration`, `protocol.profiles`, secret handling in `infra.settings` |
| Architecture inputs | `SECURITY_ARCHITECTURE.md`, `../spec/json/SIGNATURE_AND_HASH_PROVENANCE.md`, `CANONICALIZATION_CONTRACT.md`, `ARTIFACT_LIFECYCLE.md`, `ERROR_MODEL.md` |
| Symmetry class | **COMMON-WITH-ROLE-SECTIONS** (role identity only; crypto is identical) |

## 2. Status

**APPROVED — PHASE 2 LOCKED.** Approved after Stage 2-CLOSE supervising review.
**Implementation status: IMPLEMENTED-E2E.** The cryptographic chain this PRD
owns is implemented and covered end to end: canonical hashed bytes
(`protocol/canonical.py`, kept separate from the wire/artifact decimal spelling
authority), the sealed **eight**-member record, SHA-256 commitment
(`protocol/commitment.py`) and its recomputation
(`protocol/audit_commitment.py`), a CSPRNG nonce source
(`protocol/secure_nonce.py`) held secret until the final nonce reveal, keyed
Step-0 and config authentication (`protocol/keyed_auth.py`,
`protocol/config_lock.py`), `TAMPERED` on any recomputed-hash mismatch, and the
`config_sha256` / `scent_model_sha256` digest binding — all pinned by golden
vectors. No third-party crypto dependency was added; the standard library
provides SHA-256 and HMAC. **Physical scent truthfulness is deliberately not
part of this status** — it is authorized as JDEC-018 and scheduled for Part 2B.

## 3. Purpose

Specify every cryptographic and secret-handling requirement: exact canonical bytes,
Step-0 producer authentication with a pre-supplied key, config equality **and**
authentication, the commit-reveal construction and nonce lifecycle, final audit and
TAMPERED detection, the result-approval digest, compatibility codecs, and the key/secret
lifecycle — with **terminology that is never conflated**.

## 4. Problem Statement

Every integrity guarantee in this project reduces to *"both peers hash the same bytes and
one of them proves it produced them."* A single ambiguity — which bytes, which primitive,
which key, when the nonce is revealed — silently converts an honest match into a disputed
or void one. The reference implementation demonstrates the exact hazard: it calls an
**unkeyed** `SHA256(terms‖nonce)` a *"signature"*. This PRD exists to make that class of
error impossible in strict mode.

## 5. Scope

Canonicalization · Step-0 authentication · declaration authentication · config equality +
authentication + lock · commitment construction · nonce lifecycle · Commit→Ack→Reveal
integrity · final audit and tamper detection · commitment/auth compatibility profiles ·
result approval digest · key and secret lifecycle · the security negative-test matrix.

## 6. Out of Scope

Game strategy (PRD-03) · public tunnel lifecycle (PRD-05) · Gmail sending and OAuth scope
(PRD-07) · GUI display (PRD-07) · state-machine mechanics (PRD-02 — this PRD owns the
*cryptographic correctness* of what those states carry).

## 7. Actors

This **POLICE** agent (producer/verifier) · the opponent peer (untrusted producer and
verifier) · the replay verifier (PRD-07, which **calls this PRD's interfaces**) · the local
operator (provisions the pre-supplied key out of band).

## 8. Definitions

| Term | Exactly what it is |
|---|---|
| **HASH** | Unkeyed digest. Proves content integrity. **Does not authenticate a producer.** |
| **MAC / HMAC** | **Keyed** authenticator (symmetric). Proves the holder of a shared key produced it. **Not** a digital signature. |
| **DIGITAL SIGNATURE** | Asymmetric (private-key sign / public-key verify), e.g. Ed25519. **Not** a MAC. |
| **COMMITMENT** | A hiding + binding value published before the secret is revealed. |
| **ACKNOWLEDGEMENT** | Two parties comparing and agreeing on the same digest. Not authentication. |
| **CONTENT DIGEST** | Unkeyed hash used for equality/integrity of a document. |
| **GIT COMMIT SHA** | **Source-code identity only.** Never a message-authentication primitive. |

## 9. Locked Source Requirements

| ID | Modality | Requirement |
|---|---|---|
| **CRYPTO-001** | MUST | SHA-256-based **commit-reveal** for every move |
| **CRYPTO-002** | MUST | Keep each **nonce secret until the end of the game** (final audit) |
| **CRYPTO-003** | MUST | On any hash mismatch at audit, **technically disqualify** the game (score 0 to the forger) |
| **CRYPTO-004** | MUST | Declare **only the truth** when a capture is claimed |
| **CRYPTO-005** | **MUST NOT** (POLICE) | Never falsely declare a capture |
| **CRYPTO-006** | MUST | Perform a **signed Step-0 hardware declaration** before the game starts |
| **CRYPTO-007** | MUST | Comprehensive **mutual log audit** at the end of each game before agreeing the shared result |
| **CRYPTO-008** | MUST | Follow **Commit → Acknowledge → Reveal → (final) Audit**; reveal Move+Hint but keep the nonce hidden |
| **CRYPTO-009** | MUST | Hash over **canonical JSON** (sorted keys, fixed separators) so both peers hash byte-identical input |
| **CRYPTO-010** | SHOULD | Generate nonces with a **cryptographic RNG** (`secrets`), not `random` |
| **CRYPTO-011** | MUST | **Cryptographically lock the LLM token-consumption record at Step-0** |
| **SEC-003** | **MUST NOT** | Never push secrets/credentials to the repository — even a private one |
| **SEC-004** | MUST | Add credential/secret files (`credentials.json`, `token.json`, keys) to `.gitignore` |
| **SEC-005** | MUST | If a secret leaks, **rotate** it in the console (deletion from current code is insufficient) |
| GAME-001/002 | MUST | Byte-identical signed config; MINIMUMs only raised *(owned PRD-01/02; enforced at lock here)* |
| JSON-004 | MUST | `config/game.json` canonically serializable and hashable *(owned PRD-07; construction here)* |

**Invariants:** INV-06 (commitments recompute), INV-14 (Step-0 keyed auth verifies),
INV-15 (config hash **and** tag verify). **Conflicts:** C-07 (technical_loss provenance),
C-08 (`intent` only), C-09 (reporting sanction — PRD-07).

## 10. Project / Architecture Decisions

| Decision | Provenance |
|---|---|
| Canonical params: `sort_keys`, `(",",":")`, UTF-8, NFC, LF, no trailing newline | **PROJECT-CONTRACT** (JDEC-002) + **SOURCE-MANDATORY** core (CRYPTO-009) |
| `AuthProfile.HMAC_SHA256` = project default for Step-0/config | **PROJECT-CONTRACT** (JDEC-013) |
| `AuthProfile.ED25519` = attachment-example option | **ATTACHMENT-COMPATIBILITY** (AE-02) — *not* source-mandated |
| Digests/tags stored **outside** the bytes they cover | **PROJECT-CONTRACT** (JDEC-010) |
| `context ∈ {"step0","config"}` domain separation | **PROJECT-CONTRACT** (JDEC-013) |
| `CommitmentCodec ∈ {STRICT_PROJECT, LECTURER_REFERENCE}` | **REFERENCE-COMPATIBILITY** (D-01) |
| Exact config-auth primitive | **SOURCE-UNSPECIFIED** → **NEGOTIATED-PRE-MATCH** (NDEC-007) |
| No crypto dependency added at this stage | scope |

## 11. Inputs

Pre-supplied key material (environment, out of band) · `key_id` (non-secret) · Step-0 core
data · proposed/agreed config · per-turn sealed record fields · peer messages (untrusted) ·
negotiated profiles · finalized result approval core.

## 12. Outputs

Canonical byte strings · `H_commit` values · `step0_auth` / `config_auth` envelopes
`{auth_alg, key_id, auth_tag}` · `config_sha256` · verification verdicts · audit result
(Verified OK / TAMPERED) · `result_sha256`.

## 13. Functional Requirements

### 13.1 Canonicalization

| ID | Requirement | Provenance |
|---|---|---|
| **PRD06-FR-001** | Every cryptographic operation MUST state **exactly which bytes** it covers. No operation may hash "the object" ambiguously. | **SOURCE-MANDATORY** (CRYPTO-009) |
| **PRD06-FR-002** | Canonical JSON uses **sorted keys** and **fixed compact separators** `(",", ":")`. | **SOURCE-MANDATORY** (CRYPTO-009) + JDEC-002 |
| **PRD06-FR-003** | Encoding is **UTF-8**; text is **Unicode NFC-normalised** before encoding. | **PROJECT-CONTRACT** (JDEC-002) |
| **PRD06-FR-004** | Line endings in canonical bytes are **LF**; there is **no trailing newline** inside a hashed payload. | **PROJECT-CONTRACT** (JDEC-002) |
| **PRD06-FR-005** | `ensure_ascii` is **fixed and agreed pre-match** (project default: `False`, matching the reference); it MUST be identical on both peers. | **NEGOTIATED-PRE-MATCH** (NDEC-003); **REFERENCE-COMPATIBILITY** default |
| **PRD06-FR-006** | Numbers use deterministic, locale-independent representation; integers without leading zeros; **no exponent notation**; `-0` normalised to `0`; floats written exactly as the config carries them (`0.9`, `0.10`). | **PROJECT-CONTRACT** (JDEC-002) |
| **PRD06-FR-007** | Arrays whose order is not semantic MUST be canonically **sorted** (e.g. `barriers` lexicographically by `[row, col]`). | **PROJECT-CONTRACT** (JDEC-012) |
| **PRD06-FR-008** | **Duplicate JSON keys are rejected**; `null` is not emitted inside a hashed payload (prefer absent). | **PROJECT-CONTRACT** (JDEC-002) |
| **PRD06-FR-009** | Canonical output for identical logical input MUST be **byte-identical on Linux and Windows**, verified by golden vectors. | **PROJECT-CONTRACT**; cross-OS |
| **PRD06-FR-010** | Reference-code serialization choices are adopted as **project defaults**, explicitly **not** promoted to source requirements. | **REFERENCE-COMPATIBILITY** |

### 13.2 Step-0 authentication

| ID | Requirement | Provenance |
|---|---|---|
| **PRD06-FR-020** | A **signed Step-0 declaration** MUST be produced before the game starts, covering the hardware/host spec, model, code version, played commit, token record, identities and times. | **SOURCE-MANDATORY** (CRYPTO-006) |
| **PRD06-FR-021** | In `STRICT_COUNTED_MATCH`, Step-0 MUST use **cryptographic producer authentication with a pre-supplied key**. | **SOURCE-MANDATORY** (CRYPTO-006; Ch 5 p.55–56) |
| **PRD06-FR-022** | **`SHA256(public_terms ‖ public_nonce)` — an unkeyed digest over public inputs — MUST NOT be accepted as strict producer authentication.** Anyone can recompute it; it proves integrity and agreement, not authorship. | **SOURCE-MANDATORY** (CRYPTO-006); reference-conflict finding |
| **PRD06-FR-023** | The authenticated payload is `auth_tag = KEYED_AUTH_key( "step0" ‖ canonical(step0_core) )`. `context = "step0"` is authenticated **together with** the payload. | **PROJECT-CONTRACT** (JDEC-013) |
| **PRD06-FR-024** | Supported `AuthProfile`s: **`HMAC_SHA256`** (project default — a **MAC**, not a signature) and **`ED25519`** (attachment-example — a **digital signature**, not a MAC). Terminology MUST be used correctly in code, docs and logs. | JDEC-013; **ATTACHMENT-COMPATIBILITY** (AE-02) |
| **PRD06-FR-025** | The envelope `{auth_alg, key_id, auth_tag}` is stored **outside** the authenticated bytes (**non-self-referential**). | **PROJECT-CONTRACT** (JDEC-010) |
| **PRD06-FR-026** | Only the **non-secret `key_id`** is serialized. **Key material is never stored in any artifact.** | **SOURCE-MANDATORY** (SEC-003); JDEC-013 |
| **PRD06-FR-027** | The peer's Step-0 tag MUST be **verified before counted play**; failure ⇒ `E-AUTH-FAILURE` ⇒ **refuse counted play**. | **INV-14**; `ERROR_MODEL.md` |
| **PRD06-FR-028** | **No silent downgrade:** if strict keyed authentication cannot be established, the system MUST refuse counted play rather than fall back to an unkeyed reference hash. A downgrade requires an explicit, recorded pre-match agreement and is **not** available in `STRICT_COUNTED_MATCH`. | **ARCHITECTURE-CONSTRAINT**; `COMPATIBILITY_PROFILES.md` |
| **PRD06-FR-029** | **[Amended Stage 4E-R12-R1]** **Actual** LLM token consumption MUST be metered and cryptographically locked so later denial is impossible — but **not** as a member of the Step-0 authenticated core, which is stamped **before the first move** and cannot contain a runtime total. Ch 5 §5.5 states the duty **alongside** the Step-0 signing; **App E #54** and **Ch 9 §9.3.3** place the actual totals in the **final report** (`sub_games[].tokens`, `total_tokens`), where they sit inside the RESULT APPROVAL CORE and are covered by `result_sha256` (NDEC-006) with both reports required to match or **0 to both** (C-09). What the Step-0 core **does** carry is the **agreed token cap** (`token_budget_per_series`, Ch 9 §9.3.3). **[Further corrected Stage 4E-R12-R2]** `result_sha256` secures the **finally reported** totals only — it does **not** prove that every LLM call was metered, that none was omitted, or that the totals equal runtime/provider-observed consumption, and it is **not** claimed to discharge this MUST. The runtime cryptographic locking is **SOURCE-UNSPECIFIED** in construction (no algorithm, keying, per-call schema, chain, ledger format, placement or cadence is fixed by the book) and is **not yet frozen**: it is recorded as **`TOKEN-ACCOUNTING-CRYPTO-EVIDENCE: BLOCKED-BY-CONSTRUCTION`** and **owned by this PRD**. It is a **local/runtime security obligation** — not a peer-message family, not an interoperability blocker, not a Step-0/Config/ResultAgreement message blocker — and it does not alter any family readiness. Metering itself stays with PRD-04 (`PRD04-FR-044`); the reported totals stay with PRD-07 / the result. | **SOURCE-MANDATORY** (CRYPTO-011, PERF-002, **PERF-001/E-54**) |
| **PRD06-FR-030** | The exact **played Git commit** is recorded in the Step-0 declaration; it is **source identity evidence, never authentication**. | **SOURCE-MANDATORY** (GIT-003); taxonomy §8 |

### 13.3 Config equality, authentication and lock

| ID | Requirement | Provenance |
|---|---|---|
| **PRD06-FR-040** | Both peers MUST hold a **byte-identical** binding config. | **SOURCE-MANDATORY** (GAME-001) |
| **PRD06-FR-041** | **Four distinct artefacts** are defined and never conflated: (1) **canonical config bytes**; (2) **`config_sha256`** — an *unkeyed content-equality digest*; (3) **config authentication / signature exchange** — a *distinct keyed operation*; (4) **mutual acknowledgement** — both sides agreeing the digests match. | **SOURCE-MANDATORY** (App B p.128) + taxonomy |
| **PRD06-FR-042** | `config_sha256 = SHA256(canonical(config_core))`, stored **outside** the config (non-self-referential). | JDEC-010; JSON-004 |
| **PRD06-FR-043** | `config_auth.auth_tag = KEYED_AUTH_key( "config" ‖ canonical(config_core) )`, with `context = "config"` giving **domain separation** so a Step-0 tag can never be replayed as a config tag. **[Amended Stage 4E-R12-FIX]** The authenticated core is **`ConfigLockContext` = `{game_id, game_uid, sub_game, config_sha256, profiles}`**, not the App-B core directly: that core is byte-identical across every sub-game of a series, so a proof over it alone binds no sub-game, no game identity and none of the FR-048 lock-frozen values. `config_sha256` binds all 35 core members transitively (hash-then-authenticate), so the App-B core is never polluted with protocol metadata (D4). `context`, domain separation, non-self-reference and the unkeyed `config_sha256` of FR-042 are unchanged. | JDEC-013; NDEC-007; `CONFIG_CONTRACT.md` R12-FIX-K |
| **PRD06-FR-044** | **`config_sha256` equality alone is NOT authentication.** Counted play requires hash equality **and** a verified authentication tag. | **INV-15** |
| **PRD06-FR-045** | The **exact config-auth primitive is SOURCE-UNSPECIFIED**; HMAC-SHA256 is the project default and Ed25519 a negotiable option. Step-0's explicit "pre-supplied key" wording is **not** transferred verbatim onto the looser config wording. | **NEGOTIATED-PRE-MATCH** (NDEC-007); Stage-2A-R2 provenance |
| **PRD06-FR-046** | **Appendix-F status validation happens BEFORE lock**: FIXED rejected if altered, MINIMUM rejected if lowered, NEGOTIABLE accepted if mutually agreed. **[Amended Stage 4E-R12-R3]** One NEGOTIABLE member has a narrower **project lifecycle**: `token_budget_per_series` is agreed **before `BOOT`** and authenticated inside the Step-0 core at event 1, so during config negotiation it is **equality-checked only and never counter-proposable** — a differing value is `E-CONFIG-MISMATCH` and refuses counted play, never a renegotiation. Before the `CONFIG_LOCKED` transition the locked config's `network_and_league.token_budget_per_series` **MUST equal** the declaration's authenticated cap; mismatch ⇒ `E-CONFIG-MISMATCH` ⇒ refuse counted play, with no repair and **no technical-loss score before counted play**. Its Appendix-F status remains **NEGOTIABLE** (source provenance); PRE-STEP0-FROZEN is project lifecycle, and the two are not the same axis. | **SOURCE-MANDATORY** (GAME-002); lifecycle **PROJECT-CONTRACT** (`DECLARATION_CONTRACT.md` §R12-R3) |
| **PRD06-FR-047** | Whether Step-0 and config use the **same or distinct keys is source-unspecified** and MUST be agreed pre-match; **key reuse is never assumed**. | NDEC-007 |
| **PRD06-FR-048** | On `CONFIG_LOCKED`, the following become **immutable for the sub-game**: binding numeric terms, active `AuthProfile`, active `CommitmentCodec`, active `ResultProfile`, and the agreed **series convention** (PRD-05). | PRD-02 FR-080; PRD-05 FR-034 |
| **PRD06-FR-049** | Any post-lock change attempt is a defect (`E-LOCAL-DEFECT`) or, if requested by the peer, a rejected protocol message. | `ERROR_MODEL.md` |

### 13.4 Commitment record and nonce

| ID | Requirement | Provenance |
|---|---|---|
| **PRD06-FR-060** | The approved semantic sealed record is exactly: `state`, `move`, `intent`, `hint`, `step`, `role`, `sub_game`, `nonce`. | **SOURCE-MANDATORY** (Ch 5) + **C-08** |
| **PRD06-FR-061** | `STRICT_PROJECT_COMMITMENT`: `H_commit = SHA256( canonical( sealed_record ) )` with the **nonce inside** the canonical payload. | **PROJECT-CONTRACT**; NDEC-001 |
| **PRD06-FR-062** | Exactly **one** classification field, `intent`; **no second authoritative `verdict`**. | **C-08** |
| **PRD06-FR-063** | A **fresh nonce per commitment**, generated with a **cryptographic RNG** (`secrets`, not `random`). | **SOURCE-RECOMMENDED** (CRYPTO-010, SHOULD) — adopted as project MUST |
| **PRD06-FR-064** | **Nonce reuse is forbidden** and MUST be detected: a repeated nonce within a game is rejected/flagged. | **PROJECT-CONTRACT** (binding property of commit-reveal) |
| **PRD06-FR-065** | The nonce is **secret until final audit**; it MUST NOT appear in any message, log entry, GUI event, report, metric or prompt before that point. | **SOURCE-MANDATORY** (CRYPTO-002, CRYPTO-008) |
| **PRD06-FR-066** | **No source-mandated nonce length is asserted.** The project default is 16 bytes (32 hex chars), matching the reference; this is **PROJECT-CONTRACT**, negotiable. | **PROJECT-CONTRACT**; not sourced |
| **PRD06-FR-067** | The commitment alone MUST NOT reveal the move: given `H_commit` and public information, the move must not be recoverable without the nonce (hiding), and the committer must not be able to open it to a different record (binding). | **SOURCE-MANDATORY** (CRYPTO-001 purpose) |
| **PRD06-FR-068** | `state` uses the approved own-known representation `{config_sha256, self_pos, barriers(sorted), step, role}` — it MUST contain **no opponent truth**. | JDEC-012; NDEC-002; GUI-002 |

### 13.5 Commit → Ack → Reveal

| ID | Requirement | Provenance |
|---|---|---|
| **PRD06-FR-080** | The order is **Commit → Acknowledge → Reveal → (final) Audit**; reveal discloses **Move + Hint** but **keeps the nonce hidden**. | **SOURCE-MANDATORY** (CRYPTO-008) |
| **PRD06-FR-081** | The commitment MUST be sent **before** the opponent can learn the protected decision. | CRYPTO-001/008 |
| **PRD06-FR-082** | The **acknowledgement binds receipt** of a specific `H_commit` for a specific `(sub_game, step)`. | CRYPTO-008 |
| **PRD06-FR-083** | **No reveal before a valid, matching ack.** | CRYPTO-008; PRD-02 R1 |
| **PRD06-FR-084** | The reveal MUST NOT change the committed semantic content; the verifier recomputes over the **exact** canonical bytes and compares. | **SOURCE-MANDATORY** (CRYPTO-009); INV-06 |
| **PRD06-FR-085** | A recompute mismatch ⇒ **TAMPERED** with the locked sanction (technical disqualification, score 0 to the forger). **No additional sanction is invented.** | **SOURCE-MANDATORY** (CRYPTO-003); INV-06 |
| **PRD06-FR-086** | **Duplicate or stale messages cannot replace an original commitment.** A second commitment for an already-committed `(sub_game, step)` is rejected, never overwritten. | PRD-02 R8; T3 |
| **PRD06-FR-087** | The active `CommitmentCodec` and `AuthProfile` MUST NOT change between commitment and verification. | FR-048 |
| **PRD06-FR-088** | A **capture claim must be truthful**; a claim inconsistent with the deterministically validated state is rejected, and a false capture claim carries the locked sanction. | **SOURCE-MANDATORY** (CRYPTO-004, CRYPTO-005) |

### 13.6 Final audit and tamper

| ID | Requirement | Provenance |
|---|---|---|
| **PRD06-FR-100** | At end of game the peers perform a **comprehensive mutual log audit before agreeing the shared result**. | **SOURCE-MANDATORY** (CRYPTO-007) |
| **PRD06-FR-101** | All required sealed evidence (including every nonce) becomes verifiable **only at final audit**. | CRYPTO-002/008 |
| **PRD06-FR-102** | The verifier recomputes **every** commitment for every step of every sub-game. | **SOURCE-MANDATORY** (REPLAY-002 mechanism; INV-06) |
| **PRD06-FR-103** | The **first mismatch is sufficient** to declare TAMPERED; the audit need not continue to be conclusive. | CRYPTO-003 |
| **PRD06-FR-104** | Evidence is **preserved** on TAMPERED (sealed record, expected vs actual digest, step identity). | REPLAY-001/002 |
| **PRD06-FR-105** | Where the locked source forbids appeal/retroactive correction, that is honoured **as sourced** (PDF p.75; App E #22) and is **not extended** to other situations. | **SOURCE-MANDATORY** |
| **PRD06-FR-106** | **C-07, C-08 and C-09 remain distinct**: technical-loss 0/0 provenance (Ch 3 + App E #48, not App F); `intent` single field; reporting sanction (PRD-07). None is merged into TAMPERED. | **C-07/C-08/C-09** |

### 13.7 Compatibility profiles

| ID | Requirement | Provenance |
|---|---|---|
| **PRD06-FR-120** | Supported commitment codecs: **`STRICT_PROJECT_COMMITMENT`** (default) and **`LECTURER_REFERENCE_COMMITMENT`**. The reference codec may differ in **field set**, **nonce placement** (outside the canonical payload) and **byte construction**. | **REFERENCE-COMPATIBILITY** (D-01/D-02) |
| **PRD06-FR-121** | The reference codec is **not SOURCE-MUST**; it is available only by explicit mutual agreement. | **REFERENCE-COMPATIBILITY** |
| **PRD06-FR-122** | Any codec/profile **and the agreed series convention** MUST be: selected before play, mutually agreed, **authenticated as part of the pre-series negotiation evidence**, **recorded in the negotiation record (never as an official artifact schema field)**, **immutable after config lock**, and used **identically by committer and verifier**. **[Amended Stage 4E-R12]** This applies to every profile **except `AuthProfile`/`KeyId`**, for which it would be circular: they *are* the authentication mechanism, so they cannot be authenticated by pre-series negotiation evidence that does not yet exist. They are **provisioned out of band with the key before `BOOT`**, are **compared not negotiated** on the wire, and any difference refuses counted play (FR-027/FR-028). Their immutability and identical-use obligations are unchanged and start earlier. | FR-048/087; PRD-05 FR-034/034a; `SIGNATURE_AND_HASH_PROVENANCE.md` R12-A |
| **PRD06-FR-123** | **Compatibility MUST NOT weaken a strict binding requirement.** A profile that would remove keyed Step-0 authentication, alter an Appendix-F value, disable audit, or relax privacy is **rejected**, and counted play is refused. | `COMPATIBILITY_PROFILES.md` governing rule |
| **PRD06-FR-124** | A **profile-downgrade attempt** by the peer (offering weaker crypto after agreement) is rejected as a protocol violation, not silently accepted. | T5/T6 |

### 13.8 Result approval digest

| ID | Requirement | Provenance |
|---|---|---|
| **PRD06-FR-140** | `result_sha256 = SHA256( canonical_bytes( RESULT_APPROVAL_CORE ) )`. | **PROJECT-CONTRACT**; NDEC-006 |
| **PRD06-FR-141** | `RESULT_APPROVAL_CORE` **includes**: `game_id`, `game_uid`, `declaration_ref`, team `group_id`s, the four GitHub links, per-sub-game `{sub_game, cop_score, thief_score, outcome, github_commit, tokens}`, `cumulative`, `total_tokens`, `timestamp`. **[Amended Stage 4E-R13-R1]** The three participant-owned members are **participant-scoped two-value objects keyed `{group_a, group_b}`** — `sub_games[].github_commit`, `sub_games[].tokens` and `total_tokens`. **A scalar whose meaning depends on which peer emitted the report is forbidden inside the shared core.** Member list and count are otherwise unchanged; this is a shape refinement, not an addition. | JDEC-014; NDEC-006; `RESULT_CONTRACT.md` §R13-R1 |
| **PRD06-FR-142** | It **excludes**: `result_sha256` itself, the `mutual_agreement` flag, `reported_by`, and any reporter-local presentation metadata. *(Stage 4E-R2-FIX2 propagation: this row previously named `mutual_agreement.sha256` and `mutual_agreement.confirmed`, the nested object form `RESULT_CONTRACT.md` withdrew at Stage 4F-R1 and NDEC-006 dropped at Stage 4E-R2-FIX1. The exclusion semantics are unchanged — neither the approval digest nor the agreement state may sit inside the bytes it approves — and the algorithm, canonicalization and approval-core field set are untouched.)* | JDEC-010/014 |
| **PRD06-FR-143** | **NON-SELF-REFERENTIAL**: the digest field is never part of the bytes from which its own value is computed. | JDEC-010 |
| **PRD06-FR-144** | `result_sha256` is an **unkeyed content-agreement digest** supporting mutual acknowledgement. **No keyed result signature is introduced** unless separately selected as a documented project extension. | taxonomy; NDEC-006 |
| **PRD06-FR-145** | Both peers compute the core independently and compare; the reporting sanction on mismatch/absence is **PRD-07 / C-09**, not a crypto sanction. **[Stage 4E-R13 note, RESOLVED at Stage 4E-R13-R1]** Independent computation requires every core member to be **jointly derivable**. `sub_games[].tokens`, `total_tokens` and `sub_games[].github_commit` are participant-owned and were not transmitted before the digest was computed. **Resolved**: each peer sends exactly one `ResultAgreement` request carrying the agreed `timestamp` and its own `ResultContribution` *(timestamp added Stage 4E-R13-R2)*, the deterministic timestamp proposer sends first, the operation's successful response is the receiver's locally computed `Sha256Digest`, and both peers then build the same participant-scoped core. **`RESULT-APPROVAL-CORE-JOINT-DERIVABILITY: RESOLVED-PROJECT`** (`RESULT_CONTRACT.md` §R13-R1). FR-140…FR-144 are otherwise unchanged. | C-09 (PRD-07 owns) |

### 13.9 Key and secret lifecycle

| ID | Requirement | Provenance |
|---|---|---|
| **PRD06-FR-160** | The pre-supplied key is **provisioned out of band** and loaded **process-locally from the environment**. | **SOURCE-MANDATORY** (CRYPTO-006 "pre-supplied"); SEC-003 |
| **PRD06-FR-161** | Key material MUST NOT appear in: **Git**, any JSON artifact, logs, GUI, exception text, metric labels, LLM prompts, or test fixtures. | **SOURCE-MANDATORY** (SEC-003) |
| **PRD06-FR-162** | Credential/secret files (`credentials.json`, `token.json`, key files) MUST be **git-ignored**. | **SOURCE-MANDATORY** (SEC-004) |
| **PRD06-FR-163** | If a secret is ever leaked or committed, it MUST be **rotated at the provider/console**; deleting it from current code is explicitly insufficient. | **SOURCE-MANDATORY** (SEC-005) |
| **PRD06-FR-164** | Tests use **clearly fake keys** (obviously non-real values); no real secret is documented anywhere. | **PROJECT-CONTRACT** |
| **PRD06-FR-165** | Key material is held for the **minimum necessary lifetime** and best-effort cleared after use. The design explicitly **does not claim guaranteed memory erasure in Python**; this is a best-effort control, not a security guarantee. | **PROJECT-CONTRACT** (honest limitation) |
| **PRD06-FR-166** | Digest/tag comparison uses a **constant-time comparison** where the language provides it (e.g. `secrets.compare_digest`). | **PROJECT-CONTRACT**; `SECURITY_ARCHITECTURE.md` |
| **PRD06-FR-167** | A missing required secret at start-up ⇒ **refuse to start a counted match** (fail closed), with an error naming only the missing setting. | `CONFIG_ARCHITECTURE.md` |

## 14. Non-Functional Requirements

| ID | Requirement |
|---|---|
| **PRD06-NFR-001** | Canonicalization + hashing of a turn record completes in **< 2 ms** (measurable) so it never pressures the step budget. |
| **PRD06-NFR-002** | All crypto logic is **pure and offline-testable** with golden vectors; no network, no clock. |
| **PRD06-NFR-003** | **No cryptographic dependency is added at this stage**; strict mode uses only the standard library (`hashlib`, `hmac`, `secrets`). Ed25519 would require a justified dependency and is not adopted now. |
| **PRD06-NFR-004** | Every file ≤ **150 lines**; canonical, commitment, keyed_auth, config_lock, declaration and profiles are separate modules. |
| **PRD06-NFR-005** | **Exactly one** implementation of each cryptographic operation exists in the codebase; PRD-07 replay calls it rather than duplicating it. |

## 15. Lifecycle / State Responsibilities

Owns: canonical byte production, pending nonce (single custodian), commitment values,
auth envelopes, `config_sha256`, locked-config handle, active profiles, audit verdict,
`result_sha256`. **Does not own:** state-machine phase (PRD-02), artifacts/report (PRD-07),
transport (PRD-05), game truth (PRD-01).

## 16. Validation Rules

Canonical form valid (no duplicate keys, no `null`, sorted, NFC, LF) · `key_id` known ·
`auth_alg` is an agreed profile · tag verifies · `config_sha256` equal · Appendix-F status
satisfied · commitment matches `(sub_game, step)` cursor · no duplicate commitment · no
nonce reuse · reveal consistent with commitment · profile unchanged since lock · result
core excludes its own digest.

## 17. Failure Behaviour

`E-AUTH-FAILURE` (unknown `key_id`, bad tag, no compatible mechanism) ⇒ **refuse counted
play** · `E-CONFIG-MISMATCH` ⇒ refuse counted play · `E-HASH-MISMATCH` /
`E-NONCE-MISMATCH` / `E-REPLAY-MISMATCH` ⇒ **TAMPERED** (terminal, locked sanction) ·
`E-PROTO-STALE` for duplicate commitments · `E-LOCAL-DEFECT` for post-lock mutation.
**Integrity failures are never retried.** No sanction beyond the locked set.

## 18. Security / Privacy

Untrusted peer input validated before effect · fail closed on integrity · no secret in any
output surface · nonce secret until audit · `state` carries no opponent truth · constant-time
comparisons · bounded parsing before verification · domain separation prevents cross-object
tag replay · Git SHA never treated as authentication.

## 19. Determinism / Reproducibility

All crypto operations are **deterministic given their inputs**, except nonce generation
(CSPRNG by design). Golden vectors pin canonical bytes and digests. Verification is fully
reproducible offline from artifacts, on both OSes.

## 20. Performance / Deadline Constraints

Per-turn crypto ≪ step budget (NFR-001). Full-series audit (6 sub-games × steps) completes
within the audit window; complexity is linear in the number of steps.

## 21. Cross-Platform Constraints

**Byte-identical canonical output and identical digests on Linux and Windows** — the single
highest-risk cross-platform property, pinned by golden-vector tests in CI on both OSes
(NFC, LF, UTF-8, sorted keys, number formatting).

## 22. Observability / Evidence

Auth verification results (by `key_id`, **never key bytes**), `auth_alg` in force, config
hash comparison outcome, commitment counts, audit verdict per step, first-mismatch
location, profile in force, nonce-reuse detections, constant-time comparison usage.
**Never emitted:** key material, nonces before audit, credentials.

## 23. Acceptance Criteria

| ID | Criterion |
|---|---|
| **PRD06-AC-001** | Strict Step-0 succeeds with a valid pre-supplied key and the peer's tag verifies; play proceeds. |
| **PRD06-AC-002** | **A plain unkeyed `SHA256(terms‖nonce)` presented as Step-0 authentication is REJECTED in strict mode** (`E-AUTH-FAILURE`), and there is no automatic downgrade path. |
| **PRD06-AC-003** | A wrong key or unknown `key_id` ⇒ `E-AUTH-FAILURE` ⇒ counted play refused. |
| **PRD06-AC-004** | A mutated declaration fails Step-0 verification. |
| **PRD06-AC-005** | Byte-different configs ⇒ `config_sha256` mismatch ⇒ counted play refused. |
| **PRD06-AC-006** | Equal `config_sha256` but **invalid config auth tag** ⇒ counted play refused (proving hash equality alone is insufficient). |
| **PRD06-AC-007** | A FIXED value altered / a MINIMUM lowered is rejected **before** lock. |
| **PRD06-AC-008** | Commitment reproducibility: recomputing `H_commit` from the revealed record + nonce reproduces the stored value exactly. |
| **PRD06-AC-009** | Changing the move, `intent` or `hint` after commitment causes a mismatch ⇒ TAMPERED. |
| **PRD06-AC-010** | A reused nonce is detected and rejected. |
| **PRD06-AC-011** | The nonce is **absent** from every message, log entry, GUI event, report and prompt before final audit (scan). |
| **PRD06-AC-012** | Early-reveal and missing-ack attempts are rejected. |
| **PRD06-AC-013** | A duplicate/stale commitment for an already-committed step does not replace the original. |
| **PRD06-AC-014** | A one-byte log mutation is detected at audit ⇒ **TAMPERED**, with preserved evidence naming the failing step. |
| **PRD06-AC-015** | A profile downgrade offered after config lock is rejected. |
| **PRD06-AC-016** | Selecting `LECTURER_REFERENCE_COMMITMENT` produces reference-shaped bytes and verifies **only** when both sides use it; mixing codecs fails deterministically. |
| **PRD06-AC-017** | `result_sha256` recomputation over `RESULT_APPROVAL_CORE` is stable, and **including the digest field in the core changes the value — proving non-self-reference is enforced**. |
| **PRD06-AC-018** | Scan: no key material, credential or nonce-before-audit in artifacts, logs, metrics, errors or prompts. |
| **PRD06-AC-019** | Golden canonical vectors produce **byte-identical output and identical digests on Linux and Windows**. |
| **PRD06-AC-020** | Digest/tag comparison uses constant-time comparison (code/contract check). |
| **PRD06-AC-021** | A missing required secret prevents start-up of a counted match, with an error naming only the setting. |
| **PRD06-AC-022** | HMAC is never labelled a digital signature and Ed25519 never a MAC anywhere in code, docs or logs (terminology lint). |

## 24. Planned Tests (security negative matrix)

| ID | Test | Layer |
|---|---|---|
| **PRD06-T-001** | Wrong Step-0 key | SECURITY |
| **PRD06-T-002** | Missing Step-0 auth | SECURITY |
| **PRD06-T-003** | Unkeyed reference hash presented as strict auth ⇒ rejected | SECURITY |
| **PRD06-T-004** | Mutated declaration | SECURITY |
| **PRD06-T-005** | Config byte mismatch | PROTOCOL |
| **PRD06-T-006** | Config digest mismatch | PROTOCOL |
| **PRD06-T-007** | Config auth tag mismatch (hash equal) | SECURITY |
| **PRD06-T-008** | Appendix-F status violation pre-lock | UNIT |
| **PRD06-T-009** | Profile downgrade attempt | SECURITY |
| **PRD06-T-010** | Profile change after lock | CONTRACT |
| **PRD06-T-011** | Reused nonce | SECURITY |
| **PRD06-T-012** | Malformed commitment | PROTOCOL |
| **PRD06-T-013** | Changed move after commitment | SECURITY |
| **PRD06-T-014** | Changed `intent` / `hint` after commitment | SECURITY |
| **PRD06-T-015** | Wrong step / sub-game cursor | PROTOCOL |
| **PRD06-T-016** | Early reveal | PROTOCOL |
| **PRD06-T-017** | Missing ack | PROTOCOL |
| **PRD06-T-018** | Stale / duplicate commitment | PROTOCOL |
| **PRD06-T-019** | Hash mismatch ⇒ TAMPERED | SECURITY / REPLAY |
| **PRD06-T-020** | Mutated log (one byte) ⇒ TAMPERED | REPLAY |
| **PRD06-T-021** | Altered result approval core ⇒ digest change | UNIT |
| **PRD06-T-022** | Self-referential result-hash regression guard | UNIT |
| **PRD06-T-023** | Secret-leakage scans (artifacts/logs/metrics/errors/prompts) | SECURITY |
| **PRD06-T-024** | Linux/Windows canonical byte + digest equality (golden vectors) | PROPERTY / CROSS-PROCESS |
| **PRD06-T-025** | Terminology lint (HMAC≠signature, Ed25519≠MAC) | CONTRACT |
| **PRD06-T-026** | Constant-time comparison usage | CONTRACT |
| **PRD06-T-027** | Nonce hiding/binding property (commitment reveals nothing) | PROPERTY |

## 25. Requirement Traceability

**Primary owner:** CRYPTO-001…011 (11), SEC-003, SEC-004, SEC-005 (3) = **14**.
**Enforces on behalf of others:** GAME-001/002 (at lock), JSON-004 (canonical config),
GIT-003 (commit recorded in Step-0), PERF-002 (token lock), C-08 (`intent`).
**Consumed by:** PRD-07 replay/verifier and result digest; PRD-02 sequencing; PRD-05
readiness gate.
*(SEC-001/002/006 are Gmail-API controls owned by **PRD-07** — see crosswalk §Reassignments.)*

## 26. Dependencies on Other PRDs

**Provides:** canonical bytes, commitment/verification, auth, config lock, `result_sha256`
to PRD-02, PRD-05, PRD-07. **Consumes:** PRD-01 (`state` representation, config model),
PRD-04 (`intent`/hint content and token record), PRD-02 (sequencing/cursor).

## 27. Open Design Decisions

Whether Step-0 and config share one key · key-provisioning channel with the opponent ·
whether Ed25519 is ever enabled (needs a justified dependency) · golden-vector corpus
scope · nonce length if renegotiated · whether audit streams or batches recomputation.

## 28. Explicit Non-Goals

No PKI/CA · no encryption of game traffic (confidentiality is not a stated requirement) ·
no crypto dependency now · no Gmail/OAuth (PRD-07) · no tunnel (PRD-05) · no second crypto
implementation anywhere · no invented sanctions.

## 29. Implementation Readiness Checklist

- [x] Exact bytes defined for every cryptographic operation
- [x] Taxonomy fixed; unkeyed digest explicitly rejected as strict Step-0 auth
- [x] Config equality **and** authentication kept distinct, both required
- [x] Commitment record, nonce lifecycle and hiding/binding stated
- [x] Audit/TAMPERED behaviour with locked sanction only
- [x] Profiles selectable, recorded, frozen, and unable to weaken strict mode
- [x] Result digest non-self-referential with a regression test
- [x] Secret lifecycle incl. rotation and an honest memory-erasure limitation
- [ ] Supervising review — **pending**
- [ ] Implementation — **not started**
