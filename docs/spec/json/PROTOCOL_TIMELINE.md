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
| 8 | **Move validation** — *local legality decision + transport-level rejection outcome* | receiving peer decides **locally**; the outcome surfaces on the transport response | move legality, capture claim | **the accept/reject outcome of the operation that received the turn** — **not** a standalone semantic message (C-12); **response shape frozen at Stage 4E-R11** as a single `bool` game-legality result of the turn operation (`API_BOUNDARIES.md` O5) | — | log (separate validation record, event 9) | — | at audit |
| 9 | **Verdict (validation record)** | opponent/local | legality + capture-truth result | — *(local record; the peer-facing part is event 8's transport outcome)* | — | log (separate record) | — | — |
| 10 | **State transition** | both (state machine) | new positions/barriers | phase transition | opponent true pos (always) | — | — | — |
| 11 | **Final nonce reveal** | each → each | all nonces | **nonces** | (none) | log (final_reveal) | — | recompute all `H_commit` |
| 12 | **Final audit** — *audit-material exchange + local mutual audit* | each → each (material); then **each side locally** | full logs + nonces | **the audit material / full log each side must disclose so the opponent can recompute independently** (Ch 5 §5.4) — **not** a verdict: no `FinalAuditVerdict`, `expected_digest`, `recomputed_digest` or reason is transmitted (C-11) | — | log (`audit.result`, `entries[].verified`, `audit.tampered_step`) | recompute SHA-256 per step **locally** | Verified OK / TAMPERED — **local** Replay-Viewer/log verdict |
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

- **Event 8 is real, and Stage 4E-R10-R3 settled its mechanism.** App E #14 *does*
  require the opponent to reject an illegal move (*"no diagonal moves — sanction:
  **move rejected by the opponent** → loss"*), and Ch 6.4-6.5 reserve legality to
  the **local algorithm**, which must reject any illegal move *its own model*
  proposes — a different act that must not be conflated with the peer-facing one.
  What no source fixes is the **mechanism**: whether the peer-facing rejection is a
  standalone message, the response of the call that received the turn, or a local
  refusal surfacing through the sanction path. Stage 4E-R10-R2 stopped rather than
  guess; Stage 4E-R10-R3 resolved it by supervising decision (**C-12**):

  > The rejection is **not** modelled as a standalone `app.peer_messages` family.
  > The receiving peer validates legality **locally** with the already-owned
  > `domain.rules` / `LocalTurnService` authority, and the peer-facing outcome is
  > placed at the **transport / port response boundary** of the operation that
  > received the turn. **PROJECT-CONTRACT** under source minimality — the source is
  > **not** claimed to forbid a distinct message.

  Consequently the derived peer-visible inventory is corrected **9 → 8**, and
  `MoveValidation` is no longer a peer-message family. Four separations are
  load-bearing and must never collapse into one "accepted" flag: **(i)** transport
  delivery/parsing, **(ii)** authentication/signature/config acceptance, **(iii)**
  protocol phase/cursor/order acceptance, and **(iv)** **game-legality**
  acceptance. Appendix E #14 concerns only **(iv)**. The
  `{"accepted": is_valid, …}` return in the minimal FastMCP server (p.28) computes
  `is_valid = verify_signature(...)` — it is **(ii)**, not **(iv)** — so it remains
  **REFERENCE-EXAMPLE** and was **not** promoted; treating it as legality law would
  mislabel an authentication result as a game verdict. The exact response shape is
  **not** frozen here: `API_BOUNDARIES.md` defers concrete operation signatures to
  Stage 2B-2C and both peer ports are **async**, so the shape is recorded as
  `MOVE-REJECTION-TRANSPORT-SHAPE: BLOCKED-BY-TRANSPORT-SHAPE`. Events 8 and 9 both
  survive: a timeline event is not automatically a peer-message family, and a log
  validation record is not automatically a wire message.
- **Event 12's computation is local — and Stage 4E-R10-R1 settled the rest.** Ch 5
  §5.4 (p.55) has each side rebuild the opponent's record from *State, Move,
  Intent, Nonce* and compare against the declared commitment, and Ch 2.2.1 makes
  independent verification the whole point of having no central server. Ch 7 §7.5 +
  Figure 10 put the recomputation in the **Replay Viewer** over the persisted log,
  emitting `Verified OK` / `TAMPERED`. What was left open in 4E-R6 — *whether a
  verdict message is exchanged* — is now closed as **NOT SOURCE-REQUIRED**, and the
  project declines to invent one (**C-11**). Note the classification precisely: the
  source does **not forbid** such a message; it simply never requires one, and
  Figure 6 draws no arrow for it. Consequences, none of which shrink the audit:

  | Aspect | Status |
  |---|---|
  | **Transmitted / made available** | the **audit material / full log** each side discloses, including its nonce reveals, so the opponent can recompute independently (Ch 5 §5.4) — **SOURCE-REQUIRED** |
  | **Local** | recomputation, digest comparison, and the `FinalAuditVerdict` produced from it |
  | **Persisted** | `entries[].verified`, `audit.result`, `audit.tampered_step` and the preserved digest evidence (PRD06-FR-104), already **LOCAL-ONLY** per `LOG_CONTRACT.md` §E |

  There is therefore **no peer-visible `FinalAudit` family**, and the derived
  peer-visible inventory is corrected **10 → 9** (further corrected to **8** at Stage 4E-R10-R3, C-12). What survives untouched:
  `ProtocolPhase.FINAL_AUDIT` (a workflow phase is not a message family),
  `FinalAuditVerdict` (local audit/log/replay vocabulary), and the TAMPERED
  consequence with its frozen sanction. The exact **interchange shape** of the
  audit material is a separate artifact/transport question, recorded as
  `AUDIT-EXCHANGE-PAYLOAD`, **resolved at Stage 4E-R11-R1**: the `submit_audit`
  operation carries the **JSON-native audit-disclosure core** of the finalized
  per-sub-game log (one schema, no parallel audit bundle), while the verdict and the
  other locally-derived annotations stay local. It was never a peer-message-family
  blocker.
  Precise wording on the downstream link: a **completed mutual audit is a
  precondition to mutual result agreement** (App E; PRD06-FR-100). Result agreement
  is *downstream of* audit; it is **not** the transport of a verdict, and it stays
  `BLOCKED-BY-PAYLOAD-SHAPE` in its own right.

Event 11 needs no such caveat: *"Final Reveal: all Nonces"* is drawn in both
directions, and p.55 says each agent submits its full log **including the nonce
reveals of all its steps** — so it is **one batched message per side covering that
side's own steps**, not one message per turn.

## Stage 4E-R12 — events 1-3 refinement (event count unchanged: 15)

No event added, removed, split or merged. Three clarifications to rows 1-3:

- **Event 1** — "Hashed" now reads precisely: the `AuthProof` covers the frozen
  **STEP-0 AUTHENTICATED CORE** (`DECLARATION_CONTRACT.md`, Stage 4E-R12), not the
  whole declaration file. Cadence is **once per series**, and the profile/`key_id`
  that verify it were provisioned **out of band before `BOOT`**, never learned
  from this or any earlier message.
- **Event 2** — "Transmitted" is a **complete proposed config core, never a
  delta**, accompanied by the pre-match echo set (codec, result profile,
  tool-name profile, series convention, NDEC-001/002/003 representations) as
  **negotiation evidence, not artifact fields**. Still nothing is hashed here, and
  the messages carry no individual `AuthProof`; integrity is enforced at event 3.
- **Event 3** — the exchange verifies in a fixed order: `auth_alg`/`key_id`
  compared against the provisioned expectation → `AuthProof` verified →
  `config_sha256` equality → lock. The **lock itself is a local state transition
  with no serialized representation** (`CONFIG_CONTRACT.md` R12-E layer 4).
  Cadence is **once per sub-game**, unlike event 1.

**Stage 4E-R12-FIX — event 3 correction.** The "Hashed" cell reads
"keyed `auth_tag` over `"config"‖core`". The authenticated context is amended to
**`ConfigLockContext` = `{game_id, game_uid, sub_game, config_sha256, profiles}`**
(`CONFIG_CONTRACT.md` R12-FIX-K), because the App-B core is byte-identical across
every sub-game and therefore binds no sub-game association. `config_sha256`
itself is unchanged — still an unkeyed digest over the canonical config core —
and it binds all 35 core members transitively. **Event 1's** authenticated core
is the Step-0 core of `DECLARATION_CONTRACT.md` R12-FIX-2. The event count is
still **15**.

**Stage 4E-R12-R1 — event 1 token correction.** Event 1's "Known before" cell
already lists the agreed **token cap**, and that cap is inside the authenticated
Step-0 core. **Actual** token consumption is *not* an event-1 datum at all: it
does not exist before the first move. It is metered throughout play and reported
at **event 15** in the result JSON (`sub_games[].tokens`, `total_tokens`),
where it sits inside the **RESULT APPROVAL CORE** and is therefore covered by
`result_sha256` at **event 14**. *(Corrected Stage 4E-R12-R2: that covers the
integrity and mutual agreement of the **reported** totals; it does **not** by
itself satisfy Ch 5 §5.5's separate requirement that actual consumption be
monitored and cryptographically locked, which remains a mandatory runtime
obligation with a SOURCE-UNSPECIFIED, not-yet-frozen construction and touches no
timeline event.)* The former
`token_usage_locked` declaration field is removed; no event was added, removed or
renumbered, and timeline event 1's family is now implementation-ready.

**Stage 4E-R12-R3 — event 1 / event 2 token-cap chronology.** Event 1's "Known
before" cell has always listed the **token cap**, and event 2's has always listed
only "App F floors, board/scent/scoring". That committed reading is now stated as
law: **`token_budget_per_series` is agreed before `BOOT`**, so event 1 can
authenticate it and event 2 never negotiates it. Event 2 carries it inside the
complete proposed core for **equality only**; event 3 binds it again through
`config_sha256`. The cap's **Appendix-F status is unchanged — NEGOTIABLE** (App F
Table 18 #4); what R12-R3 fixes is its **project lifecycle**, not its source
provenance. No event was added, renumbered or re-scoped; the count is still **15**.
