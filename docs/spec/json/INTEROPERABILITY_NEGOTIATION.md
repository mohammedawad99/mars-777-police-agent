# Interoperability Negotiation Contract (NDEC) — group MaRs-777

**Status: REVIEWED — Stage-1 supervising review PASS; baseline LOCKED. Specification only; no code/schema/JSON artifact.**

Every legitimate **NEGOTIATED-PRE-MATCH** dependency — representations two peers
must agree on to complete/verify a counted match. **Not** used to negotiate FIXED
Appendix F values, to weaken MINIMUM values, or to avoid fixing project contracts
that can safely be locked. Each has a PROJECT-LOCKED **default** so agreement is
usually just confirmation.

| NDEC | Item | Default (project-locked) | Allowed alternatives | Exchange | Both-peer ack | Lock / immutability | Identity/hash reference | If no agreement | Counted play? |
|---|---|---|---|---|---|---|---|---|---|
| **NDEC-001** | Sealed commitment-record composition | fields `{state, move, intent, hint, step, role, sub_game, nonce}`, keys sorted, `intent` carries the truth/lie "verdict" (no separate `verdict`); **`move` is the generic physical *action*, not a movement token** — Ch 5 p.51 defines it as "the chosen action (movement, **barrier placement**, etc.)", so a police barrier placement **with its exact cell** is sealed here and revealed through the same member *(Stage 4E-R3)*. **Its representation is now frozen (Stage 4E-R4)** as a **tagged, structurally-exclusive JSON object** carrying exactly two sorted keys — `{"kind":"MOVE","value":"<move_set token>"}` for the movement form and `{"kind":"BARRIER","value":[row,col]}` for the police barrier-placement form. The tag vocabulary is exactly `"MOVE"` / `"BARRIER"`; `value` is a `move_set` token (`"N"`,`"S"`,`"E"`,`"W"`,`"STAY"`, App F T15 FIXED) under `MOVE`, and the two-integer coordinate array `[row,col]` already locked by JDEC-006/JDEC-012 under `BARRIER`. This closes the byte-identity gap: a barrier-carrying record is now recomputable by the peer. The shape itself is **PROJECT-CONTRACT**, not source-prescribed — Ch 5 p.53's `commit(state, move: str, …)` is EXAMPLE-ONLY and the book labels that core a simplification — so it is negotiated by this row exactly as `NDEC-002` negotiates `state`. **The `nonce` member's *representation* is frozen at Stage 4E-R6, with its rationale corrected at Stage 4E-R6-FIX1**, as the PROJECT-LOCKED default `[0-9a-f]{32}` - lowercase hexadecimal, exactly 32 characters, no whitespace, prefix or separator, never normalised. **This is PROJECT-CONTRACT, not source law, and it is *not* required for hash recomputation:** a receiver rebuilds the sealed record using the **exact string the sender revealed**, so any stable representation recomputes identically and a fixed case or length is nowhere mathematically necessary. It is fixed for three project reasons instead - a strict parser that rejects malformed input deterministically; stability under the `NDEC-003` NFC step, since an all-ASCII-hex value normalises to itself - a representation-safety property, **not** a reason recomputation would otherwise fail, because the receiver always recomputes from the exact revealed value; and a fixed 16-byte/128-bit *width* matching the reference `secrets.token_hex(16)` - width is not itself proof of entropy, which only the producer's CSPRNG can supply. The book requires a *fresh cryptographic nonce* (Ch 5 p.50-51) and fixes no encoding or length - `token_hex(16)` is **REFERENCE-EXAMPLE**. **NEGOTIATED-PRE-MATCH here means agreement on the one required profile, not selection among codecs.** For the current v1 counted-match contract the project supports **exactly one** nonce representation, so both peers must echo `[0-9a-f]{32}`; an echoed profile that differs is a **profile mismatch** and **counted play is refused before `CONFIG_LOCKED`** - never silently accepted, never normalised, and never deferred to audit time. That refusal is a LIVE compatibility check during pre-match negotiation, **not** an `InvalidNonceError` (which is malformed construction under the already-selected local profile), not a tampering verdict, not a hash mismatch and not a score sanction. Supporting a second representation is a **future-version** change requiring the contract to be extended, semantic-value support added, the profile defined here and both repositories implementing it; until then no alternative is legal in counted play. **The `role` and `intent` member representations are frozen at Stage 4E-R9-R1.** `intent` is the **SOURCE-REQUIRED** vocabulary `"truth"` / `"lie"` - Ch 5 p.51 prints both English words inside the Hebrew definition of the intent flag, so this is source law, not a project choice; no bool, no `unknown`/`neutral`/`honest`/`deceptive`, no empty string. `role` is the **PROJECT-CONTRACT** vocabulary `"police"` / `"thief"`: the source names the sides only as *Cop* / *Thief* in Figure 6 (explanatory terminology, never a byte string), so a canonical spelling had to be chosen, and the repository runtime constants map **explicitly** - `"POLICE"` → `"police"`, `"THIEF"` → `"thief"` - with no `lower()`, case-folding, normalisation or synonym acceptance, and an unrecognised runtime role refused rather than guessed. The PRD-01 score keys `{cop, thief}` are a **separate reporting vocabulary** and are deliberately *not* the sealed role. Both values are pure ASCII, hence NFC-invariant and unaffected by `ensure_ascii`. **Generation is a producer duty, not a representation claim:** a value built from a *received* string can never prove it came from a CSPRNG, so CRYPTO-010 stays a runtime obligation on the producer and secrecy-until-final-reveal stays a protocol invariant - neither is a structural check. | reorder is irrelevant (sorted keys); adding/removing a field is **not** allowed unless both agree; **the action encoding may be replaced only by another deterministic, structurally-exclusive encoding that preserves the exact barrier cell, and both peers must echo the same one; **the nonce representation has no alternative in v1** - both peers must echo the one required profile, and any other echoed form refuses counted play**; **the `role` and `intent` vocabularies have no alternative in v1 either - both peers echo `police`/`thief` and `truth`/`lie`, and any other echoed spelling refuses counted play** | in the pre-match config/declaration exchange | echo the agreed field list **and the agreed action encoding** | frozen for the series; referenced by `config_sha256` context | recorded in declaration | **no counted play** | requires agreement |
| **NDEC-002** | `state` representation in the sealed payload | `{config_sha256, self_pos:[r,c], barriers:[[r,c]…] sorted, step, role}` (own-known only; no opponent truth). **Tightened at Stage 4E-R9-R1** without changing the shape: `barriers` are sorted **lexicographically by `(row, col)` and duplicate-free in the semantic value itself**, so the canonical mapper never sorts, deduplicates or repairs - it serializes an already-valid value; empty barriers emit `[]`; `role` uses the same `"police"`/`"thief"` vocabulary as the top-level member; and the builder must refuse a record where `state.step ≠ step` or `state.role ≠ role` **before hashing** - a composition error, not a hash mismatch and not TAMPERED. The stale REVIEW-REQUIRED text in `LOG_CONTRACT.md` was repaired in the same stage; this row's PROJECT-LOCKED status is unchanged since JDEC-012 | any deterministic superset **both** accept | pre-match | echo | frozen for the series | via `config_sha256` | no counted play | requires agreement |
| **NDEC-003** | Canonicalization parameters | `sort_keys=true`, `separators=(",",":")`, UTF-8, **`ensure_ascii=False`** *(the exact current-v1 value, pinned at Stage 4E-R9-R1; it was previously written only as "agreed value" here while PRD06-FR-005 already carried the value, which left it an implementation-time choice)*, NFC normalisation of textual values before encoding, LF, no trailing newline in hashed payload, locale-independent numbers | any deterministic serializer both accept | pre-match | echo | frozen for the series | — | no counted play | requires agreement |
| **NDEC-004** | Config equality + MINIMUM/NEGOTIABLE values + `schema_version` value | App F floors/defaults; `schema_version` = `"mars777-1"` | raise MINIMUMs; any NEGOTIABLE both accept (**never** below floor; **never** change FIXED) | exchange full config; both compute `config_sha256` | compare `config_sha256` (must be equal) | byte-identical signed config; hash locked | `config_sha256` (stored in declaration/sidecar) | **refuse to play** | requires equal hash |
| **NDEC-005** | **Step-0 keyed authentication** (K1) | **HMAC-SHA256** over `"step0" ‖ canonical(Step-0 core)`, pre-shared key by `key_id` (JDEC-013); envelope `{auth_alg,key_id,auth_tag}` in the declaration | asymmetric signature if both agree (source requires **keyed** auth, not HMAC) | key **out-of-band/pre-supplied**; envelope in declaration | verify each other's `auth_tag`; `key_id` matches | frozen per game; **key never in any artifact** | `auth_tag` (non-self-referential) | **refuse counted play** if no compatible key/mechanism | requires shared key + verified tag |
| **NDEC-006** | Result-approval hashing | SHA-256 over the canonical **RESULT APPROVAL CORE** — `game_id`, `game_uid`, `declaration_ref`, team `group_id`s, four GitHub links, per-sub-game {`sub_game`, scores, `outcome`, `github_commit`, `tokens`}, `cumulative`, `total_tokens`, `timestamp` — **excluding** `result_sha256` itself, the `mutual_agreement` flag and any reporter-local presentation metadata (**Stage 2A-R2**: static declaration-owned metadata is referenced, not included). Both peers build that core independently, each computes `result_sha256`, the two digests are exchanged and compared, and **only once they are equal** does each local result record carry the identical `result_sha256` **and**, as a **separate top-level field**, `mutual_agreement = true` *(Stage 4E-R2-FIX1: this cell previously wrote `mutual_agreement.sha256` and `mutual_agreement.confirmed = true`, the nested object form `RESULT_CONTRACT.md` withdrew at Stage 4F-R1 in favour of the bool its field table, scoring rule and JSON example define; the exclusion semantics and the 11-field result count are unchanged, and no replacement nested object is introduced)* | any hash both accept | dual result emails | both `result_sha256` equal | frozen at report time | `result_sha256` (non-self-referential) | **0 to both** (E-35, C-09) | requires equal hash |
| **NDEC-007** | **Config keyed authentication (signature exchange)** (K2) | **HMAC-SHA256** over `"config" ‖ canonical(config core)`, pre-shared key by `key_id` (JDEC-013; same-or-distinct key from Step-0 unspecified → agree pre-match); envelope in a config sidecar | asymmetric signature if both agree | key out-of-band; envelope in sidecar | verify tag + `config_sha256` equality | frozen per sub-game; key never stored | `auth_tag` (non-self-referential; distinct `context` from Step-0) | **refuse counted play** on bad tag/hash mismatch | requires verified tag + equal hash |

