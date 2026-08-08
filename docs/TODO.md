# TODO - group MaRs-777 (POLICE)

> **Status: DRAFT.**
> **Purpose:** Track outstanding foundation and project tasks.
> **Authoritative source:** book v3.0.0.
> **Note:** No requirement is approved merely because this file exists.

## Done
- [x] Stage 0A - environment / tooling / Git / GitHub preflight audit.
- [x] Stage 0B - local repository foundation.
- [x] Stage 0B.1 - final evidence audit (exact future-commit validation).
- [x] Stage 0C - private GitHub repository created; initial commit pushed over SSH.
- [x] Stage 0C - CI green on ubuntu-latest + windows-latest (all 4 matrix jobs).
- [x] Stage 0D - repository protection assessed (see below).
- [x] Stage 1A - full 160-page source extraction into `docs/spec/` (reviewed; approved via Stage 1B).
- [x] Stage 1B - independent cross-audit + corrections (App F 32 rows / 14-9-9; technical_loss provenance; num_games closed; exact modality counts). See `docs/spec/STAGE_1B_CROSS_AUDIT.md`.

- [x] Stage 1B supervising review = **PASS**; corrected specification baseline approved as input to Stage 1C.
- [x] Stage 1B-CLOSE - reviewed specification baseline committed + pushed (CI green Ubuntu+Windows).
- [x] Stage 1C - four JSON **contracts** defined in `docs/spec/json/` (specification only; no schema/code).
- [x] Stage 1D - independent contract audit + interoperability lock (verdict=intent, state PROJECT-LOCKED, config_sha256 non-self-ref, game_uid SOURCE, NDEC-001…006; 0 blocking). See `docs/spec/json/STAGE_1D_AUDIT.md`.
- [x] Stage 1D.1 - cryptographic & reporting contract corrections (spec-only, no code/commit): **K1** Step-0 = **keyed** authentication with a pre-supplied key (HMAC-SHA256 default, JDEC-013; not a bare hash); **K2** config **signature exchange** beyond `config_sha256` (NDEC-007); **K3** result self-contained — FastMCP endpoints + signed hardware declarations mandatory *(**superseded by Stage 2A-R2/JDEC-014**)*; **K4** reporting-sanction conflict Ch 9 vs E-35 documented as **C-09** (strictest 0-both adopted); **K5** `game_uid` kept; **K6** `verdict`=`intent` (C-08) kept. NDEC-001…007, JDEC-001…013, INV-01…15 *(registers at that stage; **current JDEC-001…015**)*. **No key material anywhere.**

- [x] Stage 1C/1D/1D.1 - **supervising review PASS**; Stage-1 specification/JSON-contract baseline **REVIEWED / APPROVED / LOCKED**.
- [x] Stage 1-CLOSE - row-exact field matrix (**then** 77) + 26-point audit; reviewed baseline committed (`9fdbe3c`) + pushed; CI green (Ubuntu + Windows). *(Current matrix is **75** after Stage 2A-R2/JDEC-014.)*
- [x] Stage 1-CLOSE.1 - status-only relabel of the committed docs to reviewed/locked (`691280d`).
- [x] Stage 1-SYNC - reviewed COMMON Stage-1 specification baseline synchronized (read-only) to the thief repo; **COMPLETE**.
- [x] Stage 1-SYNC-CLOSE - repository-metadata repair (requirement count 79 → **91**; remote HTTPS → **SSH**) committed + pushed in both repos (`7563e09`); CI green.

