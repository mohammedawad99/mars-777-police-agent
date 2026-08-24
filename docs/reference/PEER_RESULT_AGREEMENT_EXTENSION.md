# Result agreement over `receive_control` — what a partner must implement

One extension, on a tool that already exists. **Four public tools, unchanged. No
fifth tool, no new message family.** `receive_control` gains the one semantic
kind this project's frozen matrix has always paired with it: `result_agreement`.

Without it, gameplay, the six mutual audits and the series settlement may all
complete - but the result is **never finalized**: no `RESULT_APPROVAL_CORE` is
built, no `result_sha256` exists, `mutual_agreement` never becomes true, the
official result artifact is not written, and the set therefore **never reaches
fourteen**. Reporting stays ineligible and no email is sent.

Once the agreement completes, the result is written exactly once, the official
set reaches 14/14, and automatic reporting proceeds - exactly once. Appendix E
rule 35 scores a missing report **0 for both groups**, which is why the
extension has to be agreed before a counted window.

## 1. Legacy status form — unchanged

```json
{"kind": "status", "sender": "police", "sub_game_number": 1, "status": "ready"}
```

Answer, exactly as before:

```json
{"ok": true}
```

`enable`, `status`, `restart` and `quit` all keep their meaning and their answer.

## 2. Result agreement form

```json
{
  "kind": "result_agreement",
  "payload": {
    "game_id": "MaRs-777-vs-<you>",
    "game_uid": "43994252-2e4d-2b5c-9baa-4bf7aef5b5d6",
    "declaration_ref": "declaration_MaRs-777-vs-<you>.json",
    "timestamp": "2026-08-24T12:00:00Z",
    "contribution": {
      "group_id": "MaRs-777",
      "entries": [
        {"sub_game": 1, "github_commit": "<40 lowercase hex>", "tokens": 0},
        {"sub_game": 2, "github_commit": "<40 lowercase hex>", "tokens": 0},
        {"sub_game": 3, "github_commit": "<40 lowercase hex>", "tokens": 0},
        {"sub_game": 4, "github_commit": "<40 lowercase hex>", "tokens": 0},
        {"sub_game": 5, "github_commit": "<40 lowercase hex>", "tokens": 0},
        {"sub_game": 6, "github_commit": "<40 lowercase hex>", "tokens": 0}
      ]
    }
  }
}
```

**Answer: `result_sha256` as a bare 64-character lowercase hex string** — not an
object, not `{"ok": true}`.

## 3. Order

Deterministic, never negotiated: the **byte-wise lower `group_id` proposes**.
`MaRs-777` sorts below most identifiers, so we normally send first.

1. proposer sends its request; the response is the receiver's digest;
2. receiver then sends **its own** request; the response is the proposer's digest;
3. each side compares. Equal digests on both sides ⇒ `mutual_agreement = true`.

One request each. Both directions must complete — a side that only sends has
agreed nothing.

## 4. Contribution contents

Each participant contributes **only its own** six entries:

| member | meaning |
|---|---|
| `sub_game` | 1…6, each exactly once, ascending. Never sorted, deduplicated or padded. |
| `github_commit` | the commit **declared for the role that participant actually played in that sub-game**. Roles alternate, so a participant legitimately carries two distinct commits across six entries. |
| `tokens` | that participant's **own reported** usage. It is never inferred, defaulted, or supplied on the other side's behalf. If your agent meters nothing, report what your own accounting authority answers. |

`total_tokens` is **derived** as the sum of each participant's six values.

## 5. Digest authority

```
result_sha256 = SHA256(canonical_bytes(RESULT_APPROVAL_CORE))
canonical_bytes = json.dumps(core, sort_keys=True,
                             separators=(",", ":"),
                             ensure_ascii=False).encode("utf-8")
```

`RESULT_APPROVAL_CORE`, exactly:

```
game_id · game_uid · declaration_ref
teams            {group_a:{group_id}, group_b:{group_id}}
github_links     {group_a_police, group_a_thief, group_b_police, group_b_thief}
sub_games[6]     {sub_game, cop_score, thief_score, outcome,
                  github_commit{group_a,group_b}, tokens{group_a,group_b}}
cumulative       {cop_total, thief_total, series_outcome}
total_tokens     {group_a, group_b}
timestamp
```

* **Slots** are ascending Unicode code-point order of `group_id`.
* **Scores and outcomes are jointly derived** from the settled sub-game and the
  locked scoring table — never contributed by either side.
* `outcome` is `capture` / `survival` / `technical_loss`. **`tie` is not a
  sub-game outcome.**
* `result_sha256`, `mutual_agreement` and `reported_by` are **excluded from the
  core** — a digest may not sit inside the bytes it covers.

`result_sha256` is **not** `series_consensus_sha256`. They cover different scopes
and are never aliased.

## 6. Readiness — a valid request may arrive early

Both sides finish sub-game six at different moments and the proposer sends the
instant its own settlement completes, so a correct request can reach a receiver
still assembling its own six entries. **That is not an error.**

The rule both sides implement:

* wait **boundedly** (the agreed watchdog) for your own half to assemble, then
  process the **same** request;
* on timeout, refuse with an explicit retryable *not ready* error and mutate
  nothing;
* a repeat of a request already answered returns **the same digest** — idempotent,
  never a second pass.

## 7. Failure cases

| condition | behaviour |
|---|---|
| malformed payload, unknown `kind`, absent `kind` | refuse **immediately**, no wait, nothing read |
| unauthenticated session | refuse **immediately** — authentication is checked before anything else |
| contribution `group_id` ≠ authenticated sender | refuse |
| fewer or more than six entries, or a repeated `sub_game` | refuse — never repaired |
| commit not the one declared for the role played | refuse |
| digests differ | no agreement; the result stays unreportable, and that is recorded honestly |

## 8. Minimum a partner must add

1. Accept `kind: "result_agreement"` on `receive_control` and return the digest
   string. Keep the legacy status form byte-identical.
2. Build your own six-entry contribution from facts only you own.
3. Assemble `RESULT_APPROVAL_CORE` and hash it as in §5.
4. Send your own request in the other direction and compare.
5. Implement the bounded readiness wait in §6.

Everything else — the four tools, the nine kinds, the terms, the settlement —
is unchanged.