## Rules

- **FIXED Appendix F values are never negotiated** here; **MINIMUM values only rise**;
  these NDECs cover *representation*, not the binding physics numbers.
- Defaults are PROJECT-LOCKED so that, with a compliant opponent who accepts them,
  no per-match negotiation is strictly required beyond confirming equality.
- Detection is a **hash/tag comparison** (config, commitment, result, keyed auth);
  failure behaviour is refuse-to-play (pre-game) or disqualify/0-both (report).
- **Keyed authentication (NDEC-005/007)** uses a **pre-supplied out-of-band key**
  (JDEC-013); **no key material** appears in any artifact — only a `key_id`. The
  source requires keyed authentication (Ch 5 p.55–56; App B p.128); the algorithm
  (HMAC-SHA256 default) is our choice. If the two sides cannot establish a
  compatible key/mechanism, **counted play is refused**.
- IDs NDEC-001…NDEC-007, unique.
- **NDEC-006 scope limit (Stage 4E-R2-FIX1).** NDEC-006 freezes the result-approval
  **procedure** (build the core → compute `result_sha256` → exchange → compare → set
  `mutual_agreement`) and the **result-record shape** (two separate fields). It does
  **not** freeze the Event-14 *peer-message* flow: whether the exchange is one message,
  request/response, offer + confirm, a digest echo or another pattern; whether the
  semantic message carries `game_id`/`game_uid` or relies on session context; and
  whether disagreement is signalled by `false` or by absence plus the `E-REPORT-DISAGREE`
  / C-09 path. Those remain unfrozen, so the peer-visible **Mutual result agreement**
  family stays `BLOCKED-BY-PAYLOAD-SHAPE`. A record shape is not a message shape.