- [x] Stage 2A - architecture freeze: 21 architecture docs + 7 PRD blueprints; 91/91 requirements architecture-mapped; red-team blocking findings resolved.
- [x] Stage 2A-R - read-only lecturer reference audit (`rmisegal/Game-P2P-Cop-Chase` @ `960499fd`); reference classified NON-BINDING; book wins on keyed Step-0 auth.
- [x] Stage 2A-R2 - attachment/chatbot reconciliation (AE-01…AE-04, secondary provenance); compatibility profiles; **JDEC-014** result→declaration reference; field matrix **77 → 75** (result 13 → 11). Zero chatbot questions pending.
- [x] Stage 2A-CLOSE - stale-baseline sweep + `result_sha256` audit; architecture/compatibility baseline committed + pushed (`68a9569`); CI green (Ubuntu + Windows). **Phase 2 architecture: COMPLETE.**
- [x] Stage 2B - PRD-01…04 authored in full (reviewed).
- [x] Stage 2C - PRD-05…07 authored in full (reviewed); 91/91 requirements have exactly one primary owner.
- [x] Stage 2-CLOSE - **PASS**; CLOSE-F1 + CLOSE-F2 resolved with **no artifact-contract change** (matrix stays **75**); **all 7 PRDs APPROVED — PHASE 2 LOCKED**; implementation **NOT STARTED**. Committed + pushed (`14dafed`); CI green.
- [x] Stage 2-CLOSE.1 - tracking-status repair of this file (duplicate heading + stale Pending entries); no specification, architecture, PRD, or contract change.
- [x] Stage 2-CLOSE.2 - tracking-status deduplication of this file (the next-phase entry is recorded exactly once, under Pending only); no specification, architecture, PRD, or contract change.

### Phase 3 — Deterministic Core Implementation (started)
- [x] Stage 3A - deterministic domain **foundation** (tests-first): immutable `GridConfig` (project grid minimum enforced here), immutable `Position`, immutable policy-free `Board` geometry with blocked cells, `Move` = N/S/E/W/STAY, stable `MOVE_ORDER`, destination calculation, bounds/blocked legality, deterministic `legal_moves`, typed `apply_move` failure. Role-neutral, no opponent truth, no I/O. **Supervising review PASS.**
- [x] Stage 3A-CLOSE - final audits, narrow tracking update, commit + push + CI.
- [x] Stage 3B - deterministic **game semantics** (tests-first): barrier placement, the three capture routes, terminal/survival evaluation, role-keyed scoring and bounded scent physics. **Supervising review PASS.**
- [x] Stage 3B-FIX1 - supervising correction: **JDEC-015** terminal threshold admissibility (`survival_threshold <= max_moves`) + radial scent-kernel contract hardened; `UnspecifiedTerminalError` removed.
- [x] Stage 3B-FIX2 - supervising ruling: **C-10** scent state bound vs additive update resolved as the saturating recurrence `min(0.9, max(0, (1-rho)*tau + delta))`.
- [x] Stage 3B-CLOSE - final audits, tracking finalization, commit + push + CI.
- [x] Stage 3C - local application / turn orchestration **foundation** (tests-first): `LocalTruth` (board, own position, completed steps), typed `MoveAction`/`BarrierAction`, role-specific `LocalTurnService` (police move **or** barrier; thief move only), atomic local effect application, local step accounting and max-moves exhaustion. **Supervising review PASS.**
- [x] Stage 3C-FIX1 - state-ownership correction: removed the duplicated `barriers_placed` counter from `LocalTruth`; barrier usage now has **one** authoritative representation (the public board plus the validated `BarrierQuota`), so no local count can drift.
- [x] Stage 3C-CLOSE - final audits, PRD-02 status alignment, commit + push + CI.

