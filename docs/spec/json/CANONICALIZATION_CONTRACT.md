# Canonicalization Contract — group MaRs-777

**Status: REVIEWED — Stage-1 supervising review PASS; baseline LOCKED. Specifies behavior; does NOT implement it.**

Three distinct layers. Sources: Ch 5 §5.3 (PDF p.50–53), Ch 5 §5.4 (p.55), Ch 7
§7.4–7.5 (p.72–74), App B §B.2–B.3 (p.127–129), App E #17–19.

## Layer 1 — JSON file serialization (declaration / config / log / result)

Whatever is **hashed or exchanged for equality** must be canonical so both peers
and the grader compute identical bytes. App B (p.127) requires JSON to be
"canonically serializable (sorted keys) and therefore consistently hashable
(`config_sha256`)".

| Aspect | Rule | Provenance |
|---|---|---|
| key ordering | **sorted keys** | SOURCE-SEMANTIC (App B p.127; Ch 5 p.50) |
| whitespace / separators | **fixed, compact separators** | SOURCE-SEMANTIC (Ch 5 p.50 "fixed separators"); exact `(",",":")` EXAMPLE-ONLY → PC (JDEC-002) |
| encoding | **UTF-8** | SOURCE-EXPLICIT-in-example (Ch 5 p.53 `.encode("utf-8")`) + SOURCE-SEMANTIC |
| non-ASCII escaping (`ensure_ascii`) | deterministic, agreed; **not** book-specified | **PROJECT-CONTRACT** (JDEC-002) — never claimed as lecturer-required |
| line endings | LF only for any hashed/stored canonical bytes | **PROJECT-CONTRACT** (JDEC-002); aligns with repo `.gitattributes` |
| final newline | none inside a hashed payload | **PROJECT-CONTRACT** (JDEC-002) |
| numbers | integers as integers; floats verbatim as in Appendix F (`0.9`, `0.10`) | SOURCE-SEMANTIC (App F values) + PC on float formatting (JDEC-002) |
| booleans / null | JSON `true`/`false`/`null` | PROJECT-CONTRACT (standard JSON) |
| arrays | order-significant (e.g., `move_set`, `thief_start`) | SOURCE-SEMANTIC (App B) |

## Layer 2 — cryptographic commitment payload (per turn)

`H_commit = SHA256( canonical_json(sealed_record) )` where `sealed_record` is the
8-field set `{state, move, intent, hint, step, role, sub_game, nonce}` (Ch 5 p.50).
`intent` **is** the truth/lie classification — there is **no separate `verdict`
field** (C-08 / NDEC-001; the code comment's "verdict" = intent classification).
The reference (Ch 5 p.53):

```
json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
hashlib.sha256(...).hexdigest()
```

- `sort_keys=True`, `separators=(",",":")`, `.encode("utf-8")`, `sha256` — the
  reference-code serialization. **Adopting these exact params is PROJECT-CONTRACT**
  (JDEC-002); the *requirement* (canonical, sorted, fixed separators, UTF-8, SHA-256,
  byte-identical) is SOURCE-SEMANTIC/EXPLICIT.
- **Nonce:** fresh cryptographic random per commit (`secrets`, not `random`) — Ch 5
  p.53, CRYPTO-010; `token_hex(16)` length is EXAMPLE-ONLY → PC.
- The nonce is included in the hashed payload but **withheld from the wire** until
  final audit (Ch 5 p.51).
- The Ch 7 `f"{nonce}|{move}"` verifier payload is **EXAMPLE-ONLY** and does **not**
  define the real payload (see LOG_CONTRACT).
- **`move` value representation (Stage 4E-R4).** `move` is the generic *physical
  action* (Ch 5 p.51), so its value is a **tagged, structurally-exclusive object**
  with exactly two sorted keys:

  ```
  movement : {"kind":"MOVE","value":"N"}          value ∈ move_set (App F T15 FIXED)
  barrier  : {"kind":"BARRIER","value":[row,col]} value = the exact placed cell
  ```

  The tag makes the two forms unambiguous without relying on JSON type-sniffing,
  and keeps the slot extensible for the source's *"etc."* without re-negotiating
  the sealed field set. `[row,col]` is **not** a new convention: it is the
  coordinate array already locked by JDEC-006 and used by JDEC-012's `state`.
  Adopting this exact shape is **PROJECT-CONTRACT**, carried pre-match by
  **NDEC-001**; Ch 5 p.53's `move: str` is EXAMPLE-ONLY and prescribes nothing.

## Layer 3 — SHA-256 verification procedure

Per Ch 5 §5.4 / Ch 7 §7.4:
1. Read a log entry's revealed data + the final-audit nonce.
2. Rebuild the canonical `sealed_record`, serialize (Layer 2), `sha256` it.
3. Compare (constant-time, `secrets.compare_digest` in reference) to the stored `H_commit`.
4. Match → per-step "Verified OK"; any mismatch → "TAMPERED" → **whole match void**, no appeal.

## Layer 4 — keyed-authentication payload (Step-0 / config, Stage 1D.1)

Distinct from the unkeyed hashes of Layers 1–3. A **keyed authentication** proves
the producer holds the pre-supplied key (K1/K2) — it is **not** a bare hash and
**not** an asymmetric signature.

- **Authenticated payload:** `auth_tag = KEYED_AUTH_key( context ‖ canonical(core) )`
  with default `KEYED_AUTH = HMAC-SHA256` (JDEC-013). `core` is canonicalized by
  **Layer 1** (sorted keys, fixed separators, UTF-8, NFC, LF, no trailing newline).
- **Domain separation:** `context ∈ {"step0","config"}` is authenticated **together
  with** the payload, so a valid `"step0"` tag cannot be replayed as a `"config"` tag
  (and vice-versa). The concatenation `‖` uses a fixed, unambiguous framing agreed
  pre-match (NDEC-003/005/007) so `context` and `core` cannot be confused.
- **Self-reference exclusion:** the envelope `{auth_alg, key_id, auth_tag}` is
  **never** part of the bytes it authenticates — the tag is computed over
  `context ‖ core` only (mirrors the non-self-referential rule for `config_sha256`
  and `result_sha256`). A construction that hashes/authenticates over bytes
  containing its own tag is **rejected**.
- **Key material:** the pre-supplied key is **out-of-band**; only the non-secret
  `key_id` is serialized. **No key byte enters any canonical payload, artifact, or
  log.**
- **Same-or-distinct key** for Step-0 vs config is **source-unspecified** → agreed
  pre-match; domain separation makes reuse safe if agreed, but reuse is **not
  assumed**.

## Cross-platform note (Windows/Linux)

Because the same bytes must hash identically on both peers' OSes (CI runs Ubuntu +
Windows), all canonical bytes use **LF** and **UTF-8** and avoid locale-dependent
float/number formatting. This is a **PROJECT-CONTRACT** hardening (JDEC-002) where
the book is silent on byte-level OS issues; it aligns with the repo's LF/UTF-8
`.gitattributes` policy. **No implementation here** — behavior only.

