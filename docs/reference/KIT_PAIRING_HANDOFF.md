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

## Identifiers — case matters

`game_id` is derived exactly as the kit derives it,
`"-vs-".join(sorted([group_a, group_b]))`, **with the original case preserved**.
Ours contains `MaRs-777`, which is source-legal (App E #45: exactly 8
characters, no spaces) and case-sensitive. We do not fold it, and a peer that
lowercases it will derive a different `game_id` than we do.

`game_uid` is unchanged and unaffected by any of this:
`UUID(SHA256(canonical(terms) | sorted-pair)[:16])`.

Our official artifact filenames carry that `game_id` verbatim, so all fourteen
names are derivable by either side from the pair alone.

## Authentication — required for counted play

The course book requires Step-0 to be cryptographically authenticated with a
**pre-supplied key**. The kit's `terms_signature` is an **unkeyed content
agreement** — anyone holding the terms and the nonce recomputes it — so it proves
both sides read the same fourteen values and nothing about who is speaking. It
is not a substitute, and we will not weaken this for a counted game.

For a **development friendly** none of this is needed: we play today with no
keyed proof and label the whole run non-counted.

For **counted** play, this is the exact non-secret contract we would need a
partner to support. Nothing here is frozen as a field name until a real partner
agrees one.

| | |
|---|---|
| Algorithm | `HMAC-SHA256`, profile token `HMAC_SHA256` |
| Key | one pre-supplied shared secret per pairing, exchanged **out of band** before the match. Never on the wire, never in an artifact, never in this document |
| Key identifier | a short non-secret `key_id` label each side declares, so a proof can never be read under a key it did not name |
| Authenticated bytes | `b"step0"` immediately followed by the canonical JSON of the sender's own Step-0 core — no separator, no length prefix |
| The core | `game_id`, `game_uid`, `times.game_start`, the **sender's own** team subtree, `token_budget_per_series` |
| Canonical form | the same compact, sorted, `ensure_ascii=False` UTF-8 encoding the kit already uses |
| When | with the pre-game greeting, before the first turn of the series |
| What the peer sends | its own proof over **its own** core, tagged with its profile and `key_id` |
| What we send | ours, the same way. Each side authenticates only its own subtree, because at that moment neither has seen the other's |
| Failure | refused, on the record, with our `E-AUTH-FAILURE` identity. No retry as unauthenticated, and no downgrade |

**How this rides the kit wire.** The pinned `negotiate` message carries pairing
and locked-model declarations **beside** `terms` rather than inside it, so an
agreed extra top-level key adds nothing to the signed set and cannot invalidate
`terms_signature`. It needs no change to the game wire, no change to the tool
schema, and no change to the required terms. One caveat, and it is the reason
this needs agreeing rather than assuming: a peer running the kit **unmodified**
drops unknown keys when it parses a greeting, so it will neither read our proof
nor produce one. Both sides have to opt in.

If a partner cannot carry it in `negotiate`, an out-of-band pre-match keyed proof
is the fallback we would discuss.

## Result agreement — required for counted play, and not yet carriable

Our counted result is agreed, not assumed: each side independently builds the
approval core, computes `result_sha256`, sends exactly one result agreement,
checks the peer's digest against its own, and only on equality is
`mutual_agreement` set true. A missing or contradictory report zeroes **both**
teams (App E #35), which is why we will not shortcut it.

The pinned four-tool surface has **no operation that can carry this**:
`receive_control` has a closed four-word vocabulary, returns `{"ok": true}` and
carries no digest back, and the pinned driver never calls it at all. So for a
counted series a partner would need to agree a way to exchange the two digests —
the same conversation as the keyed proof above.

For a **development friendly** this is simply absent, and we say so in our own
evidence rather than inventing an agreement.

## What we have demonstrated

A complete six-sub-game alternating friendly against the pinned sparring peer,
over real FastMCP HTTP between independent processes: every sub-game settled,
**both sides agreed every row**, and both commitment chains reproduced in both
directions for all six. The pinned artifact checker passes over the peer's set.

## Not included here, deliberately

No authentication secret, no tunnel credential, no private backend URL, and no
historical endpoint. The live group URL is exchanged when a match is scheduled.

## Copy-paste message for another group

> **MaRs-777 — interoperability offer (development friendly)**
>
> `group_id`: `MaRs-777` (exact, case-sensitive)
>
> We implement the shared interoperability kit
> (`Imreec/copthief-league-protocol`) pinned at
> `ad6557626587e09146af4283a5e808e7001343c5`, wire `reference-v3`.
>
> **Tools** (FastMCP over HTTPS): `negotiate`, `receive_turn`, `submit_audit`,
> `receive_control`. Note the asymmetry: `submit_audit` takes `payload`, the
> other three take `message`.
>
> **Series**: exactly six sub-games, roles alternate every sub-game, the thief
> moves first within each sub-game. **We need to agree who takes which side in
> sub-game 1** — that single choice fixes the whole schedule for both of us.
>
> **Terms**: we need the fourteen flat terms byte-exact on both sides; they are
> what the signature and the `game_uid` derive from.
>
> **Endpoint**: one stable group URL, given to you live at match time. It is
> discovered fresh for each run, so please do not cache it.
>
> **First objective**: a **non-counted friendly**. Nothing about it is reported
> or scored, on either side.
>
> **Afterwards, if you want a counted series**, there are exactly two things to
> settle: a keyed Step-0 proof (we use HMAC-SHA256 with a pre-supplied key
> exchanged out of band), and a way to exchange the two final `result_sha256`
> digests — the pinned four-tool wire has no operation for either, so both need
> an agreed extension. We are happy to work to whatever you can support.