## Stage 4E-R12 amendment to NDEC-005 and NDEC-007 (in place; NDEC count still 7)

Both rows above say the keyed primitive may be an "asymmetric signature if both
agree", which read as though the `AuthProfile` were settled by an in-band
pre-match exchange like the other NDEC rows. For every other NDEC that is correct;
for these two it is **circular**, because the Step-0 exchange is what establishes
in-band trust in the first place (`SIGNATURE_AND_HASH_PROVENANCE.md` R12-A).

**Amended reading — no new NDEC, no row removed, no default changed:**

- **`AuthProfile` and `KeyId` are agreed out of band, with the key, before `BOOT`.**
  "If both agree" still holds — the agreement is simply not carried by any
  protocol message. `HMAC_SHA256` remains the project-locked default and
  `ED25519` the alternative.
- **`auth_alg` and `key_id` on the wire are compared against the provisioned
  expectation, never used to select a verifier.** A difference refuses counted
  play (`E-AUTH-FAILURE`); it is never normalised or accommodated.
- **Serialized spellings are exactly `"HMAC_SHA256"` / `"ED25519"`**, and
  `auth_tag` is fixed-width lowercase hex (64 / 128 characters) — R12-C.
- **NDEC-005** authenticates the **STEP-0 AUTHENTICATED CORE** now frozen in
  `DECLARATION_CONTRACT.md` (own subtree + game identity + `game_start` +
  `token_budget_per_series`, excluding the envelope, the opponent's subtree and
  `game_end`), **once per series**. *(Corrected Stage 4E-R12-R3: this line still
  listed `token_budget_per_series` among the exclusions after Stage 4E-R12-R1 had
  moved it into the core. The cap is **agreed before `BOOT`** — see
  `DECLARATION_CONTRACT.md` §R12-R3 — so authenticating it at event 1 is
  chronologically sound.)*
