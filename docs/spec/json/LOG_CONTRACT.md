# Log Contract — `log_<game_id>_g<NN>.json` — group MaRs-777

**Status: REVIEWED — Stage-1 supervising review PASS; baseline LOCKED. Contract
specification only — no JSON file, no schema, no code.** This is the most
integrity-sensitive contract.

Per-sub-game record enabling full cryptographic verification in the Replay Viewer:
Commit-Reveal commitments, acknowledgements, moves, hints, and — at final audit —
the nonces, so every step's commitment can be recomputed and compared. Primary
sources: **Ch 5 §5.3–5.4 (PDF p.50–55)**, **Ch 7 §7.4–7.5 (PDF p.72–74)**, **Ch 9
§9.3.3 (PDF p.94)**.

**Simplified-example warning (approved Stage 1B):** the Ch 5 core code hashes
`{state, move, intent, nonce}` (PDF p.53) and the Ch 7 verifier uses a
`f"{nonce}|{move}"` payload (PDF p.74). **Both are explicitly simplified
illustrations.** Ch 5 prose (PDF p.50) states the **real sealed record is richer**
and also includes `hint`, `verdict`/intent-classification, `step`, `role`,
`sub_game`. **Neither simplified example is adopted as the complete log format.**
The fuller Ch 5 record governs; the Ch 7 `nonce|move` snippet does **not** override
it.

## A. Persistent log document structure

| Field | Proposed key | Provenance | Required | Type | Source | Notes |
|---|---|---|---|---|---|---|
| game id | `game_id` | SOURCE-SEMANTIC + PC | Required | string | Ch 9 p.94 | INV-01 |
| shared uid | `game_uid` | SOURCE-SEMANTIC + PC | Required | string | Ch 9 p.95 | INV-01 |
| sub-game number | `sub_game` | SOURCE-SEMANTIC (named) + PC key | Required | int/string(NN) | Ch 5 p.50 | INV-02; NN width JDEC-004 |
| config hash ref | `config_sha256` | SOURCE-SEMANTIC | Required | string(hex) | Ch 5 p.127 | INV-03 (log ↔ played config) |
| turn entries | `entries[]` | SOURCE-SEMANTIC + PC | Required | array[object] | Ch 5 §5.3–5.4 | one per turn (see B–D) |
| final verification | `audit` | SOURCE-SEMANTIC + PC | Required | object | Ch 5 p.55; Ch 7 p.74 | see E |
| log schema version | `schema_version` | PROJECT-CONTRACT | Optional | string | — | JDEC-003 |

## B. Per-turn sealed / hashed commitment payload

The bytes that are hashed to form `H_commit`. **This is a distinct object from the
persistent entry** — it is the canonical serialization that both peers hash
identically (see `CANONICALIZATION_CONTRACT.md`).

| Component | Proposed key | Provenance | Required | Type | Source |
|---|---|---|---|---|---|
| board state | `state` | SOURCE-SEMANTIC (named); representation **PROJECT-LOCKED** (JDEC-012) | Required | object — exactly `{config_sha256, self_pos, barriers, step, role}` | Ch 5 p.51 |
| physical **action** | `move` | SOURCE-SEMANTIC (named) | Required | tagged object `{kind,value}` — **frozen Stage 4E-R4**, see below | Ch 5 p.51 |
| intent flag | `intent` | SOURCE-SEMANTIC (named; truth/lie) | Required | string, exactly `"truth"` \| `"lie"` — **both words printed in the source** | Ch 5 p.51 |
| verbal hint | `hint` | SOURCE-SEMANTIC (part of full record) | Required | string | Ch 5 p.50 |
| step number | `step` | SOURCE-SEMANTIC (part of full record) | Required | int | Ch 5 p.50 |
| role | `role` | SOURCE-SEMANTIC (part of full record); vocabulary **PROJECT-CONTRACT** (4E-R9-R1) | Required | string, exactly `"police"` \| `"thief"` | Ch 5 p.50 |
| sub-game | `sub_game` | SOURCE-SEMANTIC (part of full record) | Required | int | Ch 5 p.50 |
| nonce | `nonce` | SOURCE-SEMANTIC (named) | Required | string (crypto-random) | Ch 5 p.50–51 |

