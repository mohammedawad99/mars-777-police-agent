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
| board state | `state` | SOURCE-SEMANTIC (named) | Required | string/object | Ch 5 p.51 |
| physical move | `move` | SOURCE-SEMANTIC (named) | Required | string | Ch 5 p.51 |
| intent flag | `intent` | SOURCE-SEMANTIC (named; truth/lie) | Required | string enum | Ch 5 p.51 |
| verbal hint | `hint` | SOURCE-SEMANTIC (part of full record) | Required | string | Ch 5 p.50 |
| step number | `step` | SOURCE-SEMANTIC (part of full record) | Required | int | Ch 5 p.50 |
| role | `role` | SOURCE-SEMANTIC (part of full record) | Required | string enum (police/thief) | Ch 5 p.50 |
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
  **LOCAL-ONLY**.

## C. Acknowledgement record

Ack that the opponent's commitment was received and locked (Ch 5 §5.3.2, p.51).
**Not necessarily the same object as the commitment** — an acknowledgement is a
separate log event.

| Field | Proposed key | Provenance | Required | Type | Source |
|---|---|---|---|---|---|
| acked step | `ack_of_step` | SOURCE-SEMANTIC + PC | Required | int | Ch 5 p.51 |
| acked commit hash | `ack_commit` | SOURCE-SEMANTIC + PC | Required | string(hex) | Ch 5 p.51 |
| acking role | `by_role` | SOURCE-SEMANTIC + PC | Required | string enum | Ch 5 p.51 |

## D. Reveal data

Sent after both are locked: the move + verbal sentence; **nonce stays hidden**
until end-of-game audit (Ch 5 §5.3.2, p.51).

| Field | Proposed key | Provenance | Required | Type | Source |
|---|---|---|---|---|---|
| revealed move | `move` | SOURCE-SEMANTIC (named) | Required | string | Ch 5 p.51 |
| revealed hint | `hint` | SOURCE-SEMANTIC | Required | string | Ch 5 p.51 |
| (nonce — final audit only) | `nonce` | SOURCE-SEMANTIC | Required at audit | string | Ch 5 p.51,55 |

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
- **Fresh crypto nonce** — Ch 5 p.51,53 (`secrets.token_hex(16)` in reference; using a CSPRNG is CRYPTO-010; exact length is EXAMPLE-ONLY → PC).
- **Exact same bytes on both peers** — Ch 5 p.50 ("both peers hash byte-identical input").
- **`ensure_ascii`**: the book is **silent**. It is **NOT** claimed as a lecturer requirement. Because hints may be non-ASCII (natural language), a deterministic choice is required for byte-identity → **PROJECT-CONTRACT** (JDEC-002), not SOURCE-EXPLICIT.

## Classification totals

- SOURCE-EXPLICIT: 0 keys (Ch 5/7 name field *meanings* in prose/example code, not a printed JSON layout).
- SOURCE-SEMANTIC: the full field set (state, move, intent, hint, step, role, sub_game, nonce, ack, reveal, verification).
- PROJECT-CONTRACT: entry nesting & key spellings (JDEC-007), canonical params (JDEC-002), NN width (JDEC-004).
- EXAMPLE-ONLY (NOT adopted): the 4-field `{state,move,intent,nonce}` core and the `nonce|move` verifier payload.
- REVIEW-REQUIRED: exact `state` representation (string vs structured board), and whether ack/reveal are separate `entries[]` events or sub-objects of a turn entry.

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
      "move": "N",
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
- `state` deliberately omitted from the illustrative reveal entry (its exact
  representation is **[RR]**); it is part of the **hashed** payload (§B), which is a
  distinct object from this persistent log entry.
- Placeholder hashes/nonces are literal `PLACEHOLDER…` strings — **not** real
  cryptographic material.
