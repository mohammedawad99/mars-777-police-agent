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
| non-ASCII escaping (`ensure_ascii`) | **`ensure_ascii=False`** — the exact current-v1 value, not an implementation-time choice; **not** book-specified | **PROJECT-CONTRACT** (JDEC-002, PRD06-FR-005) — never claimed as lecturer-required |
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
  coordinate array locked by **JDEC-012** and used by that decision's `state`
  representation. *(Stage 4E-R9-R1 citation repair: this sentence previously credited
  **JDEC-006**, which is the declaration presentation-key decision and says nothing
  about coordinates. The representation itself is unchanged — only the citation was
  wrong, and no new decision was created.)*
  Adopting this exact shape is **PROJECT-CONTRACT**, carried pre-match by
  **NDEC-001**; Ch 5 p.53's `move: str` is EXAMPLE-ONLY and prescribes nothing.

- **`role` and `intent` value representations (Stage 4E-R9-R1).** Both are closed
  ASCII vocabularies emitted **exactly**, never case-folded, trimmed, normalised or
  re-spelled:

  ```
  role   : "police" | "thief"     PROJECT-CONTRACT (NDEC-001; see §Sealed member
                                  vocabularies below)
  intent : "truth"  | "lie"       SOURCE-REQUIRED vocabulary (Ch 5 p.51 names both
                                  words); the Python type carrying it is PROJECT-CONTRACT
  ```

  Because both are pure ASCII they are NFC-invariant and unaffected by `ensure_ascii`.
  The NFC step therefore bites only on `hint`, the one free-text sealed member.

- **`state` value representation.** The sealed `state` is the PROJECT-LOCKED own-known
  object of **JDEC-012 / NDEC-002 / PRD06-FR-068** — `{config_sha256, self_pos,
  barriers, step, role}` — with `barriers` **already lexicographically sorted by
  `(row, col)` and duplicate-free before the mapper sees it**. The canonical mapper
  does **not** sort, deduplicate or repair; it serializes an already-valid semantic
  value. Empty barriers emit `[]`. No opponent position or private truth is
  representable in it.

## Layer 3 — SHA-256 verification procedure

Per Ch 5 §5.4 / Ch 7 §7.4:
1. Read a log entry's revealed data + the final-audit nonce.
2. Rebuild the canonical `sealed_record`, serialize (Layer 2), `sha256` it.
3. Compare (constant-time, `secrets.compare_digest` in reference) to the stored `H_commit`.
4. Match → per-step "Verified OK"; any mismatch → "TAMPERED" → **whole match void**, no appeal.

### Three layers of that comparison (Stage 4E-R9-R1)

Steps 1–4 above describe the *whole* procedure end to end. They are owned by three
different layers, and conflating them would put a sanction inside a hash function:

| Layer | Owner | Does | Digest inequality is… |
|---|---|---|---|
| 1. **Pure codec / recompute** | `protocol.canonical` + `protocol.commitment` | rebuilds the sealed record, serializes, hashes, and **compares** two digests | **comparison material** (a plain `bool`) — *not* an exception, not a verdict |
| 2. **Audit / consumer** | the audit consumer over the persisted log (Replay Viewer path, Ch 7 §7.5) | interprets a false comparison as a cryptographic integrity failure | classified `E-HASH-MISMATCH` and/or `FinalAuditVerdict.TAMPERED`, per those existing contracts |
| 3. **Protocol / sanction** | the protocol and scoring layers | applies the TAMPERED consequence (match void, no appeal) | a score/technical-loss outcome |

The pure primitive of layer 1 **must not raise `E-HASH-MISMATCH` merely because two
digests differ** — a comparison that returns `False` is its correct, successful
result. `API_BOUNDARIES.md`'s `CommitmentPort` "mismatch ⇒ `E-HASH-MISMATCH`
(terminal)" describes the **port outcome seen by the consumer** (layer 2), not the raw
comparison primitive. No error ID is added, removed or renamed by this clarification.

## Sealed member vocabularies (Stage 4E-R9-R1)