`H_commit = SHA256( canonical_json({state, move, intent, hint, step, role, sub_game, nonce}) )`.
The **nonce is transmitted only at final audit** (Ch 5 p.51), never at commit/reveal.

### Stage 1D locks (verdict, state, interop)

- **`verdict` (D1):** the Ch 5 code comment's "verdict" = the Hebrew prose's
  "intent classification (סיווג הכוונה)" = the truth/lie tag = the core **`intent`**
  field, chosen **at commit** (Ch 5 p.50). It is **not** a post-reveal validation
  and is **not a separate field** (that would double-count and diverge the hash).
  The sealed set stays the **8 fields** above with `intent` carrying the verdict.
  Source terminology ambiguity recorded as **C-08**. (The post-reveal legality/
  capture "verdict" is a *different* object — see `PROTOCOL_TIMELINE.md` event 9.)
- **`state` (JDEC-012):** PROJECT-LOCKED representation
  `{config_sha256, self_pos:[r,c], barriers:[[r,c]…] sorted, step, role}` — own-known
  info only, **no opponent private truth**; see `STAGE_1D_AUDIT.md` §E.
- **Interoperability:** because the opponent recomputes this hash at mutual audit,
  the exact field set, key order, canonicalization, and `state` representation are
  **NEGOTIATED-PRE-MATCH** (NDEC-001/002/003) with the PROJECT-LOCKED defaults above
  — **not** "resolved later by the opponent". The persistent log *file* structure is
  **LOCAL-ONLY** *(narrowed at Stage 4E-R11-R1: internal logger mechanics and the
  locally-derived verification annotations remain local, while the finalized
  document's **audit-disclosure core** is interoperable at final audit — see the
  Stage 4E-R11-R1 section below and the amended JDEC-007)*.

## C. Acknowledgement record

Ack that the opponent's commitment was received and locked (Ch 5 §5.3.2, p.51).
**Not necessarily the same object as the commitment** — an acknowledgement is a
separate log event.

| Field | Proposed key | Provenance | Required | Type | Source | Origin (Stage 4E-R3) |
|---|---|---|---|---|---|---|
| acked step | `ack_of_step` | SOURCE-SEMANTIC + PC | Required | int | Ch 5 p.51 | copied from the peer message's turn cursor (`step`) |
| acked commit hash | `ack_commit` | SOURCE-SEMANTIC + PC | Required | string(hex) | Ch 5 p.51 | copied from the peer message (`h_commit`) |
| acking role | `by_role` | SOURCE-SEMANTIC + PC | Required | string enum | Ch 5 p.51 | **LOG ATTRIBUTION, not a transmitted field** (Stage 4E-R3) |

## D. Reveal data

Sent after both are locked: the move + verbal sentence; **nonce stays hidden**
until end-of-game audit (Ch 5 §5.3.2, p.51).

| Field | Proposed key | Provenance | Required | Type | Source |
|---|---|---|---|---|---|
| revealed **action** | `move` | SOURCE-SEMANTIC (named) | Required | **the same tagged object as §B** — one action, one encoding | Ch 5 p.51 |
| revealed hint | `hint` | SOURCE-SEMANTIC | Required | string | Ch 5 p.51 |
| (nonce — final audit only) | `nonce` | SOURCE-SEMANTIC | Required at audit | string | Ch 5 p.51,55 |

### Stage 4E-R3 — `move` is the physical **action**, and `by_role` is log attribution