- **NDEC-007** authenticates the **config core** (35 members) **once per
  sub-game**, and `PRD06-FR-047`'s same-or-distinct key question is unchanged and
  still agreed out of band.

The exchange, ack, lock, identity-reference and refusal columns of both rows are
otherwise unchanged, and no NDEC default was weakened.

### Stage 4E-R12-FIX amendment to NDEC-007 (in place; NDEC count still 7)

NDEC-007's default reads "**HMAC-SHA256** over `"config" ‖ canonical(config core)`".
The **context authenticated is amended** to
**`ConfigLockContext` = `{game_id, game_uid, sub_game, config_sha256, profiles}`**
(`CONFIG_CONTRACT.md` R12-FIX-K). The App-B config core is byte-identical across
every sub-game of a series, so a proof over it alone binds no sub-game, no game
identity and none of the values `PRD06-FR-048` freezes at the lock; the digest
binds all 35 core members transitively, so nothing is lost and the binding core
stays free of protocol metadata (**D4**).

Unchanged: the `"config"` context string and its domain separation from
`"step0"`; non-self-reference (the envelope is never inside its own authenticated
bytes); the unkeyed `config_sha256` and its equality check; the out-of-band key
and `key_id`-only serialization; `PRD06-FR-047`'s same-or-distinct key question;
the refuse-counted-play outcome. **No NDEC was added, removed or weakened.**
