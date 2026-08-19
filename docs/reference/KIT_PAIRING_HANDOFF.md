# MaRs-777 — pairing handoff (non-secret)

**Status: DRAFT for a development friendly. Not an offer of counted play.**

Everything here is a fact we have demonstrated or a requirement we will hold to.
Nothing here is a secret, a credential, or an endpoint that is live today.

## Identity

| | |
|---|---|
| `group_id` | `MaRs-777` (exact, case-sensitive) |
| Role backends | two independent implementations, Police and Thief, behind **one** group endpoint |
| Endpoint | one stable group MCP URL, supplied at match time — never two, never per-role |

## Interoperability profile

* **Kit pin** — `Imreec/copthief-league-protocol` @ `ad6557626587e09146af4283a5e808e7001343c5`.
  We implement that revision; we do not track its `main`.
* **Wire** — `reference-v3`. Four FastMCP tools: `negotiate`, `receive_turn`,
  `submit_audit`, `receive_control`. `submit_audit` takes `payload`; the other
  three take `message`.
* **Canonical JSON** — compact separators, sorted keys, `ensure_ascii=False`,
  UTF-8, sorted by Unicode code point.
* **Commitment** — `SHA256(canonical(payload) | nonce)`, a single `|`, nonce
  **outside** the payload. Nonces are 32 lowercase hex.
* **Identity** — `game_id = "-vs-".join(sorted(pair))`;
  `game_uid = UUID(SHA256(canonical(terms)|sorted-pair)[:16])`.
* **Series** — exactly six sub-games, `REFERENCE_ODD_EVEN_ALTERNATION`, and the
  thief takes the first turn of every sub-game.
* **Payload schema** — ours is richer than the kit minimum and we require none of
  it back. Payload key sets need not match; each side re-hashes what the other
  revealed.

## What we need agreed before a match

1. **Starting role.** Alternation makes sub-game 1 decide the whole schedule, so
   state which side each group takes in `g01`. They must be complementary.
2. **The fourteen flat terms**, exactly — they are what both signatures and the
   `game_uid` derive from. A float that differs only in `repr` is invisible in a
   diff and fatal to the signature.
3. **Scent model.** We implement the book's multiplicative family. We do **not**
   implement `subtractive_chebyshev_v1`.
4. **Exactly six sub-games.** A short series is not a series.

## Authentication — the one thing still open

The course book requires Step-0 to be cryptographically authenticated with a
**pre-supplied key**. We implement `HMAC_SHA256` and we will not weaken it for a
counted game.

The kit's `terms_signature` is an **unkeyed content agreement**: anyone holding
the terms and the nonce recomputes it, so it proves both sides read the same
fourteen values and nothing at all about who is speaking. It is not a substitute.

So:

* **Development friendly** — we can play today, with no keyed proof, and we will
  label the whole run non-counted.
* **Counted play** — needs a keyed Step-0 proof both sides can produce and check.
  Our preferred route is an **agreed keyed extension carried in `negotiate`**: it
  needs no change to the game wire and no change to the signed `terms`. We are
  open to an agreed alternative that keeps pre-supplied-key semantics.

## What we have demonstrated

A complete six-sub-game alternating friendly against the pinned sparring peer,
over real FastMCP HTTP between independent processes: every sub-game settled,
**both sides agreed every row**, and both commitment chains reproduced in both
directions for all six. The pinned artifact checker passes over the peer's set.

## Not included here, deliberately

No authentication secret, no tunnel credential, no private backend URL, and no
historical endpoint. The live group URL is exchanged when a match is scheduled.