**Source (Ch 5 §5.3.1, PDF p.51, printed 35).** The sealed record's `Move` member is
defined as *"**הפעולה הפיזית**. המהלך הנבחר (**תנועה, הצבת חסם** וכדומה)"* — **the physical
action; the chosen action (movement, **barrier placement**, etc.)** — *"this is the core
that is to be locked against change"*. `move` is therefore a **generic action slot**, not
the movement vocabulary: `move_set` (`["N","S","E","W","STAY"]`, App F T15 FIXED) is the
vocabulary of the *movement* form only. Ch 5 §5.3.2 (same page) has Reveal send *"**את
הפעולה (Move)** ואת המשפט המילולי"* — **the action (Move)** and the verbal sentence — so
the revealed object is the same generic action, and it is the same one the commitment
sealed. Ch 3 §3.4 (p.37, printed 21) supplies the other half: a turn is **a single
action**, the police may place a barrier only *"in a turn in which he forgoes movement"*,
and the **declaration duty** is explicit — *"על השוטר להכריז באמת על כל הצבת מחסום ועל
מיקומה המדויק; אין להציב מחסום בהיחבא"* (**must truthfully declare every barrier placement
and its exact location; never place one in hiding**), repeated in the Iron Rules (p.38,
printed 22). A police barrier placement with its exact cell is therefore carried by the
ordinary `move` action at Reveal and bound by the same `H_commit` — **no eleventh
peer-visible family is needed, and none is created.**

**RESOLVED at Stage 4E-R4 — the action representation is now frozen.** The value of
`move` is a **tagged, structurally-exclusive object** with exactly two sorted keys:
`{"kind":"MOVE","value":"<move_set token>"}` for the movement form and
`{"kind":"BARRIER","value":[row,col]}` for the police barrier-placement form. The
movement form reuses the FIXED `move_set` vocabulary verbatim; the barrier form carries
**the exact placed cell** as the `[row,col]` coordinate array already locked by JDEC-006
and used by JDEC-012's `state`, so no new coordinate convention is invented. The tag
keeps the two forms unambiguous without JSON type-sniffing and leaves the slot
extensible for the source's *"etc."* without re-opening the sealed field set. A
barrier-carrying record is therefore now recomputable byte-identically, which removes
the byte-identity blocker; **Reveal is reclassified BLOCKED-BY-FUTURE-SEMANTIC-TYPE**,
waiting only on the shared `domain.actions` value being implemented. The exact shape is
**PROJECT-CONTRACT** carried pre-match by **NDEC-001** — the reference
`commit(state, move: str, intent)` snippet (p.53) is **EXAMPLE-ONLY**, the book labels
that 4-field core a simplification, and it neither narrows `move` to a movement string
nor prescribes any JSON shape.

**`by_role` (§C) is LOG ATTRIBUTION, not transmitted content.** Ch 5 §5.3.2 says only
*"**היריב מאשר** כי קיבל את ההתחייבות וכי הוא נעול עליה"* — the opponent confirms it
received the commitment and is locked onto it. The acknowledging party exists
(SOURCE-SEMANTIC) but is nowhere stated to be a payload field, and Figure 6 (p.52) carries
it as the message's **direction between two lifelines**. The local writer can always
derive it: there is exactly one opponent process (ARCH-001/002), the role each side plays
in the sub-game is immutable from `CONFIG_LOCKED` (PRD06-FR-048), and the writer knows
whether it sent or received the acknowledgement. Because the role is never transmitted,
there is nothing for a hostile peer to forge. The reference FastMCP snippet's
`{"accepted": ...}` return (p.28) is **NON-BINDING** example code for a different tool and
introduces no `accepted` field here.

### Stage 4E-R9-R1 — the three sealed members that had no exact representation

Stage 4E-R9 audited all eight sealed members before writing a codec and stopped
**BLOCKED-BEFORE-CODE**: `move`, `hint`, `step`, `sub_game` and `nonce` were exact, but
`role`, `intent` and `state` were not. This section closes those three, and nothing
else changes: the field set is still **8**, the peer-visible family inventory is still
**10**, and no register ID was created.

**`role` — three vocabularies existed, one is now the sealed one.** The source names
the two sides but never fixes a byte string: Figure 6 (p.52) labels its lifelines
**`Cop`** and **`Thief`**, which is explanatory terminology, not serialization law.
Meanwhile the repositories carry `ROLE = "POLICE"` / `VALID_ROLES = {"POLICE","THIEF"}`
and PRD-01 (FR-070/071/072, AC-008/009/010) keys **scores** as `{cop, thief}`. Three
deliberately distinct vocabularies are therefore frozen:

