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
- [x] Stage 1D.1 - cryptographic & reporting contract corrections (spec-only, no code/commit): **K1** Step-0 = **keyed** authentication with a pre-supplied key (HMAC-SHA256 default, JDEC-013; not a bare hash); **K2** config **signature exchange** beyond `config_sha256` (NDEC-007); **K3** result self-contained — FastMCP endpoints + signed hardware declarations mandatory *(**superseded by Stage 2A-R2/JDEC-014**)*; **K4** reporting-sanction conflict Ch 9 vs E-35 documented as **C-09** (strictest 0-both adopted); **K5** `game_uid` kept; **K6** `verdict`=`intent` (C-08) kept. NDEC-001…007, JDEC-001…013, INV-01…15 *(registers at that stage; **current JDEC-001…014**)*. **No key material anywhere.**

- [x] Stage 1C/1D/1D.1 - **supervising review PASS**; Stage-1 specification/JSON-contract baseline **REVIEWED / APPROVED / LOCKED**.
- [x] Stage 1-CLOSE - row-exact field matrix (**then** 77) + 26-point audit; reviewed baseline committed (`9fdbe3c`) + pushed; CI green (Ubuntu + Windows). *(Current matrix is **75** after Stage 2A-R2/JDEC-014.)*
- [x] Stage 1-CLOSE.1 - status-only relabel of the committed docs to reviewed/locked (this commit).

- [x] Stage 2A - architecture freeze: 21 architecture docs + 7 PRD blueprints; 91/91 requirements architecture-mapped; red-team blocking findings resolved.
- [x] Stage 2A-R - read-only lecturer reference audit (`rmisegal/Game-P2P-Cop-Chase` @ `960499fd`); reference classified NON-BINDING; book wins on keyed Step-0 auth.
- [x] Stage 2A-R2 - attachment/chatbot reconciliation (AE-01…AE-04, secondary provenance); compatibility profiles; **JDEC-014** result→declaration reference; field matrix **77 → 75** (result 13 → 11). Zero chatbot questions pending.

## In progress
- [x] Stage 2B - PRD-01…04 authored in full (reviewed).
- [x] Stage 2C - PRD-05…07 authored in full (reviewed); 91/91 requirements have one primary owner.
- [x] Stage 2-CLOSE - **PASS**; CLOSE-F1 + CLOSE-F2 resolved with **no artifact-contract change** (matrix stays 75); **all 7 PRDs APPROVED — PHASE 2 LOCKED**; implementation NOT STARTED.

## In progress
- [ ] Supervising review of the Phase-2 closure commit; then **Phase 3 — Deterministic Core Implementation**.

## Pending
- [ ] Branch protection / rulesets - **blocked**: unavailable on the current GitHub
      plan for private repos (Stage 0D). Needs Pro upgrade, org, or public-at-submission.
- [x] Full 160-page source extraction - done (Stage 1A: `docs/spec/`).
- [x] JSON contract construction - done and reviewed (Stage 1C/1D/1D.1; `docs/spec/json/`).
- [ ] Example-simulator (Appendix D) review - non-binding; pending.
- [x] Stage 1B - independent cross-audit of the extraction - done (supervising review PASS).
- [ ] **Next authorized step:** controlled synchronization of the reviewed COMMON specification baseline to the thief repo (not started; must be reviewed before PRD/architecture).
- [ ] PRD-01 game logic (Base Logic; board/movement/barriers/capture/scoring).
- [ ] PRD-02 local FastMCP (MCP infra + orchestrator/state-machine).
- [ ] PRD-03 baseline / blind strategy.
- [ ] PRD-04 language & scent.
- [ ] PRD-05 public network / tunnel / league.
- [ ] PRD-06 security & cryptography (commit-reveal, Step-0).
- [ ] PRD-07 reporting, GUI, replay (Gmail gatekeeper, Live GUI, Replay Viewer).
- [ ] Collaborator (Rawey7) access - pending explicit instruction.

_No game logic, JSON schema, or protocol code has been implemented. Stage 1A is
specification-only._