### Phase 4 — Protocol Foundation (started)
- [x] Stage 4A - local protocol **state machine** foundation (tests-first): the frozen 18-phase graph (15 normal + 3 fault) with **31** legal directed edges, exhaustively verified over all 324 ordered pairs; `ProtocolMachine` owns **only** the current phase; normal bootstrap via `ProtocolMachine.start()` at BOOT. **Supervising review PASS.**
- [x] Stage 4A-FIX1 - **TECHNICAL_LOSS lifecycle correction**: the frozen table made "technical loss" an entry condition of SUBGAME_COMPLETE and told the phase to "proceed per series rules", while R5 names only TAMPERED and FAILED as never returning to play - yet it listed no successor. One edge added, `TECHNICAL_LOSS -> SUBGAME_COMPLETE`, recorded in `STATE_MACHINE.md` §4 as an implementation-discovered architecture correction. TAMPERED and FAILED stay absorbing.
- [x] Stage 4A-CLOSE - final graph/ownership audit, bootstrap guard, tracking, commit + push + CI.
- [x] Stage 4B - protocol event / **transition evidence** foundation (tests-first): every successful `advance()` now returns one immutable `TransitionResult` carrying a `TransitionEvidence` of exactly `source_phase` + `target_phase`, per R7 and `PROTOCOL_TIMELINE.md` event 10 (transmitted "phase transition", persisted "—", hashed "—"). No transition-signal vocabulary is frozen anywhere, so **no event enum was invented**; there is no evidence-less transition path and no compatibility shim. **Supervising review PASS.**
- [x] Stage 4B-FIX1 - supervising corrections: (a) `TransitionEvidence` is now **valid by construction** - the pair must be an edge of the single `_ALLOWED` graph, so a record of a step R1/R5 forbid (e.g. `COMMIT_SENT -> REVEAL`, `TAMPERED -> SUBGAME_COMPLETE`) cannot be built; 31 legal pairs constructible, 293 illegal pairs and all 18 self-loops rejected. The replay corruption boundary moved forward to the constructor and negative replay coverage was **extended** (duplicated record, out-of-position record) rather than weakened. (b) A reported "153-line" file was reconciled as a **cross-repo semantic-diff count**, not physical LOC; the repository-wide audit proves max **150** and **0** files over the limit.
- [x] Stage 4B-CLOSE - final evidence/graph invariant audit, repository-wide LOC proof, tracking finalization, commit + push + CI.
- [x] Stage 4C - local **orchestrator / protocol guard** foundation (tests-first): `LocalOrchestrator` composes the `ProtocolMachine` and owns the one live fact `STATE_OWNERSHIP.md` assigns it - the **current sub-game index** - plus a read-only `SeriesConfig` projection. It delegates every phase question to `ProtocolMachine.advance()`, passes the emitted evidence through unchanged, and decides exactly one branch itself (`SUBGAME_COMPLETE -> READY / SERIES_COMPLETE`) because the cursor truthfully determines it - no `more_subgames` boolean is accepted. Ownership conflicts resolved without touching frozen architecture: `MODULE_BOUNDARIES.md`'s "turn cursor" yields to `STATE_OWNERSHIP.md` (the D17 precedent), and role alternation stays a PRD-05/`SeriesLauncher` convention (PRD02-FR-011), never derived from odd/even index. **Supervising review PASS.**
- [x] Stage 4C-FIX1 - supervising correction: the counted series is **`num_games` = 6, FIXED**, not a floor. Stage 4C had implemented `>= 6` after following stale wording in `CONFIG_CONTRACT.md` and the C-05 impact cell ("6 or the agreed higher"); Appendix F defines FIXED as "binding, unchangeable; **deviation disqualifies**" and names `num_games` in its FIXED-14 list, so 7 is as illegal as 5. The error was caught **before commit**: `MIN_NUM_GAMES` became `FIXED_NUM_GAMES`, `SeriesConfig` now requires exact equality, and the two stale sentences were corrected to match the already-locked App F / C-05 semantics - no new JDEC, conflict, requirement or register entry. The bootstrap audit confirmed `start()` is the only runtime path and no production caller constructs a `LocalOrchestrator` directly.
- [x] Stage 4C-CLOSE - final FIXED-series/cursor/ownership audit, duplicate-literal and bootstrap audit, package-surface alignment, tracking finalization, commit + push + CI.
- [ ] Stage 4D - application **port contracts** foundation - **ATTEMPTED, BLOCKED BEFORE CODE** (`PORT-DEPENDENCY-BLOCKER`). Zero repository changes were made. Three internal contradictions prevented a truthful implementation: `API_BOUNDARIES.md` fixes **no Python signatures** (confirmed by a repository-wide search finding no `def`, `Protocol` or return annotation in any architecture or PRD document); the `app.ports` row allowed **stdlib typing only** while the same architecture defines ports over `Board`/`Move`/`Outcome`/`ScoreLine`; and `PLAN.md` still claimed 18 ports where the frozen inventory is 20. No signature, payload type or method name was guessed.
- [x] Stage 4D-R1 - application port **architecture reconciliation** (documentation only): `app.ports` may now reference immutable `domain` value types and nothing else outward; `API_BOUNDARIES.md` records that any future Python signature is **PROJECT-CONTRACT** (never source- or reference-mandated) and that a port row is not an automatic Protocol mandate; the port count is corrected to **20**. See **D21**. No requirement, PRD, register or Appendix-F value changed. **CLOSED** at Stage 4D-R1-CLOSE (committed + pushed; CI green Ubuntu + Windows).

