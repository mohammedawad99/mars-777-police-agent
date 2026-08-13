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
| 7 | **Reveal** | agent → opponent | move, hint | move + hint | **nonce** (still) | log | — | **at final audit only** — the receiver correlates the Reveal with the `H_commit` it already holds for that cursor; recomputation is impossible here and happens at event 12 |
| 8 | **Move validation** — *local legality decision + transport-level rejection outcome* | receiving peer decides **locally**; the outcome surfaces on the transport response | move legality, capture claim | **the accept/reject outcome of the operation that received the turn** — **not** a standalone semantic message (C-12); **response shape frozen at Stage 4E-R11** as a single `bool` game-legality result of the turn operation (`API_BOUNDARIES.md` O5) | — | log (separate validation record, event 9) | — | at audit |
| 9 | **Verdict (validation record)** | opponent/local | legality + capture-truth result | — *(local record; the peer-facing part is event 8's transport outcome)* | — | log (separate record) | — | — |
| 10 | **State transition** | both (state machine) | new positions/barriers | phase transition | opponent true pos (always) | — | — | — |
| 11 | **Final nonce reveal** | each → each | all nonces | **nonces** | (none) | log (final_reveal) | — | recompute all `H_commit` |
| 12 | **Final audit** — *audit-material exchange + local mutual audit* | each → each (material); then **each side locally** | full logs + nonces | **the audit material / full log each side must disclose so the opponent can recompute independently** (Ch 5 §5.4) — **not** a verdict: no `FinalAuditVerdict`, `expected_digest`, `recomputed_digest` or reason is transmitted (C-11) | — | log (`audit.result`, `entries[].verified`, `audit.tampered_step`) | recompute SHA-256 per step **locally** | Verified OK / TAMPERED — **local** Replay-Viewer/log verdict |
| 13 | **Result construction** | each team | per-sub-game scores, commit, tokens, four links | — | — | result | result-approval core (NDEC-006) | dual-report compare |
| 14 | **Mutual result agreement** | both → both | own contribution + all jointly known core values | **each peer's own `ResultContribution`** (six per-sub-game commit + token values); the operation's successful response is the receiver's locally computed `Sha256Digest` *(4E-R13-R1; the digest is **not** in the request — it does not exist jointly until the peer contribution arrives)* | — | result | `result_sha256` over the participant-scoped core | both directions complete with an equal digest |
| 15 | **Gmail reporting** | each team → lecturer | full **self-contained** result JSON (identities, four links, **FastMCP endpoints**, **signed hardware declarations + `hardware_auth`**, scores, commits, tokens; K3) | result JSON attachment | **key material** | (sent) | — | grader parse/attribution; **missing-from-either-side or contradictory ⇒ 0 to both (E-35, C-09)** |

**Reveal does not recompute `H_commit`, and cannot.** The "Later verified" column
means exactly that - *later*. At event 7 the receiver holds `H_commit` (event 5)
plus the disclosed `move` and `hint`, but the sealed record has **eight** members
and three of them are still secret: the `nonce` is withheld until event 11, and
`state` and `intent` arrive only with the audit material at event 12. A live
receiver therefore has nothing to hash. What it does at event 7 is **correlate**:
this Reveal belongs to the cursor whose commitment and acknowledgement it already
recorded, and it enforces ordering, phase, staleness, sender and game legality.

This is the source's design, not a gap. Ch 5 §5.3.2 / Figure 6 sequences Commit
(`H_commit` only) → Acknowledge (locked) → Reveal (move + hint, nonce still
hidden) → Final Reveal (all nonces, end of game), and the figure's own
explanation is that a move revealed at stage 3 which does not match the stage-1
commitment fails **the hash recomputed at the audit stage**. Ch 5 §5.4 then has
both sides disclose full logs and nonces, reconstruct the opponent's committed
data, recompute SHA-256 and compare. Deferring the check is what lets a peer
reveal inconsistent material during live play and still be caught: the proof is
cryptographic and arrives at audit, where INV-06 turns a mismatch into TAMPERED.

Consequently an ordinary Reveal never raises `E-HASH-MISMATCH`. Cursor, phase,
ordering, sender and malformed-message checks stay live and typed; game legality
returns `True`/`False`; commitment correspondence is an audit-stage verdict.


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

**Stage 4E-R13-R2 — event 14 deterministic ordering (event count still 15).**
Event 14 comprises **two operation calls, one per peer, in a fixed order** — it is
**not** a new event and no sixteenth event is needed:

1. the **timestamp proposer** — the participant whose `group_id` is **byte-wise
   lower**, which is a value comparison and **not** the `group_a`/`group_b` slot —
   sends its single `ResultAgreement` request carrying the proposed `timestamp`
   and its own `ResultContribution`;
2. the **non-proposer** adopts that timestamp **verbatim**, builds its local
   `RESULT_APPROVAL_CORE` (it now holds both contributions, the common timestamp
   and every other joint member) and returns its `Sha256Digest` as that
   operation's successful response;
3. the non-proposer then sends its **own single** request, echoing the identical
   timestamp and carrying its own `ResultContribution`;
4. the proposer verifies the echoed timestamp equals the one it proposed, builds
   the identical core, and returns its `Sha256Digest`;
5. each side sets `mutual_agreement` only after the frozen two-direction gate.

**No simultaneous timestamp race and no first-arrival winner** — the ordering is
application-protocol semantics, not a transport race. Transport retries re-send
the **same immutable** semantic request and are **not** additional semantic
requests.

### Stage 5-R8 — event 8 is a turn **outcome**, not a legality bool

Event 8's response is `TurnOutcome(accepted, capture)` (`API_BOUNDARIES.md` O5 as
amended, **C-13**, **JDEC-016**). `accepted` reports only what the receiver can
check live — the mover's pre-action cell is sealed, so remote spatial legality is
**not knowable** at this point and is proved at the final audit instead. `capture`
carries the source-required answer (`NO_QUESTION` / `NOT_CAUGHT` / `CAUGHT`),
computed by the receiver from its **own** position and public facts, so no
position is ever transmitted. A declared capture ends ordinary play for that
sub-game however it is answered.

### Stage 5-R8 — event 9 is a **replay**, and it happens after event 12

Event 9 (the validation record) was always local, and it was always deferred:
legality that depends on a sealed cell, and the truth of a capture declaration,
are simply not decidable while the sub-game is being played. They are decided
once, at the end, in this order:

1. **Final nonce reveal** (event 12) — both sides release their nonces.
2. **Audit disclosure** — each side sends its own log core **plus** its own
   capture transcript.
3. **Transcript cross-check** — the received transcript must be, row for row,
   the one this side actually observed.
4. **Commitment recomputation** — the existing R7 SHA-256 pass.
5. **Semantic replay** — both trajectories reconstructed from the config-locked
   start cells, every action re-judged by the domain rules, the public barrier
   chronology rebuilt, and every capture answer recomputed against the cell its
   answerer disclosed.
6. **Sanction** — a false declaration ends the sub-game as a technical loss;
   any forgery is `TAMPERED` and blocks result agreement.

Nothing in this sequence adds a message: steps 3-6 all read material events 12
and O6 already carry.