| # | Vocabulary | Values | Used for |
|---|---|---|---|
| 1 | source / explanatory | `Cop`, `Thief` | reading the book and Figure 6 — never serialized |
| 2 | **canonical sealed role** | `"police"`, `"thief"` | the sealed record's `role` and `state.role` — **PROJECT-CONTRACT** |
| 3 | score / reporting keys | `cop`, `thief` | PRD-01 score structures — unchanged |

The runtime mapping is **explicit**, never derived: `"POLICE"` → `"police"` and
`"THIEF"` → `"thief"`. No `lower()`, no case-folding, no normalisation, no synonym or
alias acceptance; an unrecognised runtime role is refused at the owning boundary rather
than mapped to a guess. Note explicitly: **the `cop` score key is *not* the canonical
sealed role for police**, and PRD-01's score contracts are *not* re-spelled for
cosmetic uniformity — two contracts may legitimately use two words for one side.

**`intent` — the vocabulary was always in the source.** Ch 5 §5.3.1 (p.51) defines it
as *"דגל הכוונה. ערך המציין אם הרמז המילולי הנלווה אמיתי **(truth)** או מטעה **(lie)**"* —
a flag stating whether the accompanying verbal hint is true (`truth`) or misleading
(`lie`), with both English words printed in the source. The vocabulary is therefore
**SOURCE-REQUIRED**, not a project choice; only the Python type that will carry it is
PROJECT-CONTRACT. No `unknown`, `neutral`, `honest`, `deceptive`, `true`/`false` or
boolean substitute is admitted, and the empty string is not a value.

**`intent` and `hint` are separate sealed members and both are always present.**
`intent` is the truth/lie flag; `hint` is the verbal text itself. Changing either one
alone changes the sealed bytes and therefore `H_commit`. `intent` is never inferred
from the hint's wording, and it is never omitted on the grounds that Reveal transmits
the hint separately — Reveal carries `action` + `hint` on the wire, while the *sealed*
record carries all eight members including `intent` (that asymmetry is the whole point
of a commitment).

**`state` — locked shape, and the duplication with the top level is intentional.** The
representation is the JDEC-012 / NDEC-002 / PRD06-FR-068 own-known object above. Its
`barriers` are **lexicographically sorted by `(row, col)` and duplicate-free in the
semantic value itself**, so the canonical mapper never sorts, deduplicates or repairs —
it serializes an already-valid value. Empty barriers emit `[]`.

`state` repeats `step` and `role`, which also appear at the top level. That is
deliberate and is **not** a ninth field. Two invariants make the duplication safe, and
the future sealed-record builder **must refuse an inconsistent record before hashing**:

```
state.step == <top-level step>          (= cursor.step)
state.role == <top-level role>
```

A violation is a **builder/composition error** — the producer assembled two
contradictory components. It is emphatically *not* a hash mismatch and *not* TAMPERED:
nothing has been hashed yet, and no peer has done anything wrong. Hashing a
self-contradictory record would be the actual defect.

### Stage 4E-R10-R1 — what the end-of-game mutual audit actually needs

`FinalNonceReveal` is **not** the complete audit material, and this contract must not
be read as implying it is. The sealed record hashed into `H_commit` is the eight
members of §B — `state`, `move`, `intent`, `hint`, `step`, `role`, `sub_game`,
`nonce`. Of those, ordinary **Reveal** discloses the action and the hint (§D),
**FinalNonceReveal** discloses the **nonce batch** (Stage 4E-R6/R8), and the peer
therefore still lacks the disclosed `state` and `intent` it needs to rebuild the
record and recompute the digest.

Ch 5 §5.4 closes that gap at the source level: at the end of the game each agent
**submits its full log, including the nonce reveals of all its steps**, and each side
then reconstructs the opponent's data itself. So the source-required disclosure is
the **audit material / full log**, of which the nonce batch is one part.

That obligation is **not** a peer-message family (**C-11**): its interchange shape is
recorded as `AUDIT-EXCHANGE-PAYLOAD: BLOCKED-BY-INTEROPERABILITY-SHAPE` in
`INTEROPERABILITY_BLOCKERS.md` and belongs to the artifact/transport boundary.
`FinalNonceReveal` is **unchanged and not expanded** by this note. The verdict
produced from that recomputation stays local — see §E.

