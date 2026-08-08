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

## In progress
**Phase 2 — PRD and architecture — is fully complete.** **Phase 3 is under way:**
Stages 3A, 3B and 3C are closed, so the deterministic game-rule layer and the
**local** turn-execution step exist and are tested. A local action validates
through the domain, advances own truth atomically and consumes exactly one
step; it deliberately declares **no** terminal outcome, computes **no** score
and runs **no** scent lifecycle, because those need verified peer facts or a
completed full turn. **Not implemented:** the protocol state machine,
orchestrator, application ports, FastMCP, networking, cryptography, strategy,
belief, GUI, replay and reporting. PRD-01 and PRD-02 are both **IN PROGRESS**;
the next stage is tracked once, under Pending.
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
- [ ] **Stage 4A — Local Protocol State Machine Foundation** — **NEXT AUTHORIZED; NOT STARTED.** Planned: the frozen protocol/application state enum and legal transition machine; phase/cursor discipline; deterministic transition validation; terminal-state immutability; evidence/event outputs for later adapters; local effect execution connected only at the already-authorized transition boundary. **Not** in 4A: real FastMCP transport, public tunnel, commit-reveal cryptography or network I/O.
- [ ] Collaborator (Rawey7) access - pending explicit instruction.

_Phases 1 and 2 are specification and requirements only; all seven PRDs remain
APPROVED — PHASE 2 LOCKED. Phase 3 implementation has begun with the Stage-3A
domain foundation (grid config, coordinates, board geometry, move vocabulary,
movement legality). No JSON schema, protocol, networking, cryptography,
strategy, GUI or reporting code has been implemented._
