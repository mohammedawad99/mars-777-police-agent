# State Machine — group MaRs-777

**Status: STAGE 2A ARCHITECTURE FREEZE — design only.**

Owner: `app.state_machine`. It is the **sole** authority on what may happen next.
The orchestrator asks; it never assumes. Aligned with the locked protocol timeline
(`../spec/json/PROTOCOL_TIMELINE.md`, events 1–15).

## 1. States

```
BOOT → STEP0_NEGOTIATION → CONFIG_NEGOTIATION → CONFIG_LOCKED → READY
                                                                  │
        ┌─────────────────────── per turn ───────────────────────┐│
        ▼                                                        ││
  TURN_DECISION → COMMIT_SENT → ACKNOWLEDGED → REVEAL → VALIDATING → TURN_COMPLETE
        ▲                                                              │
        └──────────────────── next turn ───────────────────────────────┘
                                                                       ▼
                                          SUBGAME_COMPLETE → (next sub-game → READY)
                                                     │
                                                     ▼
                                          SERIES_COMPLETE → FINAL_AUDIT → REPORT_READY

 terminal / fault: FAILED · TAMPERED (absorbing) · TECHNICAL_LOSS → SUBGAME_COMPLETE
```

## 2. State table

| State | Entry condition | Allowed inputs/events | Outputs/actions | Deadline | Allowed next | Forbidden | Evidence | Recovery |
|---|---|---|---|---|---|---|---|---|
| **BOOT** | process start | settings loaded, key present | build composition root; start MCP server | process start-up budget | STEP0_NEGOTIATION, FAILED | any game move | boot record | abort cleanly |
| **STEP0_NEGOTIATION** | server reachable | own Step-0 built; peer Step-0 received | assemble declaration; compute + exchange `step0_auth` keyed tag; verify peer tag | negotiation window | CONFIG_NEGOTIATION, FAILED | playing counted turns | `declaration_<game_id>.json` | **refuse counted play** if no compatible key/mechanism (INV-14) |
| **CONFIG_NEGOTIATION** | Step-0 authenticated both ways | proposed values within Appendix F status rules | agree MINIMUM/NEGOTIABLE values; never alter FIXED | negotiation window | CONFIG_LOCKED, FAILED | lowering a MINIMUM; changing FIXED | negotiation record | refuse play on mismatch |
| **CONFIG_LOCKED** | `config_sha256` equal **and** config auth tag verified | lock event | freeze config; publish immutable handle | — | READY, FAILED | any config write | `config_<game_id>_g<NN>.json` + hash/tag | refuse play (INV-15) |
| **READY** | config locked, sub-game initialized | start turn | initialize truth/scent/barriers for the sub-game | — | TURN_DECISION, SUBGAME_COMPLETE | reveal, commit | sub-game start record | — |
| **TURN_DECISION** | our turn | `Observation` built | strategy proposes; **validator accepts/rejects**; draw nonce; build sealed record | step deadline (from locked config; App F default 30 s, **NEGOTIABLE**) | COMMIT_SENT, FAILED | sending before validation | decision metrics | deterministic fallback action |
| **COMMIT_SENT** | `H_commit` computed & sent | peer ack | await acknowledgement | response timeout (`response_timeout_sec`; default 30 s, **NEGOTIABLE**) | ACKNOWLEDGED, FAILED, TECHNICAL_LOSS | revealing the nonce | commit log entry | retry per Gatekeeper; then escalate |
| **ACKNOWLEDGED** | peer ack received & matched to step | reveal trigger | prepare reveal (move + hint; **nonce withheld**) | step deadline | REVEAL, FAILED | early nonce release | ack log entry | — |
| **REVEAL** | ack matched | reveal exchanged | send own reveal; receive peer reveal | response timeout | VALIDATING, FAILED, TECHNICAL_LOSS | applying effects pre-validation | reveal log entry | — |
| **VALIDATING** | both reveals present | legality + capture + hash checks | deterministic validation of the opponent's revealed action | step deadline | TURN_COMPLETE, TAMPERED, TECHNICAL_LOSS | LLM-based legality | validation record | mismatch ⇒ TAMPERED |
| **TURN_COMPLETE** | validation passed | apply effects | update truth/barriers/scent/belief; advance step | — | TURN_DECISION, SUBGAME_COMPLETE | mutating a past turn | turn record | — |
| **SUBGAME_COMPLETE** | capture / survival threshold / max_moves / technical loss | outcome computed | compute score (App F + C-07); seal sub-game log | — | READY (next), SERIES_COMPLETE | changing a sealed score | sealed log + score | — |
| **SERIES_COMPLETE** | all sub-games played (`num_games`=6 FIXED) | series totals | compute cumulative | — | FINAL_AUDIT | reporting before audit | cumulative record | — |
| **FINAL_AUDIT** | series complete | all nonces released; replay run | recompute every `H_commit`; verify | audit window | REPORT_READY, TAMPERED | selective disclosure | audit result | any mismatch ⇒ TAMPERED |
| **REPORT_READY** | audit verified | build + agree result | assemble self-contained result; exchange `result_sha256`; send JSON e-mail | reporting window | (terminal) | mutating game state | `result_<game_id>.json` | mismatch/missing ⇒ 0 both (C-09) |
| **FAILED** | unrecoverable local/transport fault | — | halt, preserve evidence | — | (terminal) | continuing counted play | failure record | operator review |
| **TAMPERED** | any recompute mismatch | — | halt; mark match void | — | (terminal) | appeal | tamper evidence | **no appeal — SOURCE-CITED: PDF p.75 "אין ערעור ואין תיקון בדיעבד" (no appeal, no retroactive correction); REPLAY-002** |
| **TECHNICAL_LOSS** | protocol/timeout condition per spec | — | record technical loss 0/0 (C-07) | — | SUBGAME_COMPLETE *(ends this sub-game only — see §4)* | inventing other sanctions; returning to a turn phase | technical-loss record | proceed per series rules |