### Stage 4E-R11-R1 — the audit-disclosure core, and what stays local

Stage 4E-R11 left one integration blocker: the finalized per-sub-game log was
classified **LOCAL-ONLY**, yet Ch 5 §5.4 requires each side to disclose enough of
it for the opponent to recompute every commitment independently. This section
reconciles the two **without a second schema**: there is still exactly one log
model, and this is a *classification* of its existing fields, not a new document.

**Field classification.** Every currently-frozen log field, classified exactly once:

| Field | Class |
|---|---|
| `game_id`, `game_uid`, `sub_game` | **SHARED-AUDIT-INPUT** — artifact identity the receiver must match against the played series |
| `config_sha256` | **SHARED-AUDIT-INPUT** — binds the log to the locked config; also `state.config_sha256` |
| `entries[]` | **SHARED-AUDIT-INPUT** — the played history container |
| `entries[].commit` (`H_commit`) | **SHARED-AUDIT-INPUT** — the value the recomputation is compared against |
| per-turn sealed-record members (`state`, `move`, `intent`, `hint`, `step`, `role`, `sub_game`) | **SHARED-AUDIT-INPUT** — without these the receiver cannot rebuild the record |
| `entries[].{ack_of_step, ack_commit}` | **SHARED-AUDIT-INPUT** — commit/ack interaction evidence |
| `entries[].by_role` | **LOCAL-ARTIFACT-METADATA** — derived attribution (Stage 4E-R3). It may exist **in a local persisted artifact** and is **not part of the `submit_audit` payload**; the receiver derives it from authenticated direction + the `CONFIG_LOCKED` role mapping and never trusts an incoming value |
| `audit.final_reveal[].nonce` | **SHARED-AUDIT-INPUT at final audit** — the eighth sealed member, withheld until then (CRYPTO-002) |
| `entries[].verified`, `audit.result`, `audit.tampered_step` | **LOCAL-DERIVED-AUDIT** — computed by the receiver, **never** accepted as peer evidence |
| `schema_version` | **LOCAL-ARTIFACT-METADATA** (optional, JDEC-003) |

**The verdict is never transmitted.** `entries[].verified`, `audit.result` and
`audit.tampered_step` are outputs of the receiver's *own* recomputation. A
sender's claimed `"Verified OK"` or `"TAMPERED"` has no standing: it is not part
of the `submit_audit` payload, and if a compatibility artifact happens to carry
such annotations they are **ignored for verdict generation**. This preserves
Stage 4E-R10-R1's ruling that `FinalAuditVerdict` is local audit/log/replay
vocabulary and never a transmitted verdict.

**Lifecycle, one schema and two states.** *DISCLOSURE-READY* — the document
carries **all and only the SHARED-AUDIT-INPUT fields**; this is what
`submit_audit` conveys. The boundary is deterministic, not a preference: both
**LOCAL-DERIVED-AUDIT** (`entries[].verified`, `audit.result`,
`audit.tampered_step`) and **LOCAL-ARTIFACT-METADATA** (`entries[].by_role`,
`schema_version`) are **outside the payload**, and neither becomes optional wire
content merely because it may exist in a local persisted artifact. `by_role`
keeps its Stage 4E-R3 status as log attribution rather than transmitted content,
and `schema_version` keeps its existing optional **local artifact** rule
(JDEC-003) — no version field is added to, or implied by, the operation payload.
*AUDITED-LOCAL* — after receipt
and independent recomputation, the receiver's own persisted copy additionally
carries `entries[].verified`, `audit.result` and `audit.tampered_step`. These are
**documentation lifecycle labels, not types**: no `DisclosureLog`, `AuditedLog`
or `AuditBundle` exists. Stated without optionality: the local-derived fields are
**absent before local audit and present only in the final local artifact after
it**.

