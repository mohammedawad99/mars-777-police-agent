# Protocol Timeline — group MaRs-777

**Status: REVIEWED — Stage-1 supervising review PASS; baseline LOCKED. Specification only.** This timeline is
the authority for deciding when each field first exists (esp. whether `verdict`
can be pre-commit — it can: it is the commit-time `intent` classification).
Sources: Ch 5 §5.3–5.5 (PDF p.50–56), Ch 7 §7.4 (p.72–74), Ch 9 (p.85–96), App B/C/F.

Legend: Producer→Recipient; "hashed" = enters a SHA-256 payload; "secret" = not on
the wire yet.

| # | Event | Producer→Recipient | Known before | Transmitted | Still secret | Persisted | Hashed | Later verified |
|---|---|---|---|---|---|---|---|---|
| 1 | **Step-0 declaration + keyed authentication** | each team → opponent/lecturer | hardware, OS/CPU/RAM/GPU, model, code version, `github_commit`, token cap, identities, times; **pre-supplied key (out-of-band)** | Step-0 content + `step0_auth {auth_alg,key_id,auth_tag}` | **key material (never on the wire)** | declaration | **keyed auth** `auth_tag` over `"step0"‖core` (K1, NDEC-005) | tag verified pre-play; at audit / fairness scoring |
| 2 | **Config negotiation** | both teams | App F floors, board/scent/scoring | proposed config values | — | — | — | via config hash |
| 3 | **Config lock / hash / signature exchange** | both → both | agreed config (App B keys); **pre-supplied key** | `config_sha256` + `config_auth {auth_alg,key_id,auth_tag}` | **key material** | config (+ sidecar) | `config_sha256` over config bytes (NDEC-004) **and** keyed `auth_tag` over `"config"‖core` (K2, NDEC-007) | **both** hash-equality **and** tag verification before play |
| 4 | **Turn decision** | acting agent (local) | belief map, scent, own pos, barriers | — | move, hint, intent, nonce (chosen now) | (local) | — | — |
| 5 | **Commitment** | agent → opponent | state, move, intent, hint, step, role, sub_game, nonce | `H_commit` only | move, hint, nonce | log | **sealed payload → `H_commit`** (NDEC-001/002/003) | at reveal + final audit |
| 6 | **Acknowledgement** | opponent → agent | received `H_commit` | ack of step + commit | — | log | — | — |
| 7 | **Reveal** | agent → opponent | move, hint | move + hint | **nonce** (still) | log | — | recompute vs `H_commit` |
| 8 | **Move validation** | opponent (enforces physics) | move legality, capture claim | **[RR]** accept/reject — *shape unfrozen, see below (4E-R6)* | — | log | — | at audit |
| 9 | **Verdict (validation record)** | opponent/local | legality + capture-truth result | (result) | — | log (separate record) | — | — |
| 10 | **State transition** | both (state machine) | new positions/barriers | phase transition | opponent true pos (always) | — | — | — |
| 11 | **Final nonce reveal** | each → each | all nonces | **nonces** | (none) | log (final_reveal) | — | recompute all `H_commit` |
| 12 | **Final audit** | both (Replay Viewer) | full logs + nonces | **[RR]** audit verdicts — *the recomputation is local; whether a verdict is transmitted is unfrozen, see below (4E-R6)* | — | log (`audit.result`) | recompute SHA-256 per step | Verified OK / TAMPERED |
| 13 | **Result construction** | each team | per-sub-game scores, commit, tokens, four links | — | — | result | result-approval core (NDEC-006) | dual-report compare |
| 14 | **Mutual result agreement** | both → both | agreed result core | `result_sha256` + agreement | — | result | `result_sha256` | both reports equal hash |
| 15 | **Gmail reporting** | each team → lecturer | full **self-contained** result JSON (identities, four links, **FastMCP endpoints**, **signed hardware declarations + `hardware_auth`**, scores, commits, tokens; K3) | result JSON attachment | **key material** | (sent) | — | grader parse/attribution; **missing-from-either-side or contradictory ⇒ 0 to both (E-35, C-09)** |

## Key chronology conclusions