The eight sealed members and the exact JSON value each contributes. This table exists
so a future codec maps every member intentionally rather than reflecting over an object.

| Member | JSON value | Origin | Provenance |
|---|---|---|---|
| `state` | object — see JDEC-012 / NDEC-002 | own-known snapshot | PROJECT-CONTRACT |
| `move` | `{"kind":"MOVE","value":"<move_set token>"}` or `{"kind":"BARRIER","value":[row,col]}` | the physical action | PROJECT-CONTRACT (NDEC-001, 4E-R4) |
| `intent` | `"truth"` or `"lie"` | the truth/lie flag chosen at commit | **SOURCE-REQUIRED** (Ch 5 p.51) |
| `hint` | string, **NFC-normalised**, otherwise verbatim | the verbal sentence | SOURCE-SEMANTIC + PC (PRD06-FR-003) |
| `step` | integer | the turn's step | SOURCE-SEMANTIC |
| `role` | `"police"` or `"thief"` | the acting side for that turn | PROJECT-CONTRACT (NDEC-001, 4E-R9-R1) |
| `sub_game` | integer | the sub-game number | SOURCE-SEMANTIC |
| `nonce` | string, exactly `[0-9a-f]{32}`, verbatim | the per-commit secret | PROJECT-CONTRACT (NDEC-001, 4E-R6-FIX2) |

Exactly these eight keys, sorted. No `cursor`, no `action`, no `h_commit`, no `null`,
no optional member, and **no ninth field**.

## Future semantic types for the sealed record (Stage 4E-R9-R1; no Python yet)

Frozen so the next implementation slice implements rather than decides. Home:
**`app.sealed_record_values`** (`MODULE_BOUNDARIES.md`). No name collides with an
existing symbol in either repository — checked by import, not by grep.

**`ActorRole`** — `StrEnum`, a closed vocabulary rather than a formatted string:

```
ActorRole.POLICE.value == "police"
ActorRole.THIEF.value  == "thief"
```

Exactly two members. No third member, no `UNKNOWN`, no alias, no synonym acceptance,
no normalisation. The mapping from the repository runtime constants is **explicit** —
`"POLICE"` → `ActorRole.POLICE`, `"THIEF"` → `ActorRole.THIEF` — never `lower()` or any
case transformation, and an unrecognised runtime role is refused at the owning boundary
rather than mapped to a guess. The codec accepts an already-valid `ActorRole`, never a
role string.

**`Intent`** — `StrEnum`, the source vocabulary:

```
Intent.TRUTH.value == "truth"
Intent.LIE.value   == "lie"
```

Exactly two members; no `unknown`, `neutral`, `honest`, `deceptive`, `true`/`false`, no
bool substitute, no empty string, no normalisation, and never inferred from `hint`.

**`SealedState`** — `@dataclass(frozen=True, slots=True)`, fields in exactly this order:

```
config_sha256: Sha256Digest
self_pos:      Position
barriers:      tuple[Position, ...]
step:          int
role:          ActorRole
```

Structural rules, all exact-type and never coercive: `config_sha256` an exact
`Sha256Digest`; `self_pos` an exact `Position`; `barriers` an exact `tuple` whose every
member is an exact `Position`; `step` an exact `int` with `bool` **rejected** and
`step >= 1`; `role` an exact `ActorRole`. No dict, list, set, string or board object is
accepted or converted, and there is no opponent field — **opponent truth is not
representable**.

**Barrier invariant.** `barriers` must **already** be lexicographically sorted by
`(row, col)` and duplicate-free. An unsorted tuple and a tuple containing duplicate
`Position` values are both **invalid constructions**. The value never silently sorts,
deduplicates or coerces a `set`/`list` — the producing runtime constructs the canonical
tuple explicitly. This gives a logically set-like collection one deterministic order
*before* the mapper sees it, so canonical bytes cannot depend on producer iteration
order and semantic equality does not become order-sensitive. The empty tuple is valid.