## 3. Transition rules

- **R1 — no skipping.** `COMMIT_SENT` cannot reach `REVEAL` without `ACKNOWLEDGED`.
- **R2 — no early nonce.** No transition releases a nonce before `FINAL_AUDIT`.
- **R3 — no counted play before lock.** No turn state is reachable unless both
  `STEP0_NEGOTIATION` (keyed auth verified) and `CONFIG_LOCKED` succeeded.
- **R4 — validation precedes effect.** Effects apply only on `VALIDATING → TURN_COMPLETE`.
- **R5 — terminal is terminal.** `TAMPERED` and `FAILED` never return to play.
- **R6 — one turn at a time.** The machine is single-threaded per sub-game
  (`CONCURRENCY_MODEL.md`); a second inbound turn event is rejected as out-of-order.
- **R7 — replayable.** Every transition emits an evidence record sufficient for replay.
- **R8 — idempotent inbound.** A duplicate/stale peer message for an already-completed
  step is rejected, not re-applied (see `ERROR_MODEL.md` `E-PROTO-STALE`).

## 4. Stage 4A-FIX1 correction — TECHNICAL_LOSS lifecycle

**Implementation-discovered architecture correction, not a new lecturer rule and
not a source change.** Recorded post-lock; every other state and edge in §1–§3 is
unchanged.

The original TECHNICAL_LOSS row gave "Allowed next = (terminal for that
sub-game)" — naming no successor — which made the phase absorbing for the whole
machine. That contradicted three statements in this same file:

1. **SUBGAME_COMPLETE's entry condition** already reads
   "capture / survival threshold / max_moves / **technical loss**", so the
   sub-game boundary is meant to be entered on a technical loss;
2. **TECHNICAL_LOSS's own Recovery** column says "**proceed per series rules**",
   which an absorbing phase makes impossible; and
3. **R5** names only **TAMPERED and FAILED** as never returning to play —
   TECHNICAL_LOSS is deliberately excluded.

Primary source agrees: Ch 3 §3.5 Table 2 (PDF p.38) lists `הפסד טכני` (technical
loss, 0/0) as one of the three **sub-game** end events beside capture and
survival, and App E #48 scores all three the same way. A counted series is
`num_games` = 6 FIXED sub-games, so an ordinary technical loss ends the current
sub-game, not the series.

**Correction:** `TECHNICAL_LOSS → SUBGAME_COMPLETE`, and only that edge. It
routes through the existing sub-game boundary, which then branches to READY for
the next sub-game or to SERIES_COMPLETE — no direct `TECHNICAL_LOSS → READY` or
`TECHNICAL_LOSS → SERIES_COMPLETE` edge is created, and no recovery into a turn
phase is allowed.

**Unchanged:** TAMPERED remains absorbing ("halt; mark match void"; no appeal,
PDF p.75) and FAILED remains absorbing. The stronger TAMPERED sanction is **not**
transferred to ordinary technical loss, and the two are not merged. The state
inventory stays at 18; the graph now has 31 directed edges.

**Bootstrap:** normal construction begins at **BOOT** (`ProtocolMachine.start()`);
constructing a machine directly at an arbitrary phase is a trusted snapshot
primitive, never the untrusted runtime path.