- **`verdict` (= `intent` classification) exists at event 4/5** (the agent chooses
  truth/lie when composing the commit) ⇒ it is legitimately part of the **pre-commit
  sealed payload** as `intent`. It is **not** the post-reveal validation "verdict"
  of event 9 (a different object that exists only after reveal).
- **`nonce`** exists at event 4, is hashed at event 5, stays secret until event 11.
- **`move` at events 4/5/7 is the physical *action*, not a movement token** (Ch 5 p.51: "the chosen action (movement, **barrier placement**, etc.)"; event 7 sends "**the action (Move)** and the verbal sentence"). A police barrier placement with its **exact cell** — which Ch 3 p.37/38 require to be declared truthfully and never hidden — therefore travels in this same slot and is bound by the same `H_commit`; **no eleventh peer-visible family exists**. Its exact representation was REVIEW-REQUIRED at Stage 4E-R3 and is **frozen at Stage 4E-R4**: a tagged, structurally-exclusive object `{"kind":"MOVE","value":"<move_set token>"}` or `{"kind":"BARRIER","value":[row,col]}`, the same encoding at events 5 and 7 (`CANONICALIZATION_CONTRACT.md` Layer 2, `LOG_CONTRACT.md` §B/§D, NDEC-001).
- **`config_sha256`** exists at event 3 (before any turn), so a `state` that
  references it (event 5) is chronologically valid.
- The **DECISION → COMMIT → ACK → REVEAL → VALIDATION/VERDICT → FINAL REVEAL/AUDIT**
  order confirms the seven-object separation in `STAGE_1D_AUDIT.md` (Section D).
- **Keyed authentication (K1/K2, Stage 1D.1):** events 1 and 3 each add a
  `context`-separated `auth_tag` (HMAC-SHA256 default, JDEC-013) proving the producer
  holds the **pre-supplied key**. This is **keyed** authentication — not the unkeyed
  `config_sha256`/`H_commit`/`result_sha256` hashes and not a PKI signature. A failed
  tag or absent compatible key ⇒ **refuse counted play** before event 4.
- **Reporting (K3/C-09):** event 15's report is self-contained and both-sided; the
  keyed hardware evidence (`hardware_auth`) mirrors the event-1 `step0_auth`. No key
  byte is ever transmitted or persisted at any event.

## Stage 4E-R6 — what Figure 6 actually puts on the wire

**Figure 6 (p.52) draws exactly four message arrows**, in both directions:
*Commit: H_commit only* → *Acknowledge (locked)* → *Reveal: Move + Hint (Nonce
hidden)* → *Final Reveal: all Nonces (end of game)*, captioned as the four stages
**Commit → Acknowledge → Reveal → Audit**. There is **no move-validation arrow and
no audit-verdict arrow.** Two consequences, both recorded rather than resolved by
invention:

- **Event 8 is real but its shape is not source-frozen.** App E #14 *does* require
  the opponent to reject an illegal move (*"no diagonal moves — sanction: move
  rejected by the opponent → loss"*), and Ch 6.5 requires the local algorithm to
  reject any illegal move its own model proposes. So rejection exists. What no
  source fixes is whether it travels as a **peer-visible message with a payload**
  or is a local enforcement decision surfacing through the sanction path. The
  `{"accepted": is_valid, …}` return in the minimal FastMCP server (p.28) is
  **REFERENCE-EXAMPLE** about signature checking and was **not** promoted — the same
  snippet Stage 4E-R3 already refused to promote for the acknowledgement.
- **Event 12's computation is local.** Ch 5 §5.4 (p.55) has each side rebuild the
  opponent's record from *State, Move, Intent, Nonce* and compare against the
  declared commitment, and Ch 2.2.1 makes independent verification the whole point
  of having no central server. Ch 7 §7.5 + Figure 10 put the recomputation in the
  **Replay Viewer** over the persisted log, emitting `Verified OK` / `TAMPERED`.
  What the log holds is settled; whether a *verdict message* is exchanged is not,
  and disagreement already has a path through result agreement and C-09.

Event 11 needs no such caveat: *"Final Reveal: all Nonces"* is drawn in both
directions, and p.55 says each agent submits its full log **including the nonce
reveals of all its steps** — so it is **one batched message per side covering that
side's own steps**, not one message per turn.