## Byte-affecting red-team (Stage 1D, Section K)

Each byte-affecting choice classified **SOURCE-LOCKED (SL)** / **PROJECT-LOCKED (PL)**
/ **NOT-APPLICABLE (NA)**. The contract **rejects ambiguous representations** rather
than hoping both sides serialize identically.

| Choice | Class | Rule |
|---|---|---|
| object key ordering | SL | sorted keys (App B p.127; Ch 5 p.50) |
| array ordering | SL | preserve semantic order; `barriers` **sorted** lexicographically (JDEC-012) |
| UTF-8 | SL | encode UTF-8 before hashing (Ch 5 p.53) |
| `ensure_ascii` | PL | fixed & agreed (NDEC-003); non-ASCII hints make it decisive; not lecturer-required |
| separators | PL | `(",",":")` compact (Ch 5 example → PL, JDEC-002) |
| whitespace | PL | none (compact) |
| LF vs CRLF | PL | **LF** for all hashed bytes (aligns with repo `.gitattributes`) |
| final newline | PL | none inside a hashed payload |
| integers | SL | JSON integers, no leading zeros |
| decimal/float values | PL | verbatim App F form (`0.9`, `0.10`); no locale/exponent reformatting |
| negative zero | PL | forbid `-0` (normalize to `0`) |
| exponent notation | PL | forbid in canonical output |
| Unicode normalization | PL | normalize to **NFC** before hashing (deterministic for Hebrew hints) |
| duplicate JSON keys | PL | **forbidden** (reject) |
| null vs absent | PL | prefer **absent**; do not emit `null` in a hashed payload |
| booleans | SL | JSON `true`/`false` |
| Hebrew/non-ASCII strings | PL | NFC + agreed `ensure_ascii` (NDEC-003) |
| barrier-coordinate ordering | PL | sorted `[row,col]` (JDEC-012) |
| sealed `move` action encoding | PL | tagged object, two sorted keys `{kind,value}`; `kind ∈ {"MOVE","BARRIER"}` (NDEC-001, Stage 4E-R4) |
| movement token inside `move` | SL | a `move_set` token verbatim — `"N"`,`"S"`,`"E"`,`"W"`,`"STAY"` (App F T15 FIXED); never an integer or long name |
| barrier target inside `move` | PL | the exact placed cell as `[row,col]` (JDEC-006/012); never derived from position, direction or context |

## Provenance summary

- SOURCE-SEMANTIC/EXPLICIT: canonical JSON, sorted keys, fixed separators, UTF-8, SHA-256, fresh nonce, byte-identical.
- PROJECT-CONTRACT (JDEC-002): exact separators `(",",":")`, `ensure_ascii` handling, LF, no trailing newline in hashed payload, float formatting, cross-OS determinism.
- **No `ensure_ascii=False` is asserted as a lecturer requirement.**