## In progress
**Phase 2 — PRD and architecture — is fully complete.** **Phases 3 and 4 are under
way:** the deterministic game-rule layer (3A/3B), the local turn-execution step
(3C), the local protocol phase machine (4A), its transition evidence (4B) and
the local series orchestrator (4C) exist and are tested. The phase machine
enforces order only — the phases named COMMIT_SENT, ACKNOWLEDGED, REVEAL and
FINAL_AUDIT carry no cryptography, message bodies or transport, and the machine
never applies a local effect. Transition evidence is **structurally valid, not
authenticated**: it supports ordered **phase-path** replay only, never
game-state, movement, barrier, score, scent, commitment, nonce, network-message,
official-artifact or complete-game replay. The orchestrator implements its
**cursor/guard slice only** — a counted series is exactly 6 sub-games, the
cursor advances exactly five times and no seventh sub-game is representable.
**Recording the per-sub-game and cumulative score is also `app.orchestrator`
state per `STATE_OWNERSHIP.md`, and remains pending** a later stage, because it
needs truthful terminal facts that do not exist yet. **Not implemented:** score
recording, turn-service integration, application ports, FastMCP, networking,
cryptography, logger/replay persistence, JSON artifacts, strategy, belief, GUI
and reporting. PRD-01 and PRD-02 remain **IN PROGRESS**; the next stage is
tracked once, under Pending.
## Pending
- [ ] Branch protection / rulesets - **blocked**: unavailable on the current GitHub
      plan for private repos (Stage 0D). Needs Pro upgrade, org, or public-at-submission.