**The sealed record is persisted per turn.** `FIELD_MATRIX.md`'s log row
`{state, move, intent, hint, step, role, sub_game, nonce}` is **Required, one per
turn**, and is authoritative on this point. §B above says the hashed payload is
*"a distinct object from the persistent entry"* — that refers to the **canonical
byte serialization**, which is never stored, **not** to the members, which are.
The illustrative example omits `state` from a *reveal* entry for the same reason
and is illustrative only. This matters because the receiver cannot derive
`state.self_pos` on its own under partial observation: if it were not disclosed,
independent verification would be impossible. The `nonce` member is the sole
exception — withheld at commit time and completed at final audit from
`audit.final_reveal[]`.

**Completeness.** For every audited commitment the receiver obtains `state`,
`move`, `intent`, `hint`, `step`, `role`, `sub_game` from the per-turn sealed
record, `nonce` from `audit.final_reveal[]`, and `H_commit` from
`entries[].commit` — the eight members plus the comparison value. Each is
represented by the **already-frozen Stage 4E-R9 canonical mapping**
(`CANONICALIZATION_CONTRACT.md`); no second representation of `PhysicalAction`,
`SealedState`, `Intent`, `ActorRole`, `NonceValue` or `Sha256Digest` is created.

**Nesting — the REVIEW-REQUIRED question is closed.** The **separate-event**
form already chosen by **JDEC-007** stands: `entries[]` is an event list whose
records carry `phase ∈ {commit, ack, reveal}`. It is preserved rather than
changed, because it already maps the Commit→Ack→Reveal→Audit flow and nesting
would duplicate the turn identity into a container. Frozen with it: every entry
carries `(sub_game, step)` plus its `phase`, which is its **only** association;
replay order is the **chronological protocol order** in which events occurred and
is never re-sorted lexicographically (`sub_game`, then `step`, then commit → ack
→ reveal); commit records own `commit` and the sealed-record members, ack records
own `ack_of_step` and `ack_commit`, reveal records own the revealed `move` and
`hint`; the final nonce is associated **not** in `entries[]` but by
`audit.final_reveal[]`'s `(step, role)`; local-derived verification attaches to
the entry it verifies and to `audit`; and **no field is duplicated within a single
event**. That is deliberately narrower than "no semantic fact appears twice",
because two evidentiary roles legitimately carry the same *value*: the revealed
`move`/`hint` recorded as **historical Reveal evidence**, and the same members
disclosed as **sealed-record audit input** for recomputation. They are distinct
records with distinct purposes and are expected to agree — comparing them is
meaningful, so the contract keeps both rather than collapsing them, and no second
schema is introduced to hold either. No new peer-message field was created to solve a log question.

**Byte identity and hashing.** Semantic equality of the shared audit-input
document is required; **whole-log file byte identity between peers is not an
interoperability requirement** — the cryptographic byte-identity requirement
applies to the sealed commitment record and the other explicitly canonical
objects, which are unchanged. The receiver's `ArtifactStore` owns deterministic
local persistence. **No `log_sha256`, `audit_sha256` or `artifact_sha256`** is
added: the audit verifies individual commitments against `H_commit`, and no
log-level cryptographic commitment exists.

**Top-level shape and identity unchanged.** `game_id`, `game_uid`, `sub_game`,
`config_sha256`, `entries`, `audit` (+ optional `schema_version`); filename still
`log_<game_id>_g<NN>.json`. Nothing was added because transport now consumes it —
no `declaration`, `result`, `github_commit`, `peer_url`, filesystem path or
transport metadata. The log field count stays **9** and `FIELD_MATRIX.md` is
unchanged.

## E. Verification result