**Error contract.** `ActorRole`/`Intent` are `StrEnum`s, so an invalid member lookup
raises the ordinary **`ValueError`** — no `InvalidRoleError`/`InvalidIntentError` is
invented. `SealedState` composition failures (wrong component type, unsorted barriers,
duplicate barriers, invalid structural `step`) raise the **built-in `ValueError`**, the
same convention `NonceRevealEntry` and `FinalNonceReveal` already use for composition.
`InvalidDigestError`/`InvalidNonceError` remain owned by the *representation* values
they belong to. **No new error hierarchy.**

**LIVE, not structural.** Board bounds, barrier legality on the current board, whether
`self_pos` is blocked, barrier quotas, reachability and any opponent relation stay
domain/runtime concerns and never enter a constructor.

## Future sealed-record builder contract (Stage 4E-R9-R1; no Python yet)

Semantic inputs, all **already valid** — the builder never creates a semantic value
from a string or a dict:

```
state: SealedState · action: PhysicalAction · intent: Intent · hint: str
cursor: TurnCursor · role: ActorRole · nonce: NonceValue
```

`cursor` is **not** serialized; it supplies the scalar `step` and `sub_game`. The action
is **not** serialized under an `action` key; it fills the sealed `move` member. Before
hashing, the builder must **refuse** a record where `state.step != cursor.step` or
`state.role != role` — a composition error, not a hash mismatch and not TAMPERED.

`state` maps exactly as (barriers are already ordered, so the mapper does not sort):

```json
{"config_sha256": state.config_sha256.value,
 "self_pos": [state.self_pos.row, state.self_pos.col],
 "barriers": [[p.row, p.col] for p in state.barriers],
 "step": state.step,
 "role": state.role.value}
```

and the top level maps exactly as:

```json
{"state": <above>, "move": <Layer-2 action mapping>, "intent": intent.value,
 "hint": NFC(hint), "step": cursor.step, "role": role.value,
 "sub_game": cursor.sub_game, "nonce": nonce.value}
```

Exactly those eight keys, sorted at serialization. No `null`, no optional member, no
`cursor` key, no `h_commit` key, no ninth field. Every member is mapped **explicitly**:
no reflection, no `__dict__`, no generic dataclass or recursive object encoder, no
`pickle`, no `repr`, no custom `JSONEncoder` accepting arbitrary objects.

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
| `ensure_ascii` | PL | **`False`** — one required current-v1 value, echoed pre-match (NDEC-003, PRD06-FR-005); non-ASCII hints make it decisive; not lecturer-required |
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
| barrier target inside `move` | PL | the exact placed cell as `[row,col]` (JDEC-012); never derived from position, direction or context |
| sealed `role` vocabulary *(4E-R9-R1)* | PL | exactly `"police"` / `"thief"`; never `"POLICE"`, `"Cop"` or the `cop` score key; no case-folding, no synonym |
| sealed `intent` vocabulary *(4E-R9-R1)* | SL | exactly `"truth"` / `"lie"` — both words are printed in Ch 5 p.51; never a bool, never `"honest"`/`"deceptive"` |
| `state.barriers` order/uniqueness *(4E-R9-R1)* | PL | sorted by `(row,col)` and duplicate-free **in the semantic value**; the mapper never sorts or deduplicates |

## Provenance summary

- SOURCE-SEMANTIC/EXPLICIT: canonical JSON, sorted keys, fixed separators, UTF-8, SHA-256, fresh nonce, byte-identical; **the `truth`/`lie` intent vocabulary** (Ch 5 p.51).
- PROJECT-CONTRACT (JDEC-002): exact separators `(",",":")`, **`ensure_ascii=False`**, LF, no trailing newline in hashed payload, float formatting, cross-OS determinism; **the `police`/`thief` sealed-role vocabulary** (NDEC-001, 4E-R9-R1).
- **`ensure_ascii=False` is a PROJECT contract, not a lecturer requirement.** The book is silent; the value is fixed here because non-ASCII hints make it byte-decisive, and it must be echoed pre-match (NDEC-003). Fixing it is not the same as claiming the source demanded it.