- [x] Full 160-page source extraction - done (Stage 1A: `docs/spec/`).
- [x] JSON contract construction - done and reviewed (Stage 1C/1D/1D.1; `docs/spec/json/`).
- [ ] Example-simulator (Appendix D) review - non-binding; pending.
- [x] Stage 1B - independent cross-audit of the extraction - done (supervising review PASS).
- [x] Controlled synchronization of the reviewed COMMON specification baseline to the thief repo - **COMPLETE** (Stage 1-SYNC / 1-SYNC-CLOSE).
- [x] PRD-01 game logic (Base Logic; board/movement/barriers/capture/scoring) - **LOCKED as requirements; implementation IN PROGRESS** (Stage 3A foundation only; barriers, capture, terminal/survival, scoring and scent still pending).
- [x] PRD-02 local FastMCP (MCP infra + orchestrator/state-machine) - **LOCKED as requirements; implementation IN PROGRESS** (Stage 3C local turn foundation only; state machine, orchestrator, ports, FastMCP, Gatekeeper and runtime composition still pending).
- [x] PRD-03 baseline / blind strategy (**POLICE** role-specific) - **LOCKED as requirements; NOT IMPLEMENTED.**
- [x] PRD-04 language & scent - **LOCKED as requirements; NOT IMPLEMENTED.**
- [x] PRD-05 public network / tunnel / league - **LOCKED as requirements; NOT IMPLEMENTED.**
- [x] PRD-06 security & cryptography (commit-reveal, Step-0) - **LOCKED as requirements; NOT IMPLEMENTED.**
- [x] PRD-07 reporting, GUI, replay (Gmail gatekeeper, Live GUI, Replay Viewer) - **LOCKED as requirements; NOT IMPLEMENTED.**
- [x] **Phase 3 — Deterministic Core Implementation** — **STARTED** (Stage 3A closed; the phase itself is **not** complete).
- [x] **Stage 3B — Deterministic Game Semantics** — **CLOSED** (barriers, capture, terminal/survival, scoring, bounded scent physics).
- [x] **Stage 3C — Local Application / Turn Orchestration Foundation** — **CLOSED.**
- [x] **Stage 4A — Local Protocol State Machine Foundation** — **CLOSED.**
- [x] **Stage 4B — Protocol Event / Transition Evidence Foundation** — **CLOSED** (deterministic per-transition evidence, valid by construction against the single frozen graph; phase-path replay only). No event enum was invented: no transition-signal vocabulary is frozen in any source or architecture document.
- [x] **Stage 4C — Local Orchestrator / Protocol Guard Foundation** — **CLOSED** (sub-game cursor, the one cursor-owned branch, evidence pass-through; `num_games` = 6 FIXED). Its **score-recording** half remains open below.
- [ ] **Orchestrator score recording** — **NOT STARTED; blocked on truthful terminal facts.** `STATE_OWNERSHIP.md` assigns the recorded per-sub-game and cumulative score to `app.orchestrator` (computed by `domain.scoring`, anti-duplication rule 3). Stage 4C deliberately did not implement it: the input is a sub-game `Outcome`, which needs verified public facts the local agent does not yet have.
- [ ] **Stage 4E — Protocol Semantic Message Contracts Foundation** — **NEXT AUTHORIZED; NOT STARTED** (selected at Stage 4D-R1-CLOSE). It removes the highest-value PRD-02 blocker: `PeerTransportPort` and `PeerServerPort` both accept a "protocol message" that has no type yet, and their semantics are already frozen — `PROTOCOL_TIMELINE.md` fixes the transmitted content of the peer-visible events (Step-0 declaration + `step0_auth`, config proposal, `config_sha256` + `config_auth`, `H_commit`, acknowledgement, reveal = move + hint, final nonces, audit verdicts, `result_sha256` + agreement) and PRD02-FR-044 fixes the `(sub_game, step, phase)` envelope carried by every inbound message. Scope would be **typed internal semantic messages only** — no FastMCP wire schema, no tool names, no transport, no cryptography — and requires separate supervising authorization. Stage 4E will **audit** the nine currently identified peer-visible semantic families — Step-0 declaration exchange, config negotiation, config lock, commitment, acknowledgement, reveal, final nonce reveal, final audit, mutual result agreement — plus the shared `(sub_game, step, phase)` inbound envelope, and **mechanically determine the minimal type model**; nine families do **not** presuppose nine Python classes. Explicitly **not** in 4E: FastMCP wire schema or tools, concrete tool names, transport, server/client, tunnel, retry, Gatekeeper, cryptographic computation, canonical JSON, official artifact persistence.
- [ ] Collaborator (Rawey7) access - pending explicit instruction.

_Phases 1 and 2 are specification and requirements only; all seven PRDs remain
APPROVED — PHASE 2 LOCKED. Phase 3 implementation has begun with the Stage-3A
domain foundation (grid config, coordinates, board geometry, move vocabulary,
movement legality). No JSON schema, protocol, networking, cryptography,
strategy, GUI or reporting code has been implemented._