Post-mortem audit: recompute each step's hash from the revealed data and compare
to `H_commit`; any mismatch → TAMPERED → disqualify, score 0 (Ch 5 §5.4, Ch 7
§7.4; **CRYPTO-003**, REPLAY-002, App E #19).

| Field | Proposed key | Provenance | Required | Type | Source |
|---|---|---|---|---|---|
| per-step verdict | `entries[].verified` | SOURCE-SEMANTIC + PC | Required | bool | Ch 7 p.72–74 |
| final verdict | `audit.result` | SOURCE-SEMANTIC + PC | Required | string enum (`Verified OK`/`TAMPERED`) | Ch 7 p.72–74 |
| tampered step (if any) | `audit.tampered_step` | SOURCE-SEMANTIC + PC | Optional | int | Ch 7 p.74 |

## Canonical Commitment Payload

Source-backed requirements (details + provenance in `CANONICALIZATION_CONTRACT.md`):

- **Canonical JSON** serialization of the sealed record — Ch 5 p.50 (reference uses "sorted keys and fixed separators").
- **Sorted keys** — Ch 5 p.50, reference code `sort_keys=True` (SOURCE-SEMANTIC: required for byte-identity; the exact library param is EXAMPLE-ONLY/PC).
- **Fixed separators** — Ch 5 p.50; reference `separators=(",",":")` is EXAMPLE-ONLY → adopting it is **PROJECT-CONTRACT** (JDEC-002).
- **UTF-8** encoding before hashing — Ch 5 p.53 (`.encode("utf-8")`).
- **SHA-256** — Ch 5 §5.3, App E #17.
- **Fresh crypto nonce** — Ch 5 p.51,53. The source requires a *fresh cryptographic* nonce, secret until the final reveal; `secrets.token_hex(16)` is **REFERENCE-EXAMPLE** and fixes no encoding or length. Using a CSPRNG is CRYPTO-010, a **producer** duty that no receiver can verify from the string alone. Stage 4E-R6 adopts `[0-9a-f]{32}` as the **PROJECT-CONTRACT / NEGOTIATED-PRE-MATCH default** (NDEC-001) for parser strictness, NFC-invariance and a 128-bit entropy floor — **not** because recomputation needs it: the receiver recomputes with the exact revealed string.
- **Exact same bytes on both peers** — Ch 5 p.50 ("both peers hash byte-identical input").
- **`ensure_ascii`**: the book is **silent**. It is **NOT** claimed as a lecturer requirement. Because hints may be non-ASCII (natural language), a deterministic choice is required for byte-identity → **PROJECT-CONTRACT** (JDEC-002), not SOURCE-EXPLICIT.

## Classification totals

- SOURCE-EXPLICIT: 0 keys (Ch 5/7 name field *meanings* in prose/example code, not a printed JSON layout).
- SOURCE-SEMANTIC: the full field set (state, move, intent, hint, step, role, sub_game, nonce, ack, reveal, verification).
- PROJECT-CONTRACT: entry nesting & key spellings (JDEC-007), canonical params (JDEC-002), NN width (JDEC-004).
- EXAMPLE-ONLY (NOT adopted): the 4-field `{state,move,intent,nonce}` core and the `nonce|move` verifier payload.
- REVIEW-REQUIRED: **none remaining.** *(The `move` action representation was frozen at Stage 4E-R4; the `state` representation lock was reconciled at Stage 4E-R9-R1; and the ack/reveal **separate-`entries[]`-events vs nested sub-objects** question was closed at Stage 4E-R11-R1 in favour of the separate-event form JDEC-007 had already chosen.)* *(The `move` action representation was REVIEW-REQUIRED at Stage 4E-R3 and is **frozen at Stage 4E-R4** — see below. The exact **`state`** representation was listed here too; that text was **stale** — `state` has been PROJECT-LOCKED since JDEC-012 / NDEC-002 and §B above, and Stage 4E-R9-R1 removed the contradiction. The `role` and `intent` value vocabularies were likewise pinned at Stage 4E-R9-R1.)*

## Illustrative example (Markdown only; not a real file)

Fields marked **[PC]**; **[RR]** = review-required shape. Nonces shown only in the
final `audit` block (they are hidden until then).

```json
{
  "game_id": "mars777-vs-groupx-2026w1-uid0001",
  "game_uid": "uid0001",
  "sub_game": 1,
  "config_sha256": "PLACEHOLDER_HEX_NOT_A_REAL_HASH",
  "entries": [
    {
      "step": 1,
      "role": "police",
      "phase": "commit",
      "commit": "PLACEHOLDER_HCOMMIT_HEX",
      "verified": null
    },
    {
      "step": 1,
      "role": "police",
      "phase": "ack_of_opponent",
      "ack_of_step": 1,
      "ack_commit": "PLACEHOLDER_OPP_HCOMMIT_HEX",
      "by_role": "thief"
    },
    {
      "step": 1,
      "role": "police",
      "phase": "reveal",
      "move": {"kind":"MOVE","value":"N"},
      "hint": "circling near the north gate",
      "intent": "lie",
      "verified": true
    }
  ],
  "audit": {
    "result": "Verified OK",
    "tampered_step": null,
    "final_reveal": [
      { "step": 1, "role": "police", "nonce": "PLACEHOLDER_NONCE_HEX" }
    ]
  }
}
```

- Entry `phase`, the split of commit/ack/reveal into separate `entries[]`, and the
  `audit.final_reveal` shape are **[PC]** (JDEC-007) — a defensible representation
  of the SOURCE-SEMANTIC Commit→Ack→Reveal→Audit flow; **[RR]** whether ack/reveal
  are separate events or nested under a turn.
- `state` is deliberately omitted from the illustrative reveal entry because it is part
  of the **hashed** payload (§B), a distinct object from this persistent log entry —
  **not** because its representation is open. It is **PROJECT-LOCKED** by JDEC-012 /
  NDEC-002 / PRD06-FR-068. *(Stage 4E-R9-R1: this note previously said "its exact
  representation is **[RR]**", contradicting §B of this same file.)*
- Placeholder hashes/nonces are literal `PLACEHOLDER…` strings — **not** real
  cryptographic material.

## Stage 5-R8 — the capture transcript and the semantic finding

Two additions, both inside the one log model this contract already freezes.

**Disclosure core (SHARED-AUDIT-INPUT).** The audit-disclosure document carries
`capture[]` alongside `entries[]`: one row per reveal that produced a
`TurnOutcome`, in the order the sub-game produced them, each exactly
`{step, claim, answer}` — `claim` is `null` or `[row, col]`, and `answer` is one
of `NO_QUESTION` / `NOT_CAUGHT` / `CAUGHT`. The rows are **not** hashed: they
were never members of `H_commit` (JDEC-016). What makes them evidence is that
the receiver compares them against the rows it observed live; a disclosure whose
transcript differs in any row is refused, and a document with no `capture`
member at all is refused rather than treated as an empty transcript.

**Log events (AUDITED-LOCAL).** Every `reveal` event — ours and the peer's —
carries `capture_claim` and `capture_answer` in the same two spellings. A turn
that was sealed but never revealed writes `null` for both: `NO_QUESTION` means
"the reveal asked nothing", which is a different fact from "there was no reveal".

**`audit.semantic` (LOCAL-DERIVED-AUDIT).** The audit block gains
`{verdict, step, at_fault, also_at_fault}` — the finding **this** side's replay
reached, never one accepted from a peer, exactly like `audit.result` and
`audit.tampered_step`. `verdict` is one of `CONSISTENT`, `WRONG_START`,
`BROKEN_TRAJECTORY`, `ILLEGAL_ACTION`, `WRONG_BARRIER_SET`,
`FALSE_CAPTURE_CLAIM`, `DISHONEST_CAPTURE_ANSWER`, `FALSE_CLAIM_AFFIRMED`.
`step` and `at_fault` are `null` only when the verdict is `CONSISTENT`.

`also_at_fault` is always present and is `null` for every verdict except
`FALSE_CLAIM_AFFIRMED`, the one event with a fault on each side: the claimant
declared a capture that never happened (`CRYPTO-005`) and the answerer confirmed
it (`CRYPTO-004`). It is a second role, never a list and never free text — the
game has exactly two sides.

A disqualifying finding also drives `audit.result` to `TAMPERED` at that step,
so the file and the series gate cannot disagree. A **scored** finding
(`ILLEGAL_ACTION`, `FALSE_CAPTURE_CLAIM`, and the claimant's half of
`FALSE_CLAIM_AFFIRMED`) leaves `audit.result` at `Verified OK` and changes the
sub-game's end event to `TECHNICAL_LOSS` instead — an honest record of illegal
play is not a forgery.
