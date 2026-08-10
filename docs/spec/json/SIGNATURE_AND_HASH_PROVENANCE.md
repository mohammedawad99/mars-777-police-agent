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
| Token-usage lock | **actual** LLM token consumption (per sub-game and per series) | each team | **metered during play; disclosed in the final report** | both peers + grader | **Yes — the result JSON** (App E #54; Ch 9 §9.3.3) | `sub_games[].tokens`, `total_tokens` | reported values sit inside the **RESULT APPROVAL CORE** and are covered by `result_sha256`; **the runtime cryptographic locking of Ch 5 §5.5 is a separate, not-yet-frozen mechanism** | **Two obligations, split:** reporting = SOURCE-REQUIRED and **satisfied** (App E #54); runtime monitoring + cryptographic locking = SOURCE-REQUIRED (Ch 5 §5.5) with **construction SOURCE-UNSPECIFIED and NOT YET FROZEN** — `TOKEN-ACCOUNTING-CRYPTO-EVIDENCE: BLOCKED-BY-CONSTRUCTION`, owned by PRD-06 *(Stage 4E-R12-R1 moved this row from Step-0 to the result; Stage 4E-R12-R2 separated the two obligations and withdrew the claim that `result_sha256` satisfies the runtime one)* |
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

## Stage 4E-R12 — authentication bootstrap, vocabulary and wire encoding

Nothing below adds a hash, a tag, an artifact field or an object to the taxonomy
above. It closes three questions the taxonomy assumed answered: **which profile a
verifier uses**, **how that profile and its tag are spelled on the wire**, and
**whose key** the pre-supplied key is.

### R12-A — the bootstrap profile paradox, and why `AuthProfile` is not negotiated

Three committed statements could not all hold at once:

1. `PRD02-FR-022`'s state table verifies the peer's Step-0 auth envelope in
   **`STEP0_NEGOTIATION`**, whose only predecessor is `BOOT` ("process start,
   secrets present").
2. `PRD02-FR-080` places `AuthProfile` in the profile set "selected **before**
   counted play and **frozen at `CONFIG_LOCKED`**" — **two states later**.
3. `PRD06-FR-122` requires every profile to be "**authenticated** as part of the
   pre-series negotiation evidence".

Applied to `AuthProfile` these are **circular**: verifying the Step-0 tag needs
the profile, the profile is authenticated by the Step-0 tag, and there is no
earlier in-band state in which either could be established. `CommitmentCodec`,
`ResultProfile` and the tool-name profile are **not** circular — each is consumed
strictly *after* `CONFIG_LOCKED`, so freezing them at lock is sound. The
asymmetry is specific to the one profile that *is* the authentication mechanism.

**Resolution (PROJECT-CONTRACT; the book specifies no profile-selection
mechanism).** `AuthProfile` and `KeyId` are **provisioned out of band together
with the key material itself** — the same channel, at the same time, by the same
pre-match arrangement (`PRD06-FR-160`). They are **not** selected by any in-band
message and are **not** part of the negotiated profile set for the purposes of
`PRD02-FR-080`'s freeze point: they are already fixed on entry to `BOOT`.

**Consequences, stated exactly:**

- **`step0_auth.auth_alg` is a declared value, never a selector.** A verifier
  chooses its verification profile **only** from its locally provisioned expected
  `AuthProfile`. It then compares the received `auth_alg` against that expected
  value and **refuses counted play on any difference** (`E-AUTH-FAILURE`,
  `PRD06-FR-027`). It never verifies *under the algorithm the message names* —
  that would let the sender choose the verifier's algorithm, which is the
  classic algorithm-confusion downgrade and is exactly what `PRD06-FR-028`
  ("no silent downgrade") and `PRD06-FR-124` (profile-downgrade attempt) forbid.
  The same rule applies to `config_auth.auth_alg`.
- **`key_id` is likewise compared, never trusted as a lookup instruction.** An
  unrecognised `key_id` is a refusal, not a prompt to fetch or derive a key.
- **This is not a downgrade path.** Out-of-band provisioning *strengthens* the
  Step-0 guarantee: it removes the only pre-authentication message an attacker
  could have influenced.
- **Plain unkeyed SHA-256 remains inadmissible** as a Step-0 or config
  `AuthProfile` in `STRICT_COUNTED_MATCH` — restating `PRD06-FR-022` and the
  `COMPATIBILITY_PROFILES.md` architecture hook, now with the added force that no
  in-band message can introduce it.

### R12-B — auth semantic vocabulary (frozen)

Three semantic concepts, distinct from the JSON keys that carry them:

| Concept | Meaning | Carried by | Secret? |
|---|---|---|---|
| **`AuthProfile`** | *Which* keyed primitive authenticates a core | `auth_alg` (declared + compared) | No |
| **`KeyId`** | A non-secret label for the provisioned key | `key_id` (declared + compared) | **No — never the key** |
| **`AuthProof`** | The keyed output over `context ‖ canonical(core)` | `auth_tag` | No (the *key* is) |

`AuthProof` names the value only; it is **not** a new artifact field, **not** a
new FIELD_MATRIX row, and **not** a rename of `auth_tag`. The three envelope keys
`{auth_alg, key_id, auth_tag}` are unchanged in the declaration, the config
sidecar and the result's `hardware_auth`.

### R12-C — wire encoding (closes a live spelling divergence)

Until this stage the repository carried **two spellings of one algorithm** with no
stated relationship: `HMAC-SHA256` (hyphen) as the primitive name and `auth_alg`
example value, and `HMAC_SHA256` (underscore) as the `AuthProfile` identifier in
`PRD06-FR-024` and `COMPATIBILITY_PROFILES.md`. Two conforming peers could emit
different strings for the same primitive and refuse each other. Frozen:

| Layer | Form | Values |
|---|---|---|
| **`AuthProfile` identifier** (internal, code/docs) | `SCREAMING_SNAKE_CASE` | `HMAC_SHA256` · `ED25519` |
| **`auth_alg` serialized value** (wire/artifact) | identical to the identifier | `"HMAC_SHA256"` · `"ED25519"` |

The serialized value is **exactly the identifier** — one spelling, no aliasing, no
case-folding, no hyphen/underscore translation, no `upper()`/`lower()`, and no
acceptance of `"HMAC-SHA256"`, `"hmac-sha256"`, `"Ed25519"` or any other variant.
An unrecognised or variant spelling is a **mismatch ⇒ refuse counted play**, never
a normalisation. Prose in this repository may still write "HMAC-SHA256" when
naming the *primitive* in English; the **value** is `"HMAC_SHA256"`.

**`auth_tag` encoding:** **lowercase hexadecimal, no `0x` prefix, no separators,
no whitespace, fixed width per profile** — **64** hex characters for
`HMAC_SHA256` (32 bytes) and **128** for `ED25519` (64 bytes). Comparison is over
the decoded bytes, and a tag of the wrong width or containing an uppercase or
non-hex character is **malformed** (`E-PROTO-MALFORMED`), which is a different
outcome from a well-formed tag that fails to verify (`E-AUTH-FAILURE`). This
matches the `[0-9a-f]` lowercase-hex discipline already frozen for the commitment
nonce (NDEC-001) and keeps `ensure_ascii`/NFC irrelevant to these values.

### R12-D — key topology, and what the Step-0 proof does and does not establish

The book says only "a pre-supplied key" (מפתח המסופק מראש) and never states
whether the two peers hold the **same** key or one each. Until now the repository
left this implicit; `ADVERSARIAL_REVIEW.md` **AR-19** ("a peer signs Step-0 with a
key the other side doesn't hold") and NDEC-005's "pre-shared key" already assumed
a shared one, and `PRD06-FR-027` (each peer verifies the other's tag) is only
implementable that way.

- **Topology — SOURCE-UNSPECIFIED → PROJECT-CONTRACT:** for a counted match the
  two peers hold **one shared symmetric key per `key_id`**, provisioned out of
  band. Per-team keys are not adopted, because a verifier that lacks the
  producer's key cannot satisfy `PRD06-FR-027` and the check would silently
  become the grader's alone.
- **What the tag proves:** the core was produced by a **holder of the key named by
  `key_id`**, and has not been altered since — which is precisely the source's
  requirement that Step-0 "cannot be forged retroactively" (Ch 5 p.55–56) against
  third parties and against later self-revision.
- **What it does not prove — stated plainly rather than implied:** with a *shared*
  symmetric key an `HMAC_SHA256` `AuthProof` gives **no peer-vs-peer
  non-repudiation**. Either key-holder could compute either tag, so in a dispute
  strictly between the two peers the tag distinguishes them from outsiders, not
  from each other. `ED25519` — already an accepted negotiable `AuthProfile`
  (`PRD06-FR-024`) — is the option that *would* provide it. This is recorded as a
  property, not a defect: `JDEC-013` is **not** re-opened, HMAC-SHA256 remains the
  project default, and no claim anywhere in this repository may describe the
  default MAC as a digital signature or as binding one peer against the other.

## Stage 4E-R12-FIX — exact auth semantic vocabulary

### R12-FIX-A — `AuthProfile`, `KeyId`, `AuthProof` — exact representations

**`AuthProfile` — a closed set of exactly two values.** Serialized form **is** the
identifier, byte for byte:

| Value | Primitive category | Role |
|---|---|---|
| `HMAC_SHA256` | **keyed MAC** — a tag, **not** a digital signature | project default, `STRICT_COUNTED_MATCH` |
| `ED25519` | **asymmetric digital signature** — **not** a MAC | permitted only when explicitly provisioned/pre-agreed before Step-0 |

Closed set: no third value, **no aliases, no case folding, no hyphen/underscore
normalization**, no `upper()`/`lower()`, no whitespace tolerance. `"HMAC-SHA256"`,
`"hmac_sha256"`, `"Ed25519"` and `"SHA256"` are **not** members and are refused.
**Plain unkeyed SHA-256 is not an `AuthProfile` at all** — it authenticates
nobody (`PRD06-FR-022`).

**`KeyId` — a non-secret label.**

| Aspect | Rule |
|---|---|
| Semantic type | immutable value wrapping one `str` |
| Representation | **ASCII only**, characters drawn from `[A-Za-z0-9._-]` |
| Length | **non-empty**; maximum **64** characters |
| Empty | **rejected** — an empty `key_id` is never "no key" |
| Whitespace | **none permitted anywhere** — leading, trailing or internal; never stripped, never trimmed |
| Normalization | **none** — the ASCII subset is NFC-invariant by construction, so there is nothing to normalise; never case-folded; compared **exactly** |
| Secret boundary | a **label, never key material**. It must not be, contain, or be derived from the key (no prefix, no truncation, no digest of it). It **is** serialized, logged and may appear in error evidence — which is only safe because it is unrelated to the key bytes |

The ASCII restriction is **PROJECT-CONTRACT**: an identifier compared inside an
authentication decision must not depend on Unicode normalization, and the source
names no format at all.

**`AuthProof` — profile-tagged, three components, never a digest type.**

```
AuthProof(
    profile: AuthProfile,
    key_id: KeyId,
    value: str,
)
```

It distinguishes **profile**, **key_id** and **proof value** as three separate
members. **`AuthProof` is not `Sha256Digest` and an `ED25519` signature is never
modelled as one** — they are different primitives of different widths, and
`Sha256Digest` means "the result of an unkeyed SHA-256", which a signature is not.
`value` is validated **against `profile`**, so a proof is never interpretable
under a profile other than the one it declares.

**Field-name compatibility.** The JSON/artifact field remains **`auth_tag`** in
`step0_auth`, `config_auth` and `hardware_auth`. **`auth_tag` is a field-name
compatibility label only.** It does not make the value a MAC "tag" when the
profile is `ED25519`, and it changes nothing in the taxonomy above: the semantic
value is a **profile-tagged `AuthProof`**, and `auth_alg` carries its `profile`,
`key_id` its `KeyId`, `auth_tag` its `value`.

### R12-FIX-B — exact proof encodings (final PROJECT-CONTRACT)

| Profile | Bytes | Representation | Exact length | Character set |
|---|---|---|---|---|
| `HMAC_SHA256` | 32 | lowercase hexadecimal | **exactly 64** | `[0-9a-f]` |
| `ED25519` | 64 | lowercase hexadecimal | **exactly 128** | `[0-9a-f]` |

No `0x` prefix, no separators, no whitespace, no uppercase, no base64, no padding,
never normalised or case-folded. Validation is **exact length for the declared
profile** and **exact character set**; comparison is over the decoded bytes.

**Outcome separation, using existing error IDs only:**

- Wrong length, uppercase, non-hex, prefixed, padded or whitespace-bearing ⇒ a
  **malformed representation** ⇒ **`E-PROTO-MALFORMED`**.
- Well-formed for its profile but failing cryptographic verification ⇒
  **`E-AUTH-FAILURE`** ⇒ refuse counted play.
- A profile or `key_id` differing from the locally provisioned expectation ⇒
  **`E-AUTH-FAILURE`** — never a malformed error, never a fallback.

**No cryptographic dependency is introduced now.** These are representation and
validation contracts; `hmac`, `hashlib` and any signature library remain outside
the semantic layer, in `protocol.keyed_auth`.

### R12-FIX-C — bootstrap profile rule, proved

Before `BOOT`, local configuration already determines the **permitted Step-0
`AuthProfile` and `KeyId`**, provisioned out of band with the key
(`PRD06-FR-160`). The strict counted default is **`HMAC_SHA256`**; **`ED25519`
may be used only if explicitly provisioned/pre-agreed before Step-0**.

Incoming `auth_alg` and `key_id` **must exactly equal the local expected values**.
They **do not select the verifier**. There is **no fallback, no "try all
profiles", no unkeyed SHA-256 path, and no negotiation of these two values by any
message.**

**Why this prevents profile/algorithm downgrade.** An attacker's only lever over
verification would be the algorithm the verifier runs. If the verifier chose its
primitive from the received `auth_alg`, an attacker could name the weakest
accepted profile — or one whose verification is trivially satisfiable — and the
verifier would obligingly use it; that is the classic algorithm-confusion
downgrade, and a "try all profiles" verifier is strictly worse because it accepts
if **any** primitive matches, reducing the guarantee to the weakest member of the
set. Here the primitive is fixed **before** the first byte arrives, so a modified
`auth_alg` cannot change what runs — it can only fail the equality check and
refuse counted play (`E-AUTH-FAILURE`). This is the mechanism behind
`PRD06-FR-028` ("no silent downgrade") and `PRD06-FR-124` (a downgrade offer is
rejected, not accommodated), and it is why substitution of `auth_alg`/`key_id` is
**ineffective without needing them inside the authenticated bytes**, which would
re-create the self-reference the contract forbids.
